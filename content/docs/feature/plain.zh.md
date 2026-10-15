---
title: "Plain 平面仓库"
linkTitle: "Plain 平面仓库"
description: "生成平面 RPM、DEB 索引，继续中断构建，并使用签名或 Pigsty 完成标记。"
categories: [Feature]
tags: [plain, rpm, deb]
url: "/zh/docs/feature/plain/"
weight: 200
icon: fa-solid fa-folder-open
---

用 `sow create` 为一个 RPM 或 DEB 软件包目录生成索引。索引与包文件放在一起。
该命令不读取 `sow.yml`，也不创建状态数据库。

```bash
sow create /srv/offline
```

<span id="契约" data-td-print-local></span>
<span id="扫描与输出规则" data-td-print-local></span>

## 输入与输出

SOW 只扫描目录顶层以 `.rpm` 或 `.deb` 结尾的普通文件，不递归，也不跟随包文件符号链接。
包名、版本和架构来自包内信息。源码 RPM（`src` 和 `nosrc`）会被拒绝。

| 输入 | 生成文件 |
|---|---|
| RPM | `repodata/repomd.xml` 和 gzip 压缩的 `primary`、`filelists`、`other` XML |
| DEB | `Packages` 和 `Packages.gz` |
| 两种格式 | 两组索引 |

RPM 包路径使用文件名，DEB 的 `Filename` 使用 `./<文件名>`。所有有效版本都会进入索引。
同一包坐标对应不同字节时，构建报冲突。没有受支持包的目录会被拒绝；`--pigsty`
完成中断的清理操作时例外。

默认保留包文件和无关文件。某种格式不再有包时，SOW 删除该格式的旧索引，也会删除过时的
SOW 格式 RPM 元数据并替换上次运行留下的不完整输出。生成目录的权限为 `0755`，
生成文件为 `0644`。

<span id="单遍流水线" data-td-print-local></span>
<span id="最终-stat-校验保证什么" data-td-print-local></span>
<span id="确定性与-no-op" data-td-print-local></span>

## 构建与重复运行

普通未签名构建只读取每个选中包一次，同时计算 SHA-256 并解析元数据。
`--jobs` 控制并行数，默认为逻辑 CPU 数。SOW 根据解析结果生成并检查索引。

替换索引前，SOW 再次核对包文件列表、文件身份、权限、大小和修改时间。
构建期间应停止其他程序修改包文件。文件状态发生变化时，命令停止发布并返回退出码 `5`。

相同包字节和选项生成相同元数据。如果生成文件与现有文件相同，命令报告
文本字段 `noop=true` 或 JSON 字段 `noop: true`，保留现有文件。

RPM 元数据的 revision 和 data timestamp 默认都是 `0`。更新供 EL7 YUM 使用的已有仓库时，
请设置发布时间：

```bash
sow create /srv/offline --metadata-timestamp 1791849600
```

该选项只改变 `repomd.xml`，不改变压缩 XML、包文件或 DEB 索引。时间戳应从已有仓库的值
继续递增；操作方法见 [YUM 迁移](/zh/docs/tutorial/yum-migration/)。

<span id="发布与中断语义" data-td-print-local></span>

## 构建中断

SOW 先在暂存区生成并检查元数据，再替换公开文件。这些替换不构成跨全部 RPM 和 DEB 文件
的单个事务，中断可能留下混合版本或不完整索引。

再次运行相同的 `sow create` 命令即可。它会清理自己留下的临时文件，并根据目录中当前的包
重新生成索引。Plain 模式没有操作日志恢复，JSON 字段 `recovered` 始终为 `false`。

对在线服务，在单独目录构建，成功后再把完整目录切换上线。需要记录成员关系、构建快照和
事务恢复时，使用 [Managed 模式](/zh/docs/feature/managed/)。

<span id="--pigsty-marker-门禁" data-td-print-local></span>

## Pigsty 清理与完成标记

```bash
sow create /srv/offline --pigsty
```

`--pigsty` 根据包内信息删除 DEB `i386` 包和 Patroni 3.0.4 包。
它不会仅因 RPM 架构为 `i386`、`i486`、`i586` 或 `i686` 而删除该包。

索引更新和包清理完成后，SOW 写入 `repo_complete`。每行包含 SHA-256、两个空格和保留的
包文件名，按文件名排序。

SOW 在替换公开文件前移除旧标记，最后写入新标记。采用此约定的使用方应等待标记出现。
如果构建中断且标记缺失，再次运行带 `--pigsty` 的命令。目录已有 `repo_complete` 时，
不带 `--pigsty` 的命令会拒绝重建。

<span id="显式-rpm-签名" data-td-print-local></span>

## RPM 包签名

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73
```

此选项为没有可解析内嵌签名的 RPM 签名。加上 `--overwrite` 可重签所有保留的 RPM。
签名需要主机上的 `rpm` 命令和可用 GPG 密钥。SOW 对暂存副本签名并检查，再先替换包文件、
后替换索引。这条路径会多次读取包字节。

Plain 模式不签仓库元数据。Managed 元数据签名和包签名策略见[签名](/zh/docs/feature/signing/)。

<span id="锁与适用范围" data-td-print-local></span>

## 并发命令

`sow create` 锁住目标目录及其父目录。用 `-N` 在其他 SOW 写者占锁时立即退出，
或用 `-T 30s` 最多等待 30 秒。默认等待到锁可用。

完整选项与结果字段见 [`sow create`](/zh/docs/command/create/)。

<span id="继续阅读" data-td-print-local></span>
