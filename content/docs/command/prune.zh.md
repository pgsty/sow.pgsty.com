---
title: "sow prune"
linkTitle: "prune"
description: "在平面仓库中保留最新 RPM 版本。"
categories: [Command]
tags: [cli, plain, rpm]
url: "/zh/docs/command/prune/"
weight: 110
icon: fa-solid fa-scissors
---

`sow prune` 按包名和架构保留 Epoch/Version/Release 最高的 RPM，重建平面索引，再删除旧版本。EVR 比较遵循 RPM 规则，包括插入符（`^`）快照版本，例如 `2.0^20250611 < 2.0.1`。此命令需要 SOW 0.7.0 或更新版本。

## 语法 {#synopsis}

```text
sow prune DIR [--dry-run] [--strict] [--protect NAME]... [-j N] [--metadata-timestamp SECONDS] [-T DUR | -N] [--json]
```

`DIR` 必填。SOW 扫描顶层普通二进制 RPM 文件（支持 RPM v4 与 v6），不扫描子目录，不发现工作区，也不读取 `sow.yml`。在 RPM 与 DEB 混合目录中，`prune` 只更新 RPM 索引、保持 DEB 索引原样，并在 `repo_complete` 中沿用仍在目录内的已记录 DEB 摘要，不提前对未入索引的新 DEB 计算哈希。

## 预览与清理 {#preview-and-prune}

在本地发布源目录执行此命令。使用缓存旧索引的客户端可能仍需要旧 RPM，发布流程应考虑这一点。

```bash
sow prune /srv/candidate --dry-run
sow prune /srv/candidate --protect age_18 --protect age_18-llvmjit
```

`--dry-run` 执行校验并报告候选项，不修改文件。预览和正式执行时应使用相同的保护选项。

`--protect NAME` 保留该精确包名在所有架构下的全部版本。可重复指定，不接受模式匹配。默认容错模式下，损坏包、未匹配的 `--protect` 名称以及同版本冲突（保留整个包名与架构分组）会输出告警并安全跳过；如果全部 RPM 均被跳过，则保留原有的 `repodata/` 与完成标记。传入 `--strict` 可在发布前遇错即停。

## 选项 {#options}

| 选项 | 行为 |
|---|---|
| `--dry-run` | 校验并预览删除候选项，不写文件 |
| `--strict` | 遇到损坏包、未匹配的 `--protect` 名称或同版本冲突时返回非零退出码 |
| `--protect NAME` | 保留精确包名的全部版本，可重复指定 |
| `-j, --jobs N` | 软件包检查并发数，默认为 CPU 数量 |
| `--metadata-timestamp SECONDS` | 索引发布时间，以 Unix 秒表示；与 `create` 相同，默认为 `0` |
| `-T, --timeout DUR` | 限制等待目录锁的时间 |
| `-N, --no-wait` | 目录锁被占用时立即失败 |
| `--json` | 返回标准 JSON 信封 |
{.wide .expand}

`--timeout` 与 `--no-wait` 互斥。Prune 不签署软件包或仓库元数据，也不接受 `--pigsty` 或 `--passfile`。

## 完整性与恢复 {#integrity-and-recovery}

每个被删版本对应的替换 RPM 必须通过包内摘要与签名头检查，包括 RPM v6 原生 `RPMSIGTAG_OPENPGP` 标签 278，以及签名头标签 267（`RPMSIGTAG_DSA`）中的 RSA、DSA、ECDSA 和 EdDSA 数据包。SOW 将摘要校验和索引记录的内容绑定到稳定的文件身份（包括 `ctime` 与链接数 `nlink`），并在每次删除前和操作完成前重新检查替换包：若仅 `ctime` 或 `nlink` 发生变化（例如外部创建硬链接），SOW 会在已绑定的文件描述符上重算 SHA-256，从而允许无害硬链接通过，同时原地改写后恢复大小和修改时间仍会立即停止后续删除。

SOW 在绑定目标目录后立即释放父目录锁，相邻平面目录可并行运行。SOW 先发布筛选后的索引，再删除软件包。如果索引已发布或部分文件已删除后发生错误，结果会报告实际变化，并返回部分完成退出码 `3`；中断返回 `130`。SOW 不会恢复已经删除的软件包。解决报告的问题后，重新运行相同命令。

SOW 会在修改期间撤下已有的 `repo_complete` 标记（通过 `.sow-prune-repo-complete` 记录），仅在成功完成后刷新，并保留仍在目录中的已有 DEB 标记摘要。该待完成状态在中断后仍会保留。如果原先没有标记，Prune 不会创建标记，也不会应用 `create --pigsty` 的包排除规则。

JSON 结果包含 `dir`、`dry_run`、`kept`、`candidates`（每个旧 `path` 及其 `latest` 替换包）、`removed`、可选的 `skipped` 与 `warnings`、`index_updated`、`marker` 和 `noop` 字段。文本模式将告警输出到 stderr；成功的 `--json` 输出将其写入 stdout 并保持 stderr 为空。

## 支持的仓库 {#supported-repositories}

Prune 在非预览执行时拒绝 Managed 工作区以及存在 `repodata/repomd.xml.asc` 的仓库。如果已有 `repomd.xml` 登记了 SOW 不生成的独立元数据，例如软件包组、updateinfo、modules 或未知类型，也会拒绝执行。Prune 允许 SQLite 和 zchunk 等其他包索引编码，支持 RPM v4 与 v6 软件包，并在混合目录中安全保留 DEB 索引。

## 退出码 {#exit-codes}

| 退出码 | 含义 |
|---|---|
| `0` | 裁剪成功，或 `--dry-run` / `noop` 完成 |
| `1` | 目录不存在或不可读、文件系统、包解析、摘要校验或元数据渲染错误 |
| `2` | 选项无效、缺少 `DIR` 参数，或（在 `--strict` 模式下）`--protect` 指定的包名未匹配到软件包 |
| `3` | 部分完成：在发布筛选后的索引或删除至少一个 RPM 后发生失败 |
| `4` | 目录锁被其他进程持有 |
| `6` | 不支持的仓库状态（Managed 工作区、已签名 `repomd.xml`、外部元数据，或在 `--strict` 模式下遇到跳过包或相等 EVR） |
| `130` | 收到 SIGINT 或 SIGTERM 中断 |
{.wide .expand}

## 参见 {#see-also}

- [`sow create`](/zh/docs/command/create/)：移除附加元数据后重建候选仓库的步骤，以及元数据时间戳规则
- [Plain 模式](/zh/docs/feature/plain/)：平面仓库行为
- [迁移现有 YUM 仓库](/zh/docs/tutorial/yum-migration/)：替换 `createrepo_c` 并裁剪平面 RPM 目录
