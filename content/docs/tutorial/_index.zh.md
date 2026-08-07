---
title: "教程"
linkTitle: "教程"
description: "端到端实操:从一堆包文件开始,做出客户端可以直接安装的已签名软件仓库。"
url: "/zh/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

这里的每篇教程都是一次完整的旅程:从零开始,按顺序执行每条命令,最后得到一个真实 `dnf` 或
`apt` 客户端可以消费的仓库。命令可以直接复制执行,输出块全部来自真实运行记录。

如果还没装 SOW,先看[安装](/zh/docs/start/install/)与[快速上手](/zh/docs/start/quickstart/)
——那两篇能在五分钟内做出一个可用的平面仓库。下面的教程从那里接手,搭出生产形态。

{{< doc-cards cols="2" >}}
{{< doc-card title="搭建 YUM 仓库" link="/zh/docs/tutorial/yum-repo/" >}}
托管 RPM 仓库:分架构视图、noarch 中性投影、debuginfo 过滤、版本数量上限,以及可用的
dnf 客户端配置。
{{< /doc-card >}}
{{< doc-card title="搭建 APT 仓库" link="/zh/docs/tutorial/apt-repo/" >}}
托管 DEB 仓库:Debian 风格包池、by-hash 索引,以及 deb822 与传统 sources.list 两种客户端配置。
{{< /doc-card >}}
{{< doc-card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
生成专用 GPG 签名钥,为仓库元数据与 RPM 包签名,并配置客户端拒绝一切未签名内容。
{{< /doc-card >}}
{{< doc-card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
用 Nginx 通过 HTTP 发布整棵树、本地临时预览,以及在不丢硬链接去重的前提下拷到隔离主机。
{{< /doc-card >}}
{{< doc-card title="从 createrepo_c / reprepro 迁移" link="/zh/docs/tutorial/migration/" >}}
就地接管已有仓库、把 reprepro 归档搬进工作区,并看清到底什么变了、什么没变。
{{< /doc-card >}}
{{< /doc-cards >}}

## 先看哪篇

| 你的处境 | 从这里开始 |
|---|---|
| 你要为 EL8 / EL9 / EL10 分发 RPM | [搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/) |
| 你要为 Debian 或 Ubuntu 分发 DEB | [搭建 APT 仓库](/zh/docs/tutorial/apt-repo/) |
| 仓库已经有了,但客户端抱怨没签名 | [仓库签名](/zh/docs/tutorial/signing/) |
| 树已经建好,但外面访问不到 | [对外服务](/zh/docs/tutorial/serving/) |
| 你手上有 `createrepo_c` 定时任务或 reprepro 数据库 | [迁移](/zh/docs/tutorial/migration/) |

YUM 与 APT 两篇共用同一个工作区,按顺序读最顺:APT 篇会往 YUM 篇建好的仓库里再加一个 Dist。
单独看任何一篇也可以,每篇都写明了自己的前置条件。

## 本板块约定

Shell 代码块里的命令不带 `$` 提示符,方便整块复制。输出单独成块放在命令下方,只有一行时用注释
标注。需要你自行替换的值一律写成 `大写`。

每篇教程结尾都有验证步骤。验证不过就别往下走——下一步默认上一步已经产出了对应状态。
`sow check` 是说真话的那道闸:退出码 `0` 表示整棵树完整、可以直接拷贝,退出码 `5` 表示不行。
