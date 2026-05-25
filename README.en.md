# vpn-auditor

[中文](README.md)

**Connect the tunnel. Run the skill. Read the verdict.**

`vpn-auditor` is a zero-interaction Codex skill for VPN/proxy checks. It only runs checks it can prove automatically, without asking you to disconnect the VPN, explain the client, wait for peak hours, or manually open websites.

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

| 01 | 02 | 03 |
| --- | --- | --- |
| Connect VPN / proxy | Invoke `$vpn-auditor` | Read the score, evidence, and impact factors |

## Report Structure

| Section | Purpose |
| --- | --- |
| Conclusion | Final score, verdict, and one-vote veto status |
| Assessment Summary | Summarizes categories as strong, stable, limited, or weak |
| Evidence | Exit IP, DNS path, tunnel/proxy state, and target reachability |
| Impact Factors | Explains what pulled the result down without exposing scoring weights |
| Uncovered Items | Lists checks skipped because they require human action or disruptive testing |

## Automatic Check Surface

| Network Identity | Resolution Path | Connection Quality |
| --- | --- | --- |
| Public exit IP | Default DNS / scoped DNS | Public target reachability |
| Multi-probe consistency | IPv6 path evidence | Small-sample network response |
| macOS tunnel / system proxy | Local-network DNS signals | Repeated-request stability |

## Boundaries

The v1 rule is simple: test what can be proven automatically, and do not make the user part of the test rig.

| Skipped | Reason |
| --- | --- |
| Kill switch / forced disconnect | It disrupts the current network state |
| Client provenance review | It requires human judgment or extra permissions |
| Certificates, profiles, kernel extensions, MDM | They do not fit a zero-interaction run |
| Provider business-model judgment | It cannot be proven by one network check |
| Long-term peak-hour stability | It requires multi-session monitoring |
| Bank, campus, login-only sites | They can trigger risk controls or touch private data |

## Install

```bash
mkdir -p "$HOME/.codex/skills"
cp -R vpn-auditor "$HOME/.codex/skills/vpn-auditor"
```

Restart Codex if the skill list does not refresh.

## Run

Invoke `$vpn-auditor` after connecting your VPN/proxy, or run the script directly:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py"
```

Offline validation:

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py" --self-test
```

## Output Philosophy

The report shows the final score, verdict, and evidence, but it does not print the detailed weighting table. That keeps the report readable and harder to game. The project is still auditable: the implementation lives in `scripts/vpn_auditor.py`.

## License

MIT
