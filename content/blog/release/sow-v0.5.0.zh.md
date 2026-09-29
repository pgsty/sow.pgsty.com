---
title: "SOW v0.5.0"
linkTitle: "SOW v0.5.0"
date: 2026-09-29T00:00:00+08:00
authors: [Vonng]
description: "SOW v0.5.0 为 Plain RPM 仓库增加显式发布时间，在保留确定性构建的同时，支持迁移已有 YUM 仓库维护流程。"
categories: [Release]
tags: [release, plain, yum, signing, migration]
weight: -10
url: "/zh/blog/release/sow-v0.5.0/"
draft: false
---

SOW 0.5.0 主要解决已有平面 YUM 仓库接入 SOW 时的兼容问题。核心新增功能是
`sow create --metadata-timestamp SECONDS`：替换原有元数据生成器时，发布者可以保留合法的
发布时间，兼容已有 EL7 YUM 客户端的缓存。

安装方式见[下载页面](/zh/download/)，已有工作区的升级步骤见
[安装与升级](/zh/docs/start/install/#从-04-升级到-05)。

## 已有 YUM 仓库的发布时间

EL7 YUM 会比较新 `repomd.xml` 中最大的元数据时间戳与本地缓存。如果新索引的时间更早，
YUM 可能拒收它并继续使用旧索引。新的 checksum、不同的 revision 或更新的文件修改时间，
都不能替代这项比较。

此前 Plain `create` 始终写入零时间戳，便于复现输出，但直接接管已有正时间戳的在线仓库时会
遇到上述问题。0.5 增加了显式指定发布时间的入口：

```bash
# PUBLISH_TIME 由发布者根据已记录的发布历史选择。
sow create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
```

`SECONDS` 接受 `0` 到 `253402300799` 的整数。负数、非整数、溢出或重复参数会作为
用法错误拒绝。该参数只属于 `create`，不是 Managed `build`、`publish` 或 RPM leaf export
的选项。

| 项目 | 0.5 的行为 |
|---|---|
| 默认 data 时间戳 | 仍为 `0` |
| 显式时间戳 | 写入 RPM `repomd.xml` 的三条 data 记录 |
| `repomd.xml` revision | Plain 模式仍为 `0` |
| RPM 字节与包时间 | 此参数不改变它们 |
| 压缩 XML 与 gzip 头 | 只改此参数时保持原字节 |
| DEB 索引 | 不受此参数影响 |
| 重复构建元数据 | 包字节与选项相同，输出相同，空跑不写文件；强制重签属于另外的包修改操作 |

SOW 不会自动读取当前时钟，也不会替调用者维护发布时间。维护脚本应在上传目录外保存历史最大
发布时间；内容不变且现有索引、签名有效时复用它们，真正更新时递增时间。恢复旧包集合也属于
一次新发布，不能把发布时间一起倒退。若此前转换已经把在线索引重置为零，重建历史下限时还要
纳入可信的转换前备份。

`repomd.xml` 一旦变化，原有分离签名就不再有效。发布者必须重新签名、验签后再对外提供索引。
`--sign-with` 签署的是 RPM 包，不会签署 `repomd.xml`。
[迁移指南](/zh/docs/tutorial/yum-migration/)说明完整操作顺序，以及 SOW 命令与外围维护流程
各自负责的工作。

## RPM 依赖兼容性

依赖投影继续采用现代 createrepo_c 对事务前、事务后脚本依赖的处理规则。本次增加了这些阶段
单独出现，以及 Cloudberry、Percona、Grafana 软件包中实际阶段组合的回归用例。

这次增加的是测试覆盖，既没有修改依赖解析，也没有退回 createrepo_c 0.20.1 的输出规则。
依赖条目数量或 `pre="1"` 属性不同，本身不代表依赖丢失。相关上游变更见
[createrepo_c PR #427](https://github.com/rpm-software-management/createrepo_c/pull/427)。

## 仓库与发布修复

本版修复了历史 Dist 删除清理误删重新加入其他 Dist 的包。签名策略与 pool 路径检查前移，
不兼容输入会在提交期望成员前被拒绝；旧程序留下的中断操作有明确的恢复出口，保留已提交的
数据，字节遭篡改时仍然拒绝恢复。

已经发布的 payload 路径不能复用为不同内容，本地 GC 也不解除该约束；发布恢复不会覆盖
不可变 payload。SQLite 的只读快照不再让已经持久化的写入因 checkpoint 受阻而报错。
外部输入允许经过符号链接父目录，输入末级仍保留原有校验。

APT 验签兼容 GnuPG 的末尾换行约定，不忽略其他内容差异。新生成的 GPG 元数据签名统一使用
SHA-256，不受本地摘要偏好影响；新的元数据构建要求签名 key 当前可用。二进制归档与安装包
同时补齐第三方许可声明。

Pool 路径按大小写折叠比较，字节完全相同也不例外，因此仅大小写不同的文件名不会成为第二个 URL。
在大小写不敏感的文件系统上，SOW 还会拒绝仅大小写不同的源目录：工作区内在加入时拒绝，发布到
filesystem target 时在任何上传之前拒绝。并发执行的 `export rpm-leaf --hardlink` 与 `check`
不再把未变化的 Pool 字节误报为完整性错误。本地 `gc` 会忽略只存在于远端的发布清单条目（例如
R2 仅报告模式下保留的 payload）。

`sow repo migrate` 会报告 Schema 变化，未迁移的 Repository 会给出应执行的命令。退出码 `130`
只用于命令自身被中断。`file://` R2 凭据必须是普通文件；v0.4.0 中省略了非空且成员全被排除的
Dist 的 add 操作，现在可由下一次 build 收尾。

## 验收外围维护流程

迁移时应针对实际部署的 YUM/DNF 版本与架构，使用已有 metadata 缓存验收。保持 URL 和
repo ID 不变，从旧索引切换到 SOW 索引，再切换到下一次内容更新，检查索引刷新、实际包下载，
以及所配置的包与仓库签名校验。声明包数量或切换次数时，应同时保留命令、源码版本、输入清单
和对应结果，便于复核。

维护脚本保存时钟、复用签名、选择性重签的能力，不属于 `sow create` 新增的内置功能。
Plain 仍是平面目录的多文件重建流程：不生成旧式 SQLite 元数据或模块流，也不提供整个仓库的
原子切换。

## 升级与开发者说明

- 0.3 或 0.4 Managed 工作区必须先备份，再显式执行
  [`sow repo migrate`](/zh/docs/command/repo/#sow-repo-migrate)。Schema v13 为候选包池路径
  增加索引，`sow/v3` 配置与公共 `pool/ + dists/` 布局保持不变。随后逐个 build、check，
  一次性刷新受影响的 RPM 认证与 APT 元数据契约，之后未变化的 RPM 可复用匹配的 Built 证据。
- 取消操作先记录失败终态，再清理未提交的包字节；Ctrl-C 中断返回 130。空 Dist 全部输入被
  策略排除后仍能正常恢复。长读连接可以延后日志裁剪后的空间回收。
- Agent 元数据签名固定时钟，通过每个身份/时间的一次小消息探签选择实际可用子钥。新 APT
  发布拒绝弱签名摘要，历史验签与冻结操作恢复仍遵守原有语义。
- 长期维护的文档集中在本站。兼容性与性能检查分别移至 `qa/compat/`、`qa/perf/`，共享 RPM
  测试夹具移至 `internal/testdata/`；干净源码交付清单同步采用这些路径。
- 源码工具链升级为 Go 1.27.1，依赖采用 x/crypto v0.56.0；发布工作流固定 GoReleaser
  v2.18.2 及其 action 提交。
- 0.5.0 暂不支持 RPM v6 包格式的签名，签名工作流请使用 RPM v4 格式包。
- 2026-09-29 的源码 `govulncheck` 未发现可达漏洞。所依赖模块仍包含
  `GO-2026-5932` 通告，当前代码没有导入其受影响包；剥离后的二进制扫描仍可能报告模块命中。
  这不是“模块无任何通告”的声明，最终发布提交仍需重跑扫描。
- 打 tag 前，应针对最终发布版本完成全量 Go 测试、race、静态分析、漏洞与上游来源检查、
  确定性源码交付、客户端集成及归档/安装包校验。本地结果不能替代同一提交的 CI 与
  Integration 成功记录。

新建平面目录仍可沿用 `sow create DIR`。对于已有在线 YUM 仓库，请先阅读
[迁移已有 YUM 仓库](/zh/docs/tutorial/yum-migration/)，并在切换维护命令前确认实际二进制的
`create --help` 中列出了 `--metadata-timestamp`。
