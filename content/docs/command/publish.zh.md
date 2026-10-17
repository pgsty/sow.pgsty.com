---
title: "sow publish"
linkTitle: "publish"
description: "将构建快照发布到文件系统或 R2 目标。"
categories: [Command]
tags: [cli, publish, object-storage, filesystem]
url: "/zh/docs/command/publish/"
weight: 1500
icon: fa-solid fa-cloud-arrow-up
---

`sow publish` 将当前构建快照复制到 `sow.yml` 的 `targets:` 中配置的目标。目标配置指定仓库与存储类型。需要发布最新期望状态时，先完成构建。

## 语法

```text
sow publish TARGET [--abort | --rebind] [-C|--workdir DIR] [-T|--timeout DUR | -N|--no-wait] [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `--abort` | 放弃尚未进入提交阶段的中断发布 | false |
| `--rebind` | 确认并记录允许修改的目标名称、公共端点或缓存 TTL | false |
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-T, --timeout DUR` | 最长仓库等锁时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出 JSON | false |

`TARGET` 必须是已配置的 `filesystem` 或 `r2` 发布目标。`--abort` 与 `--rebind` 互斥。

## 发布前准备 {#安全边界}

需要包含最新软件包与策略变更时，先运行 `build`。dirty 仓库仍可以发布上一个已完成的构建快照。

配置目标的 Web 服务或存储桶访问权限，使 `public_endpoint` 能读取发布文件，然后运行 `sow publish TARGET`。

## 发布协议

SOW 先核对本地文件与已完成的构建快照清单，再按以下顺序发布：

1. 包文件；
2. 使用独立内容 URL 的元数据；
3. `repomd.xml`、`Release` 等客户端入口；
4. 验证公共访问并保存发布检查点。

SOW 记录进度，中断后可用同一命令继续发布。目标已包含当前构建快照时，重复运行不产生变化。

```console
sow publish local
published demo generation=00000000000000000005 to local (filesystem): phase=grace objects=14
sow publish local
publication demo generation=00000000000000000005 to local is already current (noop)
```

## 重绑定可变目标配置

首次发布会记录仓库与目标绑定。修改目标名称、公共地址或缓存 TTL 后，使用 `--rebind` 记录新设置并继续发布：

```bash
sow publish prod --rebind
```

如果修改了 `targets:` 中的目标名，命令中使用新名称。

| 可以修改 | 不可变；必须配置新目标 |
|---|---|
| 目标名称 | 仓库身份 |
| `public_endpoint` | 存储类型、存储 `endpoint` 或区域 |
| `max_cache_ttl` | 存储桶或 `prefix` |

修改 `max_cache_ttl` 前，先完成目标维护。文件系统目标有未完成的删除操作时，也需先完成删除，再修改 `public_endpoint`。首次发布到新目标时，直接运行 `sow publish TARGET`。

## Abort 与恢复

发布中断后，重新运行 `sow publish TARGET` 继续发布。

需要放弃本次发布时，在进入 `commit_intent` 阶段前运行 `sow publish TARGET --abort`。SOW 核对已上传的对象，记录放弃结果，并保留远端文件。进入 `commit_intent` 后，使用普通发布命令完成本次发布。

已发布的包 URL 对应固定内容。内容改变时，使用新的包版本与文件名。如果远端文件与本次发布记录不符，按报告处理冲突，详见[故障处理](/zh/docs/reference/troubleshooting/)。

## 公共可见性校验

记录发布检查点前，SOW 会通过 `public_endpoint` 读取并验证已发布文件。HTTP(S) 校验使用普通 GET 请求。内容过期或缺失时，在 `max_cache_ttl` 范围内重试。

文件系统目标支持 `file://` 或 HTTP(S) 公共地址，R2 目标要求 HTTP(S)。每次 R2 发布都会列举目标前缀，并对每个对象执行 HEAD。一次更新会执行两轮这样的清单检查。
每页最多并发执行八个 HEAD 请求。这是内部上限，`publish` 不接受 `--jobs`。
上传重试只有在实际传输取得进展时，才会重置空闲超时。保留 R2 中的旧对象：目标 GC 只报告、不删除，后续发布还会核对远程前缀与已记录清单。

## 移除已发布视图

只要目标仍在配置中，SOW 就不允许本地变更移除它已发布的入口，例如整个 Dist、RPM 架构视图或配套签名文件。

需要停用该目标时，先停止向它发布，从 `sow.yml` 的 `targets:` 中删除对应配置，再运行 `sow config check`。随后可以移除本地视图。此操作保留原有远程文件与发布历史。需要发布删减后的仓库时，配置使用不同存储前缀的新目标，并将客户端切换到该目标。

## 退出行为

| 代码 | 触发条件 |
|---|---|
| `0` | 发布完成，或目标已经是当前构建快照 |
| `1` | 文件系统、存储类型、网络、验证或绑定冲突（包括必须 rebind） |
| `2` | 用法、工作区发现或 `sow.yml` 无效 |
| `4` | 仓库写锁不可用 |
| `5` | 本地/发布恢复证据不一致，或源不可交付 |
| `6` | 目标不存在/不安全，或其他安全前置条件拒绝 Publish/Abort/Rebind |

## 参见

- [`sow status`](/zh/docs/command/status/) 与 [`sow check`](/zh/docs/command/check/) —— 判断当前构建快照是否正是准备交付的版本
- [`sow gc`](/zh/docs/command/gc/) —— 回收目标中不再需要的文件
- [`sow.yml` 发布目标](/zh/docs/reference/config/#publication-targets) —— 存储类型配置
- [发布模型](/zh/blog/design/publication/) —— 阶段、回执、恢复与缓存宽限期
