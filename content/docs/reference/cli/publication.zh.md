---
title: "发布、保留、GC 与导出"
linkTitle: "发布与生命周期"
description: "发布目标、保留代、保守垃圾回收与 RPM leaf 导出的命令参考。"
url: "/zh/docs/reference/cli/publication/"
weight: 950
icon: fa-solid fa-cloud-arrow-up
---

这些命令覆盖 v0.2.0 的交付生命周期。`publish`、目标 GC 与目标选择使用 `sow.yml`
中的 `targets:`;本地保留与 GC 作用于选定 Repository。`export rpm-leaf` 生成独立兼容产物。

## sow publish

```text
sow publish TARGET [--abort] [-C DIR] [-T DUR | -N] [--json]
```

把 `TARGET` 绑定 Repository 的当前已验证 Generation 发布出去。SOW 依次应用不可变包体、
校验和寻址元数据、可变指针,最后验证并记录 checkpoint。目标已经是当前代时为幂等 no-op。

```bash
sow publish prod
```

`--abort` 只在耐久 commit intent 之前可用。它会核对可能已经创建的精确对象,保留该证据,
并在不复制或删除远端对象的情况下放弃尝试。commit intent 之后只能前滚:重新运行普通 publish。

`publish` 由 target 选择 Repository,因此不接受 `--repo` 或 `--dist`。

## sow retain

```text
sow retain add GENERATION [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow retain ls             [-C DIR] [-r NAME] [--json]
sow retain rm GENERATION  [-C DIR] [-r NAME] [-T DUR | -N] [--json]
```

`retain add` 校验并冻结 Generation manifest 与元数据,作为包体的显式 GC 根。
`retain ls` 只读。`retain rm` 移除显式根,不会直接删除包字节。Generation 参数必须是
大于零的十进制整数。

## sow gc

```text
sow gc          [-C DIR] [-r NAME] [-T DUR | -N] [--json]
sow gc TARGET   [-C DIR]           [-T DUR | -N] [--json]
```

不带目标时,GC 只删除当前 Generation 以及所有保留、迁移、恢复、发布根都不可达的本地 pool
对象。删除操作写 journal;真正移除字节时会推进 Repository Generation。

带 `TARGET` 时维护发布状态:

| Provider | 行为 |
|---|---|
| `filesystem` | 只有经过缓存宽限期并记录存储/公共缺失检查后,才条件式删除合格对象 |
| `r2` | 记录精确的 report-only 候选集合;绝不发送对象删除 |

目标会选定 Repository,所以 `sow gc TARGET -r NAME` 是用法错误。

## sow export rpm-leaf

```text
sow export rpm-leaf DIST ARCH DIR [--hardlink] [-C DIR] [-r NAME] [--json]
```

把一个已构建 RPM Dist 架构导出成使用本地 `pool/...` href 的自包含仓库。`ARCH` 只能是
`x86_64` 或 `aarch64`。默认复制;`--hardlink` 是同文件系统、可信只读导出的显式优化。

```bash
sow export rpm-leaf el9 x86_64 /srv/export/el9-x86_64
```

目录包含改写后的 repodata、包体树、manifest 与 `.sow-export.json`。导出不是 Membership、
Generation、发布输入或 GC 根;SOW 也会拒绝与已配置 filesystem 发布根重叠的输出。

## 通用参数

| 参数 | 含义 |
|---|---|
| `-C, --workdir DIR` | 工作区发现起点 |
| `-r, --repo NAME` | 在支持处选择 Repository |
| `-T, --timeout DUR` | 最长写锁等待;`0` 无限等待 |
| `-N, --no-wait` | 写锁被占用时立即失败 |
| `--json` | 输出 `sow.cli/v1` envelope |

## 延伸阅读

- [`sow.yml` 发布目标](/zh/docs/reference/config/#发布目标)
- [发布模型](/zh/docs/design/publication/)
- [仓库布局](/zh/docs/reference/layout/)
