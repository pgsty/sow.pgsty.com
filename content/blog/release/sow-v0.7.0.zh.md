---
title: "SOW v0.7.0"
linkTitle: "SOW v0.7.0"
date: 2026-11-09T09:00:00+08:00
lastmod: 2026-11-09
authors: [Vonng]
description: "SOW 0.7.0 新增平面 RPM 仓库裁剪与口令文件签名，修复恢复和发布缺陷，保持工作区格式兼容。"
categories: [Release]
tags: [release, signing, rpm, recovery]
weight: -40
url: "/zh/blog/release/sow-v0.7.0/"
---

SOW 0.7.0 新增 **平面 RPM 仓库裁剪** 与统一的 **口令文件签名接口** ，并修复发布审核中发现的迁移、恢复、发布、RPM 验签与版本排序缺陷。

**发布状态：** 当前版本正在准备 GitHub 草稿发布。正式公开前，二进制下载仍提供 **0.6.1** 。本文档描述 0.7.0，使用新参数前请先检查 `sow version`。

本说明覆盖 **0.6.1** 以来的变化。数据库 schema **v13** 、配置 schema **sow/v3** 与公开仓库布局保持不变，0.5.0 至 0.6.1 的工作区无需迁移数据库。

## 裁剪旧版 RPM

`sow prune DIR` 为每组包名与架构保留最高的 Epoch/Version/Release，先发布过滤后的索引，再删除旧版 RPM。

```bash
sow prune /srv/candidate --dry-run --protect age_18 --protect age_18-llvmjit
sow prune /srv/candidate --protect age_18 --protect age_18-llvmjit
```

- `--dry-run` 只校验和预览，不写入文件。可重复的 `--protect NAME` 保留精确包名的所有版本，每个名字都必须匹配到包。
- `--metadata-timestamp SECONDS` 设置索引发布时间，默认值与 `create` 一样为 `0`。
- 替换包必须通过内嵌摘要校验。SOW 将已校验、已索引的字节绑定到包含变更时间的稳定文件身份，在每次删除之前和完成之前检查。即使原地改写后恢复大小与 mtime，也会停止后续删除。
- 清理中断后可以重跑。已有的 `repo_complete` 标记只在成功完成后恢复；错误结果会报告已经完成的修改，已删除的软件包不会自动恢复。

Prune 面向本地发布源中顶层的普通二进制 RPM 文件。它拒绝托管工作区、DEB 包或索引、包文件符号链接、源码 RPM、同一包名与架构中相同的 EVR、RPM v6、带签名的 `repomd.xml`，以及 SOW 无法生成的独立元数据。Prune 不执行签名。缓存旧索引的客户端可能仍需要旧 RPM，发布裁剪结果前需安排相应的保留策略。

详见 [prune 命令参考](/zh/docs/command/prune/)。

## 用口令文件签名

通过 `--passfile PATH`、`SOW_GPG_PASSFILE` 或 `sow.yml` 中每个密钥的 `passfile`，为受保护的 RPM 包签名密钥及 RPM/APT 元数据密钥提供口令，包括 GPG agent 密钥。

```bash
sow create ./packages --sign-with 0123456789ABCDEF --passfile /run/secrets/gpg-password
```

优先级依次为命令行、密钥配置（包括旧的 `passphrase` 引用）、环境变量。文件为非空 UTF-8 单行，最多 64 KiB；只去掉末尾一个 LF 或 CRLF，不裁剪空格和制表符。参数使用普通路径，不接受 `file://`。命令行和环境变量中的相对路径以当前目录为基准，配置中的路径以工作区根目录为基准，不搜索默认文件。

同一接口也用于签名前检查、初始化、迁移、叶子仓库导出和中断恢复。口令不会进入进程参数、仓库状态或公开文件。口令文件必须是普通文件，路径中不能有符号链接；应放在仓库外并限制读取权限。旧版元数据 `passphrase` 引用继续受支持。

各命令的支持范围及外部 GPG 要求见[口令文件契约](/zh/docs/reference/config/#passfile)。

## RPM 兼容性

- **ECDSA 与 EdDSA 签名：** 接受现代 RPM 写入 tag 267（`RPMSIGTAG_DSA`）的这两种头部签名，真实 Ed25519 与 ECDSA 签名包现在可通过验证；错误放入该标签的 RSA 签名仍会被拒绝。
- **Caret 排序：** 修正 Version 与 Release 比较，使 `2.0^20250611` 这样的快照排在 `2.0.1` 之前，托管仓库的版本上限策略也会保留较新的正式版本。
- **外来元数据：** `create` 保持既有行为，替换 `repomd.xml` 时不保留 SOW 无法生成的 group、updateinfo、modules 或未知记录。这保持了对旧版 Pigsty 仓库的兼容，包括 Pigsty v4.4.0 在 EL8/9 上生成的 modules。现在文本模式会警告丢弃的数据类型，JSON 模式在非空时增加 `dropped_metadata` 字段。外部元数据文件和签名文件本身不由 SOW 维护。
- **Prune 元数据保护：** 修改前拒绝上述独立记录，发布前再次检查；包索引的 SQLite 和 zchunk 编码仍可接受。Prune 还会拒绝超过 16 MiB 检查上限的旧索引。Create 仍可替换超大或格式错误的旧索引，但不能报告无法读取的数据类型。

如果客户端需要额外元数据，请继续用相应的生成工具维护。重建后应重新生成外部 `repomd.xml.asc` 签名。

## 托管仓库与恢复

- **迁移后的仓库保持可写。** 已完成的 C2 迁移固定引用迁移时创建的 Generation，后续构建不再使 `check`、`build`、`add` 或 `gc` 拒绝该迁移锚点；`repo rm` 也不再把已完成迁移误判为活动转换。受影响的仓库升级后即可恢复，无需手工修复数据库。
- **保护全部已发布指针。** 撤下保护检查现在覆盖已发布 Generation 的全部指针，包括最近一次发布未改变的视图。只要配置中的目标仍在发布某个 Dist、架构或签名伴生文件，就会拒绝移除它。应先停用该目标绑定，或使用新的目标名称和前缀发布。旧的公开文件会保留，需单独清理，普通发布不会自动撤下它们。
- **无关离线目标不再阻塞操作。** 发布、撤销和目标 GC 只将所选目标与其他目标的预期物理路径比较，真实的物理路径重叠仍会被拒绝。
- **恢复写到一半的计划。** GC 在 planned 阶段发现空计划、残缺计划或哈希不符时，可在尚未删除任何文件的前提下丢弃计划；保留移除在原目标仍存在时可重建计划。已经发生破坏性操作后的矛盾状态仍会报错。
- **导出未重建的 Dist。** 后续 Generation 未重建、但仍为 clean 的 Dist 可执行 `export rpm-leaf`，签名和不签名两种情况均可。
- **容忍时钟回拨。** 中断恢复通过唯一活动操作的 ID 识别任务，不再按墙上时间排序选择操作。

## 依赖与发布检查

| 组件 | 0.6.1 | 0.7.0 |
|---|---|---|
| AWS SDK core / S3 | 1.47.3 / 1.114.4 | 1.47.8 / 1.114.9 |
| Smithy | 1.28.6 | 1.28.8 |
| SQLite / libc | 1.61.0 / 1.79.0 | 1.62.0 / 1.80.1 |
| Debian 包解析器 | 0.21.1 | 0.21.3 |
| YAML | `go.yaml.in/yaml/v3` 3.0.5 | `go.yaml.in/yaml/v4` 4.0.0 |
| GoReleaser | 2.18.3 | 2.20.0 |

构建基线仍为 Go **1.27.3** 。YAML 保留严格的单文档校验与规范化配置输出；受限的本地 RPM 解析器补丁及第三方许可声明随依赖变更更新。

Integration 新增 **EL8、EL9、EL10** 受保护密钥签名的必跑测试。EL8 检测 `rpmsign --rpmv3` 能力，只跳过工具不支持的重复签名场景。发布门禁覆盖单元和竞态测试、APT/DNF 客户端、S3 兼容发布、静态分析、漏洞可达性、可复现的干净源码构建，以及归档、RPM、DEB 内容检查。本次审核未运行可选的托管 R2 live 测试；macOS amd64 已交叉编译，但未在 arm64 审核主机上执行。

## 升级

停止写入任务，以保留硬链接的方式备份完整工作区，安装 0.7.0，再对每个配置中的仓库执行：

```bash
sow version
sow build -r REPOSITORY -C /srv/sow
sow check -r REPOSITORY -C /srv/sow
```

没有变化的构建为空操作。0.3 或 0.4 工作区仍需先执行 `sow repo migrate REPOSITORY`。Plain 仓库没有数据库迁移步骤。

含有 `passfile` 的配置不能由 0.6.1 或更早版本读取，降级前应删除这些字段。口令文件不允许符号链接的限制保持不变，RPM v6 仍不受支持。

本版本生成 Linux 与 macOS 的 `amd64`、`arm64` 归档、两个 RPM、两个 DEB，以及 `SHA256SUMS`。详见[安装与升级说明](/zh/docs/start/install/#升级到-070)和 [0.6.1 以来的完整差异](https://github.com/pgsty/sow/compare/v0.6.1...v0.7.0)。
