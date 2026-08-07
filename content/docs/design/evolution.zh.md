---
title: "设计演进"
linkTitle: "设计演进"
description: "从 V1 仓库实验、v0.2 C2 视图到 0.3 单包体架构的演进路径。"
url: "/zh/docs/design/evolution/"
weight: 600
icon: fa-solid fa-timeline
---

SOW 的旧文档来自三套实质不同的系统。缺少版本边界时，互相矛盾的结论看起来像同时成立。
本页保留有价值的决策，同时明确它们各自的作用域。

## 时间线

| 版本线 | 主要问题 | 物理模型 | 处置 |
|---|---|---|---|
| V1 实验（2026-07） | 纳管 Pigsty 既有 APT/YUM 树与远端发布流程 | Git/CAS、route-aware 投影、edge/provider 契约 | 归档为研究与实现证据 |
| v0.2.0 | 交付紧凑的本地 Plain + Managed 仓库管理器 | 根 Pool + C2 view-local RPM 硬链接 | 已发布；操作文档继续在线 |
| 0.3 开发线 | 每个 Repository/target prefix 只发布一份正典包体 | 根 Pool + 纯元数据 view + target-scoped 发布 | 源码已实现；发布证据待完成 |

## V1 留下了什么

V1 大范围探索了既有仓库纳管、远端发布、供应商 fencing、边缘鉴权、迁移、恢复与大仓库证据。
它具体的 Git/CAS/route 模型大多已被替换，但几条原则保留下来：

- 身份必须绑定最终字节；
- 配置、本地状态、公共状态与供应商状态要有不同 owner；
- 发布是有顺序、可恢复的事务，不是一次 `rclone` 副作用；
- 破坏性远端操作需要精确 inventory 与供应商证据；
- 每项结论必须写明源码 revision、环境与验证层级。

旧 PRD、45 份 ADR、实现提示、迁移 runbook 与日期化 evidence 已封存在源码归档中，
不再充当当前命令或布局文档。

## v0.2 为什么选择 C2

v0.2 把产品收敛成一个本地单二进制管理器，提供两条隔离路径：`sow create` 构建平面仓库，
Managed Workspace 则管理 Package Object、Dist、membership、签名、事务构建、检查与日志。

RPM view 的实测表明：父级相对 href 可以被普通 DNF 消费，但默认 EL `reposync` 失败。
当时镜像能力属于发布门禁，因此 v0.2 选择 view-local 硬链接：

```text
pool/...                              正典包体
dists/el9/x86_64/pool/...             hardlink alias
dists/el9/x86_64/repodata/...         href="pool/..."
```

对于 v0.2 当时的合同，这是正确决定：它通过相关真实客户端矩阵，也让同文件系统 POSIX 树
保持本地磁盘去重。

## 0.3 为什么撤销这个决定

同一棵树发布到对象存储后，布局成本会突变。hardlink 身份消失，每个 Dist/architecture alias
都变成一次完整对象上传；Retention 与 snapshot 还会继续放大同一份包体。

0.3 调整优先级：每个 Repository/prefix 只有一条正典 payload 成为不变式；默认 `reposync`
消费正典树不再属于兼容承诺。需要自包含 RPM leaf 时，显式创建外部导出并承担可见的重复成本。

```text
pool/...                              唯一包体
dists/el9/x86_64/repodata/...         计算 href="../../../pool/..."
```

这不是篡改 v0.2 的历史，而是一份针对不同交付边界的新合同。

## 迁移边界

0.3 可以只读发现并展示冻结的 v0.2 配置/状态，但普通 writer 不会暗中升级。只有显式
`sow repo migrate` 才进入 journaled C2-to-single transition：

```text
planned -> staged -> commit_intent -> pointer_rollforward
        -> grace -> alias_delete -> final_manifest -> done
```

commit intent 前，`repo migrate --abort` 可以恢复 C2；之后只能前向恢复。旧 metadata 可能仍被
客户端持有，因此 legacy alias 会保留到 grace 结束，再按精确 inventory 删除，绝不触碰根 Pool。

对于缺少安全条件删除的远端供应商，迁移使用新的空 prefix，并通过外部 route/cutover 决策切换。
旧 prefix 整体退役；SOW 不会假装它已经物理去重。

## 归档策略

历史文件被保留，是因为它们能解释决策并提供日期化证据，不是因为每个文件都值得出现在导航中。
源码归档在语义上只读：

- 不修改旧 PASS 来迎合新实现；
- 新结果写成新的版本化记录；
- 保留负面 PoC，因为被否决的方案同样解释设计；
- 持续维护的设计与用户文档只放在本站；
- 取证细节查 Git 历史与封存归档。

这样既留下一个清晰的产品学习入口，也不会丢掉产生这些结论的推理过程。
