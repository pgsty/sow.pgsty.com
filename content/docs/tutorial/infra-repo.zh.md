---
title: "演练构建 pigsty-infra 仓库"
linkTitle: "构建 pigsty-infra"
description: "把既有的双架构 RPM 与 DEB 包池组织成 infra 仓库，完成本地安装验收、滚动更新、Stable 晋升与月度快照。"
url: "/zh/docs/tutorial/infra-repo/"
weight: 500
icon: fa-solid fa-hammer
---

[`pgsty/infra-pkg`](https://github.com/pgsty/infra-pkg) 是 Pigsty Infra 软件包的上游构建源码。
本教程假设双架构 RPM 与 DEB 已经构建完成，只处理后半程：从一堆包开始，用 SOW 建成真正可消费、可维护的 `infra` 仓库。

## 1. 把包集中到 ~/repo

本教程固定使用 `~/repo`，不再为每条路径定义环境变量。先把已有包复制进两个输入目录：

```bash
mkdir -p ~/repo/packages/rpm ~/repo/packages/deb
cp ~/pgsty/infra-pkg/dist/rpm/*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/*.deb ~/repo/packages/deb/
```

先确认四个“格式 × 架构”象限都有真实包体：

```bash
find ~/repo/packages/rpm -maxdepth 1 -type f -name '*.x86_64.rpm' | wc -l
find ~/repo/packages/rpm -maxdepth 1 -type f -name '*.aarch64.rpm' | wc -l
find ~/repo/packages/deb -maxdepth 1 -type f -name '*_amd64.deb' | wc -l
find ~/repo/packages/deb -maxdepth 1 -type f -name '*_arm64.deb' | wc -l
```

四个结果都必须大于零。此时目录只有输入包池：

```text
~/repo/
└── packages/
    ├── rpm/                         # x86_64 + aarch64 RPM
    └── deb/                         # amd64 + arm64 DEB
```

## 2. 创建 infra Repository 与两个 Dist

初始化 Workspace，并创建名为 `infra` 的 Repository：

```bash
sow init ~/repo
cd ~/repo
sow repo new infra
sow dist new rpm --format rpm -r infra
sow dist new deb --format deb -r infra
```

现在模型已经确定：

```text
Repository: infra
├── Dist: rpm    format=rpm    policy=latest
└── Dist: deb    format=deb    policy=latest
```

打开 `~/repo/sow.yml`，把配置整理为：

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  infra:
    dists:
      rpm:
        format: rpm
        limit: 1
      deb:
        format: deb
        limit: 1
```

`limit: 1` 按“包名 + 原生架构”只保留最新一个版本。因此 `rpm` 与 `deb` 就是两个滚动更新的
latest channel；它们仍会同时保留 x86-64 与 ARM64 两个架构。

```bash
sow config check
sow config show --all -r infra
```

## 3. 一次性导入并构建

先更新 Desired Membership，最后只构建一次：

```bash
cd ~/repo
sow add ~/repo/packages/rpm --recursive -r infra -d rpm --skip
sow add ~/repo/packages/deb --recursive -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

`sow check` 返回 `0`，才算初始化完成。再核对 SOW 从包头读出的真实格式与架构：

```bash
sow ls -r infra -d rpm -d deb --json |
  jq -r '.result.packages | group_by(.format + "/" + .canonical_arch)[] |
    "\(.[0].format)\t\(.[0].canonical_arch)\t\(length) packages"'
```

预期至少出现：

```text
deb     aarch64   ... packages
deb     x86_64    ... packages
rpm     aarch64   ... packages
rpm     x86_64    ... packages
```

SOW 使用规范化架构名，因此 DEB 的 `amd64/arm64` 在这里显示为 `x86_64/aarch64`。

## 4. 看懂生成的目录

打印实际目录：

```bash
find ~/repo -maxdepth 6 -type d | LC_ALL=C sort
```

关键结构应当是：

```text
~/repo/
├── sow.yml                            # 配置，不对外服务
├── .sow/                              # 数据库、锁、恢复状态，不对外服务
├── packages/                          # 原始输入包池，可自行归档
│   ├── rpm/
│   └── deb/
└── infra/                             # 完整的公开 Repository Root
    ├── pool/                          # RPM 与 DEB 共享的单副本包池
    └── dists/
        ├── rpm/
        │   ├── x86_64/repodata/
        │   └── aarch64/repodata/
        └── deb/
            ├── Release
            └── main/
                ├── binary-amd64/
                └── binary-arm64/
```

这里有一个容易混淆、但必须记住的路径规则：SOW 的 Dist 固定放在 `dists/` 下。因此逻辑上的
`infra/rpm` 与 `infra/deb`，真实视图路径分别是 `/infra/dists/rpm/` 和 `/infra/dists/deb/`；
包体则统一放在 `/infra/pool/`。发布或挂载时必须使用完整的 `~/repo/infra`，不能只拿走某个 Dist。

## 5. 用 Nginx 只读服务仓库

使用官方 `nginx:alpine` 镜像，把 Repository Root 只读挂载到 `/infra`：

```bash
docker network create --internal infra-lab
docker run --detach \
  --name infra-nginx \
  --network infra-lab \
  --publish 8080:80 \
  --volume "$HOME/repo/infra:/usr/share/nginx/html/infra:ro" \
  nginx:alpine
```

直接检查两种索引入口：

```bash
curl -fsS http://127.0.0.1:8080/infra/dists/rpm/x86_64/repodata/repomd.xml | head
curl -fsS http://127.0.0.1:8080/infra/dists/deb/Release | head
```

Nginx 只看得到 `~/repo/infra`，既看不到 `sow.yml` 与 `.sow/`，也无法修改仓库。

## 6. 在 EL9 中只用 infra 安装 RPM

下面的 Rocky Linux 9 容器位于 `--internal` 网络中。脚本先删除所有预置仓库，再只启用刚创建的
`infra`，因此成功安装不能依赖公网软件源。

```bash
docker run --rm --interactive --network infra-lab rockylinux:9 bash -s <<'ROCKY'
set -euxo pipefail

rm -f /etc/yum.repos.d/*.repo
cat >/etc/yum.repos.d/infra.repo <<'REPO'
[infra]
name=Pigsty Infra RPM
baseurl=http://infra-nginx/infra/dists/rpm/$basearch/
enabled=1
gpgcheck=0
repo_gpgcheck=0
REPO

dnf clean all
dnf --disablerepo='*' --enablerepo=infra makecache
dnf --disablerepo='*' --enablerepo=infra install -y pg-exporter
rpm -q --qf '%{NAME}\t%{VERSION}-%{RELEASE}\t%{ARCH}\n' pg-exporter
command -v pg_exporter
ROCKY
```

RPM 的 `baseurl` 必须落到具体架构视图。`$basearch` 会由 dnf 展开为 `x86_64` 或 `aarch64`。

## 7. 在 Ubuntu 24.04 中只用 infra 安装 DEB

APT 的 URI 指向 Repository Root，`Suites` 才是 Dist 名 `deb`：

```bash
docker run --rm --interactive --network infra-lab ubuntu:24.04 bash -s <<'UBUNTU'
set -euxo pipefail

rm -f /etc/apt/sources.list
rm -f /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources
cat >/etc/apt/sources.list.d/infra.sources <<'SOURCE'
Types: deb
URIs: http://infra-nginx/infra
Suites: deb
Components: main
Trusted: yes
SOURCE

apt-get clean
apt-get update
apt-get install -y --no-install-recommends pg-exporter
dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n' pg-exporter
command -v pg_exporter
UBUNTU
```

本教程使用隔离 HTTP 仓库，所以临时关闭了验签。正式服务应配置 RPM/APT 元数据签名，并移除
`gpgcheck=0` 与 `Trusted: yes`。

Docker 默认验证宿主机架构。若要完成四格运行矩阵，分别给两条 `docker run` 增加
`--platform linux/amd64` 与 `--platform linux/arm64` 后各跑一次；跨架构运行需要 Docker 的
binfmt/QEMU 支持。仓库清单检查与客户端安装检查是两个独立门禁。

## 8. 日常维护：添加一个新版本

更新仓库的正常动作是 `add`，不是先删除旧包。假设已经拿到新版 `pg-exporter` 的四个包体：

```bash
cp ~/pgsty/infra-pkg/dist/rpm/pg-exporter-*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/pg-exporter_*.deb ~/repo/packages/deb/

cd ~/repo
sow add ~/repo/packages/rpm/pg-exporter-*.rpm -r infra -d rpm --skip
sow add ~/repo/packages/deb/pg-exporter_*.deb -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

因为 latest Dist 配了 `limit: 1`，新版本胜出后，旧版本会自动退出该 Dist 的 Desired Membership。
旧字节不会被立即删除，也不会因为以后放宽策略而自动回来。

可以重新运行第 6、7 节的客户端，先 `makecache/update`，再安装或升级，完成更新验收。

{{% alert title="删除只用于硬订正" color="warning" %}}
正常发布不要先 `sow rm`。如果某个错误包必须紧急撤回，先用 `sow ls -r infra -d rpm --json`
或对应的 `-d deb` 找到精确 SHA-256，
再依次执行 `sow rm sha256:... -r infra -d rpm --check` 与不带 `--check` 的同一命令。
`rm` 只删除 Dist Membership，pool 字节仍由保守的 `sow gc` 独立回收；不要用裸包名误删所有版本与架构。
{{% /alert %}}

## 9. 两层保留策略：latest 与 stable

`rpm`、`deb` 的 `limit: 1` 适合持续滚动，但不能表达“保留所有正式发布历史”。为此再创建两个 Dist：

```bash
cd ~/repo
sow dist new rpm-stable --format rpm -r infra
sow dist new deb-stable --format deb -r infra
sow config show --all -r infra -d rpm-stable -d deb-stable
```

新 Dist 的默认 `limit` 是 `0`，表示保留所有版本。最终策略是：

| Dist | 格式 | `limit` | 角色 |
|---|---|---:|---|
| `rpm` | RPM | 1 | RPM latest |
| `deb` | DEB | 1 | DEB latest |
| `rpm-stable` | RPM | 0 | 累积所有已晋升 RPM |
| `deb-stable` | DEB | 0 | 累积所有已晋升 DEB |

注意：`stable` 不是把“包池里的所有历史”自动放回来，而是从现在开始，累积每次明确晋升的版本。

## 10. 把 latest 晋升到 stable

SOW 0.3.0 还没有独立的 `promote` 命令。当前可靠做法是先冻结写入并导出源 Dist 的精确 Membership，
再把这些对象加入目标 Dist。输入直接取自 `infra/pool`；SOW 会校验并复用已有 Package Object，
不会重新打包，也不会在 pool 中复制第二份包体。

先确保源状态干净，并保存本次晋升清单：

```bash
cd ~/repo
sow check -r infra
mkdir -p ~/repo/manifests

sow ls -r infra -d rpm --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-latest-202608.list
sow ls -r infra -d deb --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-latest-202608.list
```

在晋升结束前暂停对 `rpm` 与 `deb` 的写入，然后复用这些 pool 对象：

```bash
cd ~/repo
(
  set -e
  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d rpm-stable --skip
  done < ~/repo/manifests/rpm-latest-202608.list

  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d deb-stable --skip
  done < ~/repo/manifests/deb-latest-202608.list

  sow build -r infra -d rpm-stable -d deb-stable
  sow check -r infra
)
```

每次 `add` 应报告 `reused`。若中途失败，源 Dist 不受影响；修复问题后对同一清单重跑即可。
随着以后重复晋升，`rpm/deb` 仍只保留最新版本，而 `rpm-stable/deb-stable` 会逐次累积历史版本。

## 11. 从 stable 创建 2026-08 快照

客户端可见的月度快照也是两个新的 Dist：

```bash
cd ~/repo
sow dist new rpm-202608 --format rpm -r infra
sow dist new deb-202608 --format deb -r infra
sow config show --all -r infra -d rpm-202608 -d deb-202608
```

在快照窗口内暂停 stable 写入，先把其精确 Membership 固化为清单：

```bash
sow check -r infra
sow ls -r infra -d rpm-stable --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-stable-202608.list
sow ls -r infra -d deb-stable --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-stable-202608.list
```

再把清单加入对应快照 Dist：

```bash
cd ~/repo
(
  set -e
  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d rpm-202608 --skip
  done < ~/repo/manifests/rpm-stable-202608.list

  while IFS= read -r pool_path; do
    sow add "$HOME/repo/infra/$pool_path" -r infra -d deb-202608 --skip
  done < ~/repo/manifests/deb-stable-202608.list

  sow build -r infra -d rpm-202608 -d deb-202608
  sow check -r infra
)
```

把这次已验证的完整 Repository Generation 也加入保留集合，防止后续 GC 把它当作不可达历史处理：

```bash
sow retain add "$(sow status -r infra --json | jq -r '.result.built_generation')" -r infra
sow retain ls -r infra
```

`retain` 保留的是整个 Repository Generation，用于恢复与 GC 安全根；客户端可见的固定 URL 仍由
`rpm-202608` 与 `deb-202608` 两个 Dist 提供。SOW 0.3.0 尚不强制快照 Dist 只读，因而创建后不再对它们
执行 `add` 或 `rm` 是维护规约的一部分。

## 12. 客户端地址总表

同一个 Nginx 与同一份 `infra/pool` 支撑所有 channel：

| Channel | dnf `baseurl` | APT `URIs` / `Suites` |
|---|---|---|
| latest | `http://infra-nginx/infra/dists/rpm/$basearch/` | `http://infra-nginx/infra` / `deb` |
| stable | `http://infra-nginx/infra/dists/rpm-stable/$basearch/` | `http://infra-nginx/infra` / `deb-stable` |
| 2026-08 | `http://infra-nginx/infra/dists/rpm-202608/$basearch/` | `http://infra-nginx/infra` / `deb-202608` |

最终验收：

```bash
cd ~/repo
sow dist ls -r infra
sow status -r infra
sow check -r infra
```

到这里，我们得到的不是一次性演示目录，而是一个可以继续收包、晋升与做月度快照的真实 Infra
Repository：`rpm/deb` 负责快速更新，`rpm-stable/deb-stable` 负责积累正式历史，月度 Dist 提供固定入口，
所有视图复用同一份不可变包体。

实验结束后可停止临时服务：

```bash
docker rm --force infra-nginx
docker network rm infra-lab
```
