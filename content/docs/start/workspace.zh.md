---
title: "第一个工作区"
linkTitle: "第一个工作区"
description: "创建 Managed 工作区,建立 RPM 与 DEB 两种 Dist,添加软件包并查看产出。"
url: "/zh/docs/start/workspace/"
weight: 300
icon: fa-solid fa-layer-group
---

这一页大约十分钟,从零搭出一个 Managed 托管仓库:一个工作区、一个仓库、其中的一个 RPM Dist
与一个 DEB Dist,往两边添加软件包,最后看清楚磁盘上到底生成了什么。
与 [Plain 平面模式](/zh/docs/start/quickstart/)不同,工作区会**记住**你的意图 ——
你按名字增删软件包,而不是靠搬文件,SOW 只重建真正变化的部分。

## 1. 创建工作区

```bash
mkdir -p /srv/sow
cd /srv/sow
sow init .
```

```console
initialized /srv/sow: config_created=true repositories_initialized=0 dists_initialized=0
```

`init` 创建了两样东西:`sow.yml`,即这个工作区包含什么的唯一事实来源;以及隐藏目录 `.sow/`,
里面存放锁、各仓库的 SQLite 状态,以及用于崩溃恢复的操作日志。`.sow/` 下的内容你永远不需要
手工编辑,也永远不要对外服务。

```bash
cat sow.yml
```

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
```

默认两个架构。`amd64` 与 `arm64` 作为输入别名同样接受,会被规范化为 `x86_64` 与 `aarch64` ——
SOW 在所有输出里统一使用这两个 family 规范名。

`init` 是幂等的。对已初始化的工作区重跑,它只校验现状并补齐缺失部分,不会重置代际、不会重写字节。

## 2. 创建仓库

```bash
sow repo new pigsty
```

```console
created pigsty: path=/srv/sow/pigsty protected=false dists=0 generation=0 status=clean packages=0 memberships=0
```

仓库(Repository)就是工作区根目录下的一个子目录,它拥有内部的一切:自己的包池、自己发布的
Dist、自己的 SQLite 数据库和自己的锁。同一工作区内的两个仓库之间**不做**对象去重 ——
这是刻意的隔离,让你删掉其中一个时不必审计另一个。

## 3. 创建 Dist

**Dist** 是一个单一格式的具名软件包集合。名字要取用户能在 URL 里认出来的,格式必须在创建时声明:

```bash
sow dist new el9 --format rpm -r pigsty
sow dist new trixie --format deb -r pigsty
```

```console
created el9: format=rpm architectures=x86_64,aarch64 members=0/0 generation=1 dirty=false
created trixie: format=deb architectures=x86_64,aarch64 members=0/0 generation=2 dirty=false
```

两个 Dist 都继承了工作区的架构列表,`sow.yml` 也随之更新:

```yaml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

空 Dist 已经是合法仓库。SOW 为两者都写出了完整、可直接消费的索引树:

```console
pigsty/
├── pool/
└── dists/
    ├── el9/
    │   ├── x86_64/repodata/{repomd.xml, primary, filelists, other}
    │   └── aarch64/repodata/{repomd.xml, primary, filelists, other}
    └── trixie/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
            └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

客户端指向一个空 Dist 拿到的是合法的空包列表,而不是 404。注意命名差异:RPM 视图用 family
规范名 `x86_64` / `aarch64`,DEB 视图用 Debian 生态名 `binary-amd64` / `binary-arm64`,
因为 `apt` 就是按后者去取文件的。

## 4. 添加软件包

`sow add` 接受文件路径,用 `-d` 指明这些包该加入哪个 Dist:

```bash
sow add pkg/*.rpm -r pigsty -d el9
```

```console
add repository=pigsty operation=6987540345754799180 accepted=4 failed=0 memberships=+4/-0 revision=3 generation=3 dirty=false
item input="pkg/blackbox_exporter-0.28.0-1.aarch64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.aarch64" sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943 dists=el9:accepted
item input="pkg/blackbox_exporter-0.28.0-1.x86_64.rpm" status=accepted format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18 dists=el9:accepted
item input="pkg/pev2-1.23.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.23.0-1.noarch" sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229 dists=el9:accepted
item input="pkg/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm" status=accepted format=rpm coordinate="pgbouncer-0:1.25.2-43PGDG.rhel9.8.x86_64" sha256:057b821ad82ca49a693aa97ba50c1fc96925b0a58de626f014e07a0c78700e1a dists=el9:accepted
```

然后是 DEB 侧:

```bash
sow add pkg/*.deb -r pigsty -d trixie
```

```console
add repository=pigsty operation=7610015278010066624 accepted=3 failed=0 memberships=+3/-0 revision=4 generation=4 dirty=false
item input="pkg/libpq5_18.3-1.pgdg12+1_amd64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:amd64" sha256:4b5262231787caf1f367f5c8705a8a03d3176c31a15e6096946d50514db128be dists=trixie:accepted
item input="pkg/libpq5_18.3-1.pgdg12+1_arm64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:arm64" sha256:cadeb9294901ac5ae6228bd3471c444cc288d9894af0dd0730909596d9dfcefb dists=trixie:accepted
item input="pkg/pev2_1.23.0_all.deb" status=accepted format=deb coordinate="pev2=1.23.0:all" sha256:11e05aa5bf0e049097ab885ab61e41d8c72094a8e912cab613d9bb1719bb6bf9 dists=trixie:accepted
```

逐条 item 行值得细看。每行报告 SOW 从包**自身**解析出的逻辑坐标(coordinate)——
RPM 是 NEVRA,DEB 是 `name=version:arch` —— 以及该字节的 SHA-256。坐标来自 RPM 头与
Debian control 文件,绝不来自文件名,所以一个被改名的包仍然按它实际的身份建索引。

汇总行的 `dirty=false` 表示公开树在命令返回前已经重建完毕。`add` 默认自动构建;
如果你想攒几批变更、最后统一跑一次 `sow build`,加 `--skip` 即可。

重复添加同一个包会报 `status=reused`,generation 不变。若某个包对象已存在、只是要加入另一个 Dist,
则复用同一份字节,只新增一条成员记录。

## 5. 查看包池

每个被接受的包在仓库的 `pool/` 下只存一份:

```console
pigsty/pool/
├── b/blackbox_exporter/
│   ├── blackbox_exporter-0.28.0-1.aarch64.rpm
│   └── blackbox_exporter-0.28.0-1.x86_64.rpm
└── p/
    ├── pev2/
    │   ├── pev2-1.23.0-1.noarch.rpm
    │   └── pev2_1.23.0_all.deb
    ├── pgbouncer/
    │   └── pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
    └── postgresql-18/
        ├── libpq5_18.3-1.pgdg12+1_amd64.deb
        └── libpq5_18.3-1.pgdg12+1_arm64.deb
```

分组规则沿用 Debian 惯例:首字母 + 源码包名。`libpq5` 落在 `p/postgresql-18/` 下,是因为它
control 文件里的 `Source` 字段就是 `postgresql-18` —— 和 `reprepro` 放的位置完全一致。
RPM 则按包名分组。

包池内容不可变。把一个包从 Dist 移除,移除的是它的**成员关系**;字节仍留在池里,
所以之后重新加回来几乎不花代价。

## 6. 查看发布树

```console
pigsty/dists/
├── el9/
│   ├── x86_64/
│   │   ├── pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
│   │   ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm
│   │   ├── pool/p/pgbouncer/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
│   │   └── repodata/{repomd.xml, …}
│   └── aarch64/
│       ├── pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
│       ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm
│       └── repodata/{repomd.xml, …}
└── trixie/
    ├── Release
    └── main/
        ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
        └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

每个 RPM 架构视图包含本架构的包**加上** `noarch` 包 —— `pev2` 在两个视图里都出现。
视图里的这些文件是指向根包池的硬链接,不是副本,所以那个 `noarch` 包的链接数是 3
(根包池 + 两个视图),磁盘上只占一份空间:

```bash
stat -c '%h %n' pigsty/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

```console
3 pigsty/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

这就是 `pool/` 与 `dists/` 必须同文件系统的原因。它同时带来一个好处:`repodata` 里的包位置是
`pool/p/pev2/…` 这样的普通相对路径,不含逃出视图根的 `..`,而这正是 `dnf reposync`
能正确镜像该仓库的前提。

DEB 侧不需要视图目录:`Packages` 里的 `Filename:` 字段直接指向仓库包池。

```console
Filename: pool/p/postgresql-18/libpq5_18.3-1.pgdg12+1_amd64.deb
```

`Release` 为每个索引文件列出 SHA-256,并声明 `Acquire-By-Hash: yes`,于是 `apt` 会从
`by-hash/SHA256/` 目录取索引,不会撞上"下载途中索引被换掉"的经典问题:

```console
Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:06:41 UTC
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 b7a9ab7d083b89342a9895963814be117d6a387f73f7305b0d6dc47d7718eb07 1483 main/binary-amd64/Packages
 668058912c3cb51fed9074063de1a0233514c8340a2fe90136ad3f4670a06db4 828 main/binary-amd64/Packages.gz
 7b2a1c5dd08eaeb02540d6b7eeef454311179a86347a0e3900114b28a6b9dcde 1483 main/binary-arm64/Packages
 25191436907e80a72594e642408b5cea3e68bc1b979df5b7cd556d9e36296402 827 main/binary-arm64/Packages.gz
```

## 7. 检查状态

`sow status` 是廉价读取面:不做全仓哈希、不触发恢复、不构建。

```bash
sow status
```

```console
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

`ready_to_copy=true` 就是你 `rsync` 之前要确认的信号:公开树完整且自洽,此刻复制走能得到
一个可用的仓库。

`sow check` 是昂贵读取面 —— 完整的八层证明,逐层核对配置、数据库 schema、包体字节、
成员关系、索引、签名与代际清单:

```bash
sow check
```

```console
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=72
package-bytes	ok=true	checked=7
desired-membership	ok=true	checked=7
index	ok=true	checked=2
signature	ok=true	checked=11
generation-manifest	ok=true	checked=4
```

这个仓库上这一趟耗时 0.15 秒。`check` 只验证,从不修复。如果它发现仓库 dirty 或损坏,
会明确报告并以非零码退出 —— 见[退出码](/zh/docs/reference/exit-codes/)。

另外两个速览视图:

```bash
sow repo ls
sow dist ls
```

```console
NAME	PROTECTED	DISTS	GENERATION	STATUS	PACKAGES	MEMBERSHIPS
pigsty	false	2	4	clean	7	7

NAME	FORMAT	ARCHITECTURES	DESIRED	BUILT	GENERATION	DIRTY	DIRTY_REASONS
el9	rpm	x86_64,aarch64	4	4	3	false	[]
trixie	deb	x86_64,aarch64	3	3	4	false	[]
```

以及某个 Dist 的软件包清单:

```bash
sow ls -d el9
```

```console
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943	rpm:blackbox_exporter-0:0.28.0-1.aarch64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm
sha256:5759c643a789631346e3ed315a696a0118f81f7cc3c65e5a4385a876983d3a18	rpm:blackbox_exporter-0:0.28.0-1.x86_64	el9	el9	pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.x86_64.rpm
sha256:d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229	rpm:pev2-0:1.23.0-1.noarch	el9	el9	pool/p/pev2/pev2-1.23.0-1.noarch.rpm
sha256:057b821ad82ca49a693aa97ba50c1fc96925b0a58de626f014e07a0c78700e1a	rpm:pgbouncer-0:1.25.2-43PGDG.rhel9.8.x86_64	el9	el9	pool/p/pgbouncer/pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

## 如何选中操作对象

多数命令需要知道你指的是哪个工作区、哪个仓库、哪个 Dist。规则很短:

- **工作区** —— 从当前目录逐级向上查找。指定 `-C DIR` 则改为从 `DIR` 向上找,找不到就失败,
  不会退回当前目录。
- **仓库** —— `-r NAME`;或当前目录所属的仓库;或工作区里只有一个仓库时即为它。
- **Dist** —— `-d NAME`,可重复。只有在选择无歧义时才可省略。

推断不出来时,SOW 拒绝执行而不是猜:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

## 对外服务

把 Web 服务器指向仓库目录(这里是 `/srv/sow/pigsty`),URL 就由布局直接推导出来:

- `dnf` 的 `baseurl` 写 `http://host/pigsty/dists/el9/x86_64/`
- `apt` 的源写 `deb http://host/pigsty trixie main`

不要把工作区根目录暴露出去:`sow.yml` 与 `.sow/` 是私有状态。
完整的 Nginx 配置见[对外服务](/zh/docs/tutorial/serving/)。

## 下一步

- [核心概念](/zh/docs/start/concepts/) —— 期望成员集与已构建代、代际递增,以及 Dist 何时变 dirty。
- [搭建 YUM 仓库](/zh/docs/tutorial/yum-repo/) 与 [搭建 APT 仓库](/zh/docs/tutorial/apt-repo/) —— 含客户端配置的生产级实战。
- [仓库签名](/zh/docs/tutorial/signing/) —— 元数据与包体的 GPG 签名。
- [成员策略](/zh/docs/feature/policy/) —— 只保留最新 N 个版本、按模式排除。
- [`sow.yml` 配置参考](/zh/docs/reference/config/) —— 全部配置字段。
