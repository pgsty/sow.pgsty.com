---
title: "设计"
linkTitle: "设计"
description: "SOW 的长期架构决策：所有权、状态、发布顺序、恢复与证据。"
url: "/zh/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

本节记录 SOW 的所有权边界，以及保证仓库能够安全构建、复制、发布、恢复与回收的不变式。

{{< doc-cards cols="2" >}}
{{< doc-card title="设计原则" link="/zh/docs/design/principles/" >}}
决定 SOW 拥有什么、哪些状态可重建、哪些异常必须失败关闭的一组核心不变式。
{{< /doc-card >}}
{{< doc-card title="系统模型" link="/zh/docs/design/model/" >}}
工作区、仓库、Dist、Package Object、Membership、Generation 与发布目标，以及为何它们各有其主。
{{< /doc-card >}}
{{< doc-card title="发布与恢复" link="/zh/docs/design/publication/" >}}
指针最后写入、提交意图、前向恢复、保留代与证据门禁垃圾回收。
{{< /doc-card >}}
{{< doc-card title="协同发布设计提案" link="/zh/docs/design/coordinated-publication/" >}}
面向 v0.4.0 的用户流程与实现计划：由 SOW 编排、rclone 执行，并确定性恢复中断。
{{< /doc-card >}}
{{< /doc-cards >}}

规范单包体布局与其实现机制统一写在[包池与元数据视图](/zh/docs/feature/views/)；平台与集成要求
见[平台与集成](/zh/docs/reference/compatibility/)。

## 权威与证据

每项运维结论都应与它真正达到的证据层一致：

```text
设计 -> 实现 -> 聚焦测试 -> 真实客户端/Provider 实跑 -> 发布物
```

前一层通过，不代表后一层自动通过。[平台与集成](/zh/docs/reference/compatibility/)
记录自动化客户端、Provider 与文件系统覆盖；Release 制品属于独立交付门禁。
