# vpn-auditor

Codex skill for automatic VPN/proxy health checks.

`vpn-auditor` scores a connected VPN/proxy without asking the user to disconnect, switch networks, inspect the client, wait for peak hours, or perform subjective checks. It produces a Chinese-by-default report with a score, dense 5-point conclusions above 60, one-vote veto status, evidence, deductions, and uncovered automatic-test items.

## What It Tests

- Public exit IP consistency
- DNS configuration and likely leakage
- IPv6 path evidence
- Proxy/tunnel path evidence on macOS
- Public target reachability
- Small-sample download and upload response
- Basic stability through repeated requests

## What It Does Not Test

The v1 skill intentionally skips items that require human cooperation or disruptive testing:

- Kill switch / forced disconnect behavior
- Client provenance
- Certificates, profiles, kernel extensions, or MDM review
- Business logic of the provider
- Long-term peak-hour stability
- Login-only sites such as banks or campus portals

## Install

Copy this folder into the Codex skills directory:

```bash
mkdir -p "$HOME/.codex/skills"
cp -R vpn-auditor "$HOME/.codex/skills/vpn-auditor"
```

Restart Codex if the skill list does not refresh.

## Run

After connecting your VPN/proxy, invoke the skill as `$vpn-auditor`, or run the script directly:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py"
```

Offline validation:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py" --self-test
```

## Scoring

- 95-100: 极好，主力长期用。
- 90-94: 很好，可以长期主力用。
- 85-89: 好，日常很稳。
- 80-84: 良好，主力可用，但安全或体验还没到第一梯队。
- 75-79: 可用，适合日常，但短板已经会影响部分场景。
- 70-74: 勉强可用，不建议重要场景长期依赖。
- 65-69: 凑合，安全、稳定或分流至少有一项明显问题。
- 60-64: 低保可用，只适合临时过渡，不推荐主力。
- 0-59: 不推荐，基本不值得作为常用梯子。
- One-vote veto: 不安全，不看总分。

## License

MIT
