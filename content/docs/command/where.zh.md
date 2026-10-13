---
title: "sow where"
linkTitle: "where"
description: "在工作区中查找一个软件包。"
categories: [Command]
tags: [cli, managed]
url: "/zh/docs/command/where/"
weight: 1000
icon: fa-solid fa-location-dot
---

`sow where` 在工作区中查找一个软件包的期望成员位置。默认搜索全部仓库；使用 `-r` 或 `-d` 限定范围。

## 语法

```text
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

| 参数 | 含义 | 默认值 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现起点 | 当前目录 |
| `-r, --repo NAME` | 将搜索限制到一个仓库 | 全部仓库 |
| `-d, --dist NAME` | 将搜索限制到指定 Dist；可重复 | 全部 Dist |
| `--json` | 输出 JSON | false |

## 引用解析

`PACKAGE` 与 [`sow show`](/zh/docs/command/show/) 使用相同格式：SHA-256、规范 RPM/DEB 坐标、
完整文件名或裸包名。

引用必须确定一个软件包，即格式、坐标和 SHA-256 均相同的包。同一个包可以位于多个仓库。如果匹配到不同的包，使用 `-r` 或 `-d` 收窄范围，或提供精确坐标、SHA-256。

## 输出

不带 `--json` 时，`where` 先输出摘要，再为每个位置输出一行：

```console
sow where 'rpm:centos-release-0:6-0.el6.centos.5.x86_64'
reference="rpm:centos-release-0:6-0.el6.centos.5.x86_64" locations=1
repository=demo coordinate="rpm:centos-release-0:6-0.el6.centos.5.x86_64" sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16 dists=el9 built_dists=el9
```

每个位置同时给出该仓库内的期望位置 `dists` 与已构建位置 `built_dists`。查找候选包时使用期望成员集。如果包已从全部所选 Dist 中移除，命令将不再找到它，即使旧索引仍包含它。要查看这样的已存储对象，使用 `sow show PACKAGE -r NAME`，不要加 `-d`。

加上 `--json` 后，位置列表位于 `result.locations`。没有匹配包时，命令返回错误：

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## 示例

列出期望状态中包含此包的 Dist：

```bash
sow where 'rpm:patroni-0:3.0.4-1.noarch' --json |
  jq -r '.result.locations[] | "\(.repository)/\(.dists | join(","))"'
```

## 退出码

| 代码 | 触发条件 |
|---|---|
| `0` | 已输出一个解析后的软件包对象及其位置 |
| `1` | 运行时 I/O 错误 |
| `2` | 用法错误或未发现工作区 |
| `5` | 某个仓库状态库不可读或不一致 |
| `6` | 显式仓库/Dist 未配置，或引用没有匹配/在所选范围内有歧义 |

## 参见

- [`sow show`](/zh/docs/command/show/) —— 查看解析后的软件包对象
- [`sow ls`](/zh/docs/command/ls/) —— 列出一个 Dist 集合
- [包引用](/zh/docs/reference/package-ref/) —— 完整格式与匹配规则
