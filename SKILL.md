---
name: "vpn-auditor"
description: "Use when the user wants to automatically test, score, or audit a VPN, proxy, ladder, 梯子, 代理, VPN, Clash, sing-box, or network tunnel after connecting it. Produces a Chinese-by-default score report with one-vote veto checks, leakage evidence, impact factors, and uncovered automatic-test items without asking the user to manually disconnect or confirm subjective details."
---

# VPN Auditor

Run a zero-interaction VPN/proxy health check after the user has connected their VPN/proxy/ladder. The user should only need to connect the VPN, invoke this skill, and wait for the report.

## Required Behavior

- Do not ask the user to disconnect the VPN, switch networks, install certificates, explain the client, wait for peak hours, or manually check websites.
- Do not run destructive or disruptive tests such as kill-switch testing.
- Default report language follows the current conversation and memory preferences. In this workspace, default to Chinese.
- Run the bundled script and report its Markdown output:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py"
```

If the sandbox blocks network access, request network permission and rerun the same command. Do not replace the automated run with manual instructions.

## Report Contract

The report must include:

- `结论` one-liner in this style: `结论：87/100。好，日常很稳，未命中一票否决。`
- Raw score and score band.
- One-vote veto status.
- Automatic evidence.
- Impact factors, without exposing internal weights or per-item point values.
- Uncovered items.

For one-vote veto, use: `结论：不安全。命中 DNS 泄漏，一票否决。`

Do not print the full scoring rubric, category weights, or per-item score table in normal reports.

## Scope

The v1 score is based only on automatic checks the script can perform without human cooperation. Excluded from v1 scoring: kill switch, client provenance, certificates/profiles/kernel extensions, business logic, long-term peak-hour stability, and login-only sites such as banks or campus portals.

## Validation

To validate the installed skill without network access:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py" --self-test
```
