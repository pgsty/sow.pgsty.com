---
title: "服务与发布仓库"
linkTitle: "对外服务"
description: "用 Nginx 服务公共 Repository，并把已校验 Generation 发布到 filesystem target。"
url: "/zh/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW 只生成静态文件，不是 HTTP 服务器。本指南把可写 Workspace 与 Nginx 服务路径分开。

## 公共与私有路径

| 模式 | 公共单元 | 绝不能服务 |
|---|---|---|
| Plain | 传给 `sow create` 的目录 | 操作中断后可能存在的 `.sow-plain-*` 临时状态 |
| Managed | 一个 Repository 的完整 `pool/ + dists/` 树 | Workspace `sow.yml`、`.sow/`、SQLite、锁、日志与 staging |

[第一个工作区](/zh/docs/start/workspace/)里的源 Repository 是 `/srv/sow/local`。不要把
`/srv/sow` 设为 document root。

## 1. 校验源 Generation

```bash
cd /srv/sow
sow build -r local
sow check -r local
```

只有 `check` 返回 `0` 才继续。`status` 适合诊断；`check` 才是完整只读交付证明。

## 2. 配置 filesystem target

先创建 endpoint 目录。它必须是真实、规范目录，不能是 symlink；SOW 不会替你创建缺失 endpoint。

```bash
sudo install -d -m 0755 /srv/repo-public
sudo chown "$(id -u):$(id -g)" /srv/repo-public
```

第二条命令把写权限交给当前操作者；若 `sow publish` 由专用服务账户执行，应改为该账户。

在 `/srv/sow/sow.yml` 中增加 target：

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

三个布尔字段都是必填安全确认。endpoint 与 prefix 合并为 `/srv/repo-public/local`；
SOW 会在预先存在的 endpoint 下创建并拥有该 prefix。

校验并发布：

```bash
sow config check
sow publish public
```

发布先复制不可变包体和元数据，再更新可变协议指针，随后校验结果并记录 target checkpoint。
同一 Generation 重复发布是幂等空操作。

不要让其他工具写入同一 target prefix。target 契约是单 writer、独占写入。

## 3. 用 Nginx 服务 target

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

校验配置后 reload Nginx。客户端 URL 为：

```text
DNF baseurl: http://repo.example.com/local/dists/el9/x86_64/
APT source:  deb http://repo.example.com/local bookworm main
```

如果元数据或包体已签名，请单独发布对应公钥并配置 `gpgkey`/`Signed-By`；私钥绝不能放在
document root 下。

## 4. 验证服务入口

```bash
curl --fail --head \
  http://repo.example.com/local/dists/el9/x86_64/repodata/repomd.xml

curl --fail --head \
  http://repo.example.com/local/dists/bookworm/Release

curl --fail --head \
  http://repo.example.com/local/dists/bookworm/main/binary-amd64/Packages.gz
```

随后从客户端主机运行真实包管理器。HTTP 可达不等于客户端已验证，两层都要检查。

完整 Repository prefix 必须使用同一访问策略。RPM 元数据可能通过 `../../../pool/...`
解析包路径，APT `Filename` 也直接指向 `pool/...`。只保护 `dists/` 而误放开或拦截 `pool/`
都会破坏仓库。

## 手工与隔离交付

如果 `sow publish` 无法到达目标：

1. 在源端运行 `sow check`；
2. 把完整 Repository 复制到新的、非 live staging/release 目录；
3. 用 `sow changes 0` 或 archive manifest 校验传输哈希；
4. 原子切换操作者拥有的父级引用到新目录；
5. 保留上一版，直到客户端与缓存越过它。

不要直接对 live Repository root 执行无序 `rsync --delete`。它不保留 SOW 的指针顺序、
target checkpoint、缓存 grace 或恢复状态。`sow changes` 描述 Generation 差异，不代表可以
绕过这些控制直接修改 live target。

## R2 target

配置解析器与当前实现支持 `provider: r2`，提供 S3 兼容发布与只报告的 target GC。当前真实
CLI-to-R2 端到端证据尚不完整；依赖前请在非生产 prefix 验证凭据、bucket policy、公共 endpoint、
缓存、重放与恢复。详见[兼容性](/zh/docs/reference/compatibility/)。

## 下一步

- [`sow publish`](/zh/docs/command/publish/) 与 [`sow gc`](/zh/docs/command/gc/)
- [发布设计](/zh/docs/design/publication/)
- [签名教程](/zh/docs/tutorial/signing/)
