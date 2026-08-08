---
title: "兼容性边界"
linkTitle: "兼容性边界"
description: "SOW 如何分别验证协议正确性、客户端行为、镜像工具、搬迁、HTTP 规范化与存储供应商语义。"
url: "/zh/docs/design/compatibility/"
weight: 500
icon: fa-solid fa-table-cells
---

“兼容”太宽泛，不足以成为工程结论。一个包可能安装成功，但镜像工具拒绝同一份元数据；
一棵树可能在 POSIX 磁盘上去重，上传后却变成多个完整对象。因此 SOW 把兼容性拆成独立门禁。

## 分层

| 层级 | 问题 | 所需证据 |
|---|---|---|
| 格式 | 元数据是否符合 rpm-md / Debian archive 语法？ | parser 与结构校验 |
| 普通客户端 | `apt` / `dnf` / `yum` 能否刷新、解析、下载、验签并安装？ | 真实客户端实跑 |
| 镜像工具 | 指定镜像工具能否安全落地完整仓库？ | 该工具与具体版本 |
| 搬迁 | 整根复制后是否字节闭合且仍可消费？ | copy + manifest + 客户端 |
| HTTP/代理 | 相对 URL 是否在同一 prefix 内规范化，且无越界/双编码？ | 目标 HTTP 矩阵 |
| 存储 | 对象身份、条件操作、列表、缓存与删除是否符合状态机？ | 真实供应商协议测试 |

任何一行都不会从另一行或旧布局自动继承 PASS。

## `reposync` 的教训

发布前的 C2 工作曾测试让 RPM view 的元数据引用 `../../../pool/...`。在 AlmaLinux 9.8 上，普通
DNF 的 `makecache`、query、download 与 install 全部通过；默认 `dnf reposync` 却失败，
因为它把目标规范化到每仓库下载根之外，并通过 safe-path 检查拒绝写入。

C2 把默认 `reposync` 视为必选兼容面，因此在 view 内建立 `pool/...` 硬链接，
元数据 href 不再包含父级跳转。native + neutral 包矩阵最终通过普通 DNF 与默认 `reposync`；
即使复制后丢失硬链接身份，功能也保持正常。

这个结果仍是 C2 原型的有效证据，但不能证明 v0.2.0 正典单包体布局通过默认 `reposync`。

## v0.2.0 契约

当前版本明确作出以下选择：

- 必须支持 APT 与普通 DNF 消费完整 Repository；
- 必须支持 whole-root 搬迁；
- 默认 EL `reposync` 消费正典 Repository 属于明确不支持；
- 完整外部 RPM leaf export 是预期的 `reposync` fallback，需要独立真实客户端正例；
- DNF4/DNF5 的 `--safe-write-path` 等选项只能作为 best effort 说明，不能改变正典布局。

## 文件系统兼容

v0.2.0 的正典正确性不依赖 inode 或 hardlink count。普通 copy、tar 解包或对象存储上传之后，
Repository 仍必须正常工作。硬链接只允许用于私有事务状态、小型不可变 APT by-hash alias，
以及显式选择且可信的兼容导出。

本地 builder 仍依赖 POSIX 锁与原子 rename；发布树是静态的，并不意味着 NFS 等网络文件系统
自动成为受支持的构建环境。

## HTTP 与代理边界

RPM 父级相对 href 会在获取前解析。每个受支持目标都必须证明：

- `GET`、`HEAD`、Range、长度、ETag 与缓存行为正确；
- 规范化后的请求落在同一 prefix 内的正典 `pool/...` 对象；
- encoded dot segment、反斜杠、双编码、redirect 与 prefix escape 被拒绝；
- 公私鉴权覆盖完整 Repository prefix，包括 `pool/`。

edge rewrite 或部署绝对 URL 不能成为正典正确性的必要条件。

## 供应商能力边界

支持发布不代表支持安全删除。供应商可能通过流式上传、条件 put、list 与公开读取验证，
却没有原子条件删除。SOW 按供应商记录能力，并禁用无法证明安全的状态机分支。

v0.2.0 的 R2 路径已经实现，并在 GitHub Integration 中针对固定版本的 S3-compatible MinIO
fixture 运行。新的授权非生产 Cloudflare R2 实跑仍是独立供应商证据门；R2 物理删除按设计
禁用，target GC 只记录 retained candidate。

## 状态词如何阅读

| 状态 | 含义 |
|---|---|
| `DESIGNED` | 只有书面契约 |
| `IMPLEMENTED` | 源码路径已经存在 |
| `LOCALLY VERIFIED` | 聚焦本地/fault/mock 检查通过 |
| `LIVE VERIFIED` | 指定 revision 上的真实客户端或供应商通过 |
| `RELEASED` | 打包发布物包含该能力并通过所需门禁 |
| `UNSUPPORTED` | 有意排除在契约之外 |
| `UNVERIFIED` | 没有当前证据；既不等于失败，也绝不等于 PASS |

当前客户端与工具矩阵见操作层[兼容性参考](/zh/docs/reference/compatibility/)。那里会区分普通
Repository 消费与显式 RPM leaf 导出，不会把 C2 结果升级成当前正典布局的结论。
