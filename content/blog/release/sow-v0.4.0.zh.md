---
title: "SOW v0.4.0"
linkTitle: "SOW v0.4.0"
date: 2026-08-24
authors: [Vonng]
description: "SOW v0.4.0 让 Managed 校验严格收敛为单遍认证，引入独立 RPM 信任环校验与安全发布目标重绑定，并强化迁移、恢复与公共交付验证。"
categories: [Release]
tags: [release, managed, signing, publish, migration]
weight: 1
url: "/zh/blog/release/sow-v0.4.0/"
draft: false
---

SOW 0.4.0 是一次面向 Managed 仓库的完整性与恢复版本：它明确了深度校验的 I/O 契约，
禁止跨无关密钥拼装 RPM 信任，提供可审计的发布目标可变配置修正路径，并补齐 v0.3 迁移与
发布中断恢复的剩余缺口。

Plain 仓库行为与公共 `pool/ + dists/` 布局均未改变。

## 从 0.3 升级

> [!IMPORTANT] 必须逐个显式迁移 v0.3 Repository
> 先停止全部 Workspace 写入并完成备份，再安装 0.4.0；在执行普通读写命令之前，对每个 Repository 运行一次
> `sow repo migrate REPOSITORY`。迁移是显式、单向的；完成后不要再用 SOW 0.3 打开数据库。

```bash
cp -a /srv/sow /srv/sow.backup-before-0.4.0
sow repo migrate pigsty -C /srv/sow
sow repo migrate pgsql -C /srv/sow
sow check -r pigsty -C /srv/sow
sow check -r pgsql -C /srv/sow
```

Schema v11 修复了 v0.3 的 Dist 生命周期缺陷：过去一个 Dist 变化时，另一个仍 dirty 的 Dist
可能被遗漏，导致 Repository 错误显示为 clean；现在 Repository 状态始终在修改 Dist 的同一事务
中派生。迁移也会修复发布与签名者证据，但不会猜测 v0.3 未记录的历史签名身份：这类身份保持
显式未验证，不能变成 retained trust assertion。

Schema v12 回填只追加的发布目标绑定账本。首次绑定、迁移回填与之后每次操作者确认的 rebind
都会形成彼此独立、不可变的 revision。

## 每个物理包体只做一次真实性认证

每次 `sow check` 都会对每个唯一物理包体执行恰好一次权威内容哈希，即使缓存指纹仍然匹配也
不会跳过。证据绑定设备号、inode、size、mtime、ctime，以及真正被读取的文件描述符。同一物理
对象的硬链接可以共享证明；路径替换或并发身份变化会让证据失效并失败关闭。

验证 retained Generation、遍历最终 Manifest 与生成 `sow changes` 时复用同一份已认证证据。
因此增加 retained Generation 或 Dist 不会放大包体哈希次数。DEB 与无签名 RPM 只需一遍完整
包体流；带签名 RPM 最多再增加一遍从主 Header 到 EOF 的签名流，且与 Dist 或信任环数量无关。

软件包事实也只按本次选中的摘要集合，以有界、确定性的 SQLite 批次读取。64 MiB 包体的暖构建
不读取包体；指纹漂移与 facts 缺失共享同一次权威包体读取，不再分别扫描。

## 独立 RPM 信任环

RPM 嵌入签名会在每个候选 trust ring 内独立验证：所有可识别签名 packet 必须在同一个 ring 中
通过，且至少一条通过的路径必须认证 payload。这样既保留历史 CentOS v3/v4 签名与有意双签包的
支持，又禁止把不同 ring 的 packet×key 成功项拼成虚假的单 key retained 信任结论。

当前策略 ring、每个 retained 单 key ring 与组合 trusted ring 共用同一遍签名流。增加密钥只会
改变授权结论，不会增加读取包体的次数。

## 安全重绑定目标与公共验证

`sow publish TARGET --rebind` 是显式、由操作者确认的修正路径：它允许修正目标的可变配置，
同时保留原存储身份与恢复状态。

| 可通过 `--rebind` 修改 | 必须配置新目标 |
|---|---|
| 目标名称 | Repository 身份 |
| `public_endpoint` | Provider 或存储 `endpoint` |
| `max_cache_ttl` | region、bucket 或 `prefix` |

普通 publish 遇到不一致时会明确提示 `--rebind`，绝不会静默接受新值。Rebind 与 publish 使用同一
组独占锁，追加一条审计 revision，并可继续前滚处于 commit-intent 的 active attempt。目标维护
未完成时禁止改变 TTL；filesystem 正在进行 conditional-delete 维护时禁止改变公共端点。历史
grace deadline 永远不会被缩短。

Filesystem 与 R2 的 HTTP(S) 公共端点现在共用同一套强化 verifier。响应 Header 与 Body 空闲进度
分别设定 Deadline，因此大对象只要持续前进，即使总传输超过两分钟也可完成。普通 canonical GET
始终是最终权威；no-cache 请求只用于促进 revalidation。陈旧内容与 404 按 `max_cache_ttl` 等待，
408/425/429/5xx 使用较短的有界重试窗口，超长响应失败关闭。Filesystem 公共缺失必须最终由
canonical 404/410 证明。R2 远端删除仍明确禁用，Target GC 只报告候选。

Filesystem 目标还会在持久绑定之前按 prospective physical path 检查别名，包括大小写不敏感
卷上的大小写别名。预检失败不会留下 binding row，也不会创建目标 prefix。

## 恢复、CLI 与实现收敛

- 增量发布恢复只接受每个指针的精确旧 Checkpoint 或目标 Generation 字节；未知或第三种身份
  仍然失败关闭。
- 日常发布只验证精确 Changed Object Set，不再下载完整 Public Generation。No-op 与
  Applied-checkpoint Recovery 复用完整私有 Inventory Evidence；Target GC 只扫描所需协议 Pointer。
- R2 操作采用分阶段 Header/Idle Deadline、有界条件式 Multipart Upload、可重试读写，并在
  Complete Multipart 前核对整对象 SHA-256。
- Generation signer row 成为覆盖局部构建、Dist 增删、迁移、Retention 与本地 GC 的精确
  Manifest side table。
- 默认重复执行 `sow add` 时，即使 Package Object 已复用，也会收敛先前 `--skip` 或配置变更
  留下的选中 dirty Dist。
- `sow rm --check` 与写操作共享配置门禁，返回精确、完全不写入的预览；结果不再依赖 scratch
  文件系统是否同设备。
- 所有 Managed 命令现在都有面向人的输出；`--json` 继续提供稳定 `sow.cli/v1` Envelope，并在
  失败时保留已提交的部分结果及诊断性的 check/preview 结果。
- 退役的 APT v1 Builder、External Sort、Empty-Dist 实现与 Git-tracked by-hash ledger 已移除；
  当前 Plain/Managed APT 解析与渲染路径仍有覆盖。

## 验证与制品

Release 门禁覆盖完整 Go 测试、vet、staticcheck、dead-code reachability、漏洞与 RPM Fork
Provenance 检查、Race Test、Linux amd64/arm64 构建，以及上述确定性包体/facts I/O 契约。
Release 二进制使用 Go 1.27.0 从 `v0.4.0` 源码 Tag 构建。从源码构建现在要求 Go 1.27.0 或更新
版本（0.3 为 1.26.5）；AWS SDK、SQLite、压缩与加密依赖同步刷新，质量门禁固定 staticcheck
v0.8.1、deadcode v0.49.0 与 govulncheck v1.7.0。

本次制品包含四个 Linux/macOS 归档、两个 RPM、两个 DEB 与 `SHA256SUMS`。每个归档包含
`sow`、`README.md`、`CHANGELOG.md` 与 `LICENSE`；Linux 原生包随二进制安装 Apache-2.0
许可证。

## 获取发布版本

通过[下载页面](/zh/download/)获取平台对应命令与已验证摘要，或查看
[GitHub Release](https://github.com/pgsty/sow/releases/tag/v0.4.0)。安装后先运行 `sow version`，
逐个迁移 v0.3 Repository，再以 `sow check` 作为发布前门禁。

长期维护的契约见 [Managed 工作区](/zh/docs/feature/managed/)、
[签名模型](/zh/docs/feature/signing/)与[发布与恢复](/zh/blog/design/publication/)。
