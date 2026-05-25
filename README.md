<div align="center">

# vpn-auditor

[English](README.en.md)

**连好代理。运行 skill。等结果。**

`vpn-auditor` 是一个零交互 VPN / 代理 / 梯子体检 skill。它只做能自动证明的检查，不要求你断开 VPN、解释客户端、等晚高峰，或手动打开网站。

</div>

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

<table>
  <tr>
    <td align="center" width="33%"><sub>01</sub><br><strong>连接 VPN / 代理</strong></td>
    <td align="center" width="33%"><sub>02</sub><br><strong>调用 <code>$vpn-auditor</code></strong></td>
    <td align="center" width="33%"><sub>03</sub><br><strong>读取分数、证据和影响因素</strong></td>
  </tr>
</table>

## 输出结构

<table>
  <tr>
    <td width="50%"><strong>结论</strong><br>最终分数、等级判断、一票否决状态</td>
    <td width="50%"><strong>评估摘要</strong><br>用“强 / 稳 / 有短板 / 偏弱”概括各类表现</td>
  </tr>
  <tr>
    <td width="50%"><strong>自动检测证据</strong><br>出口 IP、DNS 路径、隧道/代理状态、目标可达性</td>
    <td width="50%"><strong>影响因素</strong><br>说明结果为什么被拉低，但不展示详细权重表</td>
  </tr>
  <tr>
    <td colspan="2"><strong>本轮未覆盖</strong><br>列出需要人工配合或破坏性测试的跳过项</td>
  </tr>
</table>

## 自动检查面

<table>
  <tr>
    <th width="33%">网络身份</th>
    <th width="33%">解析路径</th>
    <th width="33%">连接质量</th>
  </tr>
  <tr>
    <td>公网出口 IP</td>
    <td>默认 DNS / scoped DNS</td>
    <td>公开目标可达性</td>
  </tr>
  <tr>
    <td>多探针一致性</td>
    <td>IPv6 路径证据</td>
    <td>小样本网络响应</td>
  </tr>
  <tr>
    <td>macOS 隧道 / 系统代理</td>
    <td>本地网络 DNS 迹象</td>
    <td>连续请求稳定性</td>
  </tr>
</table>

## 边界

v1 的原则是：能自动测就测，不能自动证明就不打扰用户。

<table>
  <tr>
    <th width="42%">不做</th>
    <th>原因</th>
  </tr>
  <tr>
    <td>kill switch / 强制断网</td>
    <td>会破坏当前网络状态</td>
  </tr>
  <tr>
    <td>客户端来源审查</td>
    <td>需要人工判断或额外权限</td>
  </tr>
  <tr>
    <td>证书、描述文件、内核扩展、MDM 检查</td>
    <td>不适合零交互流程</td>
  </tr>
  <tr>
    <td>服务商商业模式判断</td>
    <td>无法由一次网络体检自动证明</td>
  </tr>
  <tr>
    <td>长期高峰期稳定性</td>
    <td>需要多时段监控</td>
  </tr>
  <tr>
    <td>银行、校园网、登录类站点</td>
    <td>可能触发风控或涉及隐私</td>
  </tr>
</table>

## 安装

```bash
mkdir -p "$HOME/.codex/skills"
cp -R vpn-auditor "$HOME/.codex/skills/vpn-auditor"
```

如果 Codex 的 skill 列表没有刷新，重启 Codex。

## 使用

连接好 VPN / 代理后，调用 `$vpn-auditor`。也可以直接运行脚本：

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py"
```

离线自测：

```bash
python3 "$HOME/.codex/skills/vpn-auditor/scripts/vpn_auditor.py" --self-test
```

## 输出原则

报告展示最终分数、结论和证据，但不打印详细权重表。这样报告更容易读，也不容易被刻意刷分。项目仍然可审计：实现逻辑在 `scripts/vpn_auditor.py`。

## License

MIT
