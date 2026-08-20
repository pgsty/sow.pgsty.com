---
title: "参考"
linkTitle: "参考"
description: "配置 Schema、包引用、磁盘布局、退出码、JSON 输出、平台与集成。"
url: "/zh/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

这一部分记录配置字段、包引用、路径、退出码、JSON、平台与集成等稳定契约。CLI 语法和状态变化
见[命令](/zh/docs/command/)，使用模型见[上手](/zh/docs/start/)。

输出示例只说明形态；标识符、路径、哈希、时间戳与计数会随工作区变化。二进制自带的
`sow help` 始终是精确语法权威。

{{< cards >}}
{{< card title="配置参考" link="/zh/docs/reference/config/" >}}
完整配置 schema：工作区、仓库、Dist、成员策略、签名与发布目标。
{{< /card >}}
{{< card title="包引用" link="/zh/docs/reference/package-ref/" >}}
命令行上指代一个软件包的五种写法、歧义如何裁决,以及 `rm` / `show` / `where` 各自接受哪些形态。
{{< /card >}}
{{< card title="仓库布局" link="/zh/docs/reference/layout/" >}}
Plain 与 Managed 两种模式下 SOW 创建的每一条路径、包池分组规则、名称约束,
以及绝对不能通过 HTTP 暴露的目录。
{{< /card >}}
{{< card title="退出码" link="/zh/docs/reference/exit-codes/" >}}
七个退出码分别代表什么。
{{< /card >}}
{{< card title="JSON 输出" link="/zh/docs/reference/json/" >}}
`sow.cli/v1` Envelope、各顶层字段含义与主要命令族的 Result 形态。
{{< /card >}}
{{< card title="平台与集成" link="/zh/docs/reference/compatibility/" >}}
Release 目标、文件系统要求、仓库客户端检查、发布 Provider，以及各项自动化集成的确切范围。
{{< /card >}}
{{< /cards >}}

## 约定

命令示例不带 `$` 提示符，方便整块复制。输出块只代表结构，可变值与长结构会在标注处省略。
二进制自带的 `sow help` 始终是精确语法权威。

语法块中占位符用大写(`NAME`、`DIR`、`PACKAGE`),字面量用小写。方括号表示可选参数,
`...` 表示可重复,竖线分隔互斥项 —— 与 `sow help` 的写法一致。
