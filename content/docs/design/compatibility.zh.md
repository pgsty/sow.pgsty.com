---
title: "兼容性边界"
linkTitle: "兼容性边界"
description: "为什么 SOW 分别评估格式、产品 CLI、客户端、镜像工具、文件系统、HTTP 与 Provider。"
url: "/zh/docs/design/compatibility/"
weight: 500
icon: fa-solid fa-table-cells
---

“兼容”不是一个状态。SOW 分开处理以下契约：

| 契约 | 所需证据 |
|---|---|
| 元数据格式 | parser、renderer 与 closure 校验 |
| 产品 CLI | 生产二进制在全新 Workspace 上运行 |
| 包管理器 | 指定客户端完成刷新、解析、按配置验签、下载与安装 |
| 镜像工具 | 指定工具在自身路径规则内落地完整仓库 |
| Workspace 文件系统 | 指定文件系统上的锁、fsync、安全路径与原子 rename |
| 发布 Provider | 当前 CLI 路径在该 Provider 上完成发布、恢复与公共验证 |
| HTTP/CDN | 实际 URL 规范化、访问策略、缓存行为与协议入口 |

一个契约的证据不会提升另一个契约的状态。

## 规范 Repository 与镜像 leaf

一个 Repository 拥有一条规范包池。RPM view 只保留元数据，并通过父级相对 href 指回包池。
只有把 `pool/ + dists/` 一起交付，这个 whole-Repository 布局才闭合；它不符合默认
`dnf reposync` 的 leaf-root 安全规则。

因此 SOW 明确定义两种不同产物：

- 作为 `pool/ + dists/` 整体服务和发布的规范 Repository；
- 为下游镜像流程生成、带本地 `pool/` 的显式 `sow export rpm-leaf` 产物。

任一产物通过都不能证明另一个。export 也不属于 membership、Generation、retention 或
publication 状态。

## 文件系统边界

Workspace 正确性依赖本地 POSIX 语义。公共树不依赖 pool 与 view 之间的包体硬链接，可以整根
复制；私有工作区状态不能进入服务前缀。

安全部署应使用 `sow publish`，或先 stage 完整已校验树，再原子切换操作者拥有的父级引用。
直接对 live tree 做无序原地同步，不继承 SOW 的指针顺序与恢复保证。

## Provider 边界

解析器接受 `filesystem` 与 `r2`，但配置通过只是第一道门。Provider 结论还需要上传、重放、
恢复、公共验证，以及在允许删除时的条件删除证据。

- filesystem 发布已实现，并通过当前 CLI 做过本地实跑。
- R2 发布已实现，但现行 MinIO Integration 作业测试的是另一套 Provider package，因此当前
  R2 CLI/Provider 端到端门禁仍未完成。
- R2 target GC 按设计只报告，绝不发送对象删除。

## HTTP 边界

SOW 发布文件并验证配置的 `public_endpoint`；它不拥有 Web server、反向代理、CDN、DNS、
鉴权或缓存配置。部署必须自行验证完整 prefix 上的 RPM/DEB 入口、包路径、签名、range/length
行为与访问策略。

## 状态术语

| 术语 | 含义 |
|---|---|
| 已实现 | 源码路径存在 |
| 聚焦测试已验证 | 仓库测试覆盖指定行为 |
| 客户端已验证 | 指定真实客户端完成指定操作 |
| Provider 已验证 | 当前 CLI 在该 Provider 上完成指定流程 |
| 不支持 | 明确排除在契约外 |
| 未验证 | 没有当前证据；既不是 PASS，也不是已知失败 |

各表面的当前状态见[兼容性参考](/zh/docs/reference/compatibility/)。
