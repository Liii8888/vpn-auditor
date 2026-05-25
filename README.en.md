<div align="center">

# vpn-auditor

[中文](README.md)

**Connect the tunnel. Run the skill. Read the verdict.**

`vpn-auditor` is a zero-interaction Codex skill for VPN/proxy checks. It only runs checks it can prove automatically, without asking you to disconnect the VPN, explain the client, wait for peak hours, or manually open websites.

</div>

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

<table>
  <tr>
    <td align="center" width="33%"><sub>01</sub><br><strong>Connect VPN / proxy</strong></td>
    <td align="center" width="33%"><sub>02</sub><br><strong>Invoke <code>$vpn-auditor</code></strong></td>
    <td align="center" width="33%"><sub>03</sub><br><strong>Read the score, evidence, and impact factors</strong></td>
  </tr>
</table>

## Report Structure

<table>
  <tr>
    <td width="50%"><strong>Conclusion</strong><br>Final score, verdict, and one-vote veto status</td>
    <td width="50%"><strong>Assessment Summary</strong><br>Summarizes categories as strong, stable, limited, or weak</td>
  </tr>
  <tr>
    <td width="50%"><strong>Evidence</strong><br>Exit IP, DNS path, tunnel/proxy state, and target reachability</td>
    <td width="50%"><strong>Impact Factors</strong><br>Explains what pulled the result down without exposing scoring weights</td>
  </tr>
  <tr>
    <td colspan="2"><strong>Uncovered Items</strong><br>Lists checks skipped because they require human action or disruptive testing</td>
  </tr>
</table>

## Automatic Check Surface

<table>
  <tr>
    <th width="33%">Network Identity</th>
    <th width="33%">Resolution Path</th>
    <th width="33%">Connection Quality</th>
  </tr>
  <tr>
    <td>Public exit IP</td>
    <td>Default DNS / scoped DNS</td>
    <td>Public target reachability</td>
  </tr>
  <tr>
    <td>Multi-probe consistency</td>
    <td>IPv6 path evidence</td>
    <td>Small-sample network response</td>
  </tr>
  <tr>
    <td>macOS tunnel / system proxy</td>
    <td>Local-network DNS signals</td>
    <td>Repeated-request stability</td>
  </tr>
</table>

## Boundaries

The v1 rule is simple: test what can be proven automatically, and do not make the user part of the test rig.

<table>
  <tr>
    <th width="42%">Skipped</th>
    <th>Reason</th>
  </tr>
  <tr>
    <td>Kill switch / forced disconnect</td>
    <td>It disrupts the current network state</td>
  </tr>
  <tr>
    <td>Client provenance review</td>
    <td>It requires human judgment or extra permissions</td>
  </tr>
  <tr>
    <td>Certificates, profiles, kernel extensions, MDM</td>
    <td>They do not fit a zero-interaction run</td>
  </tr>
  <tr>
    <td>Provider business-model judgment</td>
    <td>It cannot be proven by one network check</td>
  </tr>
  <tr>
    <td>Long-term peak-hour stability</td>
    <td>It requires multi-session monitoring</td>
  </tr>
  <tr>
    <td>Bank, campus, login-only sites</td>
    <td>They can trigger risk controls or touch private data</td>
  </tr>
</table>

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
