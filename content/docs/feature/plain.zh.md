---
title: "Plain 平面仓库"
linkTitle: "Plain 平面仓库"
description: "sow create 的单遍扫描、覆盖重建契约，以及确定性输出与 Pigsty 完成标记。"
url: "/zh/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

`sow create` 接手一个已经放着 `.rpm` / `.deb` 的目录，在包旁边生成平面仓库索引。Plain 模式没有工作区、配置文件、数据库、期望状态，也没有操作 journal。包目录就是权威事实来源，所有索引都是当前目录内容的可丢弃投影。

这个边界是刻意的：Managed 仓库保存状态并恢复事务；Plain 仓库失败了就便宜地重建。一次运行失败或被中断后，重新执行同一条命令，覆盖派生元数据即可。

## 契约

Plain 模式由四条规则定义：

1. **包是权威事实。** 默认 `create` 不修改包字节，只替换 `repodata/`、`Packages` 与 `Packages.gz`。`--pigsty` 和显式 RPM 签名是文档明确列出的例外。
2. **包内容只扫一遍。** 默认未签名路径中，每个选中包只打开一次、完整计算一次 SHA-256，并在同一遍里解析。完整 RPM/DEB 元数据保留给渲染阶段；渲染与输出校验不会再次打开包体。
3. **收尾只做一次便宜校验。** 发布前重新列出顶层包集合，把 `stat` 事实与扫描快照比较，不再计算第二遍包 SHA-256。
4. **失败就重建。** Plain 没有事务 journal、pre-image、前滚或回滚。失败可能留下部分已替换的派生元数据；下一次 `sow create` 丢弃自有临时残留，按当前包目录完整重建。

输入字节不变时，输出仍然确定，重复运行报告 `noop=true`。

## 单遍流水线

`--jobs` 默认等于逻辑 CPU 数，控制唯一一次包内容扫描：

```text
锁定目录
  -> 列出并排序顶层 RPM/DEB
  -> 并行打开 + SHA-256 + 解析（每包一次）
  -> 处理坐标冲突与 Pigsty 过滤
  -> 从保留的解析事实渲染 RPM/DEB 元数据
  -> 只校验生成的元数据
  -> 重新列目录并比较包 stat 快照
  -> 覆盖派生输出；--pigsty 最后写 repo_complete
```

worker 完成先后不会影响结果：解析事实始终按规范 basename / 索引顺序消费。RPM XML 直接使用 worker 保留下来的完整解析对象；DEB `Packages` 直接使用保留的 control 段落与该 worker 已经算出的 SHA-256。

输出自校验仍会读取生成的 XML、`repomd.xml`、`Packages` 与 `Packages.gz`。这些是很小的派生元数据，不会再次读取包体。

### 最终 stat 校验保证什么

收尾校验要求：

- 顶层普通 `.rpm` / `.deb` basename 的排序集合完全相同；
- 文件 identity / inode 相同；
- 文件类型与 mode 不变；
- size 与 mtime 不变。

任一事实不同，都在发布前以完整性退出码 `5` 拒绝。这能以一次列目录的成本发现正常的新增、删除、替换、截断与重写竞争。

它刻意不是密码学复验。若外部写者原地改字节，同时伪造保持 inode、size 与 mtime 不变，`stat` 无法发现。Plain 接受这个权衡，因为目标场景是本机单进程、协作写入、结果可重建。需要对抗并发篡改证据或持久恢复时，应使用 Managed 仓库。

## 扫描与输出规则

- 只考虑目录顶层普通文件；永不递归，也不跟随符号链接。
- 只选择 `.rpm` 与 `.deb` 后缀。
- 包身份与架构来自 RPM header 或 DEB control，绝不从文件名猜；RPM `src` / `nosrc` 被拒绝。
- 所有合法版本都进索引；同一逻辑坐标对应不同字节流时拒绝。
- 默认模式拒绝空目录；`--pigsty` 可以把一次中断清理后已经为空的权威包集合收敛完成。

有 RPM 就生成 `repodata/`，有 DEB 就生成 `Packages` 与 `Packages.gz`：

```text
/srv/repo/
├── pev2-1.23.0-1.noarch.rpm
├── xray_26.2.6-1_amd64.deb
├── Packages
├── Packages.gz
└── repodata/
    ├── <sha256>-primary.xml.gz
    ├── <sha256>-filelists.xml.gz
    ├── <sha256>-other.xml.gz
    └── repomd.xml
```

平面位置全部是相对路径：RPM 使用裸 basename，DEB 使用 `./<basename>`。公开目录固定 `0755`，生成文件与 `repo_complete` 固定 `0644`，不受 umask 影响。

某种包格式消失时，SOW 删除该格式已知的派生输出。重跑也会覆盖中断留下的半套输出，例如只有一个 `Packages`；新一代不再引用的 SOW checksum 形状 RPM 元数据会被移除，未知文件保持不动。

## 确定性与 no-op

`repomd.xml` 的 revision 与 timestamp 固定为 `0`，gzip header 固定，排序规范化。因此同一包集合生成逐字节一致的元数据。发布前 SOW 会比较 stage 与 live 元数据；如果无需清理/签名且所有输出已经相同，就只删私有 stage，不替换公开 inode，并返回 `noop=true`。

稳定 CLI schema 仍保留 `recovered` 字段以维持兼容，但 Plain create 已不做 journal 恢复，始终报告 `false`。

## 发布与中断语义

开始发布前，全部元数据都已在目标目录内的私有 stage 生成并验证。单文件替换使用同文件系统 rename；RPM 先安装 checksum 命名元数据，最后替换 `repomd.xml`。

这不是多文件事务。进程在发布中被杀，可能留下新 RPM 元数据配旧 DEB 元数据、只剩一个 DEB 索引文件，或多余的旧 checksum RPM 元数据。这些状态不是需要调和的事务证据，只是可丢弃输出。下一次运行按当前包集合重新渲染完整投影，覆盖或删除残留。

实现不再创建 `.sow-plain-operation.json` 或 recovery trash。启动时会先丢弃保留命名空间中的 `.sow-plain-stage-*`、历史 `.sow-plain-recovery-*`、journal-write 残留与旧版 Plain journal，然后开始全新扫描。

## `--pigsty` marker 门禁

`--pigsty` 还会删除命中兼容规则的解析包事实（DEB `i386` 与 Patroni 3.0.4），并把剩余包按 basename 排序写入 `repo_complete`，格式为 `<sha256><两个空格><basename>`。RPM 不会仅因为架构是 `i386/i486/i586/i686` 而被删除。

发布顺序为：

```text
stage + 校验
  -> 最终 stat 校验
  -> 撤下旧 repo_complete
  -> 安装显式请求签名后的 RPM（如有）
  -> 安装 RPM 与 DEB 元数据
  -> 删除命中清理规则的包
  -> 最后写 repo_complete
```

marker 缺失就表示“尚未完成”，消费方不得使用该目录。若运行在撤 marker 后停止，重新执行 `sow create --pigsty`：它扫描现在仍存在的包，覆盖元数据、完成清理，最后写新 marker，不需要历史动作日志。

默认模式看到已有 `repo_complete` 会拒绝运行，避免未受门禁控制的命令留下过期就绪声明。

## 显式 RPM 签名

`--sign-with` 是修改包体的显式授权，也是独立慢路径。SOW 在私有 stage 副本上签名，验证嵌入签名与 signature-neutral digest，重新解析结果，再先于元数据安装签后字节。这些必要的复制、签名与签后验证读取不属于默认未签名的一遍保证。签名中断后同样按当前包目录重跑，不从 journal 重放签名事务。

## 锁与适用范围

`sow create` 在一次运行期间锁定目标目录及其稳定父目录；`--timeout` / `--no-wait` 控制协作锁等待。锁能阻止另一个协作 SOW 进程同时写入，但不会把任意外部包修改变成受支持负载。

本地单进程创建一个可随时重建的平面仓库，用 Plain。需要期望状态、审计历史、原子 generation 切换或证据驱动崩溃恢复，用 [Managed 工作区](/zh/docs/feature/managed/)。

## 继续阅读

- [`sow create` 参考](/zh/docs/command/create/) —— 参数、输出与失败契约
- [事务与恢复](/zh/docs/feature/transactions/) —— Managed 的耐久边界
- [快速上手](/zh/docs/start/quickstart/) —— 五分钟建一个仓库
