# vpn-auditor

[中文](README.md)

> Once the tunnel is on, it asks the network itself.

`vpn-auditor` is a zero-interaction Codex skill for VPN/proxy checks. Connect the line, run the skill, and read a direct Chinese verdict. It will not ask you to disconnect the VPN, explain the client, wait for peak hours, or manually open a row of websites.

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

```text
VPN ON
  -> exit probes
  -> DNS / IPv6 / path checks
  -> public target reachability
  -> score, evidence, impact factors
```

## One Run

| You do | It does | You read |
| --- | --- | --- |
| Connect VPN / proxy | Probes exit, DNS, IPv6, path, and reachability | Score, verdict, one-vote veto |
| Do not switch networks | Avoids disruptive tests | Automatic evidence |
| Do not explain the client | Avoids subjective review | Impact factors and uncovered items |

## Report Shape

| Block | How to read it |
| --- | --- |
| Conclusion | Start here. It tells you whether this can be a main line. |
| Assessment Summary | Scans each area as strong, stable, limited, or weak. |
| Evidence | Shows exit IP, DNS, IPv6, tunnel interfaces, and target reachability. |
| Impact Factors | Explains what pulled the result down without exposing scoring weights. |
| Uncovered Items | Lists checks skipped because they need human action or disruptive testing. |

## What It Asks The Network

| Identity | Path | Experience |
| --- | --- | --- |
| Public exit IP | Default DNS / scoped DNS | Public target reachability |
| Multi-probe consistency | IPv6 evidence | Small-sample response |
| Local tunnel / system proxy | Local-network DNS signals | Repeated-request stability |

## What It Will Not Make You Do

| Skipped | Why |
| --- | --- |
| Kill switch / forced disconnect | It disrupts the current network |
| Client provenance review | It needs human judgment or extra permissions |
| Certificates, profiles, kernel extensions, MDM | They do not fit zero-interaction checks |
| Provider business-model judgment | One network probe cannot prove it |
| Long-term peak-hour stability | It needs multi-session monitoring |
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

## Design Rules

- Test only what can be proven automatically.
- Do not turn the user into the test operator.
- Do not print the detailed weighting table; show verdict, evidence, and impact factors.
- Keep the algorithm auditable in `scripts/vpn_auditor.py`.

## Rollback

The pre-redesign README state is tagged as `rollback/readme-swiss-20260525`. See [ROLLBACK.md](ROLLBACK.md) if you need to restore it.

## License

MIT
