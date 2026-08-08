---
title: "设计"
linkTitle: "设计"
description: "SOW 背后的架构决策：所有权、仓库布局、发布、兼容性与版本演进。"
url: "/zh/docs/design/"
weight: 350
icon: fa-solid fa-compass-drafting
---

本节记录那些即使实现重写也应当保留的设计思路：SOW 在哪里划分所有权边界，哪些不变式
保证仓库可以安全复制与发布，以及为什么某项兼容性取舍被接受或拒绝。

{{% alert title="当前版本" color="primary" %}}
本站持续维护的用户、参考与设计文档全部描述 **SOW v0.2.0**。单包体布局、发布目标、
保留与垃圾回收、显式迁移以及 RPM 兼容导出都属于这一版本线。`sow.cli/v1` 这类 wire
标识与 `sow/v3` 配置 schema 独立演进，不是产品版本号。
{{% /alert %}}

{{< doc-cards cols="2" >}}
{{< doc-card title="设计原则" link="/zh/docs/design/principles/" >}}
决定 SOW 拥有什么、哪些状态可重建、哪些异常必须失败关闭的一组核心不变式。
{{< /doc-card >}}
{{< doc-card title="系统模型" link="/zh/docs/design/model/" >}}
工作区、仓库、Dist、Package Object、Membership、Generation 与发布目标，以及为何它们各有其主。
{{< /doc-card >}}
{{< doc-card title="单包体布局" link="/zh/docs/design/single-payload/" >}}
v0.2.0 为什么让每个 Repository 只保留一条包体路径，同时渲染仅含元数据的 APT/RPM 视图。
{{< /doc-card >}}
{{< doc-card title="发布与恢复" link="/zh/docs/design/publication/" >}}
指针最后写入、提交意图、前向恢复、保留代与证据门禁垃圾回收。
{{< /doc-card >}}
{{< doc-card title="兼容性边界" link="/zh/docs/design/compatibility/" >}}
把协议、客户端、镜像工具、文件系统、HTTP 与对象存储兼容性分别验证，而不是压成一个绿色勾。
{{< /doc-card >}}
{{< doc-card title="设计演进" link="/zh/docs/design/evolution/" >}}
v0.1.0 实验、未正式发布的 C2 原型与当前 v0.2.0 单包体布局之间的关系。
{{< /doc-card >}}
{{< /doc-cards >}}

## 权威与证据

这里的页面是持续维护的设计权威。历史 PRD、评审对话、ADR 与日期化验收报告可从 Git
历史和版本标签中查阅；它们仍能证明当时 revision 与环境里的事实，但不能悄悄重定义当前产品。

一项结论要依次经过不同证据层：

```text
设计契约 -> 源码实现 -> 聚焦测试 -> 真实客户端/供应商证据 -> 发布
```

前一层通过，不代表后一层自动通过。[兼容性设计](/zh/docs/design/compatibility/)与各版本发布说明
都会明确写出最高验证层级。
