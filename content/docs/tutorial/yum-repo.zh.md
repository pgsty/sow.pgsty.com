---
title: "搭建 YUM 仓库"
linkTitle: "搭建 YUM 仓库"
description: "建一个托管 RPM 仓库:分架构视图、噪声过滤,以及可用的 dnf 客户端配置。"
url: "/zh/docs/tutorial/yum-repo/"
weight: 100
icon: fa-solid fa-box-open
---

这篇教程从零搭出一个生产形态的 RPM 仓库。做完你会得到:一个工作区(Workspace),里面有名为
`pigsty` 的仓库(Repository)和一个 `el9` Dist,由单一包池(pool)渲染出两个架构视图,
debuginfo 噪声被过滤掉,每个包只保留最新版本,以及一份 `dnf` 能吃的 `.repo` 文件。

预计十五分钟。全部命令都在本地跑,不访问网络。

## 开始之前

需要三样东西。

**SOW 已在 PATH 里**。确认一下:

```bash
sow version
```

```console
sow 0.2.0-dev darwin/arm64 go1.26.5
```

报错的话看[安装](/zh/docs/start/install/)。

**一些 RPM 文件**。自己编的、下载的、或者现成在分发的目录都行。本教程用了九个 RPM,覆盖
`x86_64`、`aarch64`、`noarch`,其中包含 `etcd` 的两个版本和一对 debuginfo 包——正是这些情况
能把有意思的行为暴露出来。

**一个可写目录**。工作区自成一体,不会往外面写任何东西。

{{% alert title="Plain 平面模式更简单" color="info" %}}
如果你只是要给一个目录里的 RPM 就地生成索引,根本用不上这些。跑 `sow create /path/to/dir` 就完事
——见[快速上手](/zh/docs/start/quickstart/)。当仓库有生命周期时才需要 Managed 托管模式:
多架构、成员规则、签名、审计、增量交付。
{{% /alert %}}

## 第 1 步:创建工作区

工作区就是一个目录,里面有 `sow.yml` 和状态目录 `.sow/`。其余一切都在它下面。

```bash
mkdir -p ~/repo && cd ~/repo
sow init .
```

```console
initialized /home/you/repo: config_created=true repositories_initialized=0 dists_initialized=0
```

`sow init` 写了一份最小 `sow.yml`:

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
```

这两个架构是整个工作区的许可上限。原生架构不在表里的包会被拒绝,而不是悄悄把你的配置撑大。

`sow init` 是幂等的。对同一目录重复执行是收敛而不是报错,所以放进 provisioning 脚本很安全。

## 第 2 步:创建仓库

一个仓库拥有自己的包池、一组 Dist 和独立的 SQLite 状态。它同时也是锁、事务与代(Generation)
的边界。

```bash
sow repo new pigsty
```

```console
created pigsty: path=/home/you/repo/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

现在有了 `~/repo/pigsty/`,这就是将来要通过 HTTP 对外服务的目录。内部状态在上一层的
`~/repo/.sow/` 里——它永远不会落进任何你发布出去的东西。

## 第 3 步:创建 RPM Dist

Dist 是一个具名的、单一格式的包集合。给 Enterprise Linux 9 建一个:

```bash
sow dist new el9 --format rpm -r pigsty
```

```console
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
```

Dist 继承了工作区的两个架构。看看它产出了什么:

```bash
find pigsty -type f | sort
```

```console
pigsty/dists/el9/aarch64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz
pigsty/dists/el9/aarch64/repodata/8402c28c7c848d02a6ef5c728a8741a2d402792bf9dc4a62ec0657912f4c1719-filelists.xml.gz
pigsty/dists/el9/aarch64/repodata/c16c7739903ecd19f56b49c14f11710643f6de391d13646c22ce95c6910d6106-other.xml.gz
pigsty/dists/el9/aarch64/repodata/repomd.xml
pigsty/dists/el9/x86_64/repodata/0df96f0b046b6c098398194f908cc99d90bf3af8c5f66d262b2e6d43a658a58f-primary.xml.gz
pigsty/dists/el9/x86_64/repodata/8402c28c7c848d02a6ef5c728a8741a2d402792bf9dc4a62ec0657912f4c1719-filelists.xml.gz
pigsty/dists/el9/x86_64/repodata/c16c7739903ecd19f56b49c14f11710643f6de391d13646c22ce95c6910d6106-other.xml.gz
pigsty/dists/el9/x86_64/repodata/repomd.xml
```

空 Dist 本身就是一个合法仓库。每个架构视图都有完整的 `repodata`,`dnf makecache` 直接就能过
——客户端不必等你的第一个包。元数据文件以自身 SHA-256 命名,`repomd.xml` 是唯一的指针。

## 第 4 步:加包

`sow add` 可以接文件、多个文件或目录。目录默认只扫顶层,加 `-R` 才递归。

```bash
sow add ~/packages/rpm -d el9
```

```console
add repository=pigsty operation=4475889911918567992 accepted=9 failed=0 memberships=+9/-0 revision=2 generation=2 dirty=false
item input="/home/you/packages/rpm/armadillo-10.8.2-3.el9.x86_64.rpm" status=accepted format=rpm coordinate="armadillo-0:10.8.2-3.el9.x86_64" sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2 dists=el9:accepted
item input="/home/you/packages/rpm/blackbox_exporter-0.28.0-1.aarch64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.12-1.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-0:3.5.12-1.el8.x86_64" sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.30-1.el9.x86_64.rpm" status=accepted format=rpm coordinate="etcd-0:3.5.30-1.el9.x86_64" sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-debuginfo-0:3.3.11-4.el8.x86_64" sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debugsource-3.3.11-4.el8.x86_64.rpm" status=accepted format=rpm coordinate="etcd-debugsource-0:3.3.11-4.el8.x86_64" sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110 dists=el9:accepted
item input="/home/you/packages/rpm/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm" status=accepted format=rpm coordinate="patroni-0:4.1.4-1PGDG.rhel9.6.noarch" sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6 dists=el9:accepted
item input="/home/you/packages/rpm/pev2-1.22.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.22.0-1.noarch" sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b dists=el9:accepted
item input="/home/you/packages/rpm/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm" status=accepted format=rpm coordinate="pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64" sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607 dists=el9:accepted
```

这一条命令里发生了好几件事,全在一个事务里。

format 与架构来自 RPM 包头,不看文件名。二进制 RPM 即使被改名成 `*.src.rpm`,仍按真实架构建索引;
包头里 arch 是 `src` 的直接拒绝。

每个包拿到一个**坐标(coordinate)**——它的 NEVRA,比如 `etcd-0:3.5.30-1.el9.x86_64`——以及标识
确切字节的 SHA-256。两者都打印出来,后续命令直接复制即可,不用手工拼。

`add` 在返回前已经把公开树建好了。`dirty=false` 与 `generation=2` 表示磁盘上的仓库此刻就是完整的。
这是默认行为;可以用 `--skip` 推迟构建,第 7 步会用到。

确认一下:

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=2 generation=2 dirty_dists= pending=0/0 locked=false
```

`ready_to_copy=true` 是脚本该判断的那个字段。它表示 `pool/` 与 `dists/` 是一套自洽的、可以原样
rsync 出去的文件集合。

## 第 5 步:读懂布局

那次 add 产出了两套结构。先看包池:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2	rpm:armadillo-0:10.8.2-3.el9.x86_64	el9	el9	pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91	rpm:etcd-0:3.5.12-1.el8.x86_64	el9	el9	pool/e/etcd/etcd-3.5.12-1.el8.x86_64.rpm
sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a	rpm:etcd-0:3.5.30-1.el9.x86_64	el9	el9	pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm
sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475	rpm:etcd-debuginfo-0:3.3.11-4.el8.x86_64	el9	el9	pool/e/etcd/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm
sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110	rpm:etcd-debugsource-0:3.3.11-4.el8.x86_64	el9	el9	pool/e/etcd/etcd-debugsource-3.3.11-4.el8.x86_64.rpm
sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6	rpm:patroni-0:4.1.4-1PGDG.rhel9.6.noarch	el9	el9	pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b	rpm:pev2-0:1.22.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.22.0-1.noarch.rpm
sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607	rpm:pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm
```

包池路径是 `pool/<首字母>/<source>/<文件名>`。RPM 的 source 取自 `SOURCERPM` 包头,所以
`etcd-debuginfo` 和 `etcd-debugsource` 与 `etcd` 一起躺在 `pool/e/etcd/`。包池相对 Dist 是扁平的:
一个对象、一个位置,无论多少 Dist 引用它。

### 架构视图

`dnf` 读的不是包池。每个 Dist 会按架构渲染出视图:

```bash
find pigsty/dists/el9 -name "*.rpm" | sort
```

```console
pigsty/dists/el9/aarch64/pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
pigsty/dists/el9/aarch64/pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
pigsty/dists/el9/aarch64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
pigsty/dists/el9/aarch64/pool/p/pgbouncer/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm
pigsty/dists/el9/x86_64/pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm
pigsty/dists/el9/x86_64/pool/e/etcd/etcd-3.5.12-1.el8.x86_64.rpm
pigsty/dists/el9/x86_64/pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm
pigsty/dists/el9/x86_64/pool/e/etcd/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm
pigsty/dists/el9/x86_64/pool/e/etcd/etcd-debugsource-3.3.11-4.el8.x86_64.rpm
pigsty/dists/el9/x86_64/pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
pigsty/dists/el9/x86_64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
```

`x86_64` 视图装 `x86_64` 加 `noarch`;`aarch64` 视图装 `aarch64` 加 `noarch`。`noarch` 不是第三种
架构,而是一个中性(neutral)投影,会落进每个适用的视图。

视图里的文件是指向根包池的硬链接,不是副本:

```bash
stat -c "%h %n" pigsty/pool/p/pev2/pev2-1.22.0-1.noarch.rpm \
                pigsty/dists/el9/x86_64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm \
                pigsty/dists/el9/aarch64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
```

```console
3 pigsty/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
3 pigsty/dists/el9/x86_64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
3 pigsty/dists/el9/aarch64/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
```

一个 inode,三个名字。一个 `noarch` 包出现在两个视图里,磁盘上只占一份空间。

{{% alert title="硬链接是硬性要求" color="warning" %}}
包池与视图必须位于同一个 POSIX 文件系统。硬链接不可用或路径跨越挂载点时,SOW 明确失败,
不会悄悄退化成复制。把 `pool/` 放一个卷、`dists/` 放另一个卷是不行的。
{{% /alert %}}

### 为什么要有视图

显而易见的替代方案是:只留一份物理包池,让包的 location 指向 `../../../pool/...`。这个方案对真实
客户端做过实测,并被否决:`dnf makecache`、`repoquery`、`download` 和 `install` 全都能过,但
`dnf reposync` 拒绝了——规范化后的本地目标逃出了它的 per-repository 下载根目录。

最终采用的布局写的是不含 `..` 的安全相对路径:

```bash
gzip -dc pigsty/dists/el9/x86_64/repodata/*-primary.xml.gz | grep -o '<location href="[^"]*"'
```

```console
<location href="pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm"
<location href="pool/e/etcd/etcd-3.5.12-1.el8.x86_64.rpm"
<location href="pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm"
<location href="pool/e/etcd/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm"
<location href="pool/e/etcd/etcd-debugsource-3.3.11-4.el8.x86_64.rpm"
<location href="pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm"
<location href="pool/p/pev2/pev2-1.22.0-1.noarch.rpm"
```

所有路径都在视图目录内解析,所以 `reposync` 能正确镜像整个仓库。

## 第 6 步:过滤噪声

现在仓库里带着 debuginfo 包和 `etcd` 的两个版本。对交付型仓库来说这通常都不对。成员策略
(membership policy)写在 `sow.yml` 里而不是命令行上,这样规则可评审、可复现。

编辑 `~/repo/sow.yml`:

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64

repos:
  pigsty:
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
```

`limit: 1` 表示每个 `(包名, 原生架构)` 组合只保留最新版本,比较规则用 RPM 自己的 EVR。
`exclude` 按分类丢包;`kind` 由二进制包名后缀推导,所以 `-debuginfo` 和 `-debugsource` 会被
自动识别,不用你写 glob。

动树之前先校验:

```bash
sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=1
```

配置合法,但已建好的树不再与它一致:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=2 generation=2 dirty_dists=el9 pending=0/0 locked=false
```

`dirty` 表示期望状态领先于磁盘上的内容。旧树仍然完整、仍能正常服务——在你收敛之前,客户端看到的
还是上一代。

```bash
sow build
```

```console
{"operation":"2673156477918637099","repository":"pigsty","dists":["el9"],"desired_revision":3,"built_generation":3,"noop":false,"dirty":false}
```

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2	rpm:armadillo-0:10.8.2-3.el9.x86_64	el9	el9	pool/a/armadillo/armadillo-10.8.2-3.el9.x86_64.rpm
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a	rpm:etcd-0:3.5.30-1.el9.x86_64	el9	el9	pool/e/etcd/etcd-3.5.30-1.el9.x86_64.rpm
sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6	rpm:patroni-0:4.1.4-1PGDG.rhel9.6.noarch	el9	el9	pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm
sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b	rpm:pev2-0:1.22.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.22.0-1.noarch.rpm
sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607	rpm:pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm
```

成员从九个变成六个。两个 debuginfo 包和旧版 `etcd` 已从索引中消失。它们的字节仍留在 `pool/` 里
——SOW 移除的是成员关系而不是包体——所以一次可能想回退的策略调整不会毁掉任何东西。

现在把同一次 `add` 再跑一遍,看策略如何汇报自己:

```bash
sow add ~/packages/rpm -d el9
```

```console
add repository=pigsty operation=3213883523634766313 accepted=6 failed=0 memberships=+0/-0 revision=3 generation=3 dirty=false
item input="/home/you/packages/rpm/armadillo-10.8.2-3.el9.x86_64.rpm" status=reused format=rpm coordinate="armadillo-0:10.8.2-3.el9.x86_64" sha256:7ce1effe2897a6cd1a31849bdb2e315b53186a1bb09ed71d8d489190795cded2 dists=el9:accepted
item input="/home/you/packages/rpm/blackbox_exporter-0.28.0-1.aarch64.rpm" status=reused format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="/home/you/packages/rpm/etcd-3.5.12-1.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-0:3.5.12-1.el8.x86_64" sha256:bc795bdd732112c36eecffa1e6f94f6c093f5deca56d71d0026ec61e89893f91 dists=el9:limited
item input="/home/you/packages/rpm/etcd-3.5.30-1.el9.x86_64.rpm" status=reused format=rpm coordinate="etcd-0:3.5.30-1.el9.x86_64" sha256:a905f9918f4ad224b3eb7fd6bafed50a578e3d321a2900fc38a642af6f342e0a dists=el9:accepted
item input="/home/you/packages/rpm/etcd-debuginfo-3.3.11-4.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-debuginfo-0:3.3.11-4.el8.x86_64" sha256:3dcee7ab93e67cf5ec4cd6a2dff2c1e4f8d189cc1751654d2fb75503cee96475 dists=el9:excluded
item input="/home/you/packages/rpm/etcd-debugsource-3.3.11-4.el8.x86_64.rpm" status=excluded format=rpm coordinate="etcd-debugsource-0:3.3.11-4.el8.x86_64" sha256:f6020dbfd40c3d68c3dc1adefbfd39f304944c7c8268c4e206139ca589d02110 dists=el9:excluded
item input="/home/you/packages/rpm/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm" status=reused format=rpm coordinate="patroni-0:4.1.4-1PGDG.rhel9.6.noarch" sha256:077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6 dists=el9:accepted
item input="/home/you/packages/rpm/pev2-1.22.0-1.noarch.rpm" status=reused format=rpm coordinate="pev2-0:1.22.0-1.noarch" sha256:a8456bb578f82d28b1beebc4d756bad4a508a3e4944ef57dc7e2fd048882423b dists=el9:accepted
item input="/home/you/packages/rpm/pgbouncer-1.25.2-42PGDG.rhel9.6.aarch64.rpm" status=reused format=rpm coordinate="pgbouncer-0:1.25.2-42PGDG.rhel9.6.aarch64" sha256:5d0e1b7a72c72b37fab5047a85e4dddecd17d41e376b96300706b68f1b3d3607 dists=el9:accepted
```

什么都没变:`memberships=+0/-0`,`generation=3` 保持不动。重复 add 同一个包是稳定的 no-op,
这正是每晚定时任务需要的性质。逐包结果写得很明白:字节已存在是 `reused`,命中规则是 `excluded`,
被 `limit` 挤掉的版本在对应 Dist 上标 `limited`。

{{% alert title="策略不会复活成员" color="warning" %}}
以后放宽规则不会把老成员找回来。调高 `limit` 或删掉一条 `exclude` 只能阻止将来的移除,已经被
移出的包必须重新显式 `add`。这是刻意设计:SOW 绝不猜测你想发布哪些历史字节。
{{% /alert %}}

## 第 7 步:批量变更而不立即发布

`add` 与 `rm` 默认会构建。批量准备时,用 `--skip` 推迟构建,最后一次性收敛。

```bash
sow add ~/packages/gdal311-3.11.0-2.rhel9.x86_64.rpm -d el9 --skip
```

```console
add repository=pigsty operation=7821893517298386853 accepted=1 failed=0 memberships=+1/-0 revision=4 generation=3 dirty=true
item input="/home/you/packages/gdal311-3.11.0-2.rhel9.x86_64.rpm" status=accepted format=rpm coordinate="gdal311-0:3.11.0-2.rhel9.x86_64" sha256:9d245f1e2c5e44543e834f2cbff4d57a11938cb3040577cbb0f12edb0fa1baeb dists=el9:accepted
```

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=4 generation=3 dirty_dists=el9 pending=1/497416 locked=false
```

新包被耐久保存在私有 pending 区(`pending=1/497416`——一个对象,497 KB)。公开树一个字节都没变,
客户端看到的仍是第 3 代。

`sow check` 就是那道不许你发布半成品的闸:

```bash
sow check
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=4 generation=3
config	ok=true	checked=3
state	ok=true	checked=1
public-modes	ok=true	checked=64
package-bytes	ok=true	checked=10
desired-membership	ok=true	checked=7
index	ok=true	checked=1
signature	ok=true	checked=18
generation-manifest	ok=true	checked=3
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

退出码 `5`。每一层都校验通过——没有任何东西损坏——但因为期望状态领先于它,这棵树还不可交付。收敛:

```bash
sow build -d el9
sow status
```

```console
{"operation":"8823464502290701703","repository":"pigsty","dists":["el9"],"desired_revision":4,"built_generation":4,"noop":false,"dirty":false}
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

## 第 8 步:配置 dnf 客户端

把 `~/repo/pigsty/` 通过 HTTP 发布出去——[对外服务](/zh/docs/tutorial/serving/)有一份实测过的
Nginx 配置。假设它可以从 `https://repo.example.com/pigsty/` 访问。

仓库 URL 指向架构视图:`dists/<dist>/$basearch`。在 Enterprise Linux 上 `$basearch` 正好展开成
`x86_64` 或 `aarch64`,这也是 RPM 视图用这两个名字的原因——一份 `.repo` 覆盖两个架构。

写 `/etc/yum.repos.d/pigsty.repo`:

{{< tabpane persist="header" >}}
{{< tab header="EL8 / EL9 / EL10" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=0
repo_gpgcheck=0
metadata_expire=300
{{< /tab >}}
{{< tab header="EL8 / EL9 / EL10(已签名)" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
metadata_expire=300
{{< /tab >}}
{{< tab header="CentOS 7(yum)" lang="ini" >}}
[pigsty-el7]
name=Pigsty EL7 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el7/$basearch
enabled=1
gpgcheck=0
repo_gpgcheck=0
{{< /tab >}}
{{< /tabpane >}}

第一个标签页是现在就能用的配置,因为你还没签任何东西。先用它把链路跑通,读完
[仓库签名](/zh/docs/tutorial/signing/)后再换到第二个——那篇讲了怎么生成密钥、怎么发布
`RPM-GPG-KEY-pigsty`,以及 `gpgcheck` 和 `repo_gpgcheck` 各自验的是什么。

`metadata_expire=300` 是调试期的方便设置,仓库稳定后应当调大。

## 第 9 步:从客户端验证

```bash
dnf clean all
dnf makecache
dnf repoquery --repo=pigsty-el9 --queryformat '%{name}-%{evr}.%{arch}'
dnf install -y pev2
```

`makecache` 能取到 `repomd.xml` 和三个 checksum 命名的文件,说明元数据格式正确;`repoquery`
能列出包,说明 `primary.xml.gz` 解析正常;`install` 成功,说明 `location href` 解析到位。

这套配置已在 AlmaLinux 8/9/10 的 dnf4 与 CentOS 7 的 yum 3.4.3 上实测通过,后者对多版本 NEVRA
列表的解析也正确。完整矩阵见[兼容性](/zh/docs/reference/compatibility/)。

### 用 reposync 做镜像

因为视图使用的是安全相对路径,`dnf reposync` 能完整镜像整个仓库:

```bash
reposync --repo=pigsty-el9 --download-metadata --downloadcomps -p /srv/mirror
```

镜像会在视图下复现 `pool/` 布局。这正是被否决的那个布局过不去、而当前布局能过的那项检查。

## 下一步去哪

{{< doc-cards cols="2" >}}
{{< doc-card title="搭建 APT 仓库" link="/zh/docs/tutorial/apt-repo/" >}}
往同一个仓库里再加一个 DEB Dist。一个包池,两套生态。
{{< /doc-card >}}
{{< doc-card title="仓库签名" link="/zh/docs/tutorial/signing/" >}}
把 `gpgcheck` 和 `repo_gpgcheck` 真正打开。
{{< /doc-card >}}
{{< doc-card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
实测过的 Nginx 配置与离线拷贝流程。
{{< /doc-card >}}
{{< doc-card title="成员策略" link="/zh/docs/feature/policy/" >}}
每个 `exclude` 字段、`kind` 枚举,以及 `limit` 如何比较版本。
{{< /doc-card >}}
{{< /doc-cards >}}

命令语法与退出码见[命令行](/zh/docs/reference/cli/)与[退出码](/zh/docs/reference/exit-codes/)。
包含 `.sow/` 内部结构的完整目录树见[仓库布局](/zh/docs/reference/layout/)。
