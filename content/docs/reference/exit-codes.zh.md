---
title: "退出码"
linkTitle: "退出码"
description: "七个退出码分别代表什么,以及每个码一条可复现的触发命令。"
url: "/zh/docs/reference/exit-codes/"
weight: 500
icon: fa-solid fa-triangle-exclamation
---

每条 `sow` 命令都以七个退出码之一结束。它们是稳定的、对所有命令一致,
并且就是设计来给脚本做分支判断的 —— 区分"这件事失败了"和"这件事被正确地拒绝了",
正是设置多个非零码的全部意义。

| 码 | 含义 |
|---|---|
| `0` | 完整成功,或幂等 no-op |
| `1` | 运行时 I/O、解析器、渲染器或未知内部错误 |
| `2` | 用法、工作区发现或配置错误 |
| `3` | 部分成功:至少一项已提交,至少一项失败 |
| `4` | 写锁不可用 —— 被占用且指定了 `--no-wait`,或等待超时 |
| `5` | 完整性/恢复错误,或 `check` 判定当前结果不可交付 |
| `6` | 预期拒绝:冲突、protected、无匹配、架构不兼容 |

人类可读的结果写 stdout,警告与诊断写 stderr。每个码在 stderr 上有稳定的消息前缀,
在 [JSON 输出](/zh/docs/reference/json/)中有对应的 `class`:

| 码 | stderr 前缀 | JSON `class` |
|---|---|---|
| `1` | 随子系统而异 | `runtime` |
| `2` | `usage error:` / `workspace discovery error:` / `configuration error:` | `usage` |
| `3` | `... batch partially succeeded` | `partial` |
| `4` | `lock unavailable:` | `lock` |
| `5` | `integrity or recovery error:` | `integrity` |
| `6` | `operation rejected:` | `rejected` |

`sow create` 是前缀那一列的例外:它不在 Managed 层内,stderr 上打印的是原始领域错误
(`plain: scan …`、`plain: marker gate …`),没有 `operation rejected:` 前缀。该前缀仍然出现在
它的 JSON `errors[].message` 里。

---

## 0 —— 成功或无操作

命令完成了你要求的事,或者发现无事可做。两者都算成功:对未变化的目录重跑
`sow create`,或对 clean 仓库执行 `sow build`,都返回 `0` 并如实说明。

```bash
sow create /srv/offline --json
```

```console
{"schema":"sow.cli/v1","command":"create","ok":true,...,"result":{"dir":"/srv/offline","rpm":4,"deb":3,"kept":[...],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

`"noop":true` 才是区分"没干活"与"干了活"的依据,退出码不区分这两者。

`sow status` 是有意为之的特例:只要状态数据库可读,它在 `clean`、`dirty`、
`recovering`、`error` 四种状态下都返回 `0` —— 让脚本去读结构化状态,
而不是从退出码反推。需要"闸门"时请用 `sow check`。

## 1 —— 运行时错误

I/O、解析或渲染层面出了问题:目录不可写、磁盘满、包读不出来。
这类是**环境问题**,不是用法问题。

```bash
chmod 500 /srv/readonly
sow create /srv/readonly
```

```console
plain: create stage /srv/readonly: mkdir /srv/readonly/.sow-plain-stage-1457115008: permission denied
```

stage 目录之所以一开始就创建,正是为了让这类失败发生在**任何东西被发布之前**。
本来就有合法索引的仓库,索引依然完好。

## 2 —— 用法、发现或配置错误

你要求的事情 CLI 无法执行:未知参数、目标不明确、找不到工作区,或 `sow.yml` 解析不通过。
**什么都没有尝试执行**。

未知参数:

```bash
sow status --nope
```

```console
usage error: unknown option "--nope"
```

互斥参数:

```bash
sow build -N -T 5s
```

```console
usage error: --no-wait and non-zero --timeout are mutually exclusive
```

目标不明确 —— 仓库有两个 Dist,而命令需要确定其一:

```bash
sow ls
```

```console
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

当前目录向上找不到任何工作区 —— 错误会说明搜索位置与修复方式:

```console
workspace discovery error: managed: workspace discovery or configuration error: workspace not found (searched cwd="/home/vonng"); run sow init or set --workdir/SOW_DIR
```

起始目录本身不是真实目录(比如符号链接,macOS 上的 `/tmp` 就是)时,搜索根本不会开始:

```console
workspace discovery error: managed: workspace discovery or configuration error: discover workspace from cwd "/tmp": start is not a directory
```

配置文件格式有问题 —— 注意错误会指出具体行号:

```bash
sow config check
```

```console
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 3: field repositories not found in type config.Config
```

[`sow.yml`](/zh/docs/reference/config/) 的所有文法与 schema 错误都归到这一码。

## 3 —— 部分成功

一个批次里有的项已提交、有的项失败。这个码存在的意义是:你永远不必猜测一次失败的
`sow add` 是否让仓库毫发无损 —— 返回 `3` 就意味着合法的包**已经进去了**,
失败的那些会被逐条点名。

```bash
sow add ./incoming/ -d el9
```

```console
add repository=pigsty operation=9162553676349401125 accepted=1 failed=1 memberships=+1/-0 revision=6 generation=6 dirty=false
item input="/incoming/broken-1.0-1.x86_64.rpm" status=failed error="invalid RPM package: parse RPM reader: unexpected EOF"
item input="/incoming/pgbouncer_fdw_18-1.4.0-1PGDG.rhel9.8.x86_64.rpm" status=reused format=rpm coordinate="pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64" sha256:45171966... dists=el9:accepted
managed: batch partially succeeded
```

失败的输入文件原地不动。加上 `--json` 时,已提交的项仍然完整列出 ——
非零退出**从不**截断 result:

```console
{..., "ok":false, "result":{"accepted":1,"failed":1,"items":[...]}, "errors":[{"code":3,"class":"partial","message":"managed: batch partially succeeded"}]}
```

`sow init` 在已提交了部分声明的仓库或 Dist、随后在后面某项上失败时,也用这个码。

## 4 —— 锁不可用

另一个进程持有写锁。SOW 在设计上就是单写者(single-writer),
所以这是**正常且预期**的结果 —— 重试,或者多等一会儿。

带 `--no-wait` 时立即失败:

```bash
sow build -N
```

```console
lock unavailable: managed: lock unavailable
```

带超时时,恰好等待这么久后失败:

```bash
time sow build -T 2s
```

```console
lock unavailable: managed: lock unavailable

real	0m2.016s
```

`-T 0`(默认)一直等待。只读命令不取写锁,永远不会返回 `4`;
`sow status` 甚至把这种争用作为一个字段报告出来:

```console
repository=pigsty status=clean ready_to_copy=false revision=7 generation=7 dirty_dists= pending=0/0 locked=true
```

## 5 —— 完整性、恢复,或不可交付

两种不同的情况共用这个码,它们的含义都是"先别把这棵树发出去"。

常见的那种:仓库的期望状态领先于已构建的内容 —— `sow add --skip` 之后,
或者改了策略/签名之后,对它执行 `sow check`。每一层校验都通过,
仓库只是**尚未收敛**:

```bash
sow rm 'rpm:pev2-0:1.23.0-1.noarch' -d el9 --skip
sow check
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=7 generation=6
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=69
package-bytes	ok=true	checked=7
desired-membership	ok=true	checked=6
index	ok=true	checked=2
signature	ok=true	checked=11
generation-manifest	ok=true	checked=6
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
```

解决办法是 `sow build`。这正是部署脚本应该拿来做闸门的码 ——
它区分的是"磁盘上的树完整且最新"与"磁盘上的树完整但过期"。

少见的那种是真正的完整性失败:状态数据库、journal 与文件树互相矛盾,
且 SOW 无法安全地自行裁决。此时它拒绝覆盖任何东西,你应该从备份恢复,而不是强行修复。
这里**有意**没有 `--force`。

## 6 —— 预期拒绝

命令写法正确、环境也没问题,是 SOW 主动判定"不行"。
这些是策略与安全决策,不是故障。

受保护的仓库:

```bash
sow repo rm pigsty -f
```

```console
operation rejected: managed: operation rejected: repository "pigsty" is protected
```

匹配不到任何东西的引用:

```bash
sow rm nosuchpkg -d el9
```

```console
operation rejected: managed: operation rejected: package reference not found: package reference "nosuchpkg" matches no Desired Membership
```

有歧义的裸名 —— 候选会一并列出,方便你挑一个:

```bash
sow show libpq5 -d trixie
```

```console
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1.pgdg12+1:amd64 sha256:310611d0..., deb:libpq5=18.3-1.pgdg12+1:amd64 sha256:4b526223..., deb:libpq5=18.3-1.pgdg12+1:arm64 sha256:cadeb929...
```

工作区不允许的架构。注意逐项错误会点名检测到的值,并告诉你去哪里改:

```bash
sow add ./centos-release-6-0.el6.centos.5.i686.rpm -d el9 --json
```

```console
"items":[{"input":".../centos-release-6-0.el6.centos.5.i686.rpm","status":"failed",
 "error":"managed: operation rejected: unknown rpm package architecture \"i686\"; supported rpm package architectures are [x86_64, aarch64, noarch] (canonical families [x86_64, aarch64, neutral]); use a supported package or update only supported architecture families in sow.yml"}]
```

目录里没有任何可索引的包:

```bash
sow create /srv/empty
```

```console
plain: scan /srv/empty: no supported top-level regular RPM or DEB packages
```

`--pigsty` 完成标记挡住了对既有构建的覆盖:

```bash
sow create /www/pigsty
```

```console
plain: marker gate /www/pigsty/repo_complete: repo_complete exists; use --pigsty or remove it explicitly before rebuilding
```

签名 key 引用文法正确但解析不出密钥 —— 文法错误是 `2`,解析失败是 `6`:

```console
operation rejected: ... deb metadata key: key reference does not resolve to a bounded regular file
operation rejected: ... deb metadata key: environment key reference SOW_METADATA_KEY is unset
```

## 在脚本里使用

这些码的设计目标就是让部署流水线**不必解析文本**即可分支:

```bash
#!/usr/bin/env bash
set -uo pipefail

sow add /incoming/*.rpm -r pigsty -d el9
case $? in
  0) ;;                                        # 全部落地
  3) echo "部分包被拒绝,继续处理已落地的部分" >&2 ;;
  4) echo "另一个写者持有锁,稍后重试" >&2; exit 75 ;;
  *) echo "add 失败" >&2; exit 1 ;;
esac

# 用完整且最新的树作为复制闸门
if ! sow check -r pigsty; then
  echo "仓库尚不可复制" >&2
  exit 1
fi

rsync -a --delete /srv/repo/pigsty/ mirror:/var/www/pigsty/
```

两个值得养成的习惯:把 `4` 当作**可重试**而不是致命错误;
永远不要把 `6` 当作崩溃 —— 它通常意味着需要改的是你的输入,而不是 SOW。

## 延伸阅读

- [JSON 输出](/zh/docs/reference/json/) —— `errors` 数组与它的 `class` 字段
- [`sow check`](/zh/docs/reference/cli/build/) —— 退出码 `5` 背后的有序分层校验
- [事务与恢复](/zh/docs/feature/transactions/) —— `recovering` 与 `error` 状态的含义
