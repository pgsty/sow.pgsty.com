---
title: "迁移已有 YUM 仓库"
linkTitle: "迁移 YUM 仓库"
description: "将已有平面 RPM 仓库切换至 SOW，保留客户端缓存兼容性、软件包信任与发布时钟。"
categories: [Tutorial]
tags: [yum, plain, migration, signing]
url: "/zh/docs/tutorial/yum-migration/"
weight: 150
icon: fa-solid fa-arrows-rotate
---

本指南适用于 RPM 与 `repodata/` 放在同一层目录的平面仓库，例如此前用 `createrepo_c`
维护的仓库。它使用 Plain `sow create`，不创建 Managed 工作区。发布时间参数是
**SOW 0.5.0 新增功能**，请使用该版本或更新版本。

## 1. 明确迁移范围

在候选副本上操作，并完整保留旧软件包与元数据备份。可能重签的 RPM 不要用硬链接复制。
先确认真正使用的二进制：

```bash
SOW=/path/to/sow
"$SOW" version
"$SOW" create --help
```

帮助中必须包含 `--metadata-timestamp`；正式版 0.4.0 不接受该参数。

| 检查项 | 需要明确的选择 |
|---|---|
| 软件包布局 | Plain 只读取顶层普通 RPM；嵌套目录需要单独规划迁移 |
| 客户端功能 | Plain 生成 primary/filelists/other XML，不生成 SQLite 数据库或模块流 |
| 包信任 | 保留合法上游签名，或明确换成自己的密钥 |
| 索引信任 | 客户端启用 `repo_gpgcheck=1` 时，单独签署并验证新 `repomd.xml` |
| 已有客户端 | 保留旧缓存，使用原来的 URL 和 repo ID 验收 |

在存在模块过滤的环境中，为普通 RPM 保留适当的 `module_hotfixes=1` 策略。这不会恢复
`dnf module install` 所需的模块流或 profile。

## 2. 保留发布时间历史

EL7 YUM 可能拒收 data 最大时间早于缓存的索引。检查当前 `repomd.xml` 与可信旧副本中的
`<data><timestamp>`，取客户端可能见过的最大值。如果在线索引此前已被写成零，只看这个
零值无法恢复历史。revision 和文件 mtime 不能替代该记录。

维护脚本应在同一个仓库锁内操作，并在上传目录外保存历史最大发布时间。真正产生新一代内容时，
选择：

```text
下一次时间 = max(当前 Unix 秒,
                 当前索引最大时间 + 1,
                 已保存的历史最大时间 + 1,
                 可信历史下限 + 1)
```

在切换公开索引之前持久保存该值。发布失败可以消耗一个时间值，跳号没有问题。恢复旧内容，或把
同一公开 URL 对应的本地目录移到新位置时，也必须保留这份时钟。

内容不变时，维护脚本可以在检查完整元数据内容身份、引用文件校验和以及签名后，复用旧索引与
分离签名。零时间或已经倒退的时间仍需修复。每次直接调用 `create` 都传入当前时间，会让索引
每次变化，从而失去空跑不写文件的效果。

## 3. 构建并签署候选

下面演示一次重建。先准备独立的 `/srv/yum.candidate` 副本，将 `HISTORICAL_MAX` 设为从当前
索引、持久时钟和可信历史中核实的最大值，将 `SIGN_KEY` 设为元数据签名密钥的完整指纹。
示例用 Python 3 选择严格递增的时间：

```bash
set -euo pipefail
: "${SOW:?Set the path to the tested SOW binary}"
: "${HISTORICAL_MAX:?Set the verified historical maximum Unix second}"
: "${SIGN_KEY:?Set the full metadata signing fingerprint}"
PUBLISH_TIME=$(python3 -c 'import sys,time; h=int(sys.argv[1]); assert 0 <= h < 9223372036854775807; print(max(int(time.time()), h+1))' "$HISTORICAL_MAX")

"$SOW" create /srv/yum.candidate --metadata-timestamp "$PUBLISH_TIME"
gpg --batch --yes --armor --detach-sign --local-user "$SIGN_KEY" \
  --output /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
gpg --verify /srv/yum.candidate/repodata/repomd.xml.asc \
  /srv/yum.candidate/repodata/repomd.xml
```

这段命令只生成候选，不会保存持久时钟或发布目录。切换线上内容前，还要由维护系统持久记录
`PUBLISH_TIME`。验签应绑定预期公钥，不能只判断大信任库里是否存在某把可用公钥。

`--sign-with KEY` 只为未签名 RPM 补签；已经签名的包会保留原字节，包括其他供应商签署的包。
如果策略要求每个 RPM 都由自己的密钥签署，应逐包验证目标密钥，并只在候选中重签不满足要求的
包。`--overwrite` 是显式的批量替代方案：它重签所有保留 RPM，改变包字节，因此必须根据最终
包字节重建索引。最后一次 `create` 完成后，始终重新生成对应的索引分离签名。

## 4. 切换前验收

对候选与预期服务端点检查以下事项：

1. 三类 XML 与 RPM 集合对应，引用文件校验和正确。若只改变发布时间，RPM 与压缩 XML 应保持
   逐字节一致。
2. 每个软件包与索引签名都满足预期客户端信任策略。
3. 包字节、选项和时间戳相同时，重复构建元数据应为空操作；此项检查不要强制重签包。维护脚本还应
   保留旧的有效分离签名，避免重新签名。
4. 带旧缓存的客户端接受新索引，并实际下载、验证软件包。这个测试保留原 URL、repo ID 与缓存。
5. 第二次真实内容更新使用更晚的时间，同一客户端仍能接受。需要确认安装行为时，在可丢弃主机上
   使用生产中的确切客户端补做安装测试。

对已有签名仓库，验收全程保留 `gpgcheck=1` 与 `repo_gpgcheck=1`。清缓存或关闭验签，会绕过
本来需要测试的行为。与旧 createrepo_c 比较时，应核对依赖含义，而非要求 XML 逐字节一致；
相关规则见[平台与集成](/zh/docs/reference/compatibility/)。

## 5. 发布与恢复资料保留

Plain 会替换多个文件，不提供整个目录的原子切换。发布层需要协调包文件、索引、分离签名以及
缓存的可见顺序。仍可能被缓存客户端请求的旧元数据文件应继续保留；直接运行 Plain 重建，可能
删除目录中不再引用的 SOW checksum 命名元数据。

保留原始备份与持久时钟。回滚软件包内容时，把它当成更晚的一次发布重新建库、签名。只恢复旧
`repomd.xml`、却搭配已经改变的 RPM，会重新引入校验和或时间戳问题。

Managed 的 `sow check` 不用于审计 Plain 目录。这里的验收依据是上述检查与真实 YUM/DNF
客户端。精确命令契约见 [`sow create`](/zh/docs/command/create/)，两层签名的区别见
[仓库签名](/zh/docs/tutorial/signing/)。
