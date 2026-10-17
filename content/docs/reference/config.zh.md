---
title: "sow.yml 配置参考"
linkTitle: "配置参考"
description: "工作区配置字段、默认值、校验规则、签名引用与发布目标。"
categories: [Reference]
tags: [config, managed]
url: "/zh/docs/reference/config/"
weight: 200
icon: fa-solid fa-file-code
---

`sow.yml` 配置 Managed 工作区，声明仓库、Dist、包策略、签名与发布目标。
Plain 命令 `sow create` 不读取此文件。

编辑后，检查配置并查看实际生效的设置：

```bash
sow config check
sow config show --all
```

`config check` 校验 YAML、比较配置与已初始化的仓库状态，并解析签名引用。
`config show --all` 展开默认值。

<span id="文件是怎么读的" data-td-print-local></span>

## 文件规则

- 使用一个 YAML 文档，配置 `schema: sow/v3`。
- 未知字段和重复键都是错误。
- 文件放在工作区根目录，必须是只有一个硬链接的普通文件，大小不超过 16 MiB。
  不接受符号链接。
- `init`、`repo new/rm`、`dist new/rm` 在执行相应操作时更新此文件。
- 策略、签名和目标设置直接编辑文件。读取时应用默认值，不改写源文件。

旧仓库数据库或目录布局的升级方法见 [`repo migrate`](/zh/docs/command/repo/#sow-repo-migrate)。

<span id="根级字段" data-td-print-local></span>
<span id="architectures" data-td-print-local></span>
<span id="完整示例" data-td-print-local></span>

## 工作区

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos: {}
targets: {}
```

| 字段 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `schema` | 字符串 | 必填 | 必须为 `sow/v3` |
| `architectures` | 字符串列表 | `[x86_64, aarch64]` | 工作区允许的架构族 |
| `repos` | 映射 | 空 | 仓库名称和设置 |
| `targets` | 映射 | 空 | 发布目标名称和设置 |

架构别名按下表规范化：

| 输入 | 规范架构族 |
|---|---|
| `x86_64`、`amd64` | `x86_64` |
| `aarch64`、`arm64` | `aarch64` |

显式架构列表不能为空，规范化后不能有重复族。`noarch` 和 `all` 是包架构，
不能写入配置架构列表；SOW 会将这些架构无关包加入各个适用视图。

<span id="repository-仓库" data-td-print-local></span>
<span id="protected" data-td-print-local></span>
<span id="名称约束" data-td-print-local></span>

## 仓库

```yaml
repos:
  demo:
    protected: false
    signing: {}
    dists:
      el9:
        format: rpm
```

| 字段 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `protected` | 布尔值 | `false` | 阻止 `repo rm`，包括带 `-f` 的调用 |
| `signing` | 映射 | 元数据不签名；包模式为 `never` | 仓库签名设置 |
| `dists` | 映射 | 空 | Dist 名称和设置 |

`protected` 不阻止包变更或 Dist 删除。要删除受保护仓库，先设为 `false`，
检查配置，再运行 `repo rm`。

仓库、Dist 和目标名称必须匹配 `[a-z0-9][a-z0-9._-]*`。
保留名称为 `.`、`..`、`.sow`、`pool`、`dists`、`sow.yml`、`workspace.lock`、
`workspace-ops`、`repo-locks`。仓库的私有状态路径也不能冲突，例如 `db` 与 `db.db` 不能共存。

<span id="format" data-td-print-local></span>
<span id="architectures-1" data-td-print-local></span>
<span id="limit" data-td-print-local></span>

## Dist

```yaml
dists:
  el9:
    format: rpm
    architectures: [x86_64]
    limit: 2
    exclude:
      - kind: [debuginfo, debugsource, llvmjit]
```

| 字段 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `format` | 字符串 | 必填 | `rpm` 或 `deb`，初始化后不可改变 |
| `architectures` | 字符串列表 | 工作区列表 | 工作区架构族的非空子集 |
| `limit` | 整数 | `0` | 每个二进制包名、规范架构分组保留的最新版本数；`0` 为全部保留 |
| `exclude` | 规则列表 | 空 | 包排除规则 |

增加架构会使 Dist 变脏，运行 `build` 生成视图。
成员关系或构建状态仍引用某个架构时，不能移除该架构。

`limit` 不能为负数。RPM 使用 epoch-version-release 排序，DEB 使用 Debian 版本排序。
架构无关包单独成组。放宽策略不会恢复已移除成员，需要重新加入包文件。

<span id="exclude" data-td-print-local></span>

### 排除规则

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

规则内字段按 AND 组合，字段内模式按 OR 组合，规则之间按 OR 组合。
每个所选 Dist 的完整候选成员集合先执行 `exclude`，再执行 `limit`。

| 字段 | 匹配对象 |
|---|---|
| `name` | 二进制包名 |
| `source` | 规范化的 RPM `SOURCERPM` 或 DEB `Source` 名称 |
| `arch` | `x86_64`、`aarch64` 或 `neutral` |
| `kind` | RPM：`debuginfo`、`debugsource`、`llvmjit`；DEB：`dbgsym`、`dbg`；其他为 `main` |
| `format` | `rpm` 或 `deb` |

模式区分大小写，支持精确字符串或 shell 通配符（`*`、`?`、`[...]`）。
空规则、空模式、首尾空白、同字段重复模式和非法通配符都会报错。
模式值不会按可能的包属性值校验，拼错的值可能匹配不到任何包。
`kind` 由对应的包名后缀确定。

示例和结果解释见[成员策略](/zh/docs/feature/policy/)。

## 签名

签名设置属于仓库。RPM 包、RPM 元数据、DEB 元数据分别配置：

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      trusted_keys: [keys/upstream.asc]
    metadata:
      key: keys/repo-signing.asc
      passphrase: env://SOW_METADATA_PASSPHRASE
  deb:
    metadata:
      key: keys/repo-signing.asc
      passphrase: env://SOW_METADATA_PASSPHRASE
```

<span id="rpmpackages" data-td-print-local></span>

### RPM 包设置

| `rpm.packages` 字段 | 默认值 | 含义 |
|---|---|---|
| `mode` | 无密钥时 `never`，有密钥时 `fill` | `never`、`fill` 或 `always` |
| `key` | 无 | 签名密钥引用，`fill`、`always` 必填 |
| `trusted_keys` | 空 | `fill` 接受的额外公钥引用 |

`never` 保留输入字节；`fill` 保留可由当前密钥或受信密钥验证的包，其余包签名；
`always` 要求当前密钥，必要时重签。`key` 的公钥部分自动受信。
重复的受信密钥引用字符串会被拒绝。

包签名对暂存副本调用主机 `rpm` 命令，其 GPG 环境中必须已有对应私钥。
仅配置一个密钥文件不会为该环境导入私钥。

<span id="rpmmetadata-与-debmetadata" data-td-print-local></span>

### 元数据设置

`rpm.metadata` 与 `deb.metadata` 都接受：

| 字段 | 默认值 | 含义 |
|---|---|---|
| `key` | 无 | 元数据签名密钥引用 |
| `passphrase` | 无 | 加密密钥的口令引用 |

RPM 签名生成 `repodata/repomd.xml.asc`，DEB 签名生成 `InRelease`、`Release.gpg`。
没有密钥时索引不签名。DEB 包文件不会被重签。

<span id="key-引用文法" data-td-print-local></span>

### 密钥引用

| 形式 | 示例 | 内容 |
|---|---|---|
| 路径 | `keys/repo.asc` | OpenPGP 密钥文件；相对路径从工作区根开始 |
| `file://` | `file:///secure/repo.asc` | OpenPGP 密钥文件 |
| `env://` | `env://SOW_METADATA_KEY` | 环境变量保存 ASCII 装甲格式密钥、文件路径或 GPG 密钥标识 |
| `agent://` | `agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B` | 本地 GPG 环境中的密钥 |

环境变量名称使用 `[A-Za-z_][A-Za-z0-9_]*`。GPG 密钥标识可以是 16 位 key ID，
或 40、64 位指纹，十六进制字母不区分大小写。

密钥文件支持 ASCII 装甲格式和二进制 OpenPGP 数据，必须是不经过符号链接的普通文件，
大小不超过 16 MiB。相对路径从工作区根开始解析。
提供私钥内容时，元数据签名在 SOW 进程内完成；引用解析为 GPG 密钥标识时，调用外部 `gpg`，
无论该标识来自 `agent://` 还是环境变量。

签名 `key` 引用必须解析为一个主密钥。
`trusted_keys` 文件可以包含多个完整公钥，包括连续的 ASCII 装甲块。
SOW 读取整个密钥集合，拒绝格式错误或被截断的输入，不会仅使用第一个密钥而忽略后续内容。

### Passphrase 引用

口令接受路径、`file://`、`env://` 引用，配合私钥内容使用。引用解析为 GPG 密钥标识时，
由 GPG 处理口令。口令值必须非空、不含 NUL 字节，且不超过 64 KiB。
SOW 移除末尾的一个换行符，包括 CRLF。口令文件采用与密钥文件相同的路径规则。

引用语法错误返回 `2`，签名引用无法解析或不可用时返回 `6`。

不带 `--all` 时，`config show` 也可能显示 `key_fingerprint`。
启用的 RPM 包签名设置还可能显示 `key_snapshot_sha256`、`trusted_key_fingerprints` 和
`trusted_key_snapshot_sha256s`。指纹与快照数组各自排序，不能按下标配对。
这些是公钥身份的输出字段，不是 `sow.yml` 接受的配置键。

密钥轮换和包复用见[签名](/zh/docs/feature/signing/)。

<span id="发布目标" data-td-print-local></span>

## 发布目标 {#publication-targets}

```yaml
targets:
  mirror:
    repository: demo
    provider: filesystem
    endpoint: file:///srv/mirror
    prefix: demo
    public_endpoint: file:///srv/mirror/demo/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

| 字段 | 是否必填 | 含义 |
|---|---|---|
| `repository` | 是 | 已有仓库名称 |
| `provider` | 是 | `filesystem` 或 `r2` |
| `endpoint` | 是 | 无尾部斜杠的规范 `file:///absolute/path`，R2 使用 `https://host` |
| `region` | 仅 R2 | 必须为 `auto`，filesystem 禁止 |
| `bucket` | 仅 R2 | 小写、符合 DNS 标签规则的桶名，filesystem 禁止 |
| `prefix` | 否 | 相对存储前缀，空值使用存储命名空间根 |
| `credential` | 仅 R2 | `env://NAME` 或 `file:///absolute/path`，filesystem 禁止 |
| `public_endpoint` | 是 | 以 `/` 结尾的规范验证 URL；filesystem 接受 HTTP(S) 或 `file://`，R2 接受 HTTP(S) |
| `max_cache_ttl` | 是 | 规范的非负 Go duration，零值也要显式写 `0s` |
| `authoritative_workspace` | 是 | 必须为 `true` |
| `single_writer` | 是 | 必须为 `true` |
| `exclusive_write_authority` | 是 | 必须为 `true` |

最后三个字段声明此工作区负责发布，并且是目标命名空间的唯一写者。
同一存储上的目标前缀不能重叠，filesystem 目标也不能指向重叠目录。

使用规范时长，如 `0s`、`30m0s`、`24h0m0s`；`24h` 会被拒绝。
时长上限低于 Go 最大 duration，为缓存宽限期预留空间。
该值应覆盖公开服务使用的最长缓存寿命。

发布前先创建 filesystem endpoint 目录。它必须是真实的规范目录，不能是符号链接。
SOW 在其下创建 prefix。

R2 目标增加存储与凭据字段：

```yaml
targets:
  prod:
    repository: demo
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: demo
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/demo/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

被引用的环境变量或文件应包含一个 JSON 文档：

```json
{"access_key_id":"YOUR_ACCESS_KEY_ID","secret_access_key":"YOUR_SECRET_ACCESS_KEY"}
```

还可包含 `session_token`。未知字段、多余尾部数据、缺失凭据或超过 64 KiB 的内容都会被拒绝。
凭据文件必须解析为普通文件，允许指向普通文件的符号链接。
凭据不会写入公开目录或配置输出。

首次发布绑定仓库、Provider、存储身份和前缀。修改目标名称、`public_endpoint` 或
`max_cache_ttl` 时，使用
[`publish --rebind`](/zh/docs/command/publish/)。
Provider、endpoint、region、bucket、prefix 和仓库身份不能重新绑定，应配置新目标。
待完成的维护操作可能阻止修改缓存 TTL 或公开 endpoint，需先完成维护。

<span id="sowyml-里没有什么" data-td-print-local></span>

## 固定设置

仓库路径固定为 `<workspace>/<name>`，APT component 固定为 `main`。
架构视图由 Dist 配置与包内信息派生。构建快照保留使用
[`retain`](/zh/docs/command/retain/) 管理，不在配置中设置保留数量。

继续阅读[布局](/zh/docs/reference/layout/)、[发布](/zh/docs/command/publish/)和
[退出码](/zh/docs/reference/exit-codes/)。

<span id="延伸阅读" data-td-print-local></span>
