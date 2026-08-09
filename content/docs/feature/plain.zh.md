---
title: "Plain 平面仓库"
linkTitle: "Plain 平面仓库"
description: "sow create 如何把一个装满包的目录变成平面仓库:扫描、staging、原子替换、确定性输出,以及 Pigsty 兼容操作。"
url: "/zh/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

`sow create` 接手一个已经装着 `.rpm` 和 `.deb` 的目录,就地给它写一份索引。它的全部工作就是这个。本页讲清楚它读什么、写什么、承诺绝不碰什么,以及执行到一半被杀掉时怎么活下来。

## 三条不变式

每次 `sow create` 都成立的三条规则,其余行为都是它们的推论:

1. **SOW 只替换自己拥有的索引路径。** 你的包、你的 `README`、别的工具留下的残留文件 —— 一律不动。唯一例外是 `--pigsty`,那是你显式要求删除特定包。
2. **相同输入,相同字节。** 时间戳与压缩参数固定、排序稳定,所以对未变化的目录重跑会产生字节级一致的索引,并报告 `noop=true`。
3. **每个格式指针的提交是全有或全无。** 元数据先在同文件系统的 staging 区完整生成并校验,之后才用原子 rename 换入。切换前出任何错,旧索引继续对外服务。

Plain 模式没有工作区、没有配置文件、没有数据库。即使父目录里存在 `sow.yml` 它也不读,更不做工作区发现。

## 它扫描什么

```bash
sow create /srv/repo
```

- 只看目录**顶层**的普通文件。永不递归 —— `create` 根本没有 `-R`。
- 只认 `.rpm` 与 `.deb` 后缀。不跟随符号链接。
- 包事实取自 RPM 包头或 DEB 的 `control` 成员,绝不取自文件名。一个二进制 RPM 即使被改名成 `*.src.rpm`,仍按真实架构入索引;包头写着 `src` 或 `nosrc` 的则被拒绝。
- 架构从包里读出来。Plain 模式没有架构参数,也没有许可表 —— 目录里是什么架构,索引里就是什么。
- 所有合法版本都进索引。若两个文件声称同一逻辑坐标但内容不同,这是硬失败,不会静默任选其一。

## 它写什么

```console
$ sow create
created /srv/repo: rpm=2 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

目录里有 RPM 就生成 `repodata/`:

```text
/srv/repo/
├── pev2-1.23.0-1.noarch.rpm       # 你的,原封不动
├── xray-26.2.6-1.x86_64.rpm       # 你的,原封不动
├── xray_26.2.6-1_amd64.deb        # 你的,原封不动
├── Packages                       # SOW 所有
├── Packages.gz                    # SOW 所有
└── repodata/                      # SOW 所有
    ├── <sha256>-primary.xml.gz
    ├── <sha256>-filelists.xml.gz
    ├── <sha256>-other.xml.gz
    └── repomd.xml
```

平面元数据只引用同目录里的包，因此无论把目录暴露为 `file://` 源还是 HTTP 文档根，
包路径都保持相对引用：

```xml
<location href="pev2-1.23.0-1.noarch.rpm"/>
```

```text
Filename: ./xray_26.2.6-1_amd64.deb
```

DEB 侧输出 `Packages` 以及一个解压后与明文完全一致的 `Packages.gz`。只写 `SHA256`,不写 `MD5sum` 与 `SHA1`;包里没声明的字段(比如 `Section`)直接省略,而不是输出空值。

公开文件不继承你的 umask。`repodata/` 固定 `0755`;`repomd.xml`、checksum 命名的元数据、`Packages`、`Packages.gz` 与 marker 固定 `0644`。用严格 umask 的用户建出来的仓库,Web 服务器照样读得到。

## 确定性输出

`repomd.xml` 里 `<revision>0</revision>`,每个条目 `<timestamp>0</timestamp>`:

```xml
<revision>0</revision>
<data type="primary">
  <checksum type="sha256">c834c5e79f...</checksum>
  <open-checksum type="sha256">a80cb3cf91...</open-checksum>
  <location href="repodata/c834c5e79f...-primary.xml.gz"/>
  <timestamp>0</timestamp>
```

这是刻意的。写入墙上时钟会让每次重建都产出不同字节:内容寻址缓存失效、可复现构建无法比对、更没法区分"真的变了"和"什么都没变"。把时间抽掉之后,对同一目录的第二次运行就是货真价实的空操作:

```console
$ sow create --json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,
 "result":{"dir":"/srv/repo","rpm":2,"deb":1,
 "kept":["pev2-1.23.0-1.noarch.rpm","xray-26.2.6-1.x86_64.rpm","xray_26.2.6-1_amd64.deb"],
 "removed":[],"marker":false,"noop":false,"recovered":false},"errors":[]}
```

再跑一次,唯一变化的字段是 `"noop":true`,磁盘上的文件逐字节相同。

## 混合目录是一次操作

同时装着两种格式的目录,由一条命令、一个事务处理:

```console
$ sow create
created /srv/repo: rpm=2 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

两个渲染器都先 stage 并校验,任何一个才允许提交。如果 DEB 侧解析失败,RPM 索引也不会换入,命令非零退出。你不会得到 `repodata/` 是新的、`Packages` 是旧的这种混合结果。

有一处需要如实说明而不是嘴上安慰:POSIX 无法让两个文件在同一瞬间 rename。并发读者若恰好在切换窗口里同时取 `repomd.xml` 和 `Packages`,可能看到一新一旧。任何时刻每个协议视图内部都是自洽的,但默认模式不承诺跨协议的瞬时同步。如果你需要一个门禁,请用 `--pigsty`,并把 `repo_complete` 当作就绪信号。

## `--pigsty` 操作

`--pigsty` 是给 [Pigsty](https://pigsty.io) 离线构建用的单一、不可拆分的兼容开关。它捆绑了三件只有放在一起才有意义的事:

1. **删除 32 位 x86 包。** RPM 的 `i386`/`i486`/`i586`/`i686`,DEB 的 `i386` —— 依据解析出来的包事实判定,不按文件名 glob。
2. **删除 Patroni 3.0.4。** 二进制包名恰好是 `patroni`、upstream 版本恰好是 `3.0.4`。RPM 比较 `VERSION` 并忽略 epoch 与 release;DEB 先剥掉 epoch 与 Debian revision 再比。`3.0.4+foo` 不算命中。
3. **写出 `repo_complete`。** 全部索引成功之后,把剩余顶层包写成 `<sha256><两个空格><basename>`,按 basename 稳定排序。

真正让这件事安全的是顺序,而顺序是固定的:

```text
扫描 / 解析 / 哈希
  → stage 并校验两种格式(以及可选的 RPM 签名)
  → 持久化 journal
  → 撤下旧 marker
  → 从 staged 字节替换已签名的 RPM 包体
  → 安装 RPM 不可变元数据
  → 原子替换 repomd.xml
  → 原子替换 Packages 与 Packages.gz
  → 把每个待清理包 rename 进 recovery trash
  → 原子写入新 marker
  → fsync
  → 删除 trash 与 journal
```

顺着读一遍,两条性质自然浮出水面:新索引在任何包被移走**之前**就已发布,所以它永远不会引用一个已经被删掉的文件;旧 marker 在索引变化**之前**就已撤下,所以以 `repo_complete` 为门禁的消费方永远不会看到一个"活得比自己的包清单还久"的 marker。

默认模式(不带 `--pigsty`)下,目标目录里已存在 `repo_complete` 是硬错误,在写任何东西之前就失败。SOW 不会留下一个为刚被替换的内容宣称"已完成"的 marker —— 要么显式选择原子操作,要么你自己把 marker 挪走。

## 就地签名 RPM

```bash
sow create /srv/repo --sign-with 6D5C5A26C36B1F73 --overwrite
```

`-S/--sign-with KEY` 是修改包体的显式授权。`KEY` 必须是恰好 16、40 或 64 位十六进制 GPG key ID/fingerprint；不接受 `0x` 前缀。SOW 规范化为大写,并作为 `_gpg_name` macro 传给环境中的 `rpm --addsign`。私钥、passphrase、GPG home 和 pinentry 全部由运行环境提供;SOW 不接收、不持久化、不回显任何秘密。

- 不带 `--overwrite` 时,只给没有可解析嵌入式 OpenPGP 签名的 RPM 补签,已签名的保持原字节。
- `--overwrite` 必须与 `--sign-with` 同时出现,改用 `rpm --resign` 对全部保留的 RPM 强制重签。
- 签名只发生在同文件系统的私有 staged 副本上。每个结果都会被重新解析,确认嵌入签名存在、signature-neutral digest 与 NEVRA 未变,并以最终完整字节的 SHA-256 生成元数据。
- 完全相同的重复输入只签一次,复用同一份最终字节。
- 只有全部签名与元数据都验证通过,才持久化 journal;journal 把包体替换排在元数据指针切换之前,并同时绑定原始与新的 SHA-256。
- 纯 DEB 目录、缺少 `rpm` 可执行文件、key/agent 不可用或签名验证失败,都在任何公开变更之前失败。

参数与退出码见 [`sow create` 参考](/zh/docs/command/create/),操作演练见[仓库签名](/zh/docs/tutorial/signing/)。

## 崩溃恢复

操作期间,Plain 模式在目标目录里维护一份持久 journal:`.sow-plain-operation.json`。它记录解析后的输入(basename、坐标、哈希)、完整有序的文件动作列表,以及每次替换的持久 pre-image —— 旧文件的哈希、完整 mode、UID、GID,和它在同文件系统 recovery trash 里的位置。staging 区、trash、pre-image 和 journal 全部与目标同设备,所以每一步都是 rename,不存在跨设备复制。

两类失败,两种处理方式。

journal 落盘之后的**普通错误**,如果完整新状态已经耐久,就沿同一份计划**前滚**:验证并 fsync 所有公开目标、把 journal 标记为已完成、返回成功。如果新状态无法完成,则按动作逆序用持久 pre-image 恢复完整旧状态,验证后清理,再把错误返回给调用者。如果回滚自身也失败,journal 与全部证据保留,操作闭锁为错误 —— SOW 不会假装旧状态已经恢复。

**进程被杀**不会走上面任何一条路径。下一次对同一目录执行 `sow create` 时,它读取 journal、重新解析输入、把哈希与记录的证据核对,然后幂等地前滚完成。签名操作的恢复必须给出完全相同的 `--sign-with`/`--overwrite` 授权,不会用更弱的参数静默重放。证据矛盾 —— 输入变了、pre-image 缺失、路径逃逸、符号链接换掉了普通文件 —— 一律返回完整性错误 `5`,而不是猜。

这套机制的验收方式是在这些时点注入进程终止:journal 落盘后、旧 marker 撤下后、每类元数据指针切换后、每个包 rename 后、新 marker 换入前后。每次重跑都只会落到完整旧状态或完整新状态;trash 不丢包,完成 marker 不会与包清单不符。

journal 通过 no-follow、绑定文件描述符的句柄读取,上限 64 MiB,因此符号链接无法在检查与打开之间被换进来。

## 锁

`sow create` 对目标目录取写锁,同时也对它稳定的父目录取锁 —— 这样另一个协作写者就无法用 rename 把目录整个换掉、再对替身取得一把独立的锁。锁覆盖一整轮 create 或 recovery。`-T/--timeout` 与 `-N/--no-wait` 的语义与其他命令一致,见[事务与恢复](/zh/docs/feature/transactions/)。

## 继续阅读

- [`sow create` 参考](/zh/docs/command/create/) —— 全部参数、退出码与失败模式
- [快速上手](/zh/docs/start/quickstart/) —— 五分钟建一个
- [Managed 工作区](/zh/docs/feature/managed/) —— 当平面目录不够用的时候
