---
title: "事务与恢复"
linkTitle: "事务与恢复"
description: "Managed 模式的操作日志、两级锁模型、固定提交顺序与证据驱动崩溃恢复。"
url: "/zh/docs/feature/transactions/"
weight: 700
icon: fa-solid fa-shield-halved
---

本页说明 Managed 模式如何防止 live 指针指向缺失内容，以及如何协调 SQLite 状态与文件系统变更。

## 不变式

**在受支持的本地 POSIX 文件系统上，沿 Managed 协议指针读取的客户端只会得到完整旧视图或
完整新视图，包括进程中断之后。**

下面所有内容都是为了守住这条线:元数据在任何公开变更之前完整 stage 并校验,指针切换就是提交决策,每个操作都留下足够的持久证据,让下一条命令能把它做完或撤销,而不需要猜。

Plain `sow create` 刻意不属于这套事务模型。它以包目录为权威事实、把元数据视为可丢弃投影：一遍内容
扫描、一次最终 stat 校验，然后覆盖发布。中断后重新运行 `sow create`，而不是重放 journal。详见
[Plain 平面仓库](/zh/docs/feature/plain/)。

也要注意它 **没有** 声称什么。`dirty` 不是指索引写了一半；它表示 Desired 状态领先于
Built Generation，而旧的 Built View 仍然完整。SOW 也不承诺两个不同 Dist 在同一瞬间翻代；
它承诺每个协议视图始终自洽，且写命令返回时，本次 Operation 包含的每个 Dist 都处于记录的
Built Generation。

## 两类持久日志

Managed 仓库生命周期与变更使用两类持久化载体，各自作用域很窄：

| 日志 | 位置 | 覆盖范围 | 由谁恢复 |
|---|---|---|---|
| Workspace 文件 journal | `.sow/workspace-ops/active.json` | `init`、`repo new`、`repo rm` | 下一条工作区生命周期命令 |
| Repository 操作日志 | 该仓库的 SQLite | `dist new/rm`、`add`、`rm`、`build`、`log prune` | 该仓库的下一条写命令 |

这个划分不是随意的。工作区生命周期操作发生在目标仓库数据库尚不存在、或即将被删除的时候，因此不能用它；仓库变更有可用数据库，就用数据库。Plain 两者都没有，因为它的恢复单元是按包重新构建。

**Workspace journal** 保存操作类型、随机 64 位十六进制 id、仓库名,以及新旧 `sow.yml` 的原始字节与各自 SHA-256。工作区锁保证同时只有一条 active operation。`sow.yml` 的原子 rename 就是提交决策:如果当前 config 仍然哈希为旧值,就清理 planned journal 并回滚;如果哈希为新值,就幂等地补齐仓库外壳,或把自有对象移入 recovery。两边都不匹配则拒绝猜测。

**Repository 操作日志** 在任何公开文件副作用 **之前** 先向 SQLite 提交一条 `planned` Operation,随后记录每次状态迁移。它的 payload 绑定仓库、config SHA-256、精确的选中 Dist 集合、精确的 `build_dists`、`--skip` 决策,以及一个 manifest 哈希 —— 后者覆盖新对象事实、完整期望集、逐 Dist 策略结果、RPM 公钥证书快照与目标 Generation。

这不是 SQLite 的 WAL。WAL 负责 SQLite 自己的页面事务,它无法原子地协调 pool、staging 区与 `dists/`。跨数据库记录与 POSIX 文件动作的,是这套应用级操作日志。

## 操作生命周期

```text
planned → staged → applied → built → done
                       └──────────────→ done_dirty
   任一非终态 → recovering → built / rolled_back
   apply 前出错 → failed
```

| 状态 | 已耐久的东西 |
|---|---|
| `planned` | 命令、参数、目标与预期动作 |
| `staged` | 新包与元数据已写入私有 staging 区并校验 |
| `applied` | 期望状态与所需私有 pending payload 已提交;公开树可能仍是旧一代 |
| `built` | 完整静态 Generation 已切换 |
| `done` / `done_dirty` | 终态;作为审计记录保留 |

`sow log <OPERATION>` 展示带时间戳的状态迁移:

```json
"events":[
  {"sequence":0,"state":"planned","occurred_at":"2026-08-04T04:06:32.907704Z"},
  {"sequence":1,"state":"staged","occurred_at":"2026-08-04T04:06:33.067824Z"},
  {"sequence":2,"state":"applied","occurred_at":"2026-08-04T04:06:33.253073Z"},
  {"sequence":3,"state":"built","occurred_at":"2026-08-04T04:06:34.074916Z"},
  {"sequence":4,"state":"done","occurred_at":"2026-08-04T04:06:34.077441Z"}
]
```

只有你显式给出 `--skip` 才可能走到 `done_dirty`。默认 `add` 如果在 `applied` 之后渲染失败,命令返回错误、旧 Built 视图继续服务、Operation 保持可恢复 —— 它不会悄悄地以 dirty 收尾。

在 `applied` 之前失败的 Operation 会成为 `failed`。这里有一处契约上的微妙之处:`add` 必须在解析包之前先记录 `planned` Operation,所以一个架构不被许可的包确实会留下审计记录。但除了那条终态 `failed` 记录之外,什么都不会被写入 —— 没有包对象、没有成员关系、没有 pending 字节、没有公开树变化、没有 Generation。既留住了审计线索,又保证无效架构不会进入任何产品投影。

## 锁模型

锁是本机的 POSIX advisory `flock`。产品契约是单机、单写、本地 POSIX、协作式锁 —— 网络文件系统既不检测也不支持。

| 锁 | 文件 | 谁持有 |
|---|---|---|
| 工作区锁 | `.sow/workspace.lock` | `init`、`repo new/rm`、`dist new/rm` |
| 仓库锁 | `.sow/repo-locks/<repo>.lock` | `add`、`rm`、`build`、`dist new/rm`、`log prune` |
| Plain 目录锁 | 目标目录及其稳定父目录 | `sow create` |

两把都需要时,顺序固定:先工作区,后仓库,释放顺序相反。仓库锁的 inode 位于稳定路径,绝不随私有状态目录移动 —— 这样删除仓库时可以在别的进程还持有旧描述符的情况下撤下锁路径,而不会有第二个写者在新 inode 上形成。

`sow create` 同时锁住目标目录 **和** 它稳定的父目录。父目录锁的作用是:阻止另一个协作写者用 rename 把目录整个换掉,再对替身取得一把独立的锁。

只读命令从不取写锁,也不接受锁参数。其中需要组合读取配置、SQLite 与 live 元数据的那几个(`config check`、`repo ls/show`、`dist ls/show`)会在整个快照期间持有共享锁。`status` 刻意更轻:它只探测仓库锁,以便在写入进行中报告 `recovering` 或 `locked`,而不会被它阻塞。

两个参数控制等待行为,适用于所有取写锁的命令:

| 参数 | 行为 |
|---|---|
| `-T, --timeout DUR` | 最多等待 `DUR`;`0`(默认)一直等 |
| `-N, --no-wait` | 只尝试一次,锁被占用立即失败 |

两条失败路径都以 `4` 退出。`--no-wait` 与非零 `--timeout` 同时出现是用法错误,退出码 `2`。

```console
$ sow add ./build/*.rpm -r pgsql -d el9 -N
lock unavailable
```

在"宁可跳过这轮、也不要堆积"的 cron 作业里用 `-N`;在"排一小会儿队可以、但绝不能挂死"的 CI 里用 `-T 30s`。

## 提交顺序

每一代都按同样的四个阶段写入,而顺序正是不变式成立的原因:

```text
payload  →  metadata  →  pointer  →  delete
```

1. **payload** —— 规范包字节写入 `pool/`。此时还没有任何东西引用它们。
2. **metadata** —— checksum 命名的 RPM 元数据、`Packages`、`Packages.gz`,以及 by-hash 索引副本。此时仍没有指针指向它们。
3. **pointer** —— 客户端入口:RPM 的 `repomd.xml`(配置了签名则连同 `.asc`);Managed APT 则在每个架构的 direct 与 by-hash 索引都就位之后,才发布 `Release`(连同 `InRelease` 与 `Release.gpg`)。**这一步就是提交。**
4. **delete** —— 清理已过保留窗口的旧代元数据。

Pending 包体在单写者下分批提升，每次 group commit 最多 512 个对象或 1 GiB。SOW 先持久化
Pool 目录项，再删除 pending 名称；恢复因此能把 pending-only、指向同一 inode 的双链接或
Pool-only 状态重新绑定到 Operation，而不会冒同时丢失两个名称的风险。

正着读:包一定先于引用它的索引存在,索引一定先于指向它的指针存在。反着读:在一个不再引用某文件的指针耐久落地之前,那个文件不会被删。不存在任何一个窗口,让客户端沿活的指针走到一个不存在的文件。

这一切都通过与目标同文件系统的 staging 区完成,初始化时通过比较 `st_dev` 校验。挂载点或设备不同是明确失败,绝不降级为复制。文件先写入、fsync、由 SOW 自己的解析器与闭包校验器验证,之后才用原子 rename 换入。公开文件不继承你的 umask:`repodata/` 是 `0755`,索引文件与指针是 `0644`。

`sow changes` 用于审计与交付规划，描述 Generation Delta；它不能替代发布协议。请使用
`sow publish`，或把完整树复制到离线 staging 后再原子切换上线。见
[可观测与审计](/zh/docs/feature/audit/)。

## 崩溃恢复

**每条 Managed 写命令都先恢复,再做自己的事。** 没有单独的修复命令,也没有守护进程盯着陈旧状态;恢复是变更的前置条件。只要存在非终态 Operation,下一条 `add`、`rm`、`build`、`dist new/rm` 或 `log prune` 就先把它做完或回滚,然后才继续。

全局恢复顺序是固定的:先在工作区锁下恢复工作区生命周期;如果那不是一次仓库删除,再按仓库名顺序、在各自稳定的仓库锁下恢复仓库 Operation。已经越过"删除仓库"提交决策的工作区操作具有支配权,并禁止任何嵌套的仓库恢复 —— 在一个正被删除的仓库内部恢复状态毫无意义。

恢复由证据驱动,不做乐观假设。每个阶段都有明确规则:

| 已到达的阶段 | 恢复规则 |
|---|---|
| `planned` | config 仍为旧值 → 回滚 stage;否则证据冲突,退出 `5` |
| `staged` | config 仍为旧值 → 可回滚;config 已为新值 → 只允许前滚 |
| `applied` | 新 config 已原子换入,这就是提交决策,因此一律前滚 |
| `built` | 指针与目录已耐久,前滚提交数据库行 |
| `done` | 数据库、config 与树同代;清理 stage,重复恢复是空操作 |

这套规则的验收方式是在多个不同时机向 `sow add` 发送 `SIGKILL`。每一次,`status` 都报告 `recovering`,下一条写命令都先恢复该 Operation 再执行自身,最终 `check` 全部层通过,公开树从未撕裂。

```console
$ sow status
repository=pigsty status=recovering ready_to_copy=false ...
```

`sow build` 是唯一的显式前滚恢复入口:它在收敛之前,会先尝试完成或回滚任何可判定的非终态 Operation。看到 `recovering` 时,执行 `sow build` 就是标准反应。

`error` 专留给 journal、数据库与文件证据互相矛盾、任何自动选择都不安全的情况。此时 build 拒绝覆盖,最后完成的视图继续服务,你应当从备份恢复,再跑 `check` 与 `build`。这里刻意没有 `repair --force` —— 一个可能猜错的修复,比一个拒绝执行的修复更糟。

## fail-closed 的路径安全

Managed 路径从不由用户提供的字符串拼装。每次创建、rename 和删除都走同一套流程:

1. 把工作区根解析为绝对真实路径;
2. 用固定相对片段重新构造目标,并验证相对路径不含任何逃逸分量;
3. 对路径上每个已存在的受控组件执行 `Lstat`,拒绝符号链接和非预期文件类型;
4. 只删除已经先被原子移入 `.sow/.../recovery` 的对象;
5. 删除前再次证明该 recovery 目标确实位于对应的私有状态目录内。

名称必须匹配 `[a-z0-9][a-z0-9._-]*`,`.`、`..`、`.sow`、`pool`、`dists` 及工作区保留名一律拒绝。

对文件句柄也是同样的姿态。SQLite 以 `O_NOFOLLOW` 打开并绑定普通文件 inode,连接建立后再按路径复核一次;数据库、WAL、shm 或 rollback journal 中任何一个是符号链接、非普通文件、有多个硬链接,或在打开期间被换绑,都会被拒绝。`log export` 拒绝覆盖已存在的文件,也拒绝父目录是符号链接的目标 —— 这就是为什么在 macOS 上往 `/tmp` 导出会失败:那里的 `/tmp` 本身是个符号链接。

各类 journal 都有大小上限:工作区 32 MiB、仓库 Operation payload 16 MiB,外置的 mutation manifest 与 base manifest 各 64 MiB。超限既不截断也不降级,而是在提交窗口之外直接失败 —— 这样写者永远不会产出一条"自己写得进去、恢复读者却永远读不回来"的 Operation 记录。

以上没有一条声称能抵御以同一用户身份运行、拥有无限权限的恶意进程。它抵御的是现实中的失败模式:崩溃、协作进程之间的竞态,以及在检查与使用之间形态发生变化的路径。

## 继续阅读

- [可观测与审计](/zh/docs/feature/audit/) —— 如何读取这些机制维护的状态
- [退出码](/zh/docs/reference/exit-codes/) —— `4`、`5`、`6` 分别意味着什么、什么时候会看到
- [`build`](/zh/docs/command/build/)、[`status`](/zh/docs/command/status/)、[`check`](/zh/docs/command/check/) 与 [`changes`](/zh/docs/command/changes/)
