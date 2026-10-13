---
title: "演练构建 pigsty-infra 仓库"
linkTitle: "构建 pigsty-infra"
description: "把既有的双架构 RPM 与 DEB 包池组织成 infra 仓库，完成本地安装验收、滚动更新、Stable 晋升与月度快照。"
categories: [Tutorial]
tags: [yum, rpm, managed, publish]
url: "/zh/docs/tutorial/infra-repo/"
weight: 500
icon: fa-solid fa-hammer
---

[`pgsty/infra-pkg`](https://github.com/pgsty/infra-pkg) 是 Pigsty Infra 软件包的上游构建源码。
本教程使用已构建的 x86-64 与 ARM64 RPM、DEB，创建包含滚动频道、稳定发布与月度快照的 `infra` 仓库。先安装 SOW、`jq` 与 Docker。安装示例使用 `pg-exporter`；请包含该包，以及客户端镜像中尚未安装的依赖。

## 1. 把包集中到 ~/repo

为本工作区使用新的 `~/repo` 目录。从 `infra-pkg` 源码目录复制软件包到两个输入目录：

```bash
mkdir -p ~/repo/packages/rpm ~/repo/packages/deb
cp ~/pgsty/infra-pkg/dist/rpm/*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/*.deb ~/repo/packages/deb/
```

输入需同时包含 x86-64 与 ARM64 包。第 3 步会按包内元数据检查格式与架构。

<span id="2-创建-infra-repository-与两个-dist"></span>

## 2. 创建 infra 仓库与两个 Dist

初始化工作区，并创建名为 `infra` 的仓库：

```bash
sow init ~/repo
cd ~/repo
sow repo new infra
sow dist new rpm --format rpm -r infra
sow dist new deb --format deb -r infra
```

在 `~/repo/sow.yml` 中给两个 Dist 设置 `limit: 1`：

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
最新版本频道；它们仍会同时保留 x86-64 与 ARM64 两个架构。

```bash
sow config check
```

## 3. 一次性导入并构建

先导入两种格式的软件包，再统一构建索引：

```bash
cd ~/repo
sow add ~/repo/packages/rpm --recursive -r infra -d rpm --skip
sow add ~/repo/packages/deb --recursive -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

`sow check` 成功后，列出 SOW 从包内元数据读出的格式与架构：

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

关键结构应当是：

```text
~/repo/
├── sow.yml                            # 配置，不对外服务
├── .sow/                              # 数据库、锁、恢复状态，不对外服务
├── packages/                          # 原始输入包池，可自行归档
│   ├── rpm/
│   └── deb/
└── infra/                             # 完整的公开仓库根目录
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

SOW 把所有 Dist 放在 `dists/` 下，把软件包放在 `pool/` 下。发布或挂载完整的 `~/repo/infra` 目录树，让每个 Dist 都能访问其软件包。

## 5. 用 Nginx 只读服务仓库

使用官方 `nginx:alpine` 镜像，把仓库根目录只读挂载到 `/infra`：

```bash
docker network create --internal infra-lab
docker run --detach \
  --name infra-nginx \
  --network infra-lab \
  --publish 127.0.0.1:8080:80 \
  --volume "$HOME/repo/infra:/usr/share/nginx/html/infra:ro" \
  nginx:alpine
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

APT 的 URI 指向仓库根目录，`Suites` 才是 Dist 名 `deb`：

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

本例使用未签名仓库。按[仓库签名](/zh/docs/tutorial/signing/)配置后，为 RPM 元数据启用 `repo_gpgcheck=1`，为 APT 配置 `Signed-By`。RPM 包也有签名时，再启用 `gpgcheck=1`。从已签名 APT 源中删除 `Trusted: yes`。

默认情况下，Docker 容器使用宿主机架构。需要测试另一架构时，给对应的 `docker run`
增加 `--platform linux/amd64` 或 `--platform linux/arm64`；跨架构运行需要 binfmt/QEMU 支持。

## 8. 日常维护：添加一个新版本

更新仓库时直接执行 `add`。假设已经拿到新版 `pg-exporter` 的四个软件包：

```bash
cp ~/pgsty/infra-pkg/dist/rpm/pg-exporter-*.rpm ~/repo/packages/rpm/
cp ~/pgsty/infra-pkg/dist/deb/pg-exporter_*.deb ~/repo/packages/deb/

cd ~/repo
sow add ~/repo/packages/rpm/pg-exporter-*.rpm -r infra -d rpm --skip
sow add ~/repo/packages/deb/pg-exporter_*.deb -r infra -d deb --skip
sow build -r infra -d rpm -d deb
sow check -r infra
```

因为 latest Dist 配了 `limit: 1`，新版本胜出后，旧版本会自动退出该 Dist 的成员集合。
旧包文件不会被立即删除，也不会因为以后放宽策略而自动回来。

可以重新运行第 6、7 节的客户端，先 `makecache/update`，再安装或升级，完成更新验收。

撤下错误软件包时，用 `sow ls -r infra -d rpm --json` 找到其 SHA-256。先执行 `sow rm sha256:DIGEST -r infra -d rpm --check` 预览，再去掉 `--check` 执行。DEB 使用 `-d deb`。SHA-256 引用选中一个包对象；裸包名会选中其全部版本与架构。未使用的包池文件由 `sow gc` 单独回收。

## 9. 两层保留策略：latest 与 stable

`rpm`、`deb` 的 `limit: 1` 适合持续滚动，但不能表达“保留所有正式发布历史”。为此再创建两个 Dist：

```bash
cd ~/repo
sow dist new rpm-stable --format rpm -r infra
sow dist new deb-stable --format deb -r infra
sow config show -r infra -d rpm-stable -d deb-stable
```

新 Dist 的默认 `limit` 是 `0`，表示保留所有版本。最终策略是：

| Dist | 格式 | `limit` | 角色 |
|---|---|---:|---|
| `rpm` | RPM | 1 | RPM latest |
| `deb` | DEB | 1 | DEB latest |
| `rpm-stable` | RPM | 0 | 累积所有已晋升 RPM |
| `deb-stable` | DEB | 0 | 累积所有已晋升 DEB |

`stable` 从创建后开始累积每次明确晋升的版本。

## 10. 把 latest 晋升到 stable

把源 Dist 的包池文件加入目标 Dist，即可晋升软件包。SOW 校验并复用已有包对象，不增加第二份文件。导出清单前暂停其他仓库写入任务，晋升完成后再恢复。

先确保源状态干净，并保存本次晋升清单：

```bash
set -euo pipefail
cd ~/repo
sow check -r infra
mkdir -p ~/repo/manifests

sow ls -r infra -d rpm --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/rpm-latest-202608.list
sow ls -r infra -d deb --json |
  jq -r '.result.packages[].pool_path' > ~/repo/manifests/deb-latest-202608.list
```

把清单中的包池对象加入 stable Dist：

```bash
cd ~/repo
(
  set -euo pipefail
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
sow config show -r infra -d rpm-202608 -d deb-202608
```

创建快照期间，暂停其他仓库写入任务。先保存 stable 的包清单：

```bash
set -euo pipefail
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
  set -euo pipefail
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

如需在将来删除快照 Dist 后仍保留这次构建，另外记录当前仓库构建快照：

```bash
sow retain add "$(sow status -r infra --json | jq -r '.result.built_generation')" -r infra
sow retain ls -r infra
```

`retain` 保存本次构建的元数据，并防止相关包文件被垃圾回收。客户端仍通过快照 Dist 访问。
SOW 不会将这些 Dist 设为只读；创建后保留其成员与生效配置，内容才会固定。

## 12. 客户端地址总表

同一个 Nginx 与同一份 `infra/pool` 支撑所有频道：

| 频道 | dnf `baseurl` | APT `URIs` / `Suites` |
|---|---|---|
| latest | `http://infra-nginx/infra/dists/rpm/$basearch/` | `http://infra-nginx/infra` / `deb` |
| stable | `http://infra-nginx/infra/dists/rpm-stable/$basearch/` | `http://infra-nginx/infra` / `deb-stable` |
| 2026-08 | `http://infra-nginx/infra/dists/rpm-202608/$basearch/` | `http://infra-nginx/infra` / `deb-202608` |

用 `sow dist ls -r infra` 查看全部六个 Dist。

滚动 Dist 保留最新软件包，stable Dist 累积已晋升版本，月度 Dist 保留选定快照。所有视图共用同一个包池。

实验结束后可停止临时服务：

```bash
docker rm --force infra-nginx
docker network rm infra-lab
```
