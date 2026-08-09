---
title: "sow check"
linkTitle: "check"
description: "执行完整的只读完整性与可交付校验流水线。"
url: "/zh/docs/command/check/"
weight: 1300
icon: fa-solid fa-list-check
---

`sow check` 是 Managed Repository 的深度只读门禁。它哈希包体、校验状态、重建期望视图并验证
已声明签名；不会修复、构建、恢复 Operation，也不会获取写锁。

## 语法

```text
sow check [-j|--jobs N] [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-j, --jobs N` | 并行校验 Worker 数，不得小于 `1` | 逻辑 CPU 数 |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 选择 Repository | [选择规则](/zh/docs/command/) |
| `-d, --dist NAME` | 校验指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

## 校验层

SOW 0.2.0 按顺序报告九层校验：

| 层 | 校验内容 | `checked` 计数 |
|---|---|---|
| `config` | `sow.yml` 能否针对该 Repository 解析并通过校验 | 配置对象 |
| `retained` | 显式保留记录与冻结 Generation Manifest | 保留记录 |
| `state` | SQLite `quick_check`、外键、日志与恢复证据 | 一个状态库 |
| `public-modes` | 服务目录中所有文件与目录权限 | 已检查路径 |
| `package-bytes` | 包池与私有 pending 包体的 SHA-256 | Package Object |
| `desired-membership` | Membership 能否在当前策略下解析到真实对象 | 成员关系 |
| `index` | 渲染索引是否与其声明的成员关系一致 | Dist |
| `signature` | 所有已声明元数据/软件包签名是否有效 | 签名 |
| `generation-manifest` | Built Generation Manifest 是否与磁盘文件一致 | 一个 Manifest |

```console
sow check
repository=pigsty status=clean ready_to_copy=true revision=5 generation=5
config	ok=true	checked=5
retained	ok=true	checked=0
state	ok=true	checked=1
public-modes	ok=true	checked=67
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=1
```

## dirty 不可交付

dirty Repository 的九层校验可以分别成立：旧 Built Generation 完整，新 Desired 状态也有效；
但二者不一致，因此整体仍未通过交付门禁：

```console
sow check
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=5
...
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

此时退出 `5`。运行 [`sow build`](/zh/docs/command/build/) 后重新校验，不应让发布流水线放行该状态。

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 全部校验层通过，Repository 可复制交付 |
| `1` | 校验期间发生 I/O 错误 |
| `2` | 用法错误、未发现工作区或隐式 Repository 选择有歧义 |
| `5` | 某个校验层失败，或 Repository 不可交付 |
| `6` | 显式指定的 Repository 或 Dist 未配置 |

## 参见

- [`sow status`](/zh/docs/command/status/) —— 低成本状态查询
- [`sow build`](/zh/docs/command/build/) —— 收敛 Desired 与 Built
- [退出码](/zh/docs/reference/exit-codes/) —— dirty 为什么映射到 `5`
- [可观测与审计](/zh/docs/feature/audit/) —— 组合使用校验与审计
