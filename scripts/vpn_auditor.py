#!/usr/bin/env python3
"""Automatic VPN/proxy auditor for the vpn-auditor Codex skill.

The script intentionally avoids destructive tests and external Python
dependencies. It is macOS-oriented but degrades gracefully on other systems.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import ipaddress
import json
import math
import os
import platform
import re
import socket
import ssl
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable


USER_AGENT = "vpn-auditor/1.0"
DEFAULT_TIMEOUT = 6.0
PRIVATE_OK_DNS_RANGES = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("198.18.0.0/15"),
)


@dataclasses.dataclass
class FetchResult:
    name: str
    url: str
    ok: bool
    elapsed_ms: int | None = None
    status: int | None = None
    text: str = ""
    error: str = ""


@dataclasses.dataclass
class TargetResult:
    name: str
    url: str
    ok: bool
    elapsed_ms: int | None
    status: int | None
    error: str = ""


@dataclasses.dataclass
class ScoreItem:
    category: str
    name: str
    score: float
    max_score: float
    note: str


def run_cmd(args: list[str], timeout: float = 4.0) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout: {' '.join(args)}"


def fetch_url(
    name: str,
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    method: str = "GET",
    data: bytes | None = None,
) -> FetchResult:
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"User-Agent": USER_AGENT},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            body = response.read(1024 * 1024)
            elapsed = int((time.perf_counter() - start) * 1000)
            return FetchResult(
                name=name,
                url=url,
                ok=True,
                elapsed_ms=elapsed,
                status=getattr(response, "status", None),
                text=body.decode("utf-8", errors="replace"),
            )
    except urllib.error.HTTPError as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return FetchResult(name, url, False, elapsed, exc.code, "", f"HTTP {exc.code}")
    except Exception as exc:  # Network failures should become report evidence.
        elapsed = int((time.perf_counter() - start) * 1000)
        return FetchResult(name, url, False, elapsed, None, "", str(exc))


def first_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_ip(text: str) -> str | None:
    data = first_json(text)
    for key in ("ip", "query", "IPAddress"):
        value = data.get(key)
        if isinstance(value, str) and is_ip(value):
            return value
    match = re.search(r"(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w:])", text)
    if match and is_ip(match.group(0)):
        return match.group(0)
    match = re.search(r"(?<![\w:])(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F:]{2,}(?![\w:])", text)
    if match and is_ip(match.group(0)):
        return match.group(0)
    return None


def is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_private_or_local(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        return False


def is_local_dns(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    if any(ip in network for network in PRIVATE_OK_DNS_RANGES):
        return False
    return ip.is_private or ip.is_link_local or ip.is_site_local


def parse_scutil_proxy(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"\s*([A-Za-z0-9_]+)\s*:\s*(.+?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2)
    return values


def parse_dns_sections(text: str) -> dict[str, list[str]]:
    default_servers: list[str] = []
    scoped_servers: list[str] = []
    scoped = False
    for line in text.splitlines():
        if line.startswith("DNS configuration (for scoped queries)"):
            scoped = True
            continue
        match = re.search(r"nameserver\[[0-9]+\]\s*:\s*(\S+)", line)
        if match and is_ip(match.group(1)):
            if scoped:
                scoped_servers.append(match.group(1))
            else:
                default_servers.append(match.group(1))
    return {
        "default": dedupe(default_servers),
        "scoped": dedupe(scoped_servers),
        "all": dedupe(default_servers + scoped_servers),
    }


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def collect_interfaces(ifconfig_text: str) -> dict[str, Any]:
    interfaces: list[str] = []
    tunnel_interfaces: list[str] = []
    inet4: list[str] = []
    inet6_global: list[str] = []
    current = ""
    for line in ifconfig_text.splitlines():
        if line and not line.startswith("\t") and not line.startswith(" "):
            current = line.split(":", 1)[0]
            interfaces.append(current)
            if re.search(r"^(utun|tun|tap|wg|ppp|ipsec)", current):
                tunnel_interfaces.append(current)
            continue
        stripped = line.strip()
        match4 = re.match(r"inet\s+(\S+)", stripped)
        if match4 and is_ip(match4.group(1)):
            inet4.append(match4.group(1))
        match6 = re.match(r"inet6\s+(\S+)", stripped)
        if match6:
            raw = match6.group(1).split("%", 1)[0]
            if is_ip(raw):
                ip = ipaddress.ip_address(raw)
                if ip.version == 6 and not (ip.is_link_local or ip.is_loopback):
                    inet6_global.append(raw)
    return {
        "interfaces": interfaces,
        "tunnel_interfaces": dedupe(tunnel_interfaces),
        "local_ipv4": dedupe(inet4),
        "global_ipv6": dedupe(inet6_global),
    }


def collect_system_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "platform": platform.platform(),
        "commands": {},
    }
    for label, command in {
        "ifconfig": ["ifconfig"],
        "proxy": ["scutil", "--proxy"],
        "dns": ["scutil", "--dns"],
        "route": ["route", "-n", "get", "default"],
    }.items():
        code, out, err = run_cmd(command)
        state["commands"][label] = {"code": code, "stderr": err}
        state[label] = out

    state.update(collect_interfaces(state.get("ifconfig", "")))
    state["proxy_values"] = parse_scutil_proxy(state.get("proxy", ""))
    dns_sections = parse_dns_sections(state.get("dns", ""))
    state["dns_default_servers"] = dns_sections["default"]
    state["dns_scoped_servers"] = dns_sections["scoped"]
    state["dns_servers"] = dns_sections["all"]
    state["proxy_enabled"] = any(
        state["proxy_values"].get(key) == "1"
        for key in ("HTTPEnable", "HTTPSEnable", "SOCKSEnable", "ProxyAutoConfigEnable")
    )
    state["tunnel_detected"] = bool(state["tunnel_interfaces"])
    return state


def collect_public_ips() -> dict[str, Any]:
    services = [
        ("ipify-v4", "https://api.ipify.org?format=json"),
        ("icanhazip-v4", "https://ipv4.icanhazip.com/"),
        ("ipinfo", "https://ipinfo.io/json"),
        ("ipify-v6", "https://api6.ipify.org?format=json"),
        ("icanhazip-v6", "https://ipv6.icanhazip.com/"),
    ]
    results: list[FetchResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_url, name, url) for name, url in services]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    ips: list[str] = []
    evidence: list[str] = []
    for result in sorted(results, key=lambda item: item.name):
        ip = extract_ip(result.text) if result.ok else None
        if ip:
            ips.append(ip)
            evidence.append(f"{result.name}: {ip} ({result.elapsed_ms} ms)")
        else:
            reason = result.error or "未返回 IP"
            evidence.append(f"{result.name}: 失败 - {reason}")

    ipv4 = [ip for ip in ips if ipaddress.ip_address(ip).version == 4]
    ipv6 = [ip for ip in ips if ipaddress.ip_address(ip).version == 6]
    primary = ipv4[0] if ipv4 else (ipv6[0] if ipv6 else None)
    return {
        "results": results,
        "ips": dedupe(ips),
        "ipv4": dedupe(ipv4),
        "ipv6": dedupe(ipv6),
        "primary": primary,
        "evidence": evidence,
    }


def geo_lookup(ip: str | None) -> dict[str, Any]:
    if not ip:
        return {}
    result = fetch_url("ipwhois", f"https://ipwho.is/{urllib.parse.quote(ip)}", timeout=5)
    data = first_json(result.text) if result.ok else {}
    if data.get("success") is False:
        return {"ip": ip, "error": data.get("message", result.error)}
    connection = data.get("connection") if isinstance(data.get("connection"), dict) else {}
    return {
        "ip": ip,
        "country": data.get("country_code") or data.get("country"),
        "city": data.get("city"),
        "asn": connection.get("asn"),
        "org": connection.get("org") or connection.get("isp"),
        "isp": connection.get("isp"),
    }


def test_targets() -> list[TargetResult]:
    targets = [
        ("ChatGPT", "https://chatgpt.com/"),
        ("Google", "https://www.google.com/generate_204"),
        ("YouTube", "https://www.youtube.com/generate_204"),
        ("Apple", "https://www.apple.com/library/test/success.html"),
        ("Baidu", "https://www.baidu.com/"),
        ("QQ", "https://www.qq.com/"),
    ]
    results: list[TargetResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {executor.submit(fetch_url, name, url, DEFAULT_TIMEOUT): (name, url) for name, url in targets}
        for future in concurrent.futures.as_completed(future_map):
            name, url = future_map[future]
            fetched = future.result()
            ok = fetched.ok and (fetched.status is None or fetched.status < 500)
            results.append(TargetResult(name, url, ok, fetched.elapsed_ms, fetched.status, fetched.error))
    return sorted(results, key=lambda item: item.name)


def repeated_latency(url: str = "https://www.google.com/generate_204", count: int = 5) -> list[FetchResult]:
    results: list[FetchResult] = []
    for index in range(count):
        results.append(fetch_url(f"repeat-{index + 1}", url, timeout=DEFAULT_TIMEOUT))
    return results


def small_speed_tests() -> dict[str, Any]:
    download_url = "https://speed.cloudflare.com/__down?bytes=262144"
    upload_url = "https://postman-echo.com/post"
    download = fetch_url("download-256k", download_url, timeout=10)
    upload_data = b"x" * 65536
    upload = fetch_url("upload-64k", upload_url, timeout=10, method="POST", data=upload_data)
    download_mbps = None
    upload_mbps = None
    if download.ok and download.elapsed_ms and download.elapsed_ms > 0:
        download_mbps = (262144 * 8) / (download.elapsed_ms / 1000) / 1_000_000
    if upload.ok and upload.elapsed_ms and upload.elapsed_ms > 0:
        upload_mbps = (len(upload_data) * 8) / (upload.elapsed_ms / 1000) / 1_000_000
    return {
        "download": download,
        "upload": upload,
        "download_mbps": download_mbps,
        "upload_mbps": upload_mbps,
    }


def score_by_threshold(value: float | None, thresholds: list[tuple[float, float]], fallback: float = 0.0) -> float:
    if value is None or math.isnan(value):
        return fallback
    for threshold, score in thresholds:
        if value <= threshold:
            return score
    return thresholds[-1][1] if thresholds else fallback


def score_speed_floor(value: float | None, thresholds: list[tuple[float, float]], fallback: float = 0.0) -> float:
    if value is None or math.isnan(value):
        return fallback
    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return thresholds[-1][1] if thresholds else fallback


def conclusion_for_score(score: int) -> str:
    if score >= 95:
        return "极好，主力长期用"
    if score >= 90:
        return "很好，可以长期主力用"
    if score >= 85:
        return "好，日常很稳"
    if score >= 80:
        return "良好，主力可用，但安全或体验还没到第一梯队"
    if score >= 75:
        return "可用，适合日常，但短板已经会影响部分场景"
    if score >= 70:
        return "勉强可用，不建议重要场景长期依赖"
    if score >= 65:
        return "凑合，安全、稳定或分流至少有一项明显问题"
    if score >= 60:
        return "低保可用，只适合临时过渡，不推荐主力"
    return "不推荐，基本不值得作为常用梯子"


def band_for_score(score: int) -> str:
    if score < 60:
        return "0-59"
    if score >= 95:
        return "95-100"
    low = (score // 5) * 5
    high = min(100, low + 4)
    return f"{low}-{high}"


def detect_webrtc() -> dict[str, Any]:
    # A real WebRTC probe requires browser automation. The skill should not
    # install dependencies or ask the user to operate a browser, so v1 reports
    # this as uncovered unless a future bundled browser probe is added.
    return {
        "covered": False,
        "score": 3.0,
        "max_score": 5.0,
        "note": "本轮未自动运行浏览器 WebRTC 探针，按保守部分给分。",
    }


def evaluate_dns(
    default_servers: list[str],
    scoped_servers: list[str],
    exit_geo: dict[str, Any],
) -> tuple[float, list[str], list[str], list[str]]:
    notes: list[str] = []
    deductions: list[str] = []
    vetoes: list[str] = []
    if not default_servers and not scoped_servers:
        return 5.0, ["未读取到系统 DNS 服务器，按未知处理。"], ["DNS 配置不可读，保守扣分。"], []
    if not default_servers and scoped_servers:
        local_scoped = [server for server in scoped_servers if is_local_dns(server)]
        if local_scoped:
            return 5.0, [f"只读取到 scoped DNS：{', '.join(scoped_servers[:6])}"], ["未读取到默认 DNS，只看到 scoped 本地 DNS，按未知保守扣分。"], []
        return 8.0, [f"只读取到 scoped DNS：{', '.join(scoped_servers[:6])}"], ["未读取到默认 DNS，DNS 判断覆盖率下降。"], []

    local_servers = [server for server in default_servers if is_local_dns(server)]
    if local_servers:
        notes.append(f"默认 DNS 指向本地/路由器地址：{', '.join(local_servers)}")
        deductions.append("DNS 服务器包含本地或路由器地址。")
        vetoes.append("DNS 泄漏")
        return 0.0, notes, deductions, vetoes

    notes.append(f"默认 DNS：{', '.join(default_servers[:6])}")
    local_scoped = [server for server in scoped_servers if is_local_dns(server)]
    if local_scoped:
        notes.append(f"scoped DNS 含本地网络地址：{', '.join(local_scoped[:4])}，未作为默认 DNS 一票否决")
    score = 12.0
    public_dns = [server for server in default_servers if not is_private_or_local(server)]
    if not public_dns:
        score = 9.0
        notes.append("默认 DNS 使用本地代理或保留地址，未发现路由器默认 DNS")
    elif (exit_geo.get("country") not in (None, "CN")) and any(server.startswith(("114.", "223.5.", "223.6.", "180.76.")) for server in public_dns):
        score = 7.0
        deductions.append("出口不在中国大陆，但 DNS 出现常见大陆公共 DNS，可能影响分流或隐私。")
    return score, notes, deductions, vetoes


def evaluate_audit() -> dict[str, Any]:
    system = collect_system_state()
    public_ips = collect_public_ips()
    primary_ip = public_ips.get("primary")
    exit_geo = geo_lookup(primary_ip)
    target_results = test_targets()
    latency_results = repeated_latency()
    speed = small_speed_tests()
    webrtc = detect_webrtc()

    vetoes: list[str] = []
    deductions: list[str] = []
    uncovered: list[str] = [
        "kill switch / 断线保护：v1 不做破坏性断网测试。",
        "客户端来源、证书/描述文件/内核扩展、商业逻辑：需要主观或权限审查，v1 不计分。",
        "长期高峰稳定性：需要多时段观测，v1 只给本轮瞬时结果。",
        "银行/校园网登录类站点：v1 不访问需要登录或可能触发风控的网站。",
    ]

    score_items: list[ScoreItem] = []

    # Safety: public IP and route evidence.
    if not public_ips["ips"]:
        score_items.append(ScoreItem("安全与泄漏", "公网出口", 0, 12, "无法获取公网出口 IP。"))
        deductions.append("公网 IP 服务全部失败。")
    elif any(is_private_or_local(ip) for ip in public_ips["ips"]):
        score_items.append(ScoreItem("安全与泄漏", "公网出口", 0, 12, "公网测试返回本地/私有地址。"))
        vetoes.append("公网 IP 泄漏")
    else:
        countries = exit_geo.get("country") or "未知国家/地区"
        org = exit_geo.get("org") or exit_geo.get("isp") or "未知网络"
        score_items.append(ScoreItem("安全与泄漏", "公网出口", 12, 12, f"出口 {primary_ip}，{countries}，{org}。"))

    dns_score, dns_notes, dns_deductions, dns_vetoes = evaluate_dns(
        system["dns_default_servers"],
        system["dns_scoped_servers"],
        exit_geo,
    )
    score_items.append(ScoreItem("安全与泄漏", "DNS", dns_score, 12, "；".join(dns_notes)))
    deductions.extend(dns_deductions)
    vetoes.extend(dns_vetoes)

    if public_ips["ipv6"]:
        ipv6_notes = ", ".join(public_ips["ipv6"])
        if any(is_private_or_local(ip) for ip in public_ips["ipv6"]):
            score_items.append(ScoreItem("安全与泄漏", "IPv6", 0, 8, f"IPv6 返回本地/私有地址：{ipv6_notes}。"))
            vetoes.append("IPv6 泄漏")
        else:
            score_items.append(ScoreItem("安全与泄漏", "IPv6", 8, 8, f"IPv6 出口可识别：{ipv6_notes}。"))
    else:
        local_v6 = system.get("global_ipv6", [])
        if local_v6:
            score_items.append(ScoreItem("安全与泄漏", "IPv6", 5, 8, "本机有全局 IPv6，但外部 IPv6 探针不可达，按未知保守扣分。"))
            deductions.append("IPv6 探针不可达，无法完全确认 IPv6 路径。")
        else:
            score_items.append(ScoreItem("安全与泄漏", "IPv6", 7, 8, "未检测到本机全局 IPv6，未发现 IPv6 直连证据。"))

    score_items.append(ScoreItem("安全与泄漏", "WebRTC", webrtc["score"], webrtc["max_score"], webrtc["note"]))
    uncovered.append("WebRTC：当前脚本未绑定浏览器自动探针，保守部分给分，不要求人工操作。")

    path_score = 8.0 if (system["tunnel_detected"] or system["proxy_enabled"]) else 3.0
    if not (system["tunnel_detected"] or system["proxy_enabled"]):
        deductions.append("未检测到 TUN/utun 或系统代理路径。")
        if exit_geo.get("country") == "CN":
            vetoes.append("未检测到代理路径且外网出口疑似本地")
    path_note = []
    if system["tunnel_detected"]:
        path_note.append(f"隧道接口：{', '.join(system['tunnel_interfaces'][:6])}")
    if system["proxy_enabled"]:
        path_note.append("系统代理已启用")
    if not path_note:
        path_note.append("未检测到系统代理或隧道接口")
    score_items.append(ScoreItem("安全与泄漏", "代理路径", path_score, 8, "；".join(path_note)))

    unique_ip_count = len(public_ips["ips"])
    consistency_score = 5.0
    if unique_ip_count == 0:
        consistency_score = 0.0
    elif unique_ip_count > 2:
        consistency_score = 3.0
        deductions.append("多个公网 IP 探针返回差异较大，可能是负载均衡或分流不一致。")
    score_items.append(ScoreItem("安全与泄漏", "出口一致性", consistency_score, 5, f"公网探针返回 {unique_ip_count} 个唯一出口。"))

    # Stability and response.
    successful_latency = [item.elapsed_ms for item in latency_results if item.ok and item.elapsed_ms is not None]
    latency_success = len(successful_latency)
    fail_rate = 1 - latency_success / max(1, len(latency_results))
    median_latency = statistics.median(successful_latency) if successful_latency else None
    jitter = statistics.pstdev(successful_latency) if len(successful_latency) >= 2 else None

    latency_score = score_by_threshold(median_latency, [(250, 8), (500, 6), (900, 4), (1500, 2), (999999, 1)], fallback=1)
    jitter_score = score_by_threshold(jitter, [(80, 5), (180, 4), (350, 2.5), (700, 1), (999999, 0)], fallback=3)
    failure_score = score_by_threshold(fail_rate, [(0, 5), (0.2, 3.5), (0.5, 1.5), (1, 0)], fallback=0)
    repeat_score = 2.0 if latency_success >= 4 else (1.0 if latency_success >= 2 else 0.0)
    score_items.extend(
        [
            ScoreItem("稳定与响应", "握手/首包延迟", latency_score, 8, f"中位耗时 {format_ms(median_latency)}。"),
            ScoreItem("稳定与响应", "延迟波动", jitter_score, 5, f"波动 {format_ms(jitter)}。"),
            ScoreItem("稳定与响应", "失败率", failure_score, 5, f"连续请求失败率 {fail_rate:.0%}。"),
            ScoreItem("稳定与响应", "连续请求稳定性", repeat_score, 2, f"{latency_success}/{len(latency_results)} 次成功。"),
        ]
    )
    if fail_rate > 0:
        deductions.append(f"连续请求存在失败：{latency_success}/{len(latency_results)} 次成功。")

    # Speed.
    download_score = score_speed_floor(speed["download_mbps"], [(25, 8), (10, 6), (4, 4), (1, 2), (0, 0)], fallback=1)
    upload_score = score_speed_floor(speed["upload_mbps"], [(8, 3), (3, 2), (0.8, 1), (0, 0)], fallback=1)
    target_elapsed = [item.elapsed_ms for item in target_results if item.ok and item.elapsed_ms is not None]
    ttfb_median = statistics.median(target_elapsed) if target_elapsed else None
    ttfb_score = score_by_threshold(ttfb_median, [(400, 4), (900, 3), (1500, 2), (2500, 1), (999999, 0)], fallback=0)
    score_items.extend(
        [
            ScoreItem("速度", "小样本下载", download_score, 8, f"{format_mbps(speed['download_mbps'])}。"),
            ScoreItem("速度", "小样本上传", upload_score, 3, f"{format_mbps(speed['upload_mbps'])}。"),
            ScoreItem("速度", "目标首包响应", ttfb_score, 4, f"目标中位耗时 {format_ms(ttfb_median)}。"),
        ]
    )
    if not speed["download"].ok:
        deductions.append(f"下载小样本失败：{speed['download'].error}")
    if not speed["upload"].ok:
        deductions.append(f"上传小样本失败：{speed['upload'].error}")

    # Split routing quality.
    target_map = {item.name: item for item in target_results}
    foreign_names = ["ChatGPT", "Google", "YouTube"]
    domestic_names = ["Baidu", "QQ"]
    apple = target_map.get("Apple")
    foreign_ok = sum(1 for name in foreign_names if target_map.get(name) and target_map[name].ok)
    domestic_ok = sum(1 for name in domestic_names if target_map.get(name) and target_map[name].ok)
    foreign_score = min(4.0, foreign_ok / len(foreign_names) * 4)
    domestic_score = min(3.0, domestic_ok / len(domestic_names) * 3)
    apple_score = 2.0 if apple and apple.ok else 0.5
    explain_score = 1.0 if system.get("dns_servers") or system["proxy_enabled"] or system["tunnel_detected"] else 0.0
    score_items.extend(
        [
            ScoreItem("分流质量", "国外目标", foreign_score, 4, f"{foreign_ok}/{len(foreign_names)} 个公开目标可达。"),
            ScoreItem("分流质量", "国内目标", domestic_score, 3, f"{domestic_ok}/{len(domestic_names)} 个公开目标可达。"),
            ScoreItem("分流质量", "Apple 服务", apple_score, 2, "Apple 连通。" if apple and apple.ok else "Apple 目标不可达或超时。"),
            ScoreItem("分流质量", "规则可解释性", explain_score, 1, "读取到系统路径/DNS 证据。" if explain_score else "系统路径证据不足。"),
        ]
    )

    # Maintainability.
    maint_score = 0.0
    maint_notes: list[str] = []
    if system["tunnel_detected"] or system["proxy_enabled"]:
        maint_score += 2
        maint_notes.append("路径可识别")
    if system.get("dns_servers"):
        maint_score += 1
        maint_notes.append("DNS 配置可读")
    if public_ips["ips"]:
        maint_score += 1
        maint_notes.append("公网出口可追踪")
    if target_results:
        maint_score += 1
        maint_notes.append("失败信息可回溯")
    score_items.append(ScoreItem("可维护性", "自动诊断证据", maint_score, 5, "、".join(maint_notes) if maint_notes else "可回溯证据不足。"))

    total = int(round(sum(item.score for item in score_items)))
    total = max(0, min(100, total))
    vetoes = dedupe(vetoes)
    return {
        "system": system,
        "public_ips": public_ips,
        "exit_geo": exit_geo,
        "target_results": target_results,
        "latency_results": latency_results,
        "speed": speed,
        "score_items": score_items,
        "score": total,
        "vetoes": vetoes,
        "deductions": dedupe([item for item in deductions if item]),
        "uncovered": dedupe(uncovered),
    }


def format_ms(value: float | int | None) -> str:
    if value is None:
        return "未知"
    return f"{int(round(value))} ms"


def format_mbps(value: float | None) -> str:
    if value is None:
        return "未知"
    return f"{value:.2f} Mbps"


def markdown_report(audit: dict[str, Any]) -> str:
    score = audit["score"]
    vetoes = audit["vetoes"]
    if vetoes:
        first_veto = vetoes[0]
        conclusion = f"结论：不安全。命中 {first_veto}，一票否决。"
    else:
        conclusion = f"结论：{score}/100。{conclusion_for_score(score)}，未命中一票否决。"

    lines: list[str] = [
        "# vpn-auditor 报告",
        "",
        conclusion,
        "",
        f"- 原始分：{score}/100",
        f"- 细分档位：{band_for_score(score)}" if not vetoes else "- 细分档位：一票否决",
        f"- 一票否决：{'、'.join(vetoes) if vetoes else '未命中'}",
    ]

    exit_geo = audit["exit_geo"]
    if exit_geo:
        geo_text = "，".join(str(part) for part in [exit_geo.get("ip"), exit_geo.get("country"), exit_geo.get("org")] if part)
        lines.append(f"- 公网出口：{geo_text or '未知'}")
    lines.append("")

    category_order = ["安全与泄漏", "稳定与响应", "速度", "分流质量", "可维护性"]
    lines.append("## 分项得分")
    lines.append("")
    lines.append("| 项目 | 得分 | 说明 |")
    lines.append("| --- | ---: | --- |")
    for category in category_order:
        items = [item for item in audit["score_items"] if item.category == category]
        if not items:
            continue
        subtotal = sum(item.score for item in items)
        max_total = sum(item.max_score for item in items)
        lines.append(f"| {category} | {subtotal:.0f}/{max_total:.0f} |  |")
        for item in items:
            lines.append(f"| {item.name} | {item.score:.0f}/{item.max_score:.0f} | {item.note} |")
    lines.append("")

    lines.append("## 自动检测证据")
    lines.append("")
    for evidence in audit["public_ips"]["evidence"]:
        lines.append(f"- {evidence}")
    dns_default = audit["system"].get("dns_default_servers", [])
    dns_scoped = audit["system"].get("dns_scoped_servers", [])
    lines.append(f"- 默认 DNS：{', '.join(dns_default) if dns_default else '未读取到'}")
    lines.append(f"- Scoped DNS：{', '.join(dns_scoped) if dns_scoped else '未读取到'}")
    tunnel_interfaces = audit["system"].get("tunnel_interfaces", [])
    lines.append(f"- 隧道接口：{', '.join(tunnel_interfaces) if tunnel_interfaces else '未检测到'}")
    lines.append(f"- 系统代理：{'已启用' if audit['system'].get('proxy_enabled') else '未启用或未检测到'}")
    for target in audit["target_results"]:
        status = "可达" if target.ok else "失败"
        extra = f"{target.elapsed_ms} ms" if target.elapsed_ms is not None else target.error
        lines.append(f"- {target.name}: {status} ({extra})")
    lines.append("")

    lines.append("## 扣分说明")
    lines.append("")
    deduction_lines = build_deduction_lines(audit["deductions"], audit["score_items"])
    if deduction_lines:
        for deduction in deduction_lines:
            lines.append(f"- {deduction}")
    else:
        lines.append("- 未发现主要扣分项。")
    lines.append("")

    lines.append("## 本轮未覆盖")
    lines.append("")
    for item in audit["uncovered"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def build_deduction_lines(manual: list[str], score_items: list[ScoreItem]) -> list[str]:
    lines = list(manual)
    for item in score_items:
        missed = item.max_score - item.score
        if missed >= 1:
            lines.append(f"{item.category}/{item.name} 扣 {missed:.0f} 分：{item.note}")
    return dedupe(lines)[:10]


def self_test() -> int:
    expected = {
        100: "95-100",
        96: "95-100",
        95: "95-100",
        94: "90-94",
        90: "90-94",
        89: "85-89",
        85: "85-89",
        84: "80-84",
        80: "80-84",
        79: "75-79",
        75: "75-79",
        74: "70-74",
        70: "70-74",
        69: "65-69",
        65: "65-69",
        64: "60-64",
        60: "60-64",
        59: "0-59",
        0: "0-59",
    }
    for score, band in expected.items():
        actual = band_for_score(score)
        if actual != band:
            print(f"band test failed: {score} expected {band}, got {actual}", file=sys.stderr)
            return 1
    snippets = {
        87: "好，日常很稳",
        80: "良好，主力可用",
        71: "勉强可用",
        59: "不推荐",
    }
    for score, snippet in snippets.items():
        if snippet not in conclusion_for_score(score):
            print(f"conclusion test failed: {score} missing {snippet}", file=sys.stderr)
            return 1
    fake = {
        "score": 87,
        "vetoes": [],
        "exit_geo": {"ip": "203.0.113.8", "country": "US", "org": "Example VPN"},
        "score_items": [ScoreItem("安全与泄漏", "公网出口", 12, 12, "ok")],
        "public_ips": {"evidence": ["ipify-v4: 203.0.113.8 (100 ms)"]},
        "system": {"dns_servers": ["1.1.1.1"], "tunnel_interfaces": ["utun4"], "proxy_enabled": False},
        "target_results": [TargetResult("Google", "https://www.google.com/", True, 120, 204)],
        "deductions": [],
        "uncovered": ["kill switch / 断线保护：v1 不做破坏性断网测试。"],
    }
    report = markdown_report(fake)
    if "结论：87/100。好，日常很稳，未命中一票否决。" not in report:
        print("report conclusion format test failed", file=sys.stderr)
        return 1
    print("vpn-auditor self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Automatic VPN/proxy auditor")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON summary")
    parser.add_argument("--self-test", action="store_true", help="run offline self tests")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    audit = evaluate_audit()
    if args.json:
        serializable = {
            "score": audit["score"],
            "band": band_for_score(audit["score"]),
            "vetoes": audit["vetoes"],
            "deductions": audit["deductions"],
            "uncovered": audit["uncovered"],
            "public_ips": audit["public_ips"]["ips"],
            "dns_default_servers": audit["system"].get("dns_default_servers", []),
            "dns_scoped_servers": audit["system"].get("dns_scoped_servers", []),
        }
        print(json.dumps(serializable, ensure_ascii=False, indent=2))
        return 0
    print(markdown_report(audit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
