# vpn-auditor

Connect the tunnel. Run the skill. Read the verdict.

`vpn-auditor` is a Codex skill for automatic VPN/proxy checks. It does not ask you to disconnect the VPN, inspect the client, wait for peak hours, or explain what you installed. It runs the checks it can prove by itself, then returns a concise Chinese report.

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

## What You Get

| Section | What it tells you |
| --- | --- |
| Conclusion | Final score, verdict, and one-vote veto status |
| Evidence | Exit IP, DNS path, tunnel/proxy state, target reachability |
| Impact Factors | Why the result was pulled down, without exposing the scoring weights |
| Uncovered Items | Checks skipped because they require human action or disruptive testing |

## What It Checks

- Public exit IP and consistency across multiple probes
- DNS path evidence, including default and scoped macOS resolvers
- IPv6 path evidence
- macOS tunnel/proxy state
- Public target reachability
- Small-sample network response
- Repeated-request stability

## What It Refuses To Do

Some tests are useful but not zero-interaction. v1 leaves them out instead of turning the user into a test fixture.

- No kill-switch testing
- No forced disconnects
- No client trust review
- No certificate/profile/kernel-extension inspection
- No provider business-model judgment
- No long-term peak-hour monitoring
- No bank, campus, or login-only site probing

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

The report gives the final score and evidence, but it does not print the detailed weighting table. That keeps the report readable and makes the result harder to game. The project is still auditable: the implementation lives in `scripts/vpn_auditor.py`.

## License

MIT
