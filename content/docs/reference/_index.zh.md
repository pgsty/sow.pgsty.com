---
title: "参考"
linkTitle: "参考"
description: "配置 Schema、包引用、磁盘布局、退出码、JSON 输出与兼容性证据。"
url: "/zh/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

这一部分记录稳定的数据与接口契约："`sow.yml` 里允许出现哪些字段"、"退出码 5 是什么意思"、
"某个文件落在哪里" —— 只给精确答案，不铺叙事。命令语法与行为放在独立的
[命令手册](/zh/docs/command/)中。如果你想先弄懂
SOW 的工作方式,请从[上手指南](/zh/docs/start/)或[功能](/zh/docs/feature/)开始,
那些页面讲模型,并在需要细节时链接回这里。

本节语法与配置规则已按 v0.2.0 二进制及其严格解析器核对。输出示例用于说明形态；
标识符、路径、哈希与计数会随工作区变化。

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
{{< card title="兼容性" link="/zh/docs/reference/compatibility/" >}}
当前构建、客户端、Provider 与文件系统的确切证据，包括尚未成立的结论。
{{< /card >}}
{{< /cards >}}

## 本节的约定

命令示例不带 `$` 提示符，方便整块复制。输出块代表 v0.2.0 的形态；标识符、时间戳、哈希、
计数与路径会变化，长结构在标注处会省略。二进制自带的 `sow help` 始终是精确语法权威。

语法块中占位符用大写(`NAME`、`DIR`、`PACKAGE`),字面量用小写。方括号表示可选参数,
`...` 表示可重复,竖线分隔互斥项 —— 与 `sow help` 的写法一致。
