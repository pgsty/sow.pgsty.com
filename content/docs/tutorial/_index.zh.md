---
title: "教程"
linkTitle: "教程"
description: "端到端实操：从一组软件包文件开始，构建客户端可直接使用的已签名软件仓库。"
categories: [Tutorial]
tags: [yum, apt, signing, publish]
url: "/zh/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

这里的教程都从全新工作区开始。请按顺序执行命令，并按你的环境替换大写占位符与包路径。

如果还没装 SOW，先看[安装](/zh/docs/start/install/)与[快速上手](/zh/docs/start/quickstart/)。
下面的教程介绍 Managed 仓库路径。

{{< cards >}}
{{< card title="搭建 YUM 仓库" link="/zh/docs/tutorial/yum-repo/" >}}
托管 RPM 仓库：分架构视图、noarch 中性投影、debuginfo 过滤、版本数量上限，以及可用的
dnf 客户端配置。
{{< /card >}}
{{< card title="搭建 APT 仓库" link="/zh/docs/tutorial/apt-repo/" >}}
托管 DEB 仓库：Debian 风格包池、by-hash 索引与 deb822 客户端配置。
{{< /card >}}
{{< card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
生成专用 GPG 签名钥，为仓库元数据与 RPM 包签名，并配置客户端拒绝一切未签名内容。
{{< /card >}}
{{< card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
用 Nginx 服务 Repository，并把已校验 Generation 发布到配置好的 filesystem target，
同时避免暴露工作区私有状态。
{{< /card >}}
{{< card title="演练构建 pigsty-infra 仓库" link="/zh/docs/tutorial/infra-repo/" >}}
把 infra-pkg 已产出的双架构 RPM 与 DEB 组织成真实仓库，并演练本地安装、滚动更新、
Stable 晋升与月度快照。
{{< /card >}}
{{< /cards >}}

## 先看哪篇

| 你的处境 | 从这里开始 |
|---|---|
| 你要向 dnf 客户端分发 RPM | [搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/) |
| 你要为 Debian 或 Ubuntu 分发 DEB | [搭建 APT 仓库](/zh/docs/tutorial/apt-repo/) |
| 需要已签名元数据或已签名 RPM 包体 | [仓库签名](/zh/docs/tutorial/signing/) |
| 树已经建好，但外部无法访问 | [对外服务](/zh/docs/tutorial/serving/) |
| 想把现有双架构包池变成可维护的 Infra 仓库 | [演练构建 pigsty-infra 仓库](/zh/docs/tutorial/infra-repo/) |

YUM 与 APT 两篇是彼此独立的全新 Workspace 路径。实际使用中，如果它们适合共用同一所有权
边界，一个 Workspace 的同一 Repository 可以同时容纳 RPM 与 DEB Dist。

## 本板块约定

Shell 代码块里的命令不带 `$` 提示符，方便整块复制。输出单独成块放在命令下方，只有一行时用注释
标注。需要你自行替换的值一律写成 `大写`。

每篇教程结尾都有验证步骤。`sow check` 返回 `0`，才证明所选 Repository 完整且与记录的
Generation 一致；非零结果不应作为交付物。
