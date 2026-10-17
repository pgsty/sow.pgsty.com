---
title: "服务与发布仓库"
linkTitle: "对外服务"
description: "把托管仓库发布到独立目录，并用 Nginx 对外提供服务。"
categories: [Tutorial]
tags: [publish, filesystem, managed]
url: "/zh/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW 生成静态仓库文件。本教程把 Managed 仓库发布到独立目录，再用 Nginx 提供服务。先完成[第一个工作区](/zh/docs/start/workspace/)。

<span id="公共与私有路径" data-td-print-local></span>

源目录是 `/srv/sow/local`，公开副本将位于 `/srv/repo-public/local`。
两者都包含完整的 `pool/` 与 `dists/` 目录树。工作区配置与私有状态保留在服务目录之外。

<span id="1-校验源-generation" data-td-print-local></span>

## 1. 构建并检查

```bash
cd /srv/sow
sow build -r local
sow check -r local
```

`check` 成功后继续。

<span id="2-配置-filesystem-target" data-td-print-local></span>

## 2. 添加 filesystem 目标

创建目标父目录，并给 SOW 操作者写权限：

```bash
sudo install -d -m 0755 /srv/repo-public
sudo chown "$(id -u):$(id -g)" /srv/repo-public
```

如果执行 `sow publish` 的账户不同，使用该账户。endpoint 必须已存在，并使用不含符号链接的物理路径。

在 `/srv/sow/sow.yml` 添加目标：

```yaml
targets:
  public:
    repository: local
    provider: filesystem
    endpoint: file:///srv/repo-public
    prefix: local
    public_endpoint: file:///srv/repo-public/local/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

SOW 根据 `endpoint` 与 `prefix` 创建 `/srv/repo-public/local`。三个必填布尔值声明：本工作区是该目标的权威来源，也是唯一写入者。其他工具使用独立前缀。

本例通过 `file://` 检查发布文件，并声明没有中间缓存。以后增加代理或 CDN 时，把 `public_endpoint` 改为公共仓库 URL，
把 `max_cache_ttl` 设为其最长缓存时间，并通过 [`publish --rebind`](/zh/docs/command/publish/) 应用变更。
SOW 据此检查交付结果，并确定旧文件何时可以删除。

发布仓库：

```bash
sow publish public
```

SOW 先复制包文件与不可变元数据，再更新客户端入口，随后检查结果并记录发布快照。内容不变时重复发布会报告空操作。

<span id="3-用-nginx-服务-target" data-td-print-local></span>

## 3. 配置 Nginx

安装 Nginx，添加以下服务器配置，并把 `repo.example.com` 换成你的主机名：

```nginx
server {
    listen 80;
    server_name repo.example.com;

    root /srv/repo-public;
    autoindex off;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ (^|/)\. {
        deny all;
    }
}
```

检查并重载配置：

```bash
sudo nginx -t
sudo nginx -s reload
```

上述命令假定 Nginx 已运行。首次安装时，在 `nginx -t` 成功后，用操作系统的服务管理器启动 Nginx。

客户端地址如下：

| 客户端 | 地址 |
|---|---|
| DNF `baseurl` | `http://repo.example.com/local/dists/el9/$basearch/` |
| APT `URIs` | `http://repo.example.com/local` |
| APT `Suites` / `Components` | `bookworm` / `main` |

完整源配置见 [YUM](/zh/docs/tutorial/yum-repo/) 或 [APT](/zh/docs/tutorial/apt-repo/) 教程。需要验签时，分发公钥并按[仓库签名](/zh/docs/tutorial/signing/)配置。

<span id="4-验证服务入口" data-td-print-local></span>

## 4. 检查客户端访问

用上表地址配置客户端，刷新索引并安装一个软件包。
这会检查 `dists/` 与 `pool/` 是否都能访问。两个目录使用相同的访问规则。

<span id="下一步" data-td-print-local></span>

## 发布更新

修改成员或配置后，构建尚未完成的变更，再发布：

```bash
sow build -r local
sow check -r local
sow publish public
```

发布中断时，重新执行 `sow publish public` 继续。恢复与目标变更见 [`sow publish`](/zh/docs/command/publish/)；缓存宽限期后的清理见 [`sow gc`](/zh/docs/command/gc/)。

<span id="手工与隔离交付" data-td-print-local></span>

## 交付到隔离主机

SOW 无法连接目标时，按以下步骤复制。创建并检查副本期间，暂停源工作区的写入。

1. 在源端执行 `sow check`。
2. 把完整仓库复制到目标的新发布目录。保留硬链接，例如使用 `rsync -aH` 或 `tar`。
3. 根据 `sow changes 0` 或归档校验清单检查传输后的文件。
4. 将服务器路径切换到新发布目录。
5. 切换后，继续让旧索引引用的软件包 URL 和不可变元数据 URL 可访问，直到最长缓存期结束，再清理旧发布。

在此期间，HTTP 服务可将新目录中缺失的路径回退到上一发布目录。

直接覆盖在线目录，可能在包文件到达前暴露新索引。先准备新目录，再整体切换。

## 提供 Plain 仓库

Plain 模式直接提供传给 `sow create` 的目录。使用上例 Nginx 隐藏文件规则，
防止访问临时文件。

<span id="r2-target" data-td-print-local></span>

## 发布到 R2

Cloudflare R2 使用 `provider: r2`。配置 endpoint、bucket、凭据引用、公共 URL 与缓存时间，详见[目标配置参考](/zh/docs/reference/config/)。先发布到测试前缀，再从实际包管理器检查。

R2 目标垃圾回收只报告待删除对象，SOW 不执行远端删除。已测试的存储操作见[平台与集成](/zh/docs/reference/compatibility/)。
