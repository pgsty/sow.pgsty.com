---
title: "参考"
linkTitle: "参考"
description: "命令语法、配置 schema、磁盘布局、退出码、JSON 输出与实测兼容矩阵。"
url: "/zh/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

这一部分是文档的"查阅"半边。它回答"这个参数到底做什么"、"`sow.yml` 里允许出现哪些字段"、
"退出码 5 是什么意思"、"某个文件落在哪里" —— 只给精确答案,不铺叙事。如果你想先弄懂
SOW 的工作方式,请从[上手指南](/zh/docs/start/)或[功能](/zh/docs/feature/)开始,
那些页面讲模型,并在需要细节时链接回这里。

本节所有内容都取自实际发布的二进制:命令输出是 `sow 0.2.0` 的真实转录,
配置规则与严格解析器一致,不是"设想中的" schema。

{{< doc-cards cols="2" >}}
{{< doc-card title="命令行" link="/zh/docs/reference/cli/" >}}
全部命令、参数、可用的全局选项,以及决定命令作用于哪个仓库和 Dist 的发现与选择规则。
{{< /doc-card >}}
{{< doc-card title="配置参考" link="/zh/docs/reference/config/" >}}
完整配置 schema:工作区、仓库、Dist、成员策略与签名树 —— 含 key 引用文法与全部校验规则。
{{< /doc-card >}}
{{< doc-card title="包引用" link="/zh/docs/reference/package-ref/" >}}
命令行上指代一个软件包的五种写法、歧义如何裁决,以及 `rm` / `show` / `where` 各自接受哪些形态。
{{< /doc-card >}}
{{< doc-card title="仓库布局" link="/zh/docs/reference/layout/" >}}
Plain 与 Managed 两种模式下 SOW 创建的每一条路径、包池分组规则、名称约束,
以及绝对不能通过 HTTP 暴露的目录。
{{< /doc-card >}}
{{< doc-card title="退出码" link="/zh/docs/reference/exit-codes/" >}}
七个退出码分别代表什么,以及每个码一条可复现的触发命令。
{{< /doc-card >}}
{{< doc-card title="JSON 输出" link="/zh/docs/reference/json/" >}}
`sow.cli/v1` 信封结构、各顶层字段含义,以及每条数据命令的 result 形态。
{{< /doc-card >}}
{{< doc-card title="兼容性" link="/zh/docs/reference/compatibility/" >}}
哪些包管理器实测消费过 SOW 构建的仓库、二进制支持哪些平台,以及你必须遵守的文件系统约束。
{{< /doc-card >}}
{{< /doc-cards >}}

## 本节的约定

命令示例不带 `$` 提示符,方便整块复制。转录中同时给出输入与输出时,命令行在前,
输出紧随其后,与二进制实际打印的一致。为了页面可读性而截断的输出,会明确标注。

语法块中占位符用大写(`NAME`、`DIR`、`PACKAGE`),字面量用小写。方括号表示可选参数,
`...` 表示可重复,竖线分隔互斥项 —— 与 `sow help` 的写法一致。
