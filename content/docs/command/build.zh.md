---
title: "sow build"
linkTitle: "build"
description: "根据期望成员与当前配置构建本地索引。"
categories: [Command]
tags: [cli, managed, generation]
url: "/zh/docs/command/build/"
weight: 1200
icon: fa-solid fa-hammer
---

`sow build` 更新本地索引，使其与期望成员和当前配置一致。在 `add --skip`、`rm --skip` 或修改策略后运行此命令。开始新构建前，它会恢复未完成的本地仓库操作。

## 语法

```text
sow build [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-j, --jobs N` | 并行工作线程数，不得小于 `1` | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择仓库 | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 构建指定 Dist；可重复 | 全部受影响 Dist |
| `-T, --timeout DUR` | 最长等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

不带 `-d` 时，SOW 构建所选仓库中全部受影响 Dist；带 `-d` 时只构建指定 Dist，
未选择的变化继续保持 dirty。

## 结果

不带 `--json` 时，`build` 输出一行人类可读摘要：

```console
sow build -r demo -d el9
built repository=demo operation=2769214987359113555 dists=el9 revision=4 generation=00000000000000000005 dirty=false
```

脚本读取结果时，使用 `--json`。

## 空操作构建

成员关系、相关策略、渲染设置与签名配置均未变化时，`build` 不执行构建，也不生成新的构建快照：

```console
sow build -r demo -d el9
build repository=demo dists=el9 already current (noop) revision=4 generation=00000000000000000005 dirty=false
```

## 应用策略变更 {#策略收敛}

`build` 会重新执行当前 `exclude` 与 `limit` 策略。收紧策略可能移除期望成员；
放宽策略不会自动恢复已被移除的包，需要重新运行 [`sow add`](/zh/docs/command/add/)。

## 提交与恢复

SOW 先将所需的待构建包放入 `pool/`，再写入索引，最后更新 `repomd.xml`、`Release` 等客户端入口。一次构建可以包含多个 Dist，它们共用本次构建快照；未选择的 dirty Dist 仍需要构建。

构建中断后，重新运行此命令。SOW 根据操作日志完成或回滚未完成的工作。如果日志、数据库与文件不一致，命令会报告完整性错误。使用 `sow check` 与 `sow log` 查看受影响的状态。

## 进度事件

耗时较长的构建会向操作日志追加结构化 `build_progress` 记录。每条事件包含 `phase`、
`completed`、`total` 与 `jobs`。当前阶段为：

- `rendering`；
- `promoting_payload`；
- `publishing_dists`；
- `normalizing_public_tree`；
- `finalizing`。

使用 [`sow log OPERATION`](/zh/docs/command/log/#查看单条-operation)
查看明细。

## 元数据签名

在 `sow.yml` 中配置元数据签名。配置的密钥引用或指纹改变时，
相关 Dist 变为 dirty，下一次 build 重新签名。

- RPM：总是生成 `repodata/repomd.xml`；配置签名后额外生成 `repomd.xml.asc`。
- DEB：总是生成 `Release`；配置签名后额外生成 `InRelease` 与 `Release.gpg`。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 构建成功或无需操作 |
| `1` | 渲染、签名或文件系统错误 |
| `2` | 用法错误、未发现工作区或隐式仓库选择有歧义 |
| `4` | 仓库写锁不可用 |
| `5` | 无法安全完成恢复，或仓库处于 `error` |
| `6` | 显式范围未配置，或当前配置拒绝既有状态 |

## 参见

- [`sow status`](/zh/docs/command/status/) —— 判断是否需要构建
- [`sow check`](/zh/docs/command/check/) —— 验证构建结果
- [`sow changes`](/zh/docs/command/changes/) —— 查看生成的文件差异
- [事务与恢复](/zh/docs/feature/transactions/) —— 完整提交协议
