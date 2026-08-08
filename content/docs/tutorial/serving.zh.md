---
title: "对外服务"
linkTitle: "对外服务"
description: "用 Nginx 服务完整 SOW 仓库、安全复制,或把 Generation 发布到已配置目标。"
url: "/zh/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW 产出的是一个静态目录。任何能提供静态文件的东西都能服务它——没有守护进程、没有应用服务器、
没有运行时组件。这篇教程讲清楚该把 web 服务器指向哪里、一份实测过的 Nginx 配置、一条命令的本地
预览,以及怎么把整棵树搬到够不着构建机的主机上。

预计十五分钟。

## 到底该发布什么

对托管工作区来说,文档根目录是**仓库**目录:

```console
~/repo/                  <- 工作区:不要发布这一层
├── sow.yml              <- 配置
├── .sow/                <- SQLite、锁、stage、恢复
└── pigsty/              <- 发布这一层
    ├── pool/
    └── dists/
```

仓库目录里正好只有 `pool/` 与 `dists/` 两项,两者都是要公开的。绝不能公开的状态——数据库、锁、
stage 区、pending 包体——都在上一层工作区根目录的 `.sow/` 里。把 web 服务器指向 `~/repo/pigsty`,
不管服务器配置里出什么错都泄露不了它。

Plain 平面模式没有工作区:你跑 `sow create` 的那个目录就是文档根,`repodata/` 与 `Packages`
与包文件同级。

用 HTTPS。APT 与 DNF 会验签,所以明文 HTTP 不至于让攻击者伪造包,但它会让链路上任何人看清每台
主机装了哪些包。

## 第 1 步:本地预览

在碰真正的 web 服务器之前,先确认这棵树能被服务:

```bash
cd ~/repo/pigsty
python3 -m http.server 8080
```

在另一个终端:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:8080/dists/el9/x86_64/repodata/repomd.xml
```

```console
200
```

这已经够你把一台测试虚机指向 `http://你的IP:8080/` 跑一次真实的 `dnf makecache`。生产不能这么用
——单线程、无缓存、无 TLS——但它能在出问题时先把 web 服务器排除在嫌疑之外。

## 第 2 步:用 Nginx 服务

下面这份配置针对一个同时含 RPM 与 DEB Dist、且元数据已签名的仓库做过端到端实测。

```nginx
server {
    listen 443 ssl;
    server_name repo.example.com;

    ssl_certificate     /etc/ssl/certs/repo.example.com.crt;
    ssl_certificate_key /etc/ssl/private/repo.example.com.key;

    root /home/you/repo/pigsty;

    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;

    # 无论 root 最终指到哪里,都不服务点文件。
    location ~ /\. { deny all; }

    # 包体不可变:路径里已经带了确切版本。
    location ~ \.(rpm|deb)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # 索引与指针每次构建都会变。
    location ~ /(repodata|dists)/ {
        add_header Cache-Control "no-cache";
    }
}
```

有四点值得说明。

`root` 指向仓库而不是工作区。配合点文件规则,`.sow/` 被挡了两道。

缓存的这个切分比看上去重要。`pool/` 里的文件内容永不变化——名字里就带着版本——所以可以永久缓存。
`repomd.xml`、`Release`、`InRelease` 是每次构建都翻的指针;CDN 或代理如果攥着旧的一份,就会把
客户端引向已经被删掉的元数据文件。这里的 `no-cache` 意思是"每次回源确认",不是"不要存",
所以省流量的好处还在,陈旧的问题没了。

`autoindex` 可选。人工浏览包池时确实好用,而且它暴露的东西客户端本来就能从索引里枚举出来。
不喜欢就关掉。

配置里没有 `try_files`、没有 rewrite、没有 MIME 特判。APT 与 DNF 请求的是精确路径,在意的是字节
而不是 `Content-Type`。

检查并重载:

```bash
nginx -t
```

```console
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

```bash
systemctl reload nginx
```

## 第 3 步:逐个入口验证

每类文件各取一个,五个都必须返回 `200`:

```bash
for u in /dists/el9/x86_64/repodata/repomd.xml \
         /dists/el9/x86_64/repodata/repomd.xml.asc \
         /dists/trixie/InRelease \
         /dists/trixie/Release.gpg \
         /pool/p/pev2/pev2-1.22.0-1.noarch.rpm; do
  printf "%-52s %s\n" "$u" \
    "$(curl -sS -o /dev/null -w '%{http_code} %{size_download}' https://repo.example.com$u)"
done
```

```console
/dists/el9/x86_64/repodata/repomd.xml                200 1517
/dists/el9/x86_64/repodata/repomd.xml.asc            200 832
/dists/trixie/InRelease                              200 1498
/dists/trixie/Release.gpg                            200 832
/pool/p/pev2/pev2-1.22.0-1.noarch.rpm                200 325925
```

再验一下 APT 实际会走的 `by-hash` 路径,哈希直接从 `Release` 里取:

```bash
HASH=$(grep -m1 " main/binary-arm64/Packages$" \
        ~/repo/pigsty/dists/trixie/Release | awk '{print $1}')
curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" \
  "https://repo.example.com/dists/trixie/main/binary-arm64/by-hash/SHA256/$HASH"
```

```console
200 3846
```

这里出 `404` 说明服务器在重写或规范化路径——`by-hash` 目录长得不寻常,有些配置会把它弄坏。
在客户端撞上之前修掉,否则 APT 会退回按名取索引,你就失去了跨重建取索引的那层保护。

## 第 4 步:同时服务多个仓库

如果一个工作区里有多个仓库,可以改把服务器根设在工作区上。这时点文件规则才真正在干活,而且还要
为 `sow.yml` 多加一条:

```nginx
server {
    listen 443 ssl;
    server_name repo.example.com;

    ssl_certificate     /etc/ssl/certs/repo.example.com.crt;
    ssl_certificate_key /etc/ssl/private/repo.example.com.key;

    root /home/you/repo;

    autoindex on;

    location ~ /\.       { deny all; }   # 挡住 /.sow/
    location = /sow.yml  { deny all; }

    location ~ \.(rpm|deb)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    location ~ /(repodata|dists)/ {
        add_header Cache-Control "no-cache";
    }
}
```

两条拒绝规则加一条真实路径,验证一下:

```console
GET /.sow/pigsty.db                    -> 403
GET /sow.yml                           -> 403
GET /pigsty/dists/trixie/InRelease     -> 200
```

客户端 URL 会多一段仓库名:`https://repo.example.com/pigsty/dists/el9/$basearch`。

{{% alert title="更推荐一个仓库一个 server 块" color="info" %}}
把根设在工作区能用,但这会让你的配置文件与状态目录离公开只差一次配置失误。如果 server 块开得起,
就让每一个都指向自己的仓库目录——那时任何拒绝规则都无事可做。
{{% /alert %}}

## 第 5 步:把整棵树拷到另一台主机

整个仓库就是 `pool/` 与 `dists/` 两个目录。拷到哪里就是一个能用的仓库——没有导入步骤,没有要搬的
数据库。

先确认这棵树可交付。这正是 `sow check` 的用途:

```bash
sow check
```

退出码 `0` 表示每一层都校验通过、树是自洽的。退出码 `5` 表示还不能交付——通常是因为仓库 dirty、
还欠一次 `sow build`。绝不要拷贝没过校验的树,那等于在发布与包体不匹配的索引。

脚本可以从 `status` 读同一个事实:

```bash
sow status --json
```

```console
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"pigsty","operation":null,"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,"desired_revision":6,"built_generation":9,"dirty_dists":[],"dirty_reasons":[],"pending":{"count":0,"bytes":0},"recent_operation":{"id":"2579903513812731490","kind":"build","state":"done","created_at":"2026-08-04T04:25:47.526819Z","updated_at":"2026-08-04T04:25:48.505935Z"},"repository_locked":false},"errors":[]}
```

判断 `.result.ready_to_copy` 即可。

### 复制闭合的公共树

```bash
rsync -a --delete ~/repo/pigsty/ user@mirror:/srv/www/pigsty/
```

v0.2.0 规范树不需要保留硬链接:包体只存在 `pool/`,视图只含元数据。关键是始终一起复制
`pool/` 与 `dists/`,并且只有在新指针就位后才应用删除。

结果与源逐字节一致:

```bash
diff -r --brief ~/repo/pigsty /srv/www/pigsty && echo "trees identical"
```

```console
trees identical
```

### 隔离介质

同样的思路,分两跳走:

```bash
sow check                                    # 闸门
tar -C ~/repo -cf /mnt/usb/pigsty.tar pigsty
# 把介质搬过去
tar -C /srv/www -xf /mnt/usb/pigsty.tar
```

归档只包含公共仓库。不要加入 `sow.yml` 或 `.sow/`;接收主机服务静态文件不需要权威数据库。

## 第 6 步:只投递变化的部分

对大仓库来说,每次构建都全量重拷太浪费。`sow changes` 给出任意历史代与当前代之间精确的文件级差异。

`changes 0` 是全量交付集——一个全新镜像需要的全部内容:

```bash
sow changes 0 | head -3
sow changes 0 | wc -l
```

```console
base=0 generation=9 dirty=false
add	payload	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm	15289542	ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943
add	payload	pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm	1451117	077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6
```

传入镜像当前所在的代,得到增量集。往一个处于第 9 代的仓库里加了一个包之后:

```bash
sow changes 9
```

```console
base=9 generation=10 dirty=false
add	payload	pool/g/gdal311-devel/gdal311-devel-3.11.0-2.rhel9.x86_64.rpm	251366	0663e42e48207189e5dde643fc779de022ade1e3ddd87519009d484bfd2d05fc
add	metadata	dists/el9/x86_64/repodata/6439665d77d7129eb17c4775148fb2ab918b00525d0012572863fedbf2eb2ff9-filelists.xml.gz	4765	6439665d77d7129eb17c4775148fb2ab918b00525d0012572863fedbf2eb2ff9
add	metadata	dists/el9/x86_64/repodata/90965c9a2093e32fb6e9a42a701a0be80510fd55a58ae8c4b7e78ccc95d3c79e-primary.xml.gz	3750	90965c9a2093e32fb6e9a42a701a0be80510fd55a58ae8c4b7e78ccc95d3c79e
add	metadata	dists/el9/x86_64/repodata/e3fb8c08073e38e189d995817588e0990db1f0b7a1b77e1a1606ac3fa9ff5e45-other.xml.gz	1917	e3fb8c08073e38e189d995817588e0990db1f0b7a1b77e1a1606ac3fa9ff5e45
update	pointer	dists/el9/aarch64/repodata/repomd.xml	1520	114f79dade90f77d11b3c452d8d59654917683f59f196c7098e68449c361f0ae
update	pointer	dists/el9/aarch64/repodata/repomd.xml.asc	832	48d7c114f84876c1247444b3792f549e9da3c775fe4d46a384839b8b37121237
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1521	c67ab04efe06c1ff2a55a3c8fecc15405346471de8ca77f76915797fa81d3a4c
update	pointer	dists/el9/x86_64/repodata/repomd.xml.asc	832	d0de8d66071a1fb6ecc1ff8a34e8b0d84689ed886169b6ea3fa696ab169e05aa
```

各列依次是操作、阶段、相对仓库根的路径、大小、SHA-256。手工应用或自己写工具时,`phase` 那一列
是必须遵守的约束:

1. `payload` —— 包文件。先拷这些,此时还没有任何东西指向它们。
2. `metadata` —— checksum 命名的索引与 `by-hash` 副本。仍未被引用。
3. `pointer` —— `repomd.xml`、`Release`、`InRelease` 及其签名。这一步就是提交:指针一落地,
   客户端就看到新一代。
4. `delete` —— 上一代引用而这一代不再引用的文件。只有全部指针都翻完之后才安全。

顺序错了,正在取文件的客户端就会拿到悬空引用。按顺序做,读者永远看到自洽的树,因为它要么读到旧
指针要么读到新指针,而两者都能解析。

`changes` 是给自定义传输使用的底层本地计划。`sow.yml` 已定义发布目标时,优先使用内置的
有序、可恢复路径:

```bash
sow publish prod
```

SOW 支持 `filesystem` 与 S3 兼容的 `r2` 目标,记录 checkpoint,并要求对未终结尝试显式恢复
或 abort。发布凭据通过 `env://` 或 `file://` 引用保存,不会进入公共树。

{{% alert title="dirty 的仓库给不出计划" color="warning" %}}
仓库处于 dirty、recovering 或 error 时,`changes` 拒绝作答——此时没有一棵自洽的物理树可供描述。
先 `sow build`,确认 `sow check` 通过,再来问。
{{% /alert %}}

## 下一步去哪

{{< doc-cards cols="2" >}}
{{< doc-card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
在发布任何要让客户端信任的东西之前,先做这一步。
{{< /doc-card >}}
{{< doc-card title="可观测与审计" link="/zh/docs/feature/audit/" >}}
`status`、`check`、`changes`、`log`——各自代价多大、各自能证明什么。
{{< /doc-card >}}
{{< doc-card title="仓库布局" link="/zh/docs/reference/layout/" >}}
树里的每一条路径,以及哪些绝不能进文档根目录。
{{< /doc-card >}}
{{< doc-card title="兼容性" link="/zh/docs/reference/compatibility/" >}}
测过哪些客户端,以及规范布局与 Provider 边界。
{{< /doc-card >}}
{{< /doc-cards >}}
