---
title: "sow ls / show / where"
linkTitle: "ls / show / where"
description: "三条只读查询：列出 Dist 的成员、查看单个包对象、在整个工作区中定位一个包。"
url: "/zh/docs/reference/cli/query/"
weight: 800
icon: fa-solid fa-magnifying-glass
---

三条命令回答三个不同的问题。`ls` 列出一个 Dist 应该包含什么，`show` 详细查看某一个包对象，`where`
找出哪些 Dist（跨仓库）在提供某个包。三者都是只读的，不取写锁，共用同一套 `--json` envelope。

## 语法

```text
sow ls [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow show PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
sow where PACKAGE [-C|--workdir DIR] [-r|--repo NAME] [-d|--dist NAME]... [--json]
```

## 公共参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `-C, --workdir DIR` | 工作区发现的起始目录 | 当前目录 |
| `-r, --repo NAME` | 选择一个仓库 | 按选择规则 |
| `-d, --dist NAME` | 选择一个 Dist；可重复 | 按选择规则 |
| `--json` | 输出版本化 JSON envelope | false |

没有 `--pool`、没有 `--match`，也没有各自的 format 参数。

## sow ls

列出选定 Dist 的期望成员集。

```console
sow ls -r pigsty -d el9
repository=pigsty dists=el9 dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16	rpm:centos-release-0:6-0.el6.centos.5.x86_64	el9	el9	pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead	rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64	el9	el9	pool/c/centos-release/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
sha256:d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab	rpm:epel-release-0:7-5.noarch	el9	el9	pool/e/epel-release/epel-release-7-5.noarch.rpm
```

`SHA256` 与 `COORDINATE` 两列就是精确引用，可以直接粘进
[`sow rm`](/zh/docs/reference/cli/rm/) 或 `sow show`。

### Desired 与 Built

`DISTS` 是期望成员，`BUILT_DISTS` 是当前已构建代实际包含的内容。仓库 dirty 时表头会指出这一点，
逐行也能看到差异——`BUILT_DISTS` 为空表示客户端还看不到这个包：

```console
sow ls -r demo
repository=demo dists=el9 dirty=true
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:ffd9e7bdaa4884831a6c055ada01dac96b84c50a8d518dac409b445af5dadc16	rpm:centos-release-0:6-0.el6.centos.5.x86_64	el9		pool/c/centos-release/centos-release-6-0.el6.centos.5.x86_64.rpm
sha256:b4111ef2a51542eacc9bd1ebd080da02e53d400f9d172530c75a1e4ac06e7ead	rpm:centos-release-0:7-2.1511.el7.centos.2.10.x86_64	el9	el9	pool/c/centos-release/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
```

### 必须明确 Dist

`ls` 需要一个无歧义的 Dist 集合。在多 Dist 仓库里，要么给 `-d`，要么在
`<repo>/dists/<dist>/` 目录下执行：

```console
sow ls -r pigsty
workspace discovery error: managed: workspace discovery or configuration error: repository "pigsty" has multiple Dists (el9, trixie); select one or more with --dist
```

属于多个 Dist 的对象会把它们全部列出，这是查看跨 Dist 共享最快的方式：

```console
sow ls -r pgsql -d trixielim
repository=pgsql dists=trixielim dirty=false
SHA256	COORDINATE	DISTS	BUILT_DISTS	POOL_PATH
sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c	deb:libpq5=18.3-1:amd64	trixie,trixielim	trixie,trixielim	pool/p/postgresql-18/libpq5_18.3-1_amd64.deb
sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c	deb:libpq5=18.3-1:arm64	trixie,trixielim	trixie,trixielim	pool/p/postgresql-18/libpq5_18.3-1_arm64.deb
sha256:f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3	deb:pg-sample=1.17-1:all	trixie,trixielim	trixie,trixielim	pool/p/pg-sample/pg-sample_1.17-1_all.deb
```

## sow show

完整打印一个 Package Object：坐标、内容哈希、规范化事实、pool 路径、签名身份与成员关系。由于没有
紧凑的表格形态，`show` 即使不加 `--json` 也在 stdout 打印 JSON。

```console
sow show 'rpm:epel-release-0:7-5.noarch' -r pigsty -d el9
{"repository":"pigsty","package":{"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","format":"rpm","coordinate":"epel-release-0:7-5.noarch","architecture":"noarch","canonical_arch":"neutral","pool_path":"pool/e/epel-release/epel-release-7-5.noarch.rpm","filename":"epel-release-7-5.noarch.rpm","size":14524,"name":"epel-release","source":"epel-release","version":"7","epoch":"0","release":"5","kind":"main","payload_sha256":"94b51b9827b4238f8aecbff8da45fa833998f8589c15316376d52201304e0136","signature_key":"24C6A8A7F4A80EB5","storage":"pool","created_revision":3,"dists":["el9"],"built_dists":["el9"]}}
```

值得记住的字段：

| 字段 | 含义 |
|---|---|
| `canonical_arch` | `x86_64`、`aarch64`，或 RPM `noarch` / DEB `all` 对应的 `neutral` |
| `kind` | 由二进制包名推导的策略分类：`main`、`debuginfo`、`debugsource`、`llvmjit`、`dbgsym`、`dbg` |
| `source` | 规范化 source 名——RPM 取 `SOURCERPM`，DEB 取 `Source`，缺失时回落到二进制包名 |
| `payload_sha256` | 仅 RPM：用于重签幂等的 signature-neutral digest |
| `signature_key` | 包内嵌签名的 key ID（如果有签名） |
| `storage` | 已发布为 `pool`；pending 对象仍在私有存储中 |

`show` 默认在选定仓库内查找。`-d` 只收窄候选集，不改变身份的定义。加 `--json` 时同一个对象出现在
标准 envelope 内：

```console
sow show 'deb:pg-sample=1.17-1:all' -r pgsql -d trixie --json
{"schema":"sow.cli/v1","command":"show","ok":true,"repository":"pgsql","operation":null,"result":{"repository":"pgsql","package":{"sha256":"f23581c5164a143e5e902232589adf1d30b73ba3857a692a11da607f246aacc3","format":"deb","coordinate":"pg-sample=1.17-1:all","architecture":"all","canonical_arch":"neutral","pool_path":"pool/p/pg-sample/pg-sample_1.17-1_all.deb","filename":"pg-sample_1.17-1_all.deb","size":566,"name":"pg-sample","source":"pg-sample","version":"1.17-1","kind":"main","storage":"pool","created_revision":4,"dists":["trixie"],"built_dists":["trixie"]}},"errors":[]}
```

### show 的裸名必须唯一

这是 `show` 与 `rm` 唯一的语义分歧。`rm foo` 意为"foo 的所有版本"；`show foo` 意为"叫 foo 的那一个
对象"，不满足唯一性时会列出候选并失败：

```console
sow show libpq5 -r pgsql -d trixie
operation rejected: managed: operation rejected: package reference "libpq5" is ambiguous: deb:libpq5=18.2-1:amd64 sha256:fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41, deb:libpq5=18.3-1:amd64 sha256:491992c502113627d44d0d66a2b189cdaa8accff293ebaf84fe10ccbc9da574c, deb:libpq5=18.3-1:arm64 sha256:3a2f7ef7cddfa3dc06280ef59eda1dab9724d57499931ee80758b11531c1f40c
```

复制其中一个坐标重跑即可。`where` 遵循同样的规则。

## sow where

在*整个*工作区——所有仓库，而不只是选定的那个——定位一个引用。它回答的是"我哪个 Dist 还在发这个
包"。

```console
sow where epel-release
{"reference":"epel-release","locations":[{"repository":"pigsty","dists":["el9"],"built_dists":["el9"],"sha256":"d6f332ed157de1d42058ec785b392a1cc4b5836c27830af8fbf083cce29ef0ab","coordinate":"rpm:epel-release-0:7-5.noarch"}]}
```

`-r` 与 `-d` 用于收窄搜索。加 `--json`：

```console
sow where 'deb:libpq5=18.2-1:amd64' --json
{"schema":"sow.cli/v1","command":"where","ok":true,"repository":null,"operation":null,"result":{"reference":"deb:libpq5=18.2-1:amd64","locations":[{"repository":"pigsty","dists":["trixie"],"built_dists":["trixie"],"sha256":"fa84dc641b7c686be2f9b512311ad0b74eac03e2afc9eff7e9af75b82b68ff41","coordinate":"deb:libpq5=18.2-1:amd64"}]},"errors":[]}
```

查不到属于拒绝，因此这条命令可以直接当脚本里的门禁用：

```console
sow where nosuchpkg
operation rejected: managed: operation rejected: package reference "nosuchpkg" was not found in the selected Workspace scope
```

## 引用文法

`show` 与 `where` 接受与 `rm` 相同的引用：`sha256:<hex>`、`rpm:<NEVRA>`、
`deb:<name>=<version>:<arch>`、完整文件名，或裸二进制包名。不带 `rpm:` 前缀的 NEVRA 不匹配。完整
规则见[包引用](/zh/docs/reference/package-ref/)。

## 示例

按 pool 路径排序审计一个 Dist 会交付什么：

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[].pool_path' | sort
```

找出所有还在等待构建的包：

```bash
sow ls -r pgsql -d el9 --json | jq -r '.result.packages[] | select(.built_dists | length == 0) | .coordinate'
```

检查受 CVE 影响的构建是否还在某处发布：

```bash
sow where 'rpm:patroni-0:3.0.4-1.noarch' --json | jq -r '.result.locations[] | "\(.repository)/\(.dists|join(","))"'
```

## 退出码

| 码 | 触发条件 |
|---|---|
| `0` | 结果已打印，包括空成员列表 |
| `1` | 读取状态时的运行时 I/O 错误 |
| `2` | 用法错误、工作区未找到，或仓库/Dist 选择有歧义 |
| `5` | 状态数据库无法读取或解析 |
| `6` | 引用无匹配，或裸名匹配到多个对象 |

## 参见

- [包引用](/zh/docs/reference/package-ref/) —— 五种引用形态与歧义规则
- [sow rm](/zh/docs/reference/cli/rm/) —— `ls` 输出的引用通常用在这里
- [sow status / check](/zh/docs/reference/cli/build/) —— 仓库级状态而非逐包信息
- [包池与架构视图](/zh/docs/feature/views/) —— `pool_path` 如何映射到客户端可见视图
- [JSON 输出](/zh/docs/reference/json/) —— 完整 result 结构
