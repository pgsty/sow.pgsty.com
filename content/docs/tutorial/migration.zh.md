---
title: "从 createrepo_c / reprepro 迁移"
linkTitle: "从 createrepo_c / reprepro 迁移"
description: "就地接管已有仓库,或把 reprepro 归档搬进工作区,附真实的逐项差异对照。"
url: "/zh/docs/tutorial/migration/"
weight: 500
icon: fa-solid fa-right-left
---

你已经有一个仓库了。这篇教程换掉构建它的工具,而不弄坏消费它的客户端——包括没人会提醒你的那些
残留文件,以及应该在动手前而不是动手后知道的布局差异。

按你手上的东西分两条路。读匹配的那条,最后再看对比表。

## 先选目标形态

| 你现在有 | 迁移到 | 读这里 |
|---|---|---|
| 对一个 RPM 目录跑 `createrepo_c` | Plain 平面模式,就地 | [路线 A](#path-a) |
| 对一个平面 DEB 目录跑 `dpkg-scanpackages` | Plain 平面模式,就地 | [路线 A](#path-a) |
| 带 `pool/` 与 `dists/` 的 reprepro 归档 | Managed 托管工作区 | [路线 B](#path-b) |
| `createrepo_c` 加一堆多架构脚本 | Managed 托管工作区 | [路线 B](#path-b) |

Plain 模式是原地替换:同一个目录、同样的 URL,一条命令顶掉一整套工具链。Managed 模式是换形态
——工作区、包池、分架构视图——换来的是成员策略、事务式构建和审计账本。只想把依赖去掉就先迁到
Plain;真正让你难受的是仓库的生命周期,那就上 Managed。

## 路线 A:createrepo_c 就地接管 {#path-a}

`sow create` 就在包所在的位置给目录建索引。不搬文件、不改名、不删任何包。

### 起始状态

一个由 `createrepo_c 0.20.1` 建好的仓库:

```bash
ls repodata
```

```console
6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
repomd.xml
```

```bash
grep -o 'type="[a-z_]*"' repodata/repomd.xml | sort -u
```

```console
type="filelists_db"
type="filelists"
type="other_db"
type="other"
type="primary_db"
type="primary"
```

六条 data 记录:三份 XML 索引加三份 SQLite 数据库。SOW 不生成 SQLite 那三份——这是明确的非目标,
不是缺口。所有仍在接收更新的 dnf 与 yum 在没有 `*_db` 记录时都会回落到 XML 索引。

### 接管

```bash
sow create /srv/yum
```

```console
created /srv/yum: rpm=3 deb=0 signed=0 removed=0 marker=false noop=false recovered=false
```

`removed=0` 就是那句保证:没有任何包被动过。`signed=0` 是因为没给 `--sign-with`,所以也没有 RPM
被重签。

### 现在磁盘上是什么

```bash
ls repodata
```

```console
6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz
f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz
fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz
repomd.xml
```

**原来七个文件,现在十个。** SOW 加了自己的三份索引,`createrepo_c` 那六份原封不动留着。这不是
疏忽:SOW 不删自己没写过的字节。这条规则让一次失败或被中断的运行毁不掉一个正常工作的仓库,
也正是这条规则使得 `--pigsty` 成为唯一会移除包的模式。

新的 `repomd.xml` 是一份干净的替换,只引用新文件:

```bash
grep -o 'type="[a-z_]*"' repodata/repomd.xml | sort -u
```

```console
type="filelists"
type="other"
type="primary"
```

```bash
grep -o '<location href="[^"]*"' repodata/repomd.xml
```

```console
<location href="repodata/f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz"
<location href="repodata/fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz"
<location href="repodata/c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz"
```

此刻仓库已经正确、已经在服务。那些旧文件是死重:没有任何东西指向它们,没见过旧 `repomd.xml` 的
客户端也永远不会去要它们。

### 清理残留

这是路线 A 里唯一的手工步骤。安全规则是:删掉 `repodata/` 里当前 `repomd.xml` 不引用的每个文件。

```bash
cat > prune-legacy-repodata.sh <<'SH'
#!/bin/sh
# Delete every repodata file the current repomd.xml no longer references.
set -eu
cd "${1:-.}/repodata"
grep -o 'href="repodata/[^"]*"' repomd.xml | sed 's|.*repodata/||; s|"$||' > .keep
printf 'repomd.xml\n' >> .keep
for f in *; do
  [ "$f" = ".keep" ] && continue
  grep -qxF "$f" .keep || { echo "removing $f"; rm -f "$f"; }
done
rm -f .keep
SH
chmod +x prune-legacy-repodata.sh
sh prune-legacy-repodata.sh /srv/yum
```

```console
removing 6167bcf3bf31ac553056a6c60004f52f33391fcf4a0d67fa12e3b812e2c85541-primary.sqlite.bz2
removing 796b249defdd03d9775a6c23db45a09215af2d88aabeadca123f237127d6a5ef-filelists.xml.gz
removing bf4a15eb0869179894d9c80cd4326dc4c5a562434f4d282ad26d5617062d16cb-other.xml.gz
removing c29e1e85aa291940096864c80fedcb7e7f53723913a9551b16c29f4ae39373a3-primary.xml.gz
removing c8ed67b5858a8eca91f6a760412c04f8f1d7be441e2b0b98722350f2929965c2-other.sqlite.bz2
removing fbb08a2d958c266757ab4eee4aec65ee15973cb9d13f67d0c16265afe52309b1-filelists.sqlite.bz2
```

```bash
ls /srv/yum/repodata
```

```console
c92f116ebd1c410ed2433551357c5bd66153e4bdc27f1668ac84cb892fbc22b1-other.xml.gz
f7d8b4a3b21af9298a9888aede0de034690ff5bddc2a1aa52f858345b8e4897a-primary.xml.gz
fd91d28cf6b949747fc38ef391122dd10cbb3e1e14ec4b295629b004627d39e3-filelists.xml.gz
repomd.xml
```

这个脚本只需在第一次 `sow create` 之后跑一遍。之后每次运行都是自清理的:SOW 知道哪些文件是自己
写的,会直接替换掉。

{{% alert title="等客户端跟上再清" color="warning" %}}
如果客户端可能缓存了旧的 `repomd.xml`,等一个 `metadata_expire` 周期再清理。在还有客户端攥着旧
指针时删掉它指名的文件,那个客户端拿到的就是 404 而不是一次平滑刷新。
{{% /alert %}}

### 确认已经稳定

```bash
sow create /srv/yum
```

```console
created /srv/yum: rpm=3 deb=0 signed=0 removed=0 marker=false noop=true recovered=false
```

`noop=true` 表示什么都没变。输出是确定性的——同样的包产出字节级一致的元数据,`<revision>` 固定、
时间戳归零——所以重复运行既不花钱又可 diff。原来调 `createrepo_c` 的定时任务变成:

```bash
sow create /srv/yum
```

### 平面 DEB 目录

同一条命令处理 `dpkg-scanpackages` 的输出,也能一趟处理同时含两种格式的目录:

```bash
sow create /srv/mixed
```

`Packages` 与 `Packages.gz` 会被重写,gzip 内容与明文完全一致。字段与 `dpkg-scanpackages` 一致,
只有两处差异:不输出 `MD5sum` 与 `SHA1`(现代客户端验的是 SHA-256),以及包没声明的字段直接省略
而不是输出空值。

### Plain 模式带不过来的东西

`modulemd` 与模块元数据、SQLite repodata、`zchunk`、`comps`/`groups`、SRPM 源码索引都是非目标
——没有计划,也不是半成品。如果你的仓库要发布 AppStream 模块或 comps 组,Plain 模式今天替代不了
`createrepo_c`。

## 路线 B:reprepro 搬进工作区 {#path-b}

reprepro 在树旁边维护一个 Berkeley DB。SOW 读不了那个数据库,也没有导入命令——但你不需要。
`pool/` 里的包就是唯一要紧的状态,其余一切 `sow add` 都能从包头重新推导出来。

### 起始状态

```bash
cd /srv/apt && find pool dists -type f | sort
```

```console
dists/trixie/main/binary-amd64/Packages
dists/trixie/main/binary-amd64/Packages.gz
dists/trixie/main/binary-amd64/Release
dists/trixie/main/binary-arm64/Packages
dists/trixie/main/binary-arm64/Packages.gz
dists/trixie/main/binary-arm64/Release
dists/trixie/Release
pool/main/a/agentsview/agentsview_0.37.5-1_amd64.deb
pool/main/a/agentsview/agentsview_0.37.5-1_arm64.deb
pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pool/main/c/caddy/caddy_2.11.4-1_amd64.deb
pool/main/c/caddy/caddy_2.11.4-1_arm64.deb
pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pool/main/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

### 建工作区并导入

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
sow repo new archive
sow dist new trixie --format deb -r archive
```

```console
initialized /home/you/repo: config_created=true repositories_initialized=0 dists_initialized=0
created archive: path=/home/you/repo/archive protected=false dists=0 generation=0 status=clean packages=0 memberships=0
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

Dist 就用客户端 sources 行里已经写着的那个 codename,这样客户端那边不用改任何东西。

然后把 `sow add` 指向旧包池,加 `-R` 递归:

```bash
sow add /srv/apt/pool -R -d trixie
```

```console
add repository=archive operation=2553339663345297053 accepted=8 failed=0 memberships=+8/-0 revision=2 generation=2 dirty=false
item input="/srv/apt/pool/main/a/agentsview/agentsview_0.37.5-1_amd64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:amd64" sha256:9f489369bbff02cde4b09397b91bbf367429d8e8cd9d97fc75ba5ea79bb9225a dists=trixie:accepted
item input="/srv/apt/pool/main/a/agentsview/agentsview_0.37.5-1_arm64.deb" status=accepted format=deb coordinate="agentsview=0.37.5-1:arm64" sha256:164fbda74eb82cedacc42902387aa0552c72286dc9e8daa964f2f09e356b3324 dists=trixie:accepted
item input="/srv/apt/pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:amd64" sha256:1ca6db58a2ca839d1bc1e0f843e971c049f664388c111af5481015baeb9bb120 dists=trixie:accepted
item input="/srv/apt/pool/main/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb" status=accepted format=deb coordinate="blackbox-exporter=0.28.0:arm64" sha256:dd3d06c3b32017b47b721e02b24954dab6179399c3cecc2ce7c5c9a27510f3f3 dists=trixie:accepted
item input="/srv/apt/pool/main/c/caddy/caddy_2.11.4-1_amd64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:amd64" sha256:79de4b2dda79161164b9b437a0f6d4339c1236f806e5750e8e488fa1e0ede679 dists=trixie:accepted
item input="/srv/apt/pool/main/c/caddy/caddy_2.11.4-1_arm64.deb" status=accepted format=deb coordinate="caddy=2.11.4-1:arm64" sha256:3a21855bb702ffaaafa30f2b626808b43e220ea26cf53ed2ea5aabed0f1aa1dc dists=trixie:accepted
item input="/srv/apt/pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.4-1.pgdg24.04+1:arm64" sha256:923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21 dists=trixie:accepted
item input="/srv/apt/pool/main/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb" status=accepted format=deb coordinate="postgresql-client-common=291.pgdg24.04+1:all" sha256:8cae086c805e44272004d111f9f1177789dc14f0bcd07fd901471915a4eed001 dists=trixie:accepted
```

旧树完全没被动过——`add` 只是读取输入并复制。在验证新树之前先留着它。

### 对比两个包池

```bash
cd ~/repo/archive && find pool -name "*.deb" | sort
```

```console
pool/a/agentsview/agentsview_0.37.5-1_amd64.deb
pool/a/agentsview/agentsview_0.37.5-1_arm64.deb
pool/b/blackbox-exporter/blackbox-exporter_0.28.0_amd64.deb
pool/b/blackbox-exporter/blackbox-exporter_0.28.0_arm64.deb
pool/c/caddy/caddy_2.11.4-1_amd64.deb
pool/c/caddy/caddy_2.11.4-1_arm64.deb
pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
pool/p/postgresql-common/postgresql-client-common_291.pgdg24.04+1_all.deb
```

每条路径都与 reprepro 一致,只少了一段:reprepro 写 `pool/main/p/postgresql-18/…`,SOW 写
`pool/p/postgresql-18/…`。两者推导分组的方式相同——先 Debian 首字母规则,再源码包名——而且都把
`libpq5` 放在 `postgresql-18` 下,因为那是它的 `Source:` 字段。

**SOW 的包池没有 component 层。** component 固定为 `main`,以它命名的目录不携带任何信息。对迁移的
具体影响是:`Filename` 值变了,意味着客户端必须取新索引而不能复用缓存。由于新的 `Release` 本来就
带着新哈希发布,这件事会在下一次 `apt update` 自动发生,你不用做什么——但它也意味着你不能用新索引
去配旧包池目录,反之亦然。

### 切换之前先验证

```bash
sow check
```

```console
repository=archive status=clean ready_to_copy=true revision=2 generation=2
config	ok=true	checked=3
state	ok=true	checked=1
public-modes	ok=true	checked=41
package-bytes	ok=true	checked=8
desired-membership	ok=true	checked=8
index	ok=true	checked=1
signature	ok=true	checked=1
generation-manifest	ok=true	checked=2
```

先把新树挂在一个临时 URL 上,指一台客户端过去,跑 `apt update` 并装点东西。然后再换文档根、
删旧树——不要提前。

### 索引层面的差异

reprepro 的 `Release` 发四种摘要,并生成分架构 `Release` 存根:

```console
Codename: trixie
Date: Tue, 04 Aug 2026 04:33:33 UTC
Architectures: amd64 arm64
Components: main
Description: legacy reprepro archive
MD5Sum:
 a4b9d08caee42b0a2764d4d0ab58c914 3670 main/binary-amd64/Packages
 1fab9172bc826e3054cf6661138732b4 10240 main/binary-amd64/Packages.gz
 b2424f6aef8e120796d78fbabf067a86 73 main/binary-amd64/Release
 …
```

SOW 只发 SHA-256,并加上 `Acquire-By-Hash: yes`——完整文件见
[搭建 APT 仓库](/zh/docs/tutorial/apt-repo/)。它不生成 `main/binary-*/Release` 存根:APT 不需要,
而 reprepro 那份里的三行信息在 Dist `Release` 里本来就有。

逐包看是同一个故事:

```console
# reprepro
Package: libpq5
Source: postgresql-18
Filename: pool/main/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
SHA1: bbbbcd35976ba44fdf423553b59cc3679c4f2183
MD5sum: 3f234b897f88f495314768956a73a055

# sow
Package: libpq5
Source: postgresql-18
Filename: pool/p/postgresql-18/libpq5_18.4-1.pgdg24.04+1_arm64.deb
Size: 248592
SHA256: 923e440808f148f7e44a29fe4c036f836911afdfeffa9dd8cb2009918b614a21
```

大小相同、SHA-256 相同,`Filename` 不同,不带弱摘要。

### 习惯上的对应

| reprepro | SOW |
|---|---|
| `reprepro includedeb trixie foo.deb` | `sow add foo.deb -d trixie` |
| `reprepro remove trixie foo` | `sow rm foo -d trixie` |
| `reprepro list trixie` | `sow ls -d trixie` |
| `reprepro check` | `sow check` |
| `conf/distributions` 里的 `Limit:` | `sow.yml` 里每个 Dist 的 `limit:` |
| `FilterList` / `FilterFormula` | `sow.yml` 里的 `exclude:` 规则 |
| `conf/distributions` 里的 `SignWith:` | `sow.yml` 里的 `signing.deb.metadata.key` |
| `--export=never` 再 `reprepro export` | `--skip` 再 `sow build` |
| `reprepro _listchecksums` | `sow changes BASE` |

SOW 每个 Repository 拥有一份权威 SQLite 状态数据库。不要把它作为公共内容复制或编辑;
`sow check` 会证明记录的 Generation、配置、元数据与包体树仍然一致。

## 完整对比

在相同包集上,对照 `createrepo_c 0.20.1` 与 reprepro 实测。

| | SOW | createrepo_c | reprepro |
|---|---|---|---|
| RPM 元数据 | `primary`/`filelists`/`other`,语义等价 | 基准 | — |
| SQLite repodata | 不生成(非目标) | 默认生成 | — |
| DEB `Packages` 字段 | 等价,仅 SHA-256 | — | 基准(MD5 + SHA1 + SHA256) |
| `by-hash` 索引 | 支持(`Acquire-By-Hash: yes`) | — | **不支持** |
| 包池布局 | `pool/<首字母>/<source>/` | — | `pool/main/<首字母>/<source>/` |
| 分架构 `Release` 存根 | 不生成(APT 不需要) | — | 生成 |
| 平台 | Linux 与 macOS,单一静态二进制 | 实际只在 Linux | 仅 Linux |
| 事务 | journal,可前滚与回滚 | 无 | 数据库可能损坏 |
| 审计 | 操作账本 + JSONL 导出 | 无 | 日志有限 |
| 依赖 | 无 | C 库:libxml2、libcurl、sqlite…… | Berkeley DB、gpgme、libarchive |

RPM 元数据在 9 个合成包与 87 个真实生产包上做过逐字段比对:name、arch、EVR、checksum、sizes、
provides、requires flags、files、changelog、header range 全部一致。只发现一处差异:当 RPM 包头把
`/bin/sh` 在 pre 与非 pre 两个上下文里各列一次时,SOW 只保留一条。

## 迁不过来的东西

以下都是非目标,不是路线图上的待办:

- `modulemd` / AppStream 模块元数据,以及 `repo2module` / `modifyrepo_c` 流程
- SQLite repodata 与 `zchunk`
- SRPM 与 DSC 源码索引
- 多机或多写者运行
- 隐式 channel 晋级语义(Dist 名只是普通标签)
- 充当 HTTP 服务或 CDN
- Web UI 或任何常驻服务
- 造包

SOW 在本地 POSIX 文件系统上维护权威工作区,同一时刻只有一个写者,并可把已验证 Generation
发布到配置好的 filesystem 或 R2 目标。如果剩余某条非目标对你是刚需,就继续使用提供它的工具。

## 下一步去哪

{{< doc-cards cols="2" >}}
{{< doc-card title="搭建 YUM 仓库" link="/zh/docs/tutorial/yum-repo/" >}}
Plain 模式不够用时,完整的 Managed RPM 流程。
{{< /doc-card >}}
{{< doc-card title="搭建 APT 仓库" link="/zh/docs/tutorial/apt-repo/" >}}
包池布局、`by-hash` 与客户端配置的细节。
{{< /doc-card >}}
{{< doc-card title="能力总览" link="/zh/docs/feature/overview/" >}}
SOW 全部能力一张表,含与传统工具的对标。
{{< /doc-card >}}
{{< doc-card title="兼容性" link="/zh/docs/reference/compatibility/" >}}
实测客户端矩阵与平台要求。
{{< /doc-card >}}
{{< /doc-cards >}}
