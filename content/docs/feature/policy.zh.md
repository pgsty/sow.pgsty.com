---
title: "成员策略"
linkTitle: "成员策略"
description: "exclude 与 limit 如何决定哪些包留在 Dist 里:规则字段、glob 匹配、版本排序,以及放宽策略为什么永远不会复活已移出的成员。"
url: "/zh/docs/feature/policy/"
weight: 500
icon: fa-solid fa-filter
---

策略回答的是这个问题:"我把整个构建目录倒进了这个 Dist,但我不想要 debuginfo 包,而且每个包只留最新版本。"两条规则完成这件事,它们按固定顺序执行,并且作用于**完整候选集**,而不是你这次恰好 add 的那几个包。

## 两条规则与它们的顺序

```text
候选集  →  exclude  →  limit  →  期望成员集(Desired Membership)
```

`exclude` 丢掉命中规则的包,`limit` 再按包名与架构限制存活的版本数。顺序固定且不可配置 —— 反过来的话,一个即将被排除的包会在离场路上白白占掉一个版本名额。

两条规则在每次 `add`、每次 `rm` 和每次 `build` 时都强制执行。最后这条很关键:在 `sow.yml` 里改 `limit` 或 `exclude` 会让受影响的 Dist 变 dirty,下一次 `build` 就把新策略重新施加到现有成员集上。想让收紧后的策略生效,你不需要重新 add 任何东西。

```yaml
dists:
  el9:
    format: rpm
    limit: 1
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

## `exclude`

`exclude` 是一个规则列表。同一条规则内,各字段之间是 **AND**;同一字段内,多个 pattern 之间是 **OR**;规则与规则之间是 **OR** —— 任一规则命中即排除。字段顺序和规则顺序都不影响结果。

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

这段读作:不分架构地丢掉所有 debug 类包,**并且**丢掉名字以 `test-` 开头或以 `-experimental` 结尾的 `aarch64` 包。

允许五个字段:

| 字段 | 匹配对象 |
|---|---|
| `name` | 二进制包名 |
| `source` | 规范化后的 source 名 |
| `arch` | `x86_64`、`aarch64` 或 `neutral` |
| `kind` | 下表固定枚举 |
| `format` | `rpm` 或 `deb` |

pattern 是区分大小写的精确字符串或 shell glob(`*`、`?`、`[]`)。没有正则,没有版本比较,没有取反,也没有表达式语言。未知字段、空规则和非法 glob 会在 `config check` 时失败,而不是静默地什么都匹配不到。

`kind` 由二进制包名推导,优先取最具体的后缀:

| 格式 | 名称后缀 | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| 任意 | 以上均不匹配 | `main` |

分类结果只来自包本身,不依赖文件所在目录,也不依赖当前主机,所以同一份输入永远分到同一类。`sow show --json` 会输出算出来的 `kind`。

被排除的包会被如实报告,不算解析失败,也不会被存下来:

```console
$ sow add pkg/blackbox_exporter-0.28.0-1.x86_64.rpm pkg/pev2-1.23.0-1.noarch.rpm -r demo -d el9
add repository=demo operation=7877233225745514469 accepted=1 failed=0 memberships=+1/-0 revision=3 generation=3 dirty=false
item input="pkg/blackbox_exporter-0.28.0-1.x86_64.rpm" status=excluded format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643… dists=el9:excluded
item input="pkg/pev2-1.23.0-1.noarch.rpm" status=accepted format=rpm coordinate="pev2-0:1.23.0-1.noarch" sha256:d06d7f23… dists=el9:accepted
```

命令退出码是 `0`。被排除的包本身没有任何问题,它只是不属于这个 Dist。如果一个包没有被任何 Dist 接受,就不会为它写下无主的 pool 对象。

## `limit`

`limit` 按 `(二进制包名, 原生架构)` 分组,保留最新的 N 个:

- `0` —— 保留全部版本,这是默认值。
- 正整数 `N` —— 按原生版本序保留最新的 N 个。
- 负数 —— 配置错误。

有两个细节能回答现实中的绝大多数疑问。

**分组键包含架构。** `limit: 1` 不是"这个 Dist 里这个包只留一个版本",而是"每个包名 + 每个原生架构留一个版本"。所以 `pg_sample-1.13`(`x86_64`)与 `pg_sample-1.17`(`noarch`)可以同时存在于 `limit: 1` 的 Dist 里,因为它们属于不同分组。中性包(`noarch`/`all`)作为自己的原生架构只计一次,尽管它会渲染进多个视图。

**排序用格式的原生规则。** RPM 用 EVR 比较 —— epoch、version、release,遵循标准 rpm 分段规则。DEB 用 Debian version 比较,版本串本身已经包含 epoch 与 revision。SOW 不发明版本方案,也不做字典序比较。

下面是 `limit: 1` 在同名同架构的两个 Debian 版本之间做决定:

```console
$ sow add pkg/libpq5_18.4-1.bookworm_amd64.deb pkg/libpq5_18.4-1.trixie_amd64.deb -r demo -d trixielim
add repository=demo operation=2402398619981505515 accepted=1 failed=0 memberships=+1/-0 revision=4 generation=4 dirty=false
item input="pkg/libpq5_18.4-1.bookworm_amd64.deb" status=excluded format=deb coordinate="libpq5=3:18.4-1.bookworm:amd64" sha256:be8a2863… dists=trixielim:limited
item input="pkg/libpq5_18.4-1.trixie_amd64.deb" status=accepted format=deb coordinate="libpq5=3:18.4-1.trixie:amd64" sha256:0a7df397… dists=trixielim:accepted
```

注意这里有两级报告:条目的整体 `status` 是 `excluded`(它最终没在任何地方成为成员),而逐 Dist 的结果是 `limited` —— 告诉你它是输在版本上,不是被某条 `exclude` 规则命中。当你同时选中多个 Dist 时,每个 Dist 各报各的结果,所以一条命令里同一个包完全可能在一个 Dist 是 `accepted`、在另一个是 `limited`。

`limit` 移除旧成员、加入新成员发生在同一个 Operation 内,所以账本上看到的是一次原子决策,而不是一次删除加一次不相干的插入。

## 策略作用于完整候选集

一个常见误读是:`add` 只对命令行上的包施加策略。并非如此。把你的输入合并进目标成员集之后,SOW 会对每个选中 Dist 的**完整**成员集执行 `exclude`,再执行 `limit`。

现实后果是:往一个已经装着版本 1 和版本 2 的 `limit: 2` Dist 里加版本 3,会在同一个操作里移除版本 1。你没法靠"分开单独 add"绕过版本上限,也不会因为"只拿增量与上限比"而落得 N+1 个成员。

## 放宽策略永远不会复活任何东西

这条语义最常被误以为是反过来的,所以值得直接演示。接着上面 `limit: 1` 的例子,把胜出的那个版本删掉:

```console
$ sow rm 'deb:libpq5=3:18.4-1.trixie:amd64' -r demo -d trixielim
$ sow ls -d trixielim
repository=demo dists=trixielim dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
```

Dist 空了。bookworm 那个构建没有回来 —— 尽管它的字节还躺在 pool 里,尽管 `limit: 1` 此刻明明空出了一个名额。

原因在于 `exclude` 与 `limit` 移除的是**真实的期望成员**。SOW 不维护一份"被策略压下、将来也许还能回来的候选"影子清单。Pool 字节是存储,不是候选集。因此提高 limit 或放宽 exclude 只是给未来的添加腾出空间;它不会回头翻历史,猜哪些你曾经拥有过的包该重新出现。

想让它回来,就再显式 add 一次:

```console
$ sow add pkg/libpq5_18.4-1.bookworm_amd64.deb -r demo -d trixielim
add repository=demo operation=590501245267266669 accepted=1 failed=0 memberships=+1/-0 revision=6 generation=6 dirty=false
item input="pkg/libpq5_18.4-1.bookworm_amd64.deb" status=accepted format=deb coordinate="libpq5=3:18.4-1.bookworm:amd64" sha256:be8a2863… dists=trixielim:accepted
```

收敛是单向的,而且这是写进不变式的:**收紧策略可以移除成员,放宽策略永远不会恢复成员。** 正是这种不对称让 `build` 在任何时刻都能安全执行。假如它是对称的,那么编辑 `sow.yml` 就可能静默地重新发布一个你刻意下架的包 —— 而这恰恰是安全更新场景里最不能出的事故。

{{% alert title="真正下架一个包" color="warning" %}}
`sow rm` 移除的是成员关系,不是 pool 字节。包会从所有索引中消失,客户端不再能通过仓库
解析它。只有当包体不再被当前、保留、恢复、发布以及活动维护操作等任何安全根引用时，
才运行 `sow gc`。
已发布目标使用 `sow gc TARGET`;filesystem 删除是条件式的,R2 只生成报告。
不要绕过 SOW 状态手工删除规范包池文件。
{{% /alert %}}

## 预览一次决策

`sow rm -c` 计算将要移除的成员、策略后果,以及此刻 build 会产生的文件变化,但什么都不写:

```bash
sow rm patroni -r pgsql -d el9 -c
```

`-c/--check` 不取写锁,并且与 `--skip` 互斥。同时给出 `--timeout` 或 `--no-wait` 属于用法错误 —— 免得有人误以为一次预览会去等待写事务。

## 继续阅读

- [`sow.yml` 配置参考](/zh/docs/reference/config/) —— 完整策略 schema
- [`sow add` 参考](/zh/docs/reference/cli/add/) —— 逐条目状态与部分成功退出码
- [包池与架构视图](/zh/docs/feature/views/) —— 存活下来的成员被渲染到哪里
- [CLI:发布、保留、GC 与导出](/zh/docs/reference/cli/publication/) —— 包体生命周期控制
