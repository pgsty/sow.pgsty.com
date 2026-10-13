---
title: "教程"
linkTitle: "教程"
description: "构建、签名、托管并更新 RPM 与 DEB 软件仓库。"
categories: [Tutorial]
tags: [yum, apt, signing, publish]
url: "/zh/docs/tutorial/"
weight: 200
icon: fa-solid fa-graduation-cap
---

本节介绍仓库创建、签名、发布与更新。尚未安装 SOW 时，先看[安装](/zh/docs/start/install/)。

<span id="先看哪篇"></span>

{{< cards >}}
{{< card title="迁移现有 YUM 仓库" link="/zh/docs/tutorial/yum-migration/" >}}
替换平面 RPM 仓库的元数据生成工具，保留发布时间、签名与客户端缓存兼容性。
{{< /card >}}
{{< card title="搭建 YUM 仓库" link="/zh/docs/tutorial/yum-repo/" >}}
创建 RPM 架构视图，过滤软件包，设置版本上限并配置 DNF。
{{< /card >}}
{{< card title="搭建 APT 仓库" link="/zh/docs/tutorial/apt-repo/" >}}
创建 DEB 包池与 by-hash 索引，并配置 APT 客户端。
{{< /card >}}
{{< card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
签署元数据与 RPM 软件包，再配置客户端验签。
{{< /card >}}
{{< card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
发布到 filesystem 目标，并用 Nginx 提供服务。
{{< /card >}}
{{< card title="构建 pigsty-infra 仓库" link="/zh/docs/tutorial/infra-repo/" >}}
同时使用两种格式与架构，测试安装，维护滚动频道、稳定发布与月度快照。
{{< /card >}}
{{< /cards >}}

<span id="本板块约定"></span>

## 使用示例

按顺序执行命令，把大写占位符与 `/path/to/` 输入路径换成实际值。`/srv` 下的示例需要可写目录，也可以换成用户主目录下的路径。

YUM 与 APT 教程分别从新工作区开始。如果要合并使用，在已有 `pigsty` 仓库中创建第二个 Dist，并在 `sow.yml` 保留两个 Dist 的定义。

各教程都包含结果检查。命令报错或操作中断时，参见[故障处理](/zh/docs/reference/troubleshooting/)。
