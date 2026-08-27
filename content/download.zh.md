---
title: "下载 SOW"
linkTitle: "下载"
description: "从 Pigsty 软件源、固定版本 RPM/DEB 安装包、Linux 与 macOS 归档或源码构建安装 SOW，并核对每个已发布制品的 SHA-256 摘要。"
url: "/zh/download/"
weight: 20
icon: fa-solid fa-download
layout: landing
landing: download
translationKey: download
categories: [Download]
tags: [install, rpm, deb, release]
search_keywords: [下载, 安装, 软件包, RPM, DEB, YUM, APT, 归档, 校验, SHA256, Pigsty, 源码]
search_boost: 1.5
---

<!-- landing 布局渲染的是 `data/landing/download/<lang>.yaml`，而不是这段正文。
     下面这段是本页的可检索文本：OINK 的离线索引会跳过没有正文的页面，而这里是
     读者会按制品名称查找的顶级导航入口。 -->

可以用 `apt install sow` 或 `dnf install sow` 从 Pigsty infra 软件源安装 SOW，也可以使用
固定版本的 RPM / DEB 安装包、面向 Linux 与 macOS（`amd64` 与 `arm64`）的 `tar.gz` 归档，
或者从某个 Tag 的源码自行构建。每条路径安装的都是同一个自包含可执行文件；每个已发布制品
都在 `SHA256SUMS` 中列出 SHA-256 摘要。安装完成后执行 `sow version` 与 `sow help`，
然后把 `sow create` 指向一个存放软件包的目录。
