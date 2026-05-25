# vpn-auditor

[English](README.en.md)

**连好代理。运行 skill。等结果。**

`vpn-auditor` 是一个零交互 VPN / 代理 / 梯子体检 skill。它只做能自动证明的检查，不要求你断开 VPN、解释客户端、等晚高峰，或手动打开网站。

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

| 01 | 02 | 03 |
| --- | --- | --- |
| 连接 VPN / 代理 | 调用 `$vpn-auditor` | 读取分数、证据和影响因素 |

## 输出结构

| 模块 | 作用 |
| --- | --- |
| 结论 | 最终分数、等级判断、一票否决状态 |
| 评估摘要 | 用“强 / 稳 / 有短板 / 偏弱”概括各类表现 |
| 自动检测证据 | 出口 IP、DNS 路径、隧道/代理状态、目标可达性 |
| 影响因素 | 说明结果为什么被拉低，但不展示详细权重表 |
| 本轮未覆盖 | 列出需要人工配合或破坏性测试的跳过项 |

## 自动检查面

| 网络身份 | 解析路径 | 连接质量 |
| --- | --- | --- |
| 公网出口 IP | 默认 DNS / scoped DNS | 公开目标可达性 |
| 多探针一致性 | IPv6 路径证据 | 小样本网络响应 |
| macOS 隧道 / 系统代理 | 本地网络 DNS 迹象 | 连续请求稳定性 |

## 边界

v1 的原则是：能自动测就测，不能自动证明就不打扰用户。

| 不做 | 原因 |
| --- | --- |
| kill switch / 强制断网 | 会破坏当前网络状态 |
| 客户端来源审查 | 需要人工判断或额外权限 |
| 证书、描述文件、内核扩展、MDM 检查 | 不适合零交互流程 |
| 服务商商业模式判断 | 无法由一次网络体检自动证明 |
| 长期高峰期稳定性 | 需要多时段监控 |
| 银行、校园网、登录类站点 | 可能触发风控或涉及隐私 |

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
