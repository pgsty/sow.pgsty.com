---
title: "搭建 APT 仓库"
linkTitle: "搭建 APT 仓库"
description: "建一个托管 DEB 仓库:Debian 风格包池、by-hash 索引,以及 deb822 与传统两套客户端配置。"
url: "/zh/docs/tutorial/apt-repo/"
weight: 200
icon: fa-solid fa-cube
---

这篇教程搭一个托管 APT 仓库:按源码包分组的 Debian 风格包池、每个架构一份索引、`by-hash`
索引副本(让客户端不会撞上重建),以及现代 deb822 与传统单行两种客户端配置。

预计十五分钟。

## 开始之前

需要装好 SOW([安装](/zh/docs/start/install/))、一些 `.deb` 文件,和一个可写目录。

这篇接着[搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/)往同一个 `pigsty` 仓库里加第二个 Dist
——一个包池,两套包生态。如果你从零开始,先跑这三条命令,然后从第 1 步继续:

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
sow repo new pigsty
```

下面用到的 DEB 包覆盖 `amd64`、`arm64` 和 `all`,其中有一个包(`libpq5`)的 `Source` 字段与
二进制包名不同——正是它能把包池布局显出来。

## 第 1 步:创建 DEB Dist

一个 Dist 只有一种格式。名字取客户端会在 sources 行里写的那个 suite——`trixie`、`noble`、
`bookworm`,看你要覆盖哪个。

```bash
sow dist new trixie --format deb -r pigsty
```

```console
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=5 dirty=false
```

Dist 继承了工作区的架构。SOW 内部把架构存成规范 CPU family(`x86_64`、`aarch64`),在 DEB 树里
按生态名渲染,于是 `x86_64` 变成 `binary-amd64`、`aarch64` 变成 `binary-arm64`。你不需要自己
在两套写法之间来回换算。

看看空 Dist 产出了什么:

```bash
find pigsty/dists/trixie -type f | sort
```

```console
pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
pigsty/dists/trixie/main/binary-amd64/Packages
pigsty/dists/trixie/main/binary-amd64/Packages.gz
pigsty/dists/trixie/main/binary-arm64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
pigsty/dists/trixie/main/binary-arm64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
pigsty/dists/trixie/main/binary-arm64/Packages
pigsty/dists/trixie/main/binary-arm64/Packages.gz
```

空仓库也是完整仓库:空 `Packages`、对应的 gzip、两者的 `by-hash` 副本,以及 Dist 根目录下的
`Release`。一个包都还没加,`apt update` 就已经能过。

component 恒为 `main`。APT 要求有一个,SOW 不建模更多,所以也就没有可以写错的 component 参数。

## 第 2 步:加包

```bash
sow add ~/packages/deb -d trixie
```

```console
add repository=pigsty operation=1500549235801273162 accepted=8 failed=0 memberships=+8/-0 revision=6 generation=6 dirty=false
item input="/home/you/packages/deb/agentsview_0.37.5-1_amd64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:amd64" sha256:9f489369bbff02cde4b09397b91bbf367429d8e8cd9d97fc75ba5ea79bb9225a dists=trixie:accepted
item input="/home/you/packages/deb/agentsview_0.37.5-1_arm64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:arm64" sha256:164fbda74eb82cedacc42902387aa0552c72286dc9e8daa964f2f09e356b3324 dists=trixie:accepted
item input="/home/you/packages/deb/blackbox-exporter_0.28.0_amd64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:amd64" sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120 dists=trixie:accepted
item input="/home/you/packages/deb/blackbox-exporter_0.28.0_arm64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:arm64" sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3 dists=trixie:accepted
item input="/home/you/packages/deb/caddy_2.11.4-1_amd64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:amd64" sha256:79de4b2dda79161164b9b437a0f6d4339c1236f806e5750e8e488fa1e0ede679 dists=trixie:accepted
item input="/home/you/packages/deb/caddy_2.11.4-1_arm64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:arm64" sha256:3a21855bb702ffaaafa30f2b626808b43e220ea26cf53ed2ea5aabed0f1aa1dc dists=trixie:accepted
item input="/home/you/packages/deb/libpq5_18.4-1.pgdg24.04+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.4-1.pgdg24.04+1:arm64" sha256:923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21 dists=trixie:accepted
item input="/home/you/packages/deb/postgresql-client-common_291.pgdg24.04+1_all.deb" status=accepted format=deb coordinate="postgresql-client-common=291.pgdg24.04+1:all" sha256:8cae086c805e44272004d111f9f1177789dc14f0bcd07fd901471915a4eed001 dists=trixie:accepted
```

DEB 坐标是 `包名=版本:架构`,例如 `libpq5=18.4-1.pgdg24.04+1:arm64`。版本是完整 Debian version,
含 epoch 与 revision;凡是需要排序的地方,SOW 都用 Debian 自己的比较规则。

所有信息都来自归档内的 `control` 文件,不看文件名。`.deb` 你随便改名,索引描述的仍是里面真实的内容。

## 第 3 步:读懂包池布局

```bash
find pigsty/pool -name "*.deb" | sort
```

```console
pigsty/pool/a/agentsview/agentsview_0.37.5-1_amd64.deb
pigsty/pool/a/agentsview/agentsview_0.37.5-1_arm64.deb
pigsty/pool/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pigsty/pool/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pigsty/pool/c/caddy/caddy_2.11.4-1_amd64.deb
pigsty/pool/c/caddy/caddy_2.11.4-1_arm64.deb
pigsty/pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pigsty/pool/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

路径是 `pool/<首字母>/<source>/<文件名>`。分组按**源码包**而不是二进制包名,所以 `libpq5` 落在
`postgresql-18` 下,`postgresql-client-common` 落在 `postgresql-common` 下——那是它们 control 文件
里的 `Source:` 字段。没有 `Source:` 的包回落到二进制名。首字母段遵循 Debian 规则:取 source
名首字符,source 名以 `lib` 开头时取前四个字符。

这与 reprepro 的分组完全一致。唯一区别是 SOW 的包池没有 component 层:SOW 写
`pool/p/postgresql-18/`,reprepro 写 `pool/main/p/postgresql-18/`。并排对比见
[迁移](/zh/docs/tutorial/migration/)。

## 第 4 步:读懂索引布局

```bash
find pigsty/dists/trixie -type f | grep -v by-hash | sort
```

```console
pigsty/dists/trixie/main/binary-amd64/Packages
pigsty/dists/trixie/main/binary-amd64/Packages.gz
pigsty/dists/trixie/main/binary-arm64/Packages
pigsty/dists/trixie/main/binary-arm64/Packages.gz
pigsty/dists/trixie/Release
```

看看 `all` 包是怎么投影的:

```bash
for a in amd64 arm64; do
  echo "-- binary-$a"
  grep -E "^(Package|Architecture):" pigsty/dists/trixie/main/binary-$a/Packages | paste - -
done
```

```console
-- binary-amd64
Package: agentsview	Architecture: amd64
Package: blackbox-exporter	Architecture: amd64
Package: caddy	Architecture: amd64
Package: postgresql-client-common	Architecture: all
-- binary-arm64
Package: agentsview	Architecture: arm64
Package: blackbox-exporter	Architecture: arm64
Package: caddy	Architecture: arm64
Package: libpq5	Architecture: arm64
Package: postgresql-client-common	Architecture: all
```

`postgresql-client-common` 是 `Architecture: all`,所以它由一个包池对象、一条成员记录同时出现在
两份索引里。`libpq5` 只有 `arm64`,就只出现在 `binary-arm64` 里——SOW 不会替你没提供的架构
凭空造一条 `amd64` 记录。

### 一段 Packages stanza

```bash
awk 'BEGIN{RS="";ORS="\n\n"} /^Package: libpq5/' pigsty/dists/trixie/main/binary-arm64/Packages
```

```console
Package: libpq5
Source: postgresql-18
Version: 18.4-1.pgdg24.04+1
Architecture: arm64
Maintainer: Debian PostgreSQL Maintainers <team+postgresql@tracker.debian.org>
Installed-Size: 1244
Depends: libc6 (>= 2.38), libgssapi-krb5-2 (>= 1.17), libldap2 (>= 2.6.2), libssl3t64 (>= 3.0.0)
Recommends: ca-certificates
Suggests: libpq-oauth
Section: libs
Priority: optional
Multi-Arch: same
Homepage: http://www.postgresql.org/
Description: PostgreSQL C client library
 libpq is a C library that enables user programs to communicate with
 the PostgreSQL database server.  The server can be on another machine
 and accessed through TCP/IP.  This version of libpq is compatible
 with servers from PostgreSQL 8.2 or later.
 .
 This package contains the run-time library, needed by packages using
 libpq. SSL certificate validation (the sslrootcert=system connection
 option) requires the ca-certificates package.
 .
 PostgreSQL is an object-relational SQL database management system.
Filename: pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
```

`Filename` 相对归档根目录——也就是你让 `apt` 指向的那个目录——所以整棵 `pool/` 树被仓库里
每个 Dist 共享。

有两样东西是刻意不写的。没有 `MD5sum`,也没有 `SHA1`:所有仍在接收安全更新的 APT 版本都验
SHA-256,输出弱摘要只会招人去信它。另外,包没声明的字段直接省略而不是输出空值——包里没有
`Section:`,索引里就没有 `Section:` 这一行。

## 第 5 步:读懂 Release 文件

```bash
cat pigsty/dists/trixie/Release
```

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:20:50 UTC
X-SOW-Generation: 6
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 c602557313a6b3e2d63768e136a665e27896f25c72d575721b7285a8f36bae38 2719 main/binary-amd64/Packages
 c4010af6637fe4cfb2ce83353c5083201db2babb2d2310960c81d33c5f8ff3d6 1274 main/binary-amd64/Packages.gz
 26e85b720b8f3482a7145322dd218232943e5535064e56c30279cace799bd931 3846 main/binary-arm64/Packages
 5814f56db24ef5c8ebd67061d64b26d581a09611437c634403e0c51ea4a952b6 1687 main/binary-arm64/Packages.gz
```

有意思的是 `Acquire-By-Hash: yes` 这一行。它告诉 APT 按内容哈希而不是按文件名去取索引:

```bash
ls pigsty/dists/trixie/main/binary-amd64/by-hash/SHA256/
```

```console
10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
c4010af6637fe4cfb2ce83353c5083201db2babb2d2310960c81d33c5f8ff3d6
c602557313a6b3e2d63768e136a665e27896f25c72d575721b7285a8f36bae38
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

没有 `by-hash` 时,一个客户端如果在你重建之前读了 `Release`、之后才取 `Packages`,就会撞上哈希
不匹配、`apt update` 失败。有了它,客户端请求的是自己刚读到的那份 `Release` 里指名的确切字节,
而那些字节还在——SOW 会把上一代索引副本与当前代并存,只有新 `Release` 就位之后才删。这是与
reprepro 最大的一处运维差异:reprepro 根本不支持 `by-hash`。

`X-SOW-Generation` 记录这棵树由哪次构建产出,纯信息性;APT 会忽略未知字段。

## 第 6 步:查询里面有什么

```bash
sow show 'deb:libpq5=18.4-1.pgdg24.04+1:arm64'
```

```console
{"repository":"pigsty","package":{"sha256":"923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21","format":"deb","coordinate":"libpq5=18.4-1.pgdg24.04+1:arm64","architecture":"arm64","canonical_arch":"aarch64","pool_path":"pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb","filename":"libpq5_18.4-1.pgdg24.04+1_arm64.deb","size":248592,"name":"libpq5","source":"postgresql-18","version":"18.4-1.pgdg24.04+1","kind":"main","storage":"pool","created_revision":6,"dists":["trixie"],"built_dists":["trixie"]}}
```

两种架构写法都会报出来:`architecture` 是生态叫法,`canonical_arch` 是 SOW 内部存的 CPU family。

裸包名在无歧义时可用,有歧义时拒绝:

```bash
sow where blackbox-exporter
```

```console
operation rejected: managed: operation rejected: package reference "blackbox-exporter" is ambiguous: deb:blackbox-exporter=0.28.0:amd64 sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120, deb:blackbox-exporter=0.28.0:arm64 sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3
```

退出码 `6`。候选项以可以直接粘回去的形式打印出来。完整文法——`sha256:`、`rpm:`、`deb:`、
文件名、裸名——见[包引用](/zh/docs/reference/package-ref/)。

仓库里有多个 Dist 之后,操作包的命令需要知道你指的是哪一个:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

退出码 `2`。加 `-d trixie` 即可。

## 第 7 步:删除前先预览

`sow rm -c` 会算出全部后果,但不取写锁、不动一个字节:

```bash
sow rm caddy -d trixie --check | jq -r '.removed[] | "\(.dist)\t\(.coordinate)"'
```

```console
trixie	deb:caddy=2.11.4-1:amd64
trixie	deb:caddy=2.11.4-1:arm64
```

`rm` 里的裸名表示所选 Dist 中该名称的全部版本与原生架构——这里是两个 `caddy` 构建。同一份输出
里还带着文件级计划:

```bash
sow rm caddy -d trixie --check | jq -r '.changes[] | "\(.op)\t\(.phase)\t\(.path)"'
```

```console
update	metadata	dists/trixie/main/binary-amd64/Packages
update	metadata	dists/trixie/main/binary-amd64/Packages.gz
add	metadata	dists/trixie/main/binary-amd64/by-hash/SHA256/260b4313742e5424c63235f568e9908701c2b6b3ab5e98d90120fa3194d8c670
add	metadata	dists/trixie/main/binary-amd64/by-hash/SHA256/c2e4559dc175b66bc6d52784e0d272bcc53596ea5372c62f15dc21a0312046f8
update	metadata	dists/trixie/main/binary-arm64/Packages
update	metadata	dists/trixie/main/binary-arm64/Packages.gz
add	metadata	dists/trixie/main/binary-arm64/by-hash/SHA256/a5ed9c07a26c462117fa6296faec08c34b52dcfa4730c2f689a2776260bdef4d
add	metadata	dists/trixie/main/binary-arm64/by-hash/SHA256/d2a892918009a7f6e7b81cb63ad89bee9523c4fade05d8535d0070ac6bd3f9a9
update	pointer	dists/trixie/Release
delete	delete	dists/trixie/main/binary-amd64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
delete	delete	dists/trixie/main/binary-amd64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
delete	delete	dists/trixie/main/binary-arm64/by-hash/SHA256/10c2221846da8b4250e556aa520c86d6674614d7c5874d8b9cb7f26d62835036
delete	delete	dists/trixie/main/binary-arm64/by-hash/SHA256/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

从上往下读 `phase` 那一列,那就是文件实际变更的顺序:新索引与它们的 `by-hash` 副本先落地,
`Release` 指针第二个翻,过期的 `by-hash` 条目最后删。任何正在 `apt update` 中途的客户端,
都能用它一开始读到的那份 `Release` 走完流程。

注意计划里没有的东西:`pool/` 下什么都没有。移除成员关系不会删除包体字节。去掉 `--check` 即执行。

## 第 8 步:配置 APT 客户端

把 `~/repo/pigsty/` 通过 HTTP 发布出去——见[对外服务](/zh/docs/tutorial/serving/)。假设它在
`https://repo.example.com/pigsty/`。

归档根目录就是仓库目录,suite 就是 Dist 名。架构目录 APT 自己会推。

{{< tabpane persist="header" >}}
{{< tab header="deb822(Debian 12+ / Ubuntu 22.04+)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /etc/apt/keyrings/pigsty.asc
{{< /tab >}}
{{< tab header="deb822(未签名,仅测试)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Trusted: yes
{{< /tab >}}
{{< tab header="传统 sources.list" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [arch=amd64 signed-by=/etc/apt/keyrings/pigsty.asc] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< tab header="传统(未签名,仅测试)" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [arch=amd64 trusted=yes] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< /tabpane >}}

能用 deb822 就用 deb822:这是 Debian 与 Ubuntu 正在迁移的格式,一行一个字段,也不需要那套
经常写错的方括号语法。

`Trusted: yes` 与 `trusted=yes` 会完全关掉签名校验。用它们先把链路跑通,然后照
[仓库签名](/zh/docs/tutorial/signing/)做完再换成 `Signed-By`。那篇讲了怎么生成密钥、怎么发布
armored 公钥,以及该放到 `/etc/apt/keyrings/` 下的什么位置。

如果希望客户端抓取你发布的全部架构,去掉 `Architectures:` / `arch=` 即可。

## 第 9 步:从客户端验证

```bash
sudo apt update
apt-cache policy libpq5
sudo apt install -y blackbox-exporter
```

`apt update` 打印出 `Get:… Packages` 且没有哈希或签名抱怨,说明 `Release` 与两份索引都解析成功;
`apt-cache policy` 把你的仓库列为候选源,说明 `Filename` 解析到位。

这套配置已在 Debian 13(apt 3.0.3)与 Debian 12(apt 2.6.1)上实测通过,含 `InRelease` 验签。
服务端日志证实两者都通过 `by-hash/SHA256/<hash>` 而不是按名取索引。完整矩阵见
[兼容性](/zh/docs/reference/compatibility/)。

{{% alert title="by-hash 需要较新的客户端" color="info" %}}
`Acquire-By-Hash` 从 APT 1.2 开始支持,覆盖所有仍在维护期的 Debian 与 Ubuntu 版本。更老的客户端
会忽略该字段、按名去取 `Packages`——仍然能用,只是失去了跨重建取索引的那层保护。
{{% /alert %}}

## 下一步去哪

{{< doc-cards cols="2" >}}
{{< doc-card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
生成密钥、产出 `InRelease` 与 `Release.gpg`,把客户端切到 `Signed-By`。
{{< /doc-card >}}
{{< doc-card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
实测过的 Nginx 配置,以及把整棵树拷到隔离主机的做法。
{{< /doc-card >}}
{{< doc-card title="搭建 YUM 仓库" link="/zh/docs/tutorial/yum-repo/" >}}
同一个仓库的 RPM 半边,含架构视图与成员策略。
{{< /doc-card >}}
{{< doc-card title="从 reprepro 迁移" link="/zh/docs/tutorial/migration/" >}}
把已有 reprepro 归档搬进工作区,附真实布局对比。
{{< /doc-card >}}
{{< /doc-cards >}}

包含 `by-hash` 与包池分组规则的完整目录树见[仓库布局](/zh/docs/reference/layout/)。
每个 `sow.yml` 字段见[配置参考](/zh/docs/reference/config/)。
