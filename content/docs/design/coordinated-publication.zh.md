---
title: "协同发布设计提案"
linkTitle: "协同发布"
description: "SOW v0.4.0 提议采用计划驱动、rclone 执行、可确定恢复 Ctrl+C 中断的发布流程。"
url: "/zh/docs/design/coordinated-publication/"
weight: 450
icon: fa-solid fa-cloud-arrow-up
---

> **状态：SOW v0.4.0 设计提案。** 本文是一份产品与实现计划，不代表 SOW v0.3.x
> 已经具备这些行为。当前可用命令仍以 [`sow publish`](/zh/docs/command/publish/) 为准。

## 最终决策

SOW v0.4.0 应当负责 **协调发布**，而不是再实现一套大批量对象存储客户端：

- **SOW 负责语义：** 冻结 Generation、精确变更集、发布波次、协议顺序、恢复状态与验证结论。
- **rclone 负责传输：** 重试、包体并行传输、S3 multipart upload 与传输级完整性检查。
- **服务层负责缓存：** 不可变包体可以缓存；提交完成后，可变仓库元数据不能继续返回旧代。

真实的首要故障模型，是单一维护者在发布途中按下 **Ctrl+C**。因此设计目标是确定性重跑与前向
收敛，而不是处理多个分布式写者，也不假装对象存储存在多 key 事务。

对用户的准确承诺是：

> 发布过程顺序确定、可以重启、只增不删，并最终精确收敛到一个冻结 Generation；但它不是覆盖
> 全部对象 key 的原子事务。

## 用户故事

### 故事一：发布前看清到底要改什么

作为仓库维护者，我希望在 SOW 写入远端之前看到目标 Generation 与每个发布波次，以便在交付前
发现误构建或异常庞大的变化。

```console
sow check --repo pgsql
sow publish prod --dry-run
```

提议中的 dry run 不显示任何凭据，但会输出：

- target 名称、Repository、base checkpoint 与目标 Generation；
- plan SHA-256；
- prepare 与 commit 阶段的对象数和字节数；
- 所有 APT/RPM view 的提交顺序；
- DeleteCandidates，并明确标记为 **不会删除**。

`--json` 输出同一份封闭的机器可读计划。dry run 不产生远端副作用，也不创建 active attempt。

### 故事二：用一个命令发布已验证 Generation

作为维护者，我希望用一个命令发布当前 Built Generation，而不必自己拆分 rclone 命令，也不必
死记 APT/RPM 指针顺序。

```console
sow publish prod
```

SOW 冻结当前 Built Generation，持久化发布计划，调用 rclone 完成 prepare 波次，按确定顺序
提交各个 view，验证结果并记录 Applied Checkpoint。后续运行只发布下一个精确 Generation 差异；
目标已经是当前代时，该命令返回 no-op。

操作者永远不会对该前缀手工运行 `rclone sync`。SOW 可以调用 `rclone copy` 与
`rclone copyto`，但发布过程绝不删除远端对象。

### 故事三：在公开提交前安全停止

作为维护者，我希望在耗时的包体传输阶段按 Ctrl+C 可以快速停止，同时不破坏当前线上仓库。

如果 Ctrl+C 发生在 prepare 阶段，SOW 取消 rclone 并给出清晰提示：

```text
publication stopped before commit; rerun `sow publish prod` to continue,
or run `sow publish prod --abort` to abandon the attempt
```

此时最多只有只增不删的包体和不可变元数据到达目标；旧仓库指针仍然有效。重跑会使用同一份冻结
计划并复用完全匹配的对象；由于尚无 commit intent，也允许使用 `--abort`。

### 故事四：在指针提交过程中停止

作为维护者，我希望在短暂的 commit 阶段按下 Ctrl+C 时，SOW 不要主动把一个 APT/RPM view
丢在半完成状态。

持久化 commit intent 后，第一次 Ctrl+C 不再启动下一个 view。如果当前 view 已开始提交，
SOW 会完成这个很小的有序提交单元、记录进度，然后退出。操作者确实需要立即退出时，可以按第二次
Ctrl+C 强制终止。

```text
interrupt received; finishing view dists/noble before stopping
publication has commit intent; rerun `sow publish prod` to roll forward
```

commit intent 之后，`--abort` 会被拒绝。重新运行原命令时，SOW 重新验证冻结计划，从头重写未完成
view，再继续后续 view。`kill -9`、终端丢失或两个指针写入之间断网，也使用同一机制恢复。

### 故事五：显式执行完整远端审计

作为维护者，我希望日常增量发布成本与变化规模成正比，同时在迁移前或怀疑漂移时，仍有一个明确的
全量完整性操作。

```console
sow audit prod
```

提议中的 audit 会：

- 枚举完整配置前缀；
- 与 Applied Checkpoint、Generation manifest 对比；
- Provider 无法返回所需 digest 时，下载并计算哈希；
- 通过 `public_endpoint` 检查公开 commit pointer；
- 报告缺失、变化和未知对象，但不删除它们。

`publish` 验证本次 changed closure 与所有受影响的最终指针；`audit` 才是昂贵的完整证明。一个由
v0.3 管理过的前缀，在首次执行 v0.4 发布前必须通过 audit，以建立传输迁移基线。

### 故事六：使用 Cloudflare R2 而不被旧缓存欺骗

作为 R2 操作者，我希望客户端看到新仓库指针时，能够取得该指针声明的对象，而不是边缘节点缓存的
旧版本。

生产切换前，服务域名应满足：

- `<prefix>/pool/**` 可以使用长 TTL；
- v0.4 首版契约要求 `<prefix>/dists/**` 全部 bypass cache；
- 如果还存在 `dists/` 之外的传统 YUM 布局，额外 bypass `**/repodata/repomd.xml*`；
- 可变元数据路径的 404 不得跨发布继续保留。

R2 API 操作是强一致的，但启用缓存的自定义域仍可能继续返回覆盖前的旧对象。SOW 可以验证已配置
的公开端点，但不负责创建 DNS、Bucket Policy 或 Cloudflare Cache Rules。

## 用户使用流程

### 一次性配置

v0.4 提案保留现有 target identity 与凭据模型。`r2` 仍是 Provider；rclone 是其默认传输引擎，
而不是新增一种 Provider 类型。

```yaml
targets:
  prod:
    repository: pgsql
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: repo/pgsql
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/repo/pgsql/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

SOW 解析已有 credential reference，通过临时私有 rclone 配置或子进程环境传递凭据。秘密不会
出现在 argv、日志、dry-run 输出或公共树中。启动时按经过测试的 rclone 版本范围执行能力检查，
而不是看到一个叫 `rclone` 的程序就直接接受。

### 日常操作

```console
sow add ./packages/*.rpm --repo pgsql --dist el9
sow build --repo pgsql
sow check --repo pgsql
sow publish prod --dry-run
sow publish prod
```

该流程有意保持 `build` 与 `publish` 分离；尚未构建的 Desired 变化不会被静默交付。

### 恢复决策

```text
commit intent 是否已经持久化？
├── 否 -> 重跑 publish，或者 publish --abort
└── 是 -> 重跑 publish；前向恢复是唯一合法路径
```

不需要增加 `--resume` 参数。每个 target 最多只有一个 active attempt，重复原命令就是恢复操作。

## 发布协议

### Plan

`sow/publication-plan/v2` 发布计划是 target-scoped、确定性且无副作用的。它绑定：

- Repository 与 target identity；
- base checkpoint 与冻结的目标 Generation；
- target manifest digest 与 plan digest；
- 每项操作的 path、size、SHA-256，以及 update 的预期旧 digest；
- prepare 波次、有序 view commit unit 与 delete candidate。

attempt 活跃期间，现有 Repository lock 与 active-publication fence 会阻止普通 SOW 变更。恢复时
始终重建并比较同一份 plan digest；commit intent 之后只要出现不一致，就会失败关闭。

### 第一波：不可变 Prepare

包体与校验和寻址元数据首先按照一份精确生成的文件清单传输。概念命令是：

```text
rclone copy <repository-root> <remote-prefix> \
  --files-from-raw <prepare-list> \
  --immutable --checksum --no-traverse
```

实际参数与最低 rclone 版本必须由发布前的集成测试确定。executor 必须保留传输完整性，且不能把
prepare 操作变成删除。如果不可变路径在目标上已经存在不同字节，发布必须失败关闭。

SOW v0.3 会在 R2 对象上保存显式 `sow-sha256` 元数据；不能假设一次批量 rclone copy 会在没有
逐文件 mapper 时，为每个输入对象写入各自不同的 SHA-256。因此，v0.4 采用与 transport 无关的
checkpoint identity：

- Generation manifest 继续作为权威 SHA-256 内容身份；
- checkpoint 记录 size、不透明 Provider identity、传输引擎/版本与成功 transfer receipt，
  但不把 ETag 冒充为 SHA-256；
- 恢复时尽可能使用 rclone 双方共有的 checksum 验证 changed closure；
- Provider 无法返回 SHA-256 时，`sow audit` 下载对象并计算哈希。

这样 rclone 可以保持为纯传输工具，不必把 SOW 状态模型塞进 metadata-mapper 子进程。迁移需要
一次 v0.3 到 v0.4 的 audit 与 checkpoint migration；旧 `sow-sha256` 仍可作为迁移证据，但
绝不能被静默重新解释为新 receipt。仅仅 size 相同，不足以迁移 checkpoint。

### 第二波：有序提交 View

首个可变名称被覆盖前，必须先持久化 commit intent。每个 view 拥有自己的 stable alias 与
pointer；不同 view 串行提交。

```text
APT view:
  stable Packages/Sources alias 及压缩形式
  -> Release.gpg（签名时）
  -> Release
  -> InRelease（签名时）

RPM view:
  repomd.xml.asc（签名时）
  -> repomd.xml
```

每个可变文件分别使用一次强制 `rclone copyto --no-check-dest --retries 1`，并设置有界 I/O
超时。SOW 检查退出状态、与 target 对账后才推进。恢复未完成 view 时，从第一个可变操作开始
重写。这是有意设计的幂等性，不是多对象原子性承诺。

APT stable alias 必须属于各自 view 的 commit unit。如果在首个 view pointer 之前先全局发布
全部仓库 alias，会扩大不一致窗口，并把原本独立的 view 耦合起来。

### 第三波：验证与 Checkpoint

普通发布验证：

- plan 本次改动的每个对象，并使用适合该对象的 Provider evidence；
- 通过公开端点验证每个受影响的最终 APT/RPM pointer；
- 各受影响 view 的引用闭包与签名；
- 最终 plan 与目标 Generation identity。

随后写入 Applied Checkpoint。日常发布不再枚举并从公网下载每一个未变化包；完整前缀证明属于
`sow audit`。

### 删除策略

`DeleteCandidates` 只保留为计划证据。发布过程既不调用 `rclone sync`，也不调用
`rclone delete`。远端物理删除与生命周期 GC 属于未来的独立设计，只有经过观察期证明新 checkpoint
与 audit evidence 足够后再考虑。

## 状态与信号

| 持久状态 | Ctrl+C 行为 | 下一项合法操作 |
|---|---|---|
| plan 尚未落盘 | 停止 | 重新开始 |
| planned / preparing | 立即取消 rclone | 重跑或 `--abort` |
| commit intent，位于 view 之间 | 不再开始下一 view | 重跑 |
| commit intent，正在提交 view | 第一次信号完成当前 view；第二次强制退出 | 重跑 |
| 所有 view 已提交、尚无 checkpoint | 停止或失败都会留下可恢复证据 | 重跑验证/checkpoint |
| Applied Checkpoint | 完成 | 下次 publish 或 audit |

命令始终输出 plan/attempt identity 与准确的下一条合法命令。机器可读进度输出 phase 与 view 边界，
但不暴露秘密或原始 rclone 配置。

## 验证与验收

只有下列矩阵在 APT 与 RPM view 上均通过，实现才可验收：

| 场景 | 必须达到的结果 |
|---|---|
| 向空前缀首次发布 | 包管理器可以成功安装 |
| 增量新增/更新包 | 传输范围受 plan 约束；客户端看到新元数据 |
| no-op 发布 | 不修改对象，checkpoint 不变 |
| prepare 期间 Ctrl+C | 旧客户端仍有效；重跑收敛 |
| 每个可变写入前后故障 | 重跑会重写 view，客户端最终收敛 |
| 最终 pointer 已写、本地 receipt 未写时故障 | reconcile 能识别已安装字节 |
| 不可变路径冲突 | 失败关闭，绝不覆盖 |
| public cache rule 缺失或陈旧 | 写 checkpoint 前公开验证失败 |
| 从 v0.3 前缀迁移 | 首次 v0.4 commit 前完成 full audit |
| 发布后 full audit | manifest、checkpoint、remote 与公开 pointer 一致 |

测试按以下层次推进：

1. 纯 plan 与 pointer-order contract test；
2. fake-rclone argv、退出码与信号测试；
3. real rclone 对本地 filesystem remote 集成；
4. 带故障注入的 S3-compatible 集成；
5. Cloudflare R2 shadow prefix 与真实 `apt`/`dnf` 客户端；
6. shadow prefix 多次中断测试通过后，才允许生产切换。

## 交付路线图

| 里程碑 | 交付物 | 出口门禁 |
|---|---|---|
| M0 — 协议 | ADR、plan schema、用户可见 dry run | APT/RPM 有序 contract test |
| M1 — prepare | 薄 rclone runner 与不可变清单复制 | 首次/增量/no-op 与 pre-commit 中断测试 |
| M2 — commit | view-owned alias、串行 `copyto`、信号边界 | 每次可变写入后故障，重跑均收敛 |
| M3 — evidence | 增量验证、`sow audit`、v0.3 migration | audit 与旧全量验证路径结果一致 |
| M4 — provider | S3/R2 集成与缓存部署契约 | 真实 APT/DNF 客户端通过 shadow domain |
| M5 — cutover | 替换生产整树同步入口 | managed repo 发布路径不再出现 `rclone sync` |

预计开发范围为 15–20 个专注开发日，随后进入观察期。alpha、beta 与 GA 的晋级由正确性门禁决定，
而不是按日历强行推进。

## v0.4.0 明确不做什么

- 多个并发写者或分布式锁；
- 通用 publication executor 插件框架；
- 多 view 并行 commit；
- 远端对象删除或自动垃圾回收；
- 自动 Cloudflare purge、DNS 或 Cache Rule 管理；
- 基于 Worker 的间接指针或 generation-prefix 切换；
- bucket versioning 事务；
- 立即删除原生 R2 transport 或现有 inventory/grace 记录。

排除这些内容，能让 v0.4.0 只做一项可控变化：保留 SOW 的发布语义，替换批量传输机制，并让
中断恢复真正可观察、可使用。

## 参考资料

- [当前发布与恢复模型](/zh/docs/design/publication/)
- [当前 `sow publish` 命令](/zh/docs/command/publish/)
- [Cloudflare R2 一致性模型](https://developers.cloudflare.com/r2/reference/consistency/)
- [Cloudflare R2 自定义域缓存](https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/)
- [rclone copy](https://rclone.org/commands/rclone_copy/)
- [rclone 全局参数与 metadata 行为](https://rclone.org/docs/)
