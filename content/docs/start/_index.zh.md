---
title: "上手指南"
linkTitle: "上手指南"
description: "安装 SOW,五分钟发布一个可用仓库,并建立它背后的心智模型。"
url: "/zh/docs/start/"
weight: 100
icon: fa-solid fa-rocket
---

SOW 是一个静态二进制,用来构建 APT 与 YUM 软件仓库。它不需要你部署服务端,不需要
`createrepo_c` 或 `reprepro`,也没有常驻进程。把二进制丢到机器上,指向一堆软件包,
把产出的目录复制到任意静态 Web 服务器即可。

它有两条互不干扰的使用路径。`sow create` 接受一个装着 `.rpm` / `.deb` 的普通目录,
就地写出仓库索引 —— 它只做这一件事,也是最快拿到可服务仓库的方式。另一条是 Managed
托管工作区:包池、具名发行版、按架构渲染的视图、成员策略、GPG 签名,以及每次变更的
审计账本。先用前者跑通,当你需要**筛选**进入仓库的内容时,再换到后者。

按顺序读完下面四页,你会把两条路径都跑通,并且清楚自己的场景该用哪一条。

{{< doc-cards cols="2" >}}
{{< doc-card title="安装" link="/zh/docs/start/install/" >}}
下载预编译二进制或从源码构建,包含支持的平台矩阵,以及仅有的两个需要外部工具的操作。
{{< /doc-card >}}
{{< doc-card title="快速上手" link="/zh/docs/start/quickstart/" >}}
五分钟:把一个装包的目录变成平面仓库,用 HTTP 暴露出去,再用 `dnf` / `apt` 装包。
{{< /doc-card >}}
{{< doc-card title="第一个工作区" link="/zh/docs/start/workspace/" >}}
十分钟:创建工作区,建一个含 RPM 与 DEB 两种 Dist 的仓库,添加软件包,查看包池与发布树。
{{< /doc-card >}}
{{< doc-card title="核心概念" link="/zh/docs/start/concepts/" >}}
心智模型:Workspace、Repository、Dist、架构视图,以及期望成员集与已构建代的区别。
{{< /doc-card >}}
{{< /doc-cards >}}

## 你需要什么

一台 Linux 或 macOS 机器(`amd64` 或 `arm64`),以及存放软件包的磁盘空间。没有别的了 ——
SOW 自己解析 RPM 头与 Debian control 文件,在进程内直接写出索引。

只有两类操作会调用环境里的外部工具:给 RPM 包体签名,以及用 `gpg-agent` 持有的私钥给
仓库元数据签名。两者都是可选的,详见[安装](/zh/docs/start/install/)。

## 接下来读什么

| 你想要…… | 阅读 |
|---|---|
| 立刻把一个装包的目录发布出去 | [快速上手](/zh/docs/start/quickstart/) |
| 长期维护一个精选仓库 | [第一个工作区](/zh/docs/start/workspace/) |
| 搞懂包池、视图与代际 | [核心概念](/zh/docs/start/concepts/) |
| 搭建生产级 YUM / APT 仓库 | [教程](/zh/docs/tutorial/) |
| 查某个参数、字段或退出码 | [参考](/zh/docs/reference/) |
