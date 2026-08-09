---
title: "sow publish"
linkTitle: "publish"
description: "将当前已验证 Generation 发布到配置的 filesystem 或 R2 目标。"
url: "/zh/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` 将某个 Repository 的当前 Built Generation 交付到 `sow.yml` 的 `targets:` 中指定的
目标。目标已经绑定 Repository 与 Provider，因此命令不接受 `--repo` 或 `--dist`。

## 语法

```text
sow publish TARGET [--abort] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--abort` | 放弃已对账、但尚未写入持久 commit intent 的尝试 | false |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-T, --timeout DUR` | 最长 Repository 等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

`TARGET` 必须是已配置的 `filesystem` 或 `r2` 发布目标。

## 发布协议

交付前，SOW 要求存在已完成的 Built Generation，并验证公开树与冻结 Generation Manifest 精确
一致；然后按以下顺序规划并写入对象：

1. 不可变包体；
2. 校验和寻址元数据；
3. 可变协议指针；
4. 验证并持久化 Checkpoint。

精确对象集合、Receipt、阶段与 commit intent 都会落盘，确保中断后可以对账恢复。目标已经位于
当前 Generation 时，重复发布是幂等空操作。

```console
sow publish prod
published pgsql generation=00000000000000000012 to prod (filesystem): phase=done objects=184
```

## Abort 与恢复

`--abort` 只允许在持久 commit intent 之前使用。SOW 会对账已经创建的对象，保留后续安全判断所需
证据，并在不继续复制或删除远端对象的前提下放弃本次尝试。

写入 commit intent 后只能前向恢复：重新运行 `sow publish TARGET`，不能使用 `--abort`。

## 安全边界

- SOW 只发布到配置目标，不接受任意目标路径。
- 尚未构建的 Desired 变化不会进入发布。dirty Repository 因而可以发布上一个完整 Built
  Generation；如果目标必须反映当前 Desired 状态，应先运行 `build`。
- 布局迁移与相互矛盾的恢复证据会阻止发布；可裁决的未完成 Dist 操作会在选择源 Generation
  之前恢复。
- 对象顺序保证包管理器指针不会引用尚不存在的内容。
- 发布命令不负责外部 Web Server、Bucket Policy、DNS 路由或缓存配置。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 发布完成，或目标已经是当前 Generation |
| `1` | 文件系统、Provider、网络或验证运行时错误 |
| `2` | 用法、工作区发现或 `sow.yml` 无效 |
| `4` | Repository 写锁不可用 |
| `5` | 本地/发布恢复证据不一致，或源不可交付 |
| `6` | 目标不存在/不匹配/不安全，或其他安全前置条件拒绝发布/Abort |

## 参见

- [`sow status`](/zh/docs/command/status/) 与 [`sow check`](/zh/docs/command/check/) —— 判断当前 Built Generation 是否正是准备交付的版本
- [`sow gc`](/zh/docs/command/gc/) —— 保守的目标维护
- [`sow.yml` 发布目标](/zh/docs/reference/config/#publication-targets) —— Provider 配置
- [发布模型](/zh/docs/design/publication/) —— 阶段、Receipt、恢复与 Cache Grace
