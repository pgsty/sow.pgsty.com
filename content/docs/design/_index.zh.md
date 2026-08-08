---
title: "设计"
linkTitle: "设计"
description: "SOW 0.2.0 的架构决策：所有权、布局、发布、恢复与兼容性。"
url: "/zh/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

本节记录那些即使实现重写也应当保留的设计思路：SOW 在哪里划分所有权边界，哪些不变式
保证仓库可以安全复制与发布，以及为什么某项兼容性取舍被接受或拒绝。

{{% alert title="当前版本" color="primary" %}}
本站持续维护的文档全部描述 **SOW v0.2.0**。配置 schema 是 `sow/v3`；`sow.cli/v1`
之类是协议标识，不是产品版本号。
{{% /alert %}}

{{< doc-cards cols="2" >}}
{{< doc-card title="设计原则" link="/zh/docs/design/principles/" >}}
决定 SOW 拥有什么、哪些状态可重建、哪些异常必须失败关闭的一组核心不变式。
{{< /doc-card >}}
{{< doc-card title="系统模型" link="/zh/docs/design/model/" >}}
工作区、仓库、Dist、Package Object、Membership、Generation 与发布目标，以及为何它们各有其主。
{{< /doc-card >}}
{{< doc-card title="单包体布局" link="/zh/docs/design/single-payload/" >}}
为什么每个 Repository 只保留一条包体路径，同时渲染仅含元数据的 APT/RPM 视图。
{{< /doc-card >}}
{{< doc-card title="发布与恢复" link="/zh/docs/design/publication/" >}}
指针最后写入、提交意图、前向恢复、保留代与证据门禁垃圾回收。
{{< /doc-card >}}
{{< doc-card title="兼容性边界" link="/zh/docs/design/compatibility/" >}}
把协议、客户端、镜像工具、文件系统、HTTP 与对象存储兼容性分别验证，而不是压成一个绿色勾。
{{< /doc-card >}}
{{< /doc-cards >}}

## 权威与证据

这些页面描述当前契约。一项结论应明确写出它真正达到的证据层：

```text
设计 -> 实现 -> 聚焦测试 -> 真实客户端/Provider 实跑 -> 发布物
```

前一层通过，不代表后一层自动通过。[兼容性参考](/zh/docs/reference/compatibility/)
只陈述当前证据，不会把相邻测试升级成产品结论。
