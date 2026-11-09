---
title: "参考"
linkTitle: "参考"
description: "查阅配置、包引用、文件路径、命令结果与故障处理方法。"
categories: [Reference]
tags: [config, cli]
url: "/zh/docs/reference/"
weight: 400
icon: fa-solid fa-book-open
---

这些页面用于查阅配置字段、包引用、文件路径和脚本接口。
命令语法见[命令参考](/zh/docs/command/)，也可运行 `sow help COMMAND`。

- [**配置参考** — `sow.yml` 的字段、默认值、校验规则、签名引用和发布目标。](/zh/docs/reference/config/)
- [**包引用** — 按摘要、坐标、文件名或包名选择软件包，解决匹配歧义。](/zh/docs/reference/package-ref/)
- [**仓库布局** — 查找包文件、索引、私有状态和发布输出的位置。](/zh/docs/reference/layout/)
- [**退出码** — 解释命令结果，并在脚本中选择下一步操作。](/zh/docs/reference/exit-codes/)
- [**JSON 输出** — 读取 `sow.cli/v1` 响应和各命令的结果字段。](/zh/docs/reference/json/)
- [**平台与集成** — 检查系统、文件系统、客户端格式和集成测试覆盖。](/zh/docs/reference/compatibility/)
- [**故障排查** — 处理配置、构建、签名和发布错误，找到下一步操作。](/zh/docs/reference/troubleshooting/)
{.cards}

<span id="conventions" data-td-print-local></span>
<span id="约定" data-td-print-local></span>

## 示例约定 {#example-conventions}

命令代码块省略 shell 提示符，便于复制。语法说明中的 `NAME`、`DIR` 等大写词是占位符。
方括号表示可选参数，`...` 表示可重复参数，`|` 分隔备选项。

输出中的路径、ID、摘要、时间和计数随工作区变化。操作 ID 和构建快照 ID 保持字符串类型，
详见 [JSON 输出](/zh/docs/reference/json/)。
