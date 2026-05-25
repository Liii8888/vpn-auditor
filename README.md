# vpn-auditor

[English](README.en.md)

连好代理。运行 skill。等结果。

`vpn-auditor` 是一个 Codex skill，用来自动体检 VPN / 代理 / 梯子。它不会让你手动断开 VPN、切换网络、解释客户端来源、等晚高峰，或者去打开一堆网站确认。它只做能自动证明的检查，然后给出一份简洁的中文报告。

```text
结论：87/100。好，日常很稳，未命中一票否决。
```

## 你会看到什么

| 模块 | 说明 |
| --- | --- |
| 结论 | 最终分数、等级判断、一票否决状态 |
| 自动检测证据 | 出口 IP、DNS 路径、隧道/代理状态、目标可达性 |
| 影响因素 | 为什么分数被拉低，但不展示详细权重表 |
| 本轮未覆盖 | 因为需要人工配合或破坏性测试而跳过的项目 |

## 它会自动检查

- 公网出口 IP 和多个探针的一致性
- DNS 路径证据，包括 macOS 的默认 resolver 和 scoped resolver
- IPv6 路径证据
- macOS 隧道接口和系统代理状态
- 公开目标站点可达性
- 小样本网络响应
- 连续请求稳定性

## 它不会做什么

有些测试确实有价值，但不适合放进零交互流程。v1 宁可跳过，也不把用户变成测试员。

- 不测试 kill switch
- 不强制断开 VPN
- 不做人肉客户端来源审查
- 不检查证书、描述文件、内核扩展或 MDM
- 不判断服务商商业模式
- 不做长期高峰期监控
- 不访问银行、校园网或其他登录类站点

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

报告会给出最终分数、结论和证据，但不会打印详细权重表。这样报告更易读，也不容易被刻意刷分。项目本身仍然可审计：实现逻辑在 `scripts/vpn_auditor.py`。

## License

MIT
