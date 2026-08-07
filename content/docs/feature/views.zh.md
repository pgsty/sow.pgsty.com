---
title: "包池与架构视图"
linkTitle: "包池与架构视图"
description: "一份字节、一个属主、多个视图:硬链接投影如何让 YUM 元数据 href 对 reposync 安全、noarch 为何进入每个视图、以及包池为什么必须同文件系统。"
url: "/zh/docs/feature/views/"
weight: 400
icon: fa-solid fa-link
---

列一遍 Managed 仓库,你会在三个不同路径上看到同一个包文件,而 `du` 坚称它只占一份空间。这不是错觉,也不是符号链接。本页讲清楚这套投影模型 —— 它为什么存在、保证了什么,以及它对你的文件系统提出的那一条约束。

## 不变式

**root pool 拥有字节。`dists/` 下的一切都是投影,可以删掉重建,而不会碰到任何被拥有的对象。**

```text
<repo>/pool/<首字母>/<source>/<file>      canonical 对象 —— 属主
<repo>/dists/<dist>/<arch>/pool/...       硬链接别名 —— 同一 inode 的视图
<repo>/dists/<dist>/<arch>/repodata/...   引用该别名的元数据
```

删除一个 Dist 只 unlink 它的别名,不做别的。Dist 维护绝不会顺带删除 pool 字节 —— 本版本刻意不提供垃圾回收。

## 一个构建完成的仓库长什么样

一个 Repository,含一个 RPM Dist(`el9`)和一个 DEB Dist(`trixie`),装着三个 RPM(一个 `noarch`、一个 `x86_64`、一个 `aarch64`)与两个 DEB:

```text
pigsty/
├── pool/
│   ├── p/pev2/pev2-1.23.0-1.noarch.rpm
│   └── x/xray/
│       ├── xray-26.2.6-1.aarch64.rpm
│       ├── xray-26.2.6-1.x86_64.rpm
│       ├── xray_26.2.6-1_amd64.deb
│       └── xray_26.2.6-1_arm64.deb
└── dists/
    ├── el9/
    │   ├── x86_64/
    │   │   ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm      # 别名
    │   │   ├── pool/x/xray/xray-26.2.6-1.x86_64.rpm      # 别名
    │   │   └── repodata/{<sha256>-*.xml.gz, repomd.xml}
    │   └── aarch64/
    │       ├── pool/p/pev2/pev2-1.23.0-1.noarch.rpm      # 别名
    │       ├── pool/x/xray/xray-26.2.6-1.aarch64.rpm     # 别名
    │       └── repodata/{<sha256>-*.xml.gz, repomd.xml}
    └── trixie/
        ├── Release
        └── main/
            ├── binary-amd64/{Packages, Packages.gz, by-hash/SHA256/…}
            └── binary-arm64/{Packages, Packages.gz, by-hash/SHA256/…}
```

Pool 路径遵循 Debian 惯例:`pool/<首字母>/<source>/<filename>`,首字母取 source 名的第一个字符 —— `lib*` 取前四个字符 —— 并统一转小写。`source` 与 `filename` 保持原始大小写。RPM 的 source 取自 `SOURCERPM`,DEB 取自 `Source` 字段;字段缺失时回落到二进制包名并记录 warning。这就是为什么 `libpq5` 落在 `pool/p/postgresql-18/`,和 `reprepro` 放的位置一模一样。

两个 Repository 永不共享 pool,相同字节在两个仓库里存两份。去重只发生在 Repository 内部,绝不跨越所有权边界。

## 视图是硬链接,而且可以验证

```console
$ stat -f '%i %N' pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
                  dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm \
                  dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
206233285 dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm
```

一个 inode,三个名字。链接计数印证了这一点:

```console
$ stat -f '%l %N' pool/p/pev2/pev2-1.23.0-1.noarch.rpm
3 pool/p/pev2/pev2-1.23.0-1.noarch.rpm

$ stat -f '%l %N' pool/x/xray/xray-26.2.6-1.x86_64.rpm
2 pool/x/xray/xray-26.2.6-1.x86_64.rpm
```

`noarch` 包有 3 个链接 —— root pool 加上两个架构视图。`x86_64` 包有 2 个 —— root pool 加上它所属的那一个视图。它们是普通硬链接,不是符号链接:没有悬空链接这种失败模式,没有需要解析的路径穿越,Web 服务器不跟随任何东西就能直接服务。

## 中性包是投影出来的,不是复制出来的

`noarch`(RPM)与 `all`(DEB)不是第三种 CPU 架构族。它们是**中性(neutral)**的,而中性是投影的属性,不是成员关系的属性:

- 一个包对象,以 SHA-256 为身份。
- 一条 Dist 成员记录 —— `(dist, content_sha256)`,唯一。
- 构建时渲染进该 Dist 的**每一个**适用架构视图。

于是 `x86_64` 视图包含 `x86_64` 加 `noarch` 包,`aarch64` 视图包含 `aarch64` 加 `noarch`,而 `sow ls` 里仍然只有一行。数据库只存逻辑架构族;状态里没有任何复制,只有渲染树里有。

中性包不会扩散到你没选的 Dist。`sow add foo.noarch.rpm -d el9` 只会放进 `el9`,即使 `el9-beta` 也接受它。

`limit` 策略把中性当作它自己的原生架构,只计一次 —— 见[成员策略](/zh/docs/feature/policy/)。

## 元数据 href 为什么是 `pool/...` 而不是 `../../../pool/...`

先看 RPM 元数据实际写了什么:

```console
$ gzip -dc dists/el9/x86_64/repodata/*-primary.xml.gz | grep -o '<location href="[^"]*"'
<location href="pool/p/pev2/pev2-1.23.0-1.noarch.rpm"
<location href="pool/x/xray/xray-26.2.6-1.x86_64.rpm"
```

相对于视图目录,任何位置都没有 `..` 分量。走到这一步,是因为先否决了那个看起来更明显的方案。

第一版候选设计根本不建别名,而是按实际深度计算相对路径,把 `location href` 直接指向共享的 root pool:`../../../pool/...`。表面上它是能用的。在 pinned AlmaLinux 9.8 容器里,针对这样构建的仓库,`makecache`、`repoquery`、`download`、`install` 全部成功。

`dnf reposync` 拒绝了。它规范化后的本地目标逃出了 per-repository 的下载根目录,于是它拒绝往自己目录之外写。就 `reposync` 而言这是正确行为;就我们而言这是布局门禁失败:镜像一个仓库是一等公民用例,所以破坏它的设计不叫"基本兼容",而叫被否决。

替代方案就是你上面看到的样子。root pool 保持 canonical 对象所有权,每个架构视图只为自己的原生 + 中性成员建同文件系统硬链接,元数据使用永远不可能逃出视图目录的 `pool/...` href。最终验收复跑中,这套方案在 `makecache`、带 location 检查的 `repoquery`、`download`、`install` 和 `reposync` 上全部通过 —— 覆盖了"原生 + `noarch`"的 `x86_64` 视图、只含 `noarch` 的 `aarch64` 视图,以及一份不保留硬链接身份的完整复制。

对运维者的结论是:Managed 的 YUM 视图目录是自包含的。把客户端、镜像作业或 `reposync` 指向 `dists/<dist>/<arch>/`,它需要的一切都不在该目录之上。

## APT 不需要视图别名

DEB 侧用另一种方式解决同一个问题,因为 APT 本来就有一个相对 archive root 的字段:

```text
Package: xray
Architecture: amd64
Filename: pool/x/xray/xray_26.2.6-1_amd64.deb
```

`Filename` 相对 archive root 解析 —— 即同时包含 `dists/` 与 `pool/` 的那个 Repository 目录 —— 所以 APT 直接够得到共享 pool。这就是为什么 `dists/trixie/` 下根本没有 `pool/` 子树,也是为什么 DEB component 固定为 `main` 且不生成每架构的 `Release` 存根:apt 不需要它们,`reprepro` 生成它们只是历史原因。

DEB 的 `Release` 携带 by-hash 声明:

```text
Origin: SOW
Suite: trixie
Codename: trixie
X-SOW-Generation: 4
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
SHA256:
 59b22f5cc246d9a8137327b9eddee4a628df92bab4d6d4597ae024564d4d6e90 372 main/binary-amd64/Packages
 f2093eacfbb5efac8a3f54853e74c122bde97a5005f93940c81dfc5073bcf30f 303 main/binary-amd64/Packages.gz
 …
```

有了 `Acquire-By-Hash: yes`,apt 从 `main/binary-amd64/by-hash/SHA256/<hash>` 拉取索引,而不是从可变的 `Packages` 路径拉 —— 验收期间的 HTTP 访问日志证实它确实这么做。这正是构建进行中客户端仍能安全 update 的原因:已经读到 `Release` 的客户端,继续拉取 `Release` 承诺的那份精确索引字节,哪怕 `Packages` 此刻已被替换。`reprepro` 完全不支持 by-hash;这里只发布 `SHA256`,不发 `MD5Sum` 与 `SHA1`。

RPM 侧靠 checksum 命名的元数据获得同样的性质:`repomd.xml` 指向 `<sha256>-primary.xml.gz`,上一代的文件在磁盘上再保留一代。见[可观测与审计](/zh/docs/feature/audit/)。

## 同文件系统是硬约束

硬链接不能跨设备。因此 SOW 在初始化时就校验 staging 区与目标的 `st_dev` 相同,并且会**明确失败**而不是降级:

- 如果 `pool/` 与 `dists/` 落在不同挂载点上,操作失败。没有静默的复制回退。
- 如果文件系统根本不支持硬链接,操作失败。

这是刻意的拒绝。静默回退到复制会在你不知情的情况下让每个仓库的磁盘占用翻倍;更糟的是,它会破坏原子性保证 —— 复制不是 rename,无法做成原子操作。一个你当场就能看到并修掉的失败,好过三个月后才发现的容量倒退。

落到实处只有一句话:不要把 `pool/` 或 `dists/` bind-mount、软链或以其他方式挪出仓库目录。布局固定,正是为了这个。

## 复制整个仓库

别名是真实的物理路径,changeset 也是这么对待它们的。`sow changes 0` 把 pool 对象和每个视图别名都列成独立的 `payload` 条目:

```console
$ sow changes 0
base=0 generation=4 dirty=false
add	payload	dists/el9/aarch64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
add	payload	dists/el9/x86_64/pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
add	payload	pool/p/pev2/pev2-1.23.0-1.noarch.rpm	316372	d06d7f23…
…
```

数据库只存逻辑架构族;物理路径由固定布局推导出来 —— 正因如此它们可以被重算和校验,而不是被信任。

把仓库复制到别处时,有两种结果,而且两种都能用:

- **保留硬链接**(`rsync -aH`、同文件系统上的 `cp -al`、文件系统级快照):目标端每个对象仍是一个 inode,磁盘占用与源端一致。
- **不保留硬链接**(普通 `rsync -a`、`scp -r`、多数对象存储同步工具):每个别名变成独立的普通文件。容量去重丢失,但所有客户端 —— 包括 `reposync` —— 行为完全不变。这一情形是显式验证过的。

如果仓库很大且以 `noarch` 为主,选传输方式之前值得先量一下这个差异。参见[对外服务](/zh/docs/tutorial/serving/)。

## 继续阅读

- [成员策略](/zh/docs/feature/policy/) —— 决定哪些包根本能被投影
- [事务与恢复](/zh/docs/feature/transactions/) —— 投影如何被安全提交
- [仓库布局](/zh/docs/reference/layout/) —— 完整路径参考
- [兼容性](/zh/docs/reference/compatibility/) —— 实测客户端矩阵
