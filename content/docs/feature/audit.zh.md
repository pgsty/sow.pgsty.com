---
title: "可观测与审计"
linkTitle: "可观测与审计"
description: "一条命令回答一个问题:status 看便宜状态、check 做完整证明、changes 给交付计划、log 查操作账本,以及代际保留窗口如何工作。"
url: "/zh/docs/feature/audit/"
weight: 800
icon: fa-solid fa-magnifying-glass-chart
---

四条只读命令回答四个不同的问题,而且每一条都拒绝替另外三条干活。这种分离是刻意的:一个偶尔会把整仓哈希一遍的"便宜状态检查"没法放进循环,一个会偷偷修东西的"完整校验"没法当证据用。

| 命令 | 回答的问题 | 开销 | 是否写入 |
|---|---|---|---|
| `status` | 这个仓库现在处于什么状态? | 便宜,不做哈希 | 从不 |
| `check` | 我能证明这棵树正确且可交付吗? | 完整校验 | 从不 |
| `changes` | 要把镜像更新到位,需要复制哪些文件? | 读 generation manifest | 从不 |
| `log` | 什么时候发生了什么、涉及哪些包? | 读账本 | 仅 `prune` |

## `status` —— 便宜的状态

```console
$ sow status
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4 dirty_dists= pending=0/0 locked=false
```

`status` 从不哈希整个仓库、从不恢复 Operation、从不构建。它报告仓库状态、期望 revision、已构建 generation、哪些 Dist 是 dirty、有多少 pending payload 对象占多少字节、锁是否被持有,以及最近一条 Operation。

一共四种状态:

| 状态 | 含义 | 客户端看到什么 |
|---|---|---|
| `clean` | Desired 与 Built 一致 | 每个视图都完整且最新 |
| `dirty` | Desired 领先,通常来自 `--skip` 或配置变化 | 旧的 Built 视图,仍然完整 |
| `recovering` | 存在非终态 Operation,下一条写命令必须先恢复 | 最后完成的协议指针 |
| `error` | 自动恢复无法安全判定,需要人工介入 | 最后完成的视图,绝不被覆盖 |

一次 `add --skip` 之后,差别立刻可见:

```console
$ sow add pkg/vray-5.44.1-1.x86_64.rpm -r pigsty -d el9 --skip
add repository=pigsty operation=1723106391526629874 accepted=1 failed=0 memberships=+1/-0 revision=5 generation=4 dirty=true

$ sow status
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9 pending=1/18787411 locked=false
```

revision 前进到 5,generation 停在 4,`el9` 变 dirty,一个 18.7 MB 的 pending 对象耐久存放在私有 pending store 里。公开的 `pool/` 与 `dists/` 逐字节没有变化。

**只要状态数据库可读,`status` 在四种状态下都返回 `0`。** 这是刻意的:脚本应当读取结构化状态,而不是从退出码反推;一个 `recovering` 的仓库是一个需要处理的事实,不是命令失败。只有状态无法读取或解析时才返回完整性错误。`ready_to_copy` 字段就是"这个能发货吗"的直接答案;需要一个会让流水线失败的严格门禁时,请用 `sow check`。

## `check` —— 完整证明

`check` 对选中的 Repository 或 Dist 按顺序做八层校验,不写任何东西:

```console
$ sow check
repository=pigsty status=clean ready_to_copy=true revision=4 generation=4
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=66
package-bytes	ok=true	checked=5
desired-membership	ok=true	checked=5
index	ok=true	checked=2
signature	ok=true	checked=9
generation-manifest	ok=true	checked=4
```

| 层 | 它证明什么 |
|---|---|
| `config` | `sow.yml` 可解析,且与实际的 Dist、架构、签名可用性一致 |
| `state` | SQLite schema、迁移账本与关系完整性 |
| `public-modes` | 每个公开文件与目录的权限位符合预期 |
| `package-bytes` | 每个 pool 与 pending 对象的哈希与记录的 SHA-256 一致 |
| `desired-membership` | 成员关系、坐标与架构别名彼此自洽 |
| `index` | 渲染出的元数据与成员集匹配,且每个引用都能解析 |
| `signature` | 包签名与已声明的元数据签名验证通过 |
| `generation-manifest` | 已构建代的 manifest 与磁盘上的实际树一致 |

`check` 不修复、不构建、不恢复 Operation。仓库 dirty 时,它会**同时**校验期望状态和旧的已构建代 —— 然后仍然拒绝认为结果可交付:

```console
$ sow check; echo "rc=$?"
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4
config	ok=true	checked=5
…
generation-manifest	ok=true	checked=4
integrity or recovery error: managed: repository is not ready to copy: repository status is dirty
rc=5
```

八层全过,退出码仍是 `5`。这个读法是对的:没有任何东西坏掉,但磁盘上的东西不是你要的东西,所以它还不能复制出去。这条命令就是该放进发布流水线的那条 —— `status` 告诉你现状,`check` 决定你发不发。

16 包工作区上八层全跑完约 0.12 s。`-j/--jobs N` 可并行哈希。

## `changes` —— 交付计划

```console
$ sow changes
base=4 generation=5 dirty=false
add	payload	dists/el9/x86_64/pool/v/vray/vray-5.44.1-1.x86_64.rpm	18787411	4bb5c796…
add	payload	pool/v/vray/vray-5.44.1-1.x86_64.rpm	18787411	4bb5c796…
add	metadata	dists/el9/x86_64/repodata/75fdd4f3…-primary.xml.gz	1089	75fdd4f3…
add	metadata	dists/el9/x86_64/repodata/a8de7a88…-filelists.xml.gz	512	a8de7a88…
add	metadata	dists/el9/x86_64/repodata/6f97bb31…-other.xml.gz	355	6f97bb31…
update	pointer	dists/el9/aarch64/repodata/repomd.xml	1510	60596dfb…
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1512	944d47f0…
delete	delete	dists/el9/x86_64/repodata/0df96f0b…-primary.xml.gz	0
delete	delete	dists/el9/x86_64/repodata/8402c28c…-filelists.xml.gz	0
delete	delete	dists/el9/x86_64/repodata/c16c7739…-other.xml.gz	0
…
```

每行是一个操作(`add`、`update`、`delete`)、一个阶段、一个相对仓库根的路径、一个大小和一个 SHA-256。**阶段顺序与 `build` 在本地磁盘上使用的顺序完全相同**:`payload → metadata → pointer → delete`。在对端按这个顺序消费该计划,镜像就永远不会处于不一致状态 —— 包先于引用它的索引落地,索引先于指向它的指针落地,而在一个不再引用某文件的指针发布之前,那个文件不会被删。

参数决定比较基准:

- **不带参数** —— 最近一代相对上一代。这是增量同步计划。
- **`changes N`** —— 从第 `N` 代到当前代的净变化。镜像落后好几代时很有用:你拿到的是一份净计划,不是回放。
- **`changes 0`** —— 当前代的完整交付清单:`pool/` 与 `dists/` 下的全部文件,不含 `sow.yml` 与 `.sow/`。全新镜像需要的就是它。

三条约束保证输出诚实。dirty 的期望状态不会进入 `changes` —— 输出会警告仓库 dirty,但仍以当前已构建代为终点,因为这份计划描述的是物理树,不是你的意图。`recovering` 或 `error` 的仓库干脆拒绝输出计划,免得把一个未决的文件动作误当成一代。`changes` 是仓库级的,不接受 `-d`;只需要某个 Dist 时,按路径过滤输出即可。

SOW 不认识远端、不持有凭据、不调用任何传输工具。`--json` 给你一个稳定结构,用来驱动 `rclone`、`rsync` 或你自己的脚本:

```json
{
  "base": 41,
  "generation": 43,
  "dirty": false,
  "changes": [
    {"op": "add", "path": "pool/p/pkg/pkg.rpm", "phase": "payload", "size": 123, "sha256": "…"}
  ]
}
```

## 代际保留

每一次真实的物理变化产生一个新的单调 Generation。元数据按 checksum 命名,而且**上一代的元数据文件会在磁盘上多留恰好一代**。

下面是第 5 代时的一个视图目录,里面躺着两代元数据:

```console
$ ls -1 dists/el9/x86_64/repodata/
1e73e26d…-primary.xml.gz        # 第 3 代
31b640e0…-filelists.xml.gz      # 第 3 代
58f05bff…-other.xml.gz          # 第 3 代
6f97bb31…-other.xml.gz          # 第 5 代,当前
75fdd4f3…-primary.xml.gz        # 第 5 代,当前
a8de7a88…-filelists.xml.gz      # 第 5 代,当前
repomd.xml

$ grep -o 'href="[^"]*"' dists/el9/x86_64/repodata/repomd.xml
href="repodata/75fdd4f3…-primary.xml.gz"
href="repodata/a8de7a88…-filelists.xml.gz"
href="repodata/6f97bb31…-other.xml.gz"
```

`repomd.xml` 只引用当前代。老的那三件套虽然不再被引用,但仍然可以被取到 —— 这正是它存在的意义。一个在构建前几秒钟下载了 `repomd.xml` 的客户端,仍然能取到那份文件承诺的元数据,而不是在事务中途撞上 404。APT 侧由 by-hash 条目提供同样的性质。

滑出保留窗口的文件会出现在下一次 `changes` 的 `delete` 阶段 —— 上面转录里的第 1 代条目就是这么来的。把那份计划应用到镜像之后,两边就重新对齐了。

## `log` —— 操作账本

每条写命令都留下一份持久记录。`sow log` 按从新到旧显示最近 50 条,`sow log OPERATION` 展开其中一条:

```json
{"id":"2299498205178002745","kind":"add","state":"done",
 "payload_json":"{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"add\",
   \"config_sha256\":\"37eb6dcf…\",\"skip\":false,\"dists\":[\"el9\"],
   \"build_dists\":[\"el9\"],\"manifest_sha256\":\"73933eb6…\"}",
 "result_json":"{\"accepted\":3,\"dropped_pending\":[],\"failed\":0}",
 "created_at":"2026-08-04T04:06:32.907704Z","updated_at":"2026-08-04T04:06:34.077441Z"}
```

单条 Operation 视图还会展开带时间戳的状态迁移、每个包的处置结果与逐 Dist 结论、成员的增删,以及带阶段标注的完整文件 Changeset。由于 payload 里记录了 `config_sha256` 与 `manifest_sha256`,你能证明这条 Operation 是针对哪份配置、朝哪个预期结果执行的 —— 而不只是"它跑过"。

`-d` 用于过滤出触及某个 Dist 的 Operation。

### 导出

```bash
sow log export pgsql-ops.jsonl -r pgsql
sow log export - -r pgsql | jq -c 'select(.operation.kind == "add")'
```

`export` 把符合条件的终态 Operation 以 JSONL 写出,一行一个对象,顺序稳定。省略文件名或传 `-` 则写到 stdout。它拒绝覆盖已存在的文件,也拒绝父目录是符号链接的目标 —— 这就是为什么在 macOS 上往 `/tmp` 导出会失败:那里的 `/tmp` 本身是符号链接。请写到你自己掌控的明确路径。

### 收缩

```console
$ sow log prune 2026-01-01 -r pgsql
{"operation":"2594304813413153341","repository":"pigsty","before":"2026-01-01T00:00:00+08:00","pruned":1}
```

`BEFORE` 是 ISO-8601 日期或 RFC 3339 时间戳;裸日期按本地零点解释,并在输出中回显为绝对时间,所以"到底删到哪儿"不存在歧义。

prune 只删除没有任何东西还需要的终态审计记录。它绝不删除非终态 Operation、恢复所需的记录、当前的包与成员状态、已构建代或 Changeset。它是仓库级操作,不接受 `-d` —— 删掉半条 Operation 会产生一条无法解释的记录。它在自己的持久 journal 保护下运行,所以 prune 中途崩溃会像其他 Operation 一样,由下一条写命令恢复。

## 串起来用

发布流水线通常长这样:

```bash
sow build -r pgsql -j 12          # 收敛
sow check -r pgsql                # 门禁:非零就不发
sow changes 41 -r pgsql --json > plan.json
```

`status` 上看板,`check` 做门禁,`changes` 驱动传输,`log` 用于事后复盘。

## 继续阅读

- [`build` / `status` / `check` / `changes` 参考](/zh/docs/reference/cli/build/)
- [`sow log` 参考](/zh/docs/reference/cli/log/)
- [JSON 输出](/zh/docs/reference/json/) —— `sow.cli/v1` envelope 与各命令 result 形态
- [事务与恢复](/zh/docs/feature/transactions/) —— 这些命令报告的状态是怎么产生的
