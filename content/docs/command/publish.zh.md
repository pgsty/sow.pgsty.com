---
title: "sow publish"
linkTitle: "publish"
description: "将当前已验证 Generation 发布到配置的 filesystem 或 R2 目标。"
categories: [Command]
tags: [cli, publish, object-storage, filesystem]
url: "/zh/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` 将某个 Repository 的当前 Built Generation 交付到 `sow.yml` 的 `targets:` 中指定的
目标。目标已经绑定 Repository 与 Provider，因此命令不接受 `--repo` 或 `--dist`。

## 语法

```text
sow publish TARGET [--abort | --rebind] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--abort` | 放弃已对账、但尚未写入持久 commit intent 的尝试 | false |
| `--rebind` | 确认并记录允许修改的目标名称、公共端点或缓存 TTL | false |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-T, --timeout DUR` | 最长 Repository 等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 `sow.cli/v1` Envelope | false |

`TARGET` 必须是已配置的 `filesystem` 或 `r2` 发布目标。`--abort` 与 `--rebind` 互斥。

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
sow publish local
published demo generation=00000000000000000005 to local (filesystem): phase=grace objects=14
sow publish local
publication demo generation=00000000000000000005 to local is already current (noop)
```

## 重绑定可变目标配置

首次成功 publish 会持久绑定 Repository、存储命名空间与 Target Identity。之后配置发生漂移时，
SOW 会拒绝静默接受。只有诊断信息明确提示 `--rebind`，并且你已经复核变更后，才执行：

```bash
sow publish prod --rebind
```

如果改的是 `targets:` Map Key，请使用新目标名。Rebind 保留 active attempt 与 checkpoint identity，
并追加不可变、由操作者确认的 binding revision。

| 可以修改 | 不可变；必须配置新目标 |
|---|---|
| 目标名称 | Repository Identity |
| `public_endpoint` | Provider、存储 `endpoint` 或 region |
| `max_cache_ttl` | bucket 或 `prefix` |

Rebind 与发布使用同一组 Workspace/Repository 锁，并在数据库事务内重新核对不可变字段；它可以
继续前滚 active commit-intent attempt。Target Maintenance 未完成时禁止改变 TTL；filesystem
正在进行 conditional-delete 维护时禁止改变 `public_endpoint`。首次绑定必须运行普通 publish，
不能使用 `--rebind`。

## Abort 与恢复

`--abort` 只允许在持久 commit intent 之前使用。SOW 会对账已经创建的对象，保留后续安全判断所需
证据，并在不继续复制或删除远端对象的前提下放弃本次尝试。

写入 commit intent 后只能前向恢复：重新运行 `sow publish TARGET`，不能使用 `--abort`。

## 公共可见性校验

Provider 存储写入成功还不够：写入 Checkpoint 之前，发布流程还要校验 canonical
`public_endpoint`。HTTP(S) 目标以普通 GET 为最终权威；no-cache Probe 只能促进 Revalidation，
必须由之后的普通 GET 才能通过。陈旧内容与缺失对象按 `max_cache_ttl` 重试；408、425、429 与
5xx 使用较短的有界重试窗口。等待 Header 与 Body 空闲进度分别计时；响应超长时失败关闭。

Filesystem 可使用 `file://` 或 HTTP(S) 公共端点。执行条件删除时，`file://` 需要精确文件身份
缺失，HTTP(S) 则需要 canonical 404/410。R2 必须使用 HTTP(S) 公共端点；R2 Target GC 仍然
只报告候选，不执行远端删除。

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
| `1` | 文件系统、Provider、网络、验证或绑定冲突（包括必须 rebind） |
| `2` | 用法、工作区发现或 `sow.yml` 无效 |
| `4` | Repository 写锁不可用 |
| `5` | 本地/发布恢复证据不一致，或源不可交付 |
| `6` | 目标不存在/不安全，或其他安全前置条件拒绝 Publish/Abort/Rebind |

## 参见

- [`sow status`](/zh/docs/command/status/) 与 [`sow check`](/zh/docs/command/check/) —— 判断当前 Built Generation 是否正是准备交付的版本
- [`sow gc`](/zh/docs/command/gc/) —— 保守的目标维护
- [`sow.yml` 发布目标](/zh/docs/reference/config/#publication-targets) —— Provider 配置
- [发布模型](/zh/blog/design/publication/) —— 阶段、Receipt、恢复与 Cache Grace
