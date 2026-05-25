---
name: "vpn-auditor"
description: "Use when the user wants to automatically test, score, or audit a VPN, proxy, ladder, 梯子, 代理, VPN, Clash, sing-box, or network tunnel after connecting it. Produces a Chinese-by-default score report with one-vote veto checks, leakage evidence, deductions, and uncovered automatic-test items without asking the user to manually disconnect or confirm subjective details."
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
- Category scores.
- Automatic evidence.
- Deductions.
- Uncovered items.

For one-vote veto, use: `结论：不安全。命中 DNS 泄漏，一票否决。`

## Scoring Model

The v1 score is an automatic-test score only:

- Safety and leakage: 50
- Stability and response: 20
- Speed: 15
- Split routing quality: 10
- Maintainability evidence: 5

Only include automatically testable items in the score. Excluded from v1 scoring: kill switch, client provenance, certificates/profiles/kernel extensions, business logic, long-term peak-hour stability, and login-only sites such as banks or campus portals.

## Score Conclusions

Scores above 60 are intentionally dense because a 5-point difference is meaningful for a good VPN/proxy:

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

## Validation

To validate the installed skill without network access:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py" --self-test
```
