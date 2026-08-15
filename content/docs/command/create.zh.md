---
title: "sow create"
linkTitle: "create"
description: "在普通目录中就地生成平面 RPM/DEB 仓库 —— Plain 平面模式的唯一入口。"
url: "/zh/docs/command/create/"
aliases: ["/docs/reference/cli/create/"]
weight: 100
icon: fa-solid fa-folder-tree
---

`sow create` 把一个已经放着 `.rpm` / `.deb` 的目录变成平面仓库（flat repository）：在包旁边写出索引
文件。它就是 Plain 平面模式的全部——没有 `sow.yml`、没有 SQLite、不做工作区发现。本页讲清扫描规则、
原子的 `--pigsty` 兼容操作，以及 `--sign-with` 的 RPM 包签名。

## 语法

```text
sow create [DIR] [-j N] [--pigsty] [-S KEY [--overwrite]] [-T DUR | -N] [--json]
```

`DIR` 默认为当前目录。

## 说明

`create` 读取 `DIR` 顶层的普通文件，按发现的内容渲染对应索引：有 RPM 就生成 `repodata/`，有 DEB 就
生成 `Packages` 与 `Packages.gz`，混合目录两套一起生成。架构全部来自包头——Plain 模式没有架构参数，
也没有架构许可表。

平面元数据只引用同目录的包：RPM 的 `location` 是裸 basename，DEB 的 `Filename` 是
`./<basename>`。无论目录作为 `file://` 源还是 HTTP 根暴露，两者都保持相对引用。

默认情况下 `create` 不删除、不移动、不重命名、不重签、不改写任何一个包字节。它只替换自己拥有的索引
路径，未知文件原样保留。

## 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-j, --jobs N` | 解析与哈希的并发 worker 数 | 逻辑 CPU 数 |
| `--pigsty` | 启用原子的 Pigsty 兼容操作 | 关闭 |
| `-S, --sign-with KEY` | 用 16/40/64 位十六进制 GPG key ID 给未签名 RPM 补签 | 关闭 |
| `--overwrite` | 重签全部 RPM；必须与 `--sign-with` 同用 | 关闭 |
| `-T, --timeout DUR` | 等待锁的最长时间；`0` 表示无限等待 | `0` |
| `-N, --no-wait` | 锁被占用时立即失败 | false |
| `--json` | 输出版本化 JSON envelope | false |
| `-h, --help` | 显示帮助 | — |

## 扫描规则

- 只考虑顶层、以 `.rpm` 或 `.deb` 结尾的普通文件。
- 不递归、不跟随符号链接、不读工作区配置。
- 所有有效版本都进入索引。两个文件对应同一逻辑坐标但内容不同时，硬失败。
- 目录里没有受支持的包属于拒绝，不是"生成空仓库"。

```console
sow create /srv/empty
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

## 确定性输出与幂等

对给定输入集，渲染出的元数据是字节稳定的：gzip 输出确定，`repomd.xml` 写 `<revision>0</revision>`
与 timestamp `0`。对未变化的目录重跑 `create` 不写任何字节，报告 `noop=true`：

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false

sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=true recovered=false
```

## repo_complete 门禁

默认模式永不生成 `repo_complete`。如果 marker 已经存在，`create` 宁可拒绝写索引，也不留下一个内容
已过期却仍宣称"完成"的旧 marker：

```console
sow create /srv/pigsty
plain: marker gate /srv/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

要么加 `--pigsty` 重跑（由它在事务内统一管理 marker），要么自己先把 marker 移走。

## --pigsty

`--pigsty` 是一个不可拆分的兼容与清理操作，同时启用三件事：

1. 根据解析后的包事实删除 32 位 x86 包：RPM `i386/i486/i586/i686`，DEB `i386`。
2. 删除二进制包名恰为 `patroni` 且 upstream 版本恰为 `3.0.4` 的 RPM/DEB。RPM 比较 `VERSION`，忽略
   epoch 与 release；DEB 先剥掉 epoch 与 Debian revision 再比。`3.0.4+foo` 不算命中。
3. 全部索引渲染成功后写出 `repo_complete`：剩余顶层 RPM/DEB 的 SHA-256，按 basename 字节序排序，
   格式为 `<sha256><两个空格><basename>`。

```console
sow create /srv/pigsty --pigsty
created /srv/pigsty: rpm=2 deb=0 signed=0 removed=2 marker=true noop=false recovered=false
```

```console
cat /srv/pigsty/repo_complete
b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead  centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab  epel-release-7-5.noarch.rpm
```

清理只触碰解析成功且命中规则的顶层普通包文件，绝不按宽泛 glob 删目录或未知文件。

提交顺序对以 marker 为门禁的调用方很关键：先撤下已有的 `repo_complete`，再切换索引，把待删包原子
rename 到同文件系统的 recovery trash，最后才写入新 marker。因此轮询 `repo_complete` 的调用方永远
看不到中间状态，客户端也不会看到索引指向已删除的包。

{{% alert title="Marker 语义" color="info" %}}
把 `repo_complete` 缺失当作"构建进行中"。这正是 `--pigsty` 设计围绕的契约。
{{% /alert %}}

## RPM 包签名

`-S/--sign-with KEY` 是修改 RPM 字节的显式授权。`KEY` 必须是恰好 16、40 或 64 位十六进制 GPG key ID/fingerprint，不接受 `0x` 前缀。SOW 将其规范化为大写，通过 `_gpg_name` macro 传给环境中的
`rpm --addsign`。私钥、passphrase、GPG home、pinentry 以及额外 RPM macro 都由你的运行环境提供——
SOW 不接收、不持久化、不回显任何秘密。

- 默认只给没有可解析嵌入 OpenPGP 签名的 RPM 补签；已有签名的包保持原字节。
- `--overwrite` 必须与 `--sign-with` 同用，改为对全部保留 RPM 执行 `rpm --resign`。
- 签名发生在同文件系统的私有 stage 副本上。每个结果都会重新解析以确认嵌入签名存在、
  signature-neutral digest 与 NEVRA 未变，并以最终完整字节生成 rpm-md。
- 目录至少要有一个顶层 RPM，且 `PATH` 中要有 `rpm`。

```console
sow create /srv/flat -S 0123456789ABCDEF --overwrite
plain: sign rpm epel-release-7-5.noarch.rpm: rpm executable is required for --sign-with
```

```console
sow create /srv/deb-only -S 0123456789ABCDEF
plain: sign rpm: --sign-with requires at least one top-level RPM package
```

```console
sow create /srv/flat --overwrite
usage error: --overwrite requires --sign-with
```

```console
sow create /srv/flat -S ZZZZ
usage error: --sign-with must be a 16, 40, or 64 hexadecimal GPG key ID/fingerprint
```

## 锁、staging 与恢复

`create` 对目标目录取写锁，服从 `--timeout`/`--no-wait`。元数据先写到同文件系统的 stage、验证通过
后才切换；失败时旧索引继续可用。

当一次运行同时发现 RPM 与 DEB 时，两套 renderer 属于同一个 Plain Operation：必须全部 stage 并验证
完毕，才开始切换。中途崩溃由轻量持久 journal 在下一次调用时前滚完成或回滚，此时报告
`recovered=true`。从中断的签名运行中恢复，必须使用完全相同的 `--sign-with`/`--overwrite` 授权——
参数更弱的调用不会静默重放它。

平面目录没有 generation 指针，包体与 `repomd.xml` 也无法用一次 POSIX rename 同时切换。因此并发读者
不获得跨文件的瞬时原子性；SOW 保证的是 journal 总能恢复到一个完整的终态。

## 示例

给混合目录建索引：

```console
sow create /srv/flat
created /srv/flat: rpm=3 deb=1 signed=0 removed=0 marker=false noop=false recovered=false
```

```console
ls /srv/flat
centos-release-6-0.el6.centos.5.x86_64.rpm
centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
epel-release-7-5.noarch.rpm
libpq5_18.3-1_amd64.deb
Packages
Packages.gz
repodata
```

机器可读结果：

```console
sow create /srv/flat --json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,"result":{"dir":"/srv/flat","rpm":3,"deb":1,"kept":["centos-release-6-0.el6.centos.5.x86_64.rpm","centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm","epel-release-7-5.noarch.rpm","libpq5_18.3-1_amd64.deb"],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

用八个 worker 替换 Pigsty 现有的平面构建：

```bash
sow create /www/pigsty -j 8 --pigsty
```

失败时的 envelope：

```console
sow create /srv/empty --json
{"schema":"sow.cli/v1","command":"create","ok":false,"repository":null,"operation":null,"result":{"dir":"","rpm":0,"deb":0,"kept":null,"removed":null,"marker":false,"noop":false,"recovered":false},"errors":[{"code":6,"class":"rejected","message":"operation rejected: plain: scan /srv/empty: no supported top-level regular RPM or DEB packages"}]}
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 索引写出成功，或输入未变化产生 no-op |
| `1` | 目录不可读或不存在、包解析失败、渲染失败、签名工具失败 |
| `2` | 用法错误——`--overwrite` 未配 `--sign-with`、key 格式非法、`--no-wait` 与非零 `--timeout` 同用 |
| `4` | 目录写锁被占用，且给了 `--no-wait` 或 `--timeout` 到期 |
| `5` | Plain journal 无法恢复到终态 |
| `6` | 未找到受支持的包、撞上 `repo_complete` 门禁、对 DEB-only 目录用 `--sign-with`、坐标冲突 |

## 参见

- [Plain 平面仓库](/zh/docs/feature/plain/) —— `create` 背后的设计
- [快速上手](/zh/docs/start/quickstart/) —— 五分钟平面仓库演练
- [仓库布局](/zh/docs/reference/layout/) —— 平面目录树长什么样
- [仓库签名](/zh/docs/tutorial/signing/) —— 生成与使用签名钥
