---
title: "快速上手"
linkTitle: "快速上手"
description: "把一个装包的目录变成可服务的仓库,再用 dnf 或 apt 从中安装。"
url: "/zh/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
---

这一页大约五分钟。你会把若干软件包放进一个目录,执行一条命令,用 HTTP 暴露出去,
然后用 `dnf` 或 `apt` 从中安装。不需要配置文件、不需要工作区、不需要数据库 ——
Plain 平面模式只是在软件包旁边写出索引,除此之外什么都不做。

## 1. 准备软件包

任何装着 `.rpm` 或 `.deb` 的目录都可以。文件原地不动,SOW 不会移动或重命名它们。

```bash
mkdir -p /srv/repo
cp ~/downloads/*.rpm /srv/repo/
ls /srv/repo
```

```console
blackbox_exporter-0.28.0-1.aarch64.rpm
blackbox_exporter-0.28.0-1.x86_64.rpm
pev2-1.23.0-1.noarch.rpm
pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

## 2. 生成索引

```bash
sow create /srv/repo
```

```console
created /srv/repo: rpm=4 deb=0 signed=0 removed=0 marker=false noop=false recovered=false
```

建仓就这一步。4 个包耗时 0.35 秒;87 个 RPM(2.9 GB)约 11 秒,时间主要花在算哈希上。

SOW 读取了每个 RPM 的头、为每个包体计算 SHA-256,并在软件包旁边写出 `repodata/` 目录:

```console
/srv/repo
├── blackbox_exporter-0.28.0-1.aarch64.rpm
├── blackbox_exporter-0.28.0-1.x86_64.rpm
├── pev2-1.23.0-1.noarch.rpm
├── pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
└── repodata
    ├── 2eda195ef4ce04cc2df3548bb056e3588b6c872c5333305ae108b26bcacdb558-other.xml.gz
    ├── 78b24c2413c1f60dd7871bf7c05834d0c363d2b4742b13da115565f23e0d41bd-filelists.xml.gz
    ├── 996f7947874e8c1ced323dcaae26e4ec20d4f7844701a8ef1cce0dc93631b6f7-primary.xml.gz
    └── repomd.xml
```

这与 `createrepo_c` 产出的 `primary` / `filelists` / `other` 布局一致:校验和命名的数据文件,
加上所有 YUM 客户端最先读取的入口 `repomd.xml`。

## 3. 对外服务

任何静态 Web 服务器都行。快速验证用 Python 自带的服务器就够了:

```bash
cd /srv/repo
python3 -m http.server 8080
```

确认入口可达:

```bash
curl -s http://localhost:8080/repodata/repomd.xml | head -3
```

```console
<?xml version="1.0" encoding="UTF-8"?>
<repomd xmlns="http://linux.duke.edu/metadata/repo" xmlns:rpm="http://linux.duke.edu/metadata/rpm">
  <revision>0</revision>
```

长期服务请改用 Nginx 托管该目录,配置示例见[对外服务](/zh/docs/tutorial/serving/)。

## 4. 从中安装

把客户端指向该目录的 URL。这里的包没有签名,所以先关闭签名校验;
如何开启见[仓库签名](/zh/docs/tutorial/signing/)。

{{< tabpane persist="header" >}}
{{< tab header="dnf / yum" lang="bash" >}}
sudo tee /etc/yum.repos.d/quickstart.repo <<'EOF'
[quickstart]
name=SOW Quick Start
baseurl=http://10.0.0.1:8080/
enabled=1
gpgcheck=0
EOF

sudo dnf makecache
sudo dnf install pgbouncer
{{< /tab >}}
{{< tab header="apt" lang="bash" >}}
echo 'deb [trusted=yes] http://10.0.0.1:8080/ ./' | \
  sudo tee /etc/apt/sources.list.d/quickstart.list

sudo apt update
sudo apt install pev2
{{< /tab >}}
{{< /tabpane >}}

APT 那行结尾的 `./` 就是告诉 `apt` 这是一个平面仓库 —— 包与索引在同一目录,没有 `dists/` 层级。
`[trusted=yes]` 是必须的,因为此时还没有 `Release` 签名。

`file://` URL 同样可用,适合从挂载的磁盘离线安装:`dnf` 用 `baseurl=file:///srv/repo`,
`apt` 用 `deb [trusted=yes] file:///srv/repo ./`。

## 5. 追加软件包

把新文件复制进去,再执行同一条命令:

```bash
cp ~/downloads/more/*.rpm /srv/repo/
sow create /srv/repo
```

SOW 重新扫描目录并重写索引。两次运行之间不保留任何记忆 —— **目录内容本身就是状态**。

对未发生变化的目录重复执行是空操作,输出会明说:

```console
created /srv/repo: rpm=4 deb=0 signed=0 removed=0 marker=false noop=true recovered=false
```

输出是确定性的:相同的输入包,产出字节级一致的索引。`repomd.xml` 里写的是
`<revision>0</revision>` 和零时间戳,正是为了让重建不会平白改变校验和、逼所有客户端重新拉取元数据。

## 6. 一个目录,两种格式

RPM 与 DEB 可以放在一起。一条 `sow create` 同时为两者建索引,并分列计数:

```bash
ls /srv/mixed
```

```console
libpq5_18.3-1.pgdg12+1_amd64.deb
pev2_1.23.0_all.deb
pev2-1.23.0-1.noarch.rpm
pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

```bash
sow create /srv/mixed
```

```console
created /srv/mixed: rpm=2 deb=2 signed=0 removed=0 marker=false noop=false recovered=false
```

你会在同一个目录里同时得到 RPM 侧的 `repodata/` 与 DEB 侧的 `Packages`、`Packages.gz`。
任何一侧解析失败,整条命令都在发布之前中止 —— 两侧要么一起提交,要么都不提交。

## 需要机器可读的输出?

任何命令加上 `--json` 都会输出带版本的信封:

```bash
sow create /srv/repo --json
```

```json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,"result":{"dir":"/srv/repo","rpm":4,"deb":0,"kept":["blackbox_exporter-0.28.0-1.aarch64.rpm","blackbox_exporter-0.28.0-1.x86_64.rpm","pev2-1.23.0-1.noarch.rpm","pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm"],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

所有命令的信封结构一致,字段说明见 [JSON 输出](/zh/docs/reference/json/)。

## 下一步

当目录里已经**恰好**是你想发布的内容时 —— 构建产物、从上游镜像拉下来的目录、离线包集 ——
Plain 平面模式
就是合适的工具。而当你需要决定**哪些**包该进仓库、在一棵树里维护多个发行版、按架构拆分,
或者需要签名与变更审计时,就该换到 Managed 托管工作区了。

- [第一个工作区](/zh/docs/start/workspace/) —— 完整走通 Managed 路径。
- [核心概念](/zh/docs/start/concepts/) —— 两种模式的差别与选型。
- [Plain 平面仓库](/zh/docs/feature/plain/) —— `sow create` 提供的保证。
- [`sow create` 参考](/zh/docs/reference/cli/create/) —— 全部参数与退出码。
