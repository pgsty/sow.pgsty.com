---
title: "sow.yml 配置参考"
linkTitle: "配置参考"
description: "工作区配置文件的全部字段、校验规则,以及一份完整可用的示例。"
categories: [Reference]
tags: [config, managed]
url: "/zh/docs/reference/config/"
weight: 200
icon: fa-solid fa-file-code
---

`sow.yml` 是 Managed 托管工作区(Workspace)唯一的配置文件。它位于工作区根目录,
声明存在哪些仓库(Repository)与 Dist,并保存每次构建都要执行的成员策略与签名设置。
Plain 平面模式(`sow create`)完全不读它。

本页列出解析器接受的每一个字段。**没有列在这里的字段一律拒绝** —— 不存在未公开的
键,也没有为将来预留的键。

## 文件是怎么读的

SOW 用严格 YAML 解析器读取 `sow.yml`。具体表现是:

- **未知字段是错误,不是警告。** 把 `repos:` 写成 `repositories:` 会直接失败(退出码 `2`),
  并指出出问题的行号。
- **只允许一个 YAML 文档。** 用 `---` 引入第二个文档会报错。
- **只接受普通文件。** `sow.yml` 是符号链接,或者大于 16 MiB,在解析前就被拒绝。
- **默认值在解析时补齐,不写回磁盘。** 想看完全展开后的形态,用 `sow config show --all`。

文件的一部分是机器维护的:`sow init`、`sow repo new`、`sow repo rm`、`sow dist new`、
`sow dist rm` 会作为各自事务的一部分原子改写 `sow.yml`。成员策略与签名则由你手工编辑 ——
没有对应的命令行参数。

任何手工修改之后,跑一次 `sow config check`。它解析文件、与每个已初始化仓库的 SQLite
状态交叉核对、并解析每一个签名 key 引用,全程只读:

```bash
sow config check
```

```console
configuration valid: /srv/repo repositories=1 dists=2
```

## 根级字段

```yaml
schema: sow/v3
architectures: [x86_64, aarch64]
repos:
  <name>: <repository>
targets:
  <name>: <publication-target>
```

| 字段 | 类型 | 必填 | 默认值 | 含义 |
|---|---|---|---|---|
| `schema` | string | 是 | — | 必须恰好是 `sow/v3`,其他值一律是配置错误。 |
| `architectures` | 字符串列表 | 否 | `[x86_64, aarch64]` | 本工作区允许管理的 CPU 架构族。 |
| `repos` | map | 否 | 空 | 仓库名到仓库配置的映射。 |
| `targets` | map | 否 | 空 | 发布目标名到目标配置的映射。 |

`schema` 配置值必须恰好是 `sow/v3`。

### architectures

这是 **上限**,不是目标。它声明 SOW 最多可以接纳哪些架构;各 Dist 默认继承整张表,
除非自己再收窄。

目前只支持两个规范族(canonical family):`x86_64` 与 `aarch64`。DEB 生态名作为输入别名
被接受,并在解析边界规范化:

| 你可以写 | 存储与展示为 |
|---|---|
| `x86_64`、`amd64` | `x86_64` |
| `aarch64`、`arm64` | `aarch64` |

所以 `architectures: [amd64, arm64]` 与 `architectures: [x86_64, aarch64]` 是同一份配置。
把同一族的两个别名都写上 —— `[amd64, x86_64]` —— 属于重复,会失败:

```console
configuration error: load config "/srv/repo/sow.yml": workspace architectures: duplicate architecture "x86_64" after normalization
```

`noarch`(RPM)与 `all`(DEB)**不是** 这里的架构。它们是中性(neutral)包,构建时投影进
每个适用视图,解析器拒绝把它们写进这个列表。不支持的值(如 `riscv64`)立即失败:

```console
configuration error: load config "/srv/repo/sow.yml": workspace architectures: unsupported architecture "riscv64"; supported canonical families are x86_64 and aarch64
```

这个列表可以整体省略,但不能写成空列表。

## Repository 仓库

```yaml
repos:
  pigsty:
    protected: true
    signing: { ... }
    dists: { ... }
```

| 字段 | 类型 | 必填 | 默认值 | 含义 |
|---|---|---|---|---|
| `protected` | bool | 否 | `false` | 为真时 `sow repo rm` 拒绝删除该仓库,`-f` 也不行。 |
| `signing` | map | 否 | 无 | 包体与元数据签名设置,见[签名](#签名)。 |
| `dists` | map | 否 | 空 | Dist 名到 Dist 配置的映射。 |

### protected

`protected: true` 是防止误删整个仓库的闸门,它只拦一件事 —— 仓库删除:

```console
operation rejected: managed: operation rejected: repository "pigsty" is protected
```

这是退出码 `6`。其余一切照常:`add`、`rm`、`build`、建/删 Dist 都不受影响。
要真的删掉一个 protected 仓库,先把 `sow.yml` 改成 `protected: false`,
用 `sow config check` 确认,再执行 `sow repo rm`。

### 名称约束

仓库名与 Dist 名共用一套文法:必须匹配 `[a-z0-9][a-z0-9._-]*` —— 小写字母、数字、
点、下划线、连字符,且以字母或数字开头。大写被拒绝,因为名称会变成目录名,
必须在大小写敏感的 Linux 与默认大小写不敏感的 macOS 文件系统上表现一致:

```console
configuration error: load config "/srv/repo/sow.yml": repository name "Infra": name "Infra" must match [a-z0-9][a-z0-9._-]*
```

下列名称是保留名,一律拒绝:`.`、`..`、`.sow`、`pool`、`dists`、`sow.yml`、
`workspace.lock`、`workspace-ops`、`repo-locks`。两个会在状态目录里撞车的仓库名
(比如 `db` 与 `db.db`)也会被拒绝:

```console
configuration error: load config "/srv/repo/sow.yml": repository names "db" and "db.db" collide at reserved state path "db.db"
```

原因见[仓库布局](/zh/docs/reference/layout/)。

## Dist

```yaml
    dists:
      el9:
        format: rpm
        architectures: [x86_64]
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]
```

| 字段 | 类型 | 必填 | 默认值 | 含义 |
|---|---|---|---|---|
| `format` | string | 是 | — | `rpm` 或 `deb`。一个 Dist 只承载一种格式。 |
| `architectures` | 字符串列表 | 否 | 继承工作区列表 | 把该 Dist 收窄到工作区架构的一个子集。 |
| `limit` | integer | 否 | `0` | 同一包名 + 架构最多保留几个版本;`0` 表示全留。 |
| `exclude` | 规则列表 | 否 | 空 | 把命中的包挡在该 Dist 之外的规则。 |

### format

`format` 是 `sow dist new` 唯一从命令行接受的业务参数,并且创建之后不可更改 ——
RPM Dist 永远不会变成 DEB Dist。格式不匹配的包根本不会成为该 Dist 的候选:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" format must be rpm or deb, got "apk"
```

### architectures

省略这个字段,Dist 继承工作区列表 —— 绝大多数情况下这就是你要的。
只有需要 **收窄** 时才声明:比如双架构工作区里,某个 `el9` Dist 只做 x86。

列表必须是工作区列表的子集,且不能为空:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" architecture "aarch64" is not allowed by workspace
```

在这里新增一个架构族会让该 Dist 变为待构建(dirty),下一次 `sow build` 渲染新视图。
移除一个仍被现有成员关系或已构建代引用的族,`config check` 与所有写命令都会拒绝。

### limit

`limit` 限定该 Dist 中同一个包保留几个版本。分组键是 **(二进制包名, 原生架构)**,
所以同一个包的 x86_64 与 aarch64 构建各自计数,`noarch`/`all` 包自成一组。

- `0`(默认)保留全部版本。
- `N > 0` 保留最新的 `N` 个,RPM 按 EVR 比较,DEB 按 Debian version 规则比较。
- 负数是配置错误:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: limit must be zero or positive, got -1
```

`limit: 1` 时,把旧版本和新版本一起加入,旧版本会被报告为 limited 且不建立成员关系:

```console
item input=".../libpq5_18.2-1.pgdg12+1_amd64.deb" status=excluded format=deb coordinate="libpq5=18.2-1.pgdg12+1:amd64" sha256:310611d0... dists=trixie:limited
item input=".../libpq5_18.3-1.pgdg12+1_amd64.deb" status=accepted format=deb coordinate="libpq5=18.3-1.pgdg12+1:amd64" sha256:4b526223... dists=trixie:accepted
```

事后调大 `limit` **不会** 复活曾被策略移出的版本。包体字节可能还留在包池里,
但成员关系已经没了;要拿回来就重新 `add` 一次。理由见[成员策略](/zh/docs/feature/policy/)。

### exclude

`exclude` 是规则列表。每条规则是若干字段的集合:规则内字段之间是 AND,
同一字段的多个 pattern 之间是 OR,规则与规则之间是 OR。任一规则命中即排除。

```yaml
exclude:
  - kind: [debuginfo, debugsource, dbgsym, dbg, llvmjit]
  - name: ["test-*", "*-experimental"]
    arch: [aarch64]
```

读作:丢掉所有 debug 类包;另外,丢掉名字以 `test-` 开头或以 `-experimental` 结尾的
aarch64 包。

允许五个字段:

| 字段 | 匹配对象 |
|---|---|
| `name` | 二进制包名 |
| `source` | 规范化后的 source 名(RPM 取 `SOURCERPM`,DEB 取 `Source`) |
| `arch` | `x86_64`、`aarch64` 或 `neutral` |
| `kind` | 见下表分类 |
| `format` | `rpm` 或 `deb` |

`kind` 由二进制包名的后缀决定,取最具体的一个:

| 格式 | 名称后缀 | `kind` |
|---|---|---|
| RPM | `-debuginfo` | `debuginfo` |
| RPM | `-debugsource` | `debugsource` |
| RPM | `-llvmjit` | `llvmjit` |
| DEB | `-dbgsym` | `dbgsym` |
| DEB | `-dbg` | `dbg` |
| 任意 | 以上都不匹配 | `main` |

pattern 区分大小写,只有两种形态:精确字符串,或使用 `*`、`?`、`[...]` 的 shell glob。
不支持正则、版本比较、否定,也没有表达式语法。空规则、空或带首尾空白的 pattern、
同一字段内重复的 pattern、非法 glob,都是配置错误:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: exclude rule 0 is empty
configuration error: load config "/srv/repo/sow.yml": repository "a" dist "d1" policy: exclude rule 0 field name has invalid glob "[bad": syntax error in pattern
```

策略顺序固定:先 `exclude`,后 `limit`。被排除的包逐条报告,不算失败:

```console
item input=".../blackbox_exporter-0.28.0-1.x86_64.rpm" status=excluded format=rpm coordinate="blackbox_exporter-0:0.28.0-1.x86_64" sha256:5759c643... dists=el9:excluded
```

## 签名

签名配置挂在仓库级(不是 Dist 级),覆盖两条互相独立的信任链:软件包本身,
以及客户端在信任其他一切之前先验证的仓库元数据。

```yaml
    signing:
      rpm:
        packages:
          mode: fill
          key: env://SOW_RPM_PACKAGE_KEY
          trusted_keys: [keys/pgdg.asc]
        metadata:
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
      deb:
        metadata:
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
```

树形是固定的:`signing.rpm` 下有 `packages` 与 `metadata`;`signing.deb` 下 **只有**
`metadata` —— DEB 包体永远不会被重签,因为 APT 通过 `Release` 验证整个仓库,
而不是逐包签名。

### rpm.packages

| 字段 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `mode` | string | 无 key 时 `never`,有 key 时 `fill` | `never`、`fill` 或 `always`。 |
| `key` | key 引用 | 无 | 当前签名身份；公钥用于验证，匹配私钥必须存在于 `rpm` 使用的 GPG 环境。`mode` 不是 `never` 时必填。 |
| `trusted_keys` | key 引用列表 | 空 | `fill` 额外认可的公钥。 |

三种模式:

- **`never`** —— 原样保存输入字节。包进来时带什么签名(或没有签名),客户端拿到的就是什么。
- **`fill`** —— 对没有签名、或签名无法被 `key` 及 `trusted_keys` 验证的包补签;
  已经能验证通过的包保持字节不变。
- **`always`** —— 最终每个包都必须由 `key` 有效签名。已经由该 key 签好的保持字节,
  其余一律重签。

有 key 时默认是 `fill`,因为它是唯一保留上游签名的模式。设成 `fill` 或 `always` 却不给
key 是错误:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: rpm packages mode "fill" requires key
```

`trusted_keys` 列出哪些公钥的签名被 `fill` 视为"已经合格"。`key` 的公钥部分自动受信,
不需要重复列出。同一个引用写两次是错误:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: duplicate rpm trusted key reference "keys/x.asc"
```

RPM 包签名是唯一会调用外部程序的操作:SOW 对 **私有 stage 副本** 调用环境里的
`rpm --addsign` / `rpm --resign`,永远不碰你的输入文件。私钥必须已经存在于 `rpm` 使用的
GPG 环境中。

### rpm.metadata 与 deb.metadata

| 字段 | 类型 | 默认值 | 含义 |
|---|---|---|---|
| `key` | key 引用 | 无 | 给仓库元数据签名的私钥。 |
| `passphrase` | passphrase 引用 | 无 | 私钥有口令时使用。 |

配置 `rpm.metadata.key`,每个 RPM 架构视图会额外发布分离签名
`repodata/repomd.xml.asc`;配置 `deb.metadata.key`,每个 DEB Dist 会额外发布
clearsign 的 `InRelease` 与分离的 `Release.gpg`。没配 key 就不生成这些文件 ——
`repomd.xml` 与 `Release` 则始终会写。

`file://` 与 `env://` 引用由 SOW 在 **进程内** 完成签名,不需要 `gpg` 可执行文件。
只有 `agent://` 需要环境里有 `gpg`。

改变 key 引用或它背后的 fingerprint 会让相关 Dist 变 dirty ——
签名身份是每个 Dist 已构建配置摘要的一部分。下一次 `sow build` 重新签名并推进新的代。

### key 引用文法

key 引用是下列四种写法之一:

| 形态 | 例子 | 说明 |
|---|---|---|
| 路径 | `keys/repo-signing.asc` | ASCII-armored key 文件。相对路径相对 **工作区根目录** 解析,不是当前目录。 |
| `file://<path>` | `file:///secure/repo-signing.asc` | 与上一行等价,只是显式写出。绝对路径因此是三个斜杠。 |
| `env://<VAR>` | `env://SOW_METADATA_KEY` | 环境变量里存的是 armored key **内容本身**,不是路径。变量名须匹配 `[A-Za-z_][A-Za-z0-9_]*`。 |
| `agent://<fingerprint>` | `agent://7F721C4AD40F...CF3B` | 委托给环境里的 `gpg-agent`。fingerprint 为 16、40 或 64 位十六进制,不区分大小写。 |

其他 scheme 一律拒绝:

```console
configuration error: load config "/srv/repo/sow.yml": repository "a" signing: deb metadata key: unsupported key reference scheme in "https://example.com/key.asc"
```

引用分两阶段校验。**文法** 在解析时检查,失败退出码 `2`;引用 **能否解析出真实密钥**
由 `sow config check` 和每条写命令检查,失败退出码 `6`:

```console
operation rejected: ... deb metadata key: key reference does not resolve to a bounded regular file
operation rejected: ... deb metadata key: environment key reference SOW_METADATA_KEY is unset
operation rejected: ... deb metadata key: gpg public-key export returned no bounded key material
```

秘密内容永远不会离开引用本身。`sow config show --all` 只显示引用与解析出的 fingerprint:

```yaml
    signing:
      deb:
        metadata:
          key: file:///srv/repo/keys/repo-signing.asc
          key_fingerprint: 7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
```

私钥与口令永远不会写进 `sow.yml`、SQLite、操作日志、JSON 输出或错误文本。

### passphrase 引用

`passphrase` 接受与 key 引用相同的路径、`file://`、`env://` 三种写法,
但 **不接受** `agent://` —— 口令是一个值,不是密钥句柄。

两条规则:

- 有 passphrase 没有 key 是错误,因为它没有可解锁的对象:

  ```console
  configuration error: ... repository "a" signing: deb metadata passphrase requires key
  ```

- passphrase 与 `agent://` key 同时出现是错误。私钥由 agent 持有并自行处理口令交互,
  第二条口令通道只会被忽略:

  ```console
  configuration error: ... repository "a" signing: rpm metadata agent key uses its ambient gpg-agent and cannot accept a passphrase reference
  ```

## 发布目标

每个目标把一个已配置 Repository 绑定到一个存储命名空间。目标名使用与仓库相同的小写文法。

```yaml
targets:
  local:
    repository: pigsty
    provider: filesystem
    endpoint: file:///srv/mirror
    prefix: pigsty
    public_endpoint: file:///srv/mirror/pigsty/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true

  prod:
    repository: pigsty
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: pigsty
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/pigsty/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

| 字段 | 必填 | 含义 |
|---|---|---|
| `repository` | 是 | 本目标拥有的现有 Repository。 |
| `provider` | 是 | `filesystem` 或 `r2`。 |
| `endpoint` | 是 | 无尾斜杠的规范 `file:///absolute/path`,或 R2 的规范 `https://host`。 |
| `region` | R2 | 必须是 `auto`;filesystem 禁用。 |
| `bucket` | R2 | 小写规范 bucket 名;filesystem 禁用。 |
| `prefix` | 是 | 相对公共树前缀;空串表示存储命名空间根。 |
| `credential` | R2 | `env://NAME` 或 `file:///absolute/path`;禁止内联秘密。 |
| `public_endpoint` | 是 | 以 `/` 结尾的规范 `https://`、`http://` 或 `file://` URL,用于公共缺失证据。 |
| `max_cache_ttl` | 是 | 规范的非负 Go duration,包括显式 `0s`。 |
| `authoritative_workspace` | 是 | 必须为 `true`。 |
| `single_writer` | 是 | 必须为 `true`。 |
| `exclusive_write_authority` | 是 | 必须为 `true`。 |

三个 authority 布尔值是显式安全确认,不是默认值。同一存储上的目标前缀不能重叠;
filesystem 目标也不能解析到重叠的有效路径。这些规则防止并发写者破坏条件式发布与 GC。

对 `provider: filesystem`，配置校验只检查 URL 形态与重叠关系。真正发布时，endpoint 目录
必须已经存在、不能是 symlink，并且必须解析为唯一规范真实目录。SOW 会在 endpoint 下创建
配置的 prefix，但不会创建 endpoint 本身。

R2 凭据是私有引用。环境变量值或被引用文件必须包含一份严格 JSON 文档，不能写路径或 Shell
赋值：

```json
{"access_key_id":"R2_ACCESS_KEY_ID","secret_access_key":"R2_SECRET_ACCESS_KEY"}
```

临时凭据可以增加可选的 `"session_token":"..."`。未知字段、尾随内容、缺少 Access/Secret，
以及超过 64 KiB 的文档都会被拒绝。`config show`、JSON 输出与公共树不会包含凭据材料。

## 完整示例

一个工作区,两个仓库:一个受保护的生产仓库(两条元数据签名链 + RPM 补签),
一个不签名、不过滤的临时仓库。

```yaml
# sow.yml —— 工作区根配置
schema: sow/v3

# 本工作区允许管理的 CPU 架构族。这是上限,不是目标。
# amd64/arm64 作为输入别名被接受,规范化为 x86_64/aarch64。
architectures: [x86_64, aarch64]

repos:

  # 生产仓库。要删除它必须先改这个文件。
  pigsty:
    protected: true

    signing:
      rpm:
        packages:
          # 对无签名或签名不受信的 RPM 补签;
          # 已由受信 key 签好的包保持字节不变。
          mode: fill
          key: keys/package-signing.asc
          trusted_keys:
            - keys/pgdg.asc        # 上游 PGDG 的签名原样认可
        metadata:
          # 每个 repomd.xml 旁边额外发布 repodata/repomd.xml.asc
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE
      deb:
        metadata:
          # 每个 Release 旁边额外发布 InRelease 与 Release.gpg
          key: keys/repo-signing.asc
          passphrase: env://SOW_METADATA_PASSPHRASE

    dists:

      # 稳定 EL9 通道:每个包只留一个版本,不要 debug 产物
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]

      # Beta 通道:同样的包,保留全部版本以便回滚
      el9-beta:
        format: rpm
        limit: 0
        exclude:
          - kind: [debuginfo, debugsource, llvmjit]

      # Debian trixie,只做 x86,保留最新版本
      trixie:
        format: deb
        architectures: [x86_64]
        limit: 1
        exclude:
          - kind: [dbgsym, dbg]
          - name: ["*-experimental"]

  # 临时仓库:不签名、不过滤、可随时删除
  sandbox:
    dists:
      el9:
        format: rpm
      trixie:
        format: deb

targets:
  prod:
    repository: pigsty
    provider: r2
    endpoint: https://0123456789abcdef.r2.cloudflarestorage.com
    region: auto
    bucket: packages
    prefix: pigsty
    credential: env://SOW_R2_CREDENTIAL
    public_endpoint: https://repo.example.com/pigsty/
    max_cache_ttl: 24h0m0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

用之前先验证:

```bash
sow config check
sow config show --all
```

## sow.yml 里没有什么

有些你可能以为能配的东西,是 **有意** 不做成配置项的:

- **仓库路径。** 仓库永远位于 `<workspace>/<name>`,没有 `path:` 字段。
  见[仓库布局](/zh/docs/reference/layout/)。
- **APT component。** 固定为 `main`;YUM 没有 component 概念。
- **架构视图。** 由 `architectures` 与包头共同推导,不能逐包声明。
- **内联秘密。** 目标只接受 credential 引用;key 与 passphrase 材料同样留在引用背后。
- **自动保留数量。** 保留是显式 `sow retain add/rm` 操作,不是配置中的滚动计数。

## 延伸阅读

- [`sow config`](/zh/docs/command/config/) —— 读取本文件的命令
- [成员策略](/zh/docs/feature/policy/) —— `exclude` 与 `limit` 随时间演化的行为
- [签名模型](/zh/docs/feature/signing/) —— 两条信任链的详细解释
- [`publish`](/zh/docs/command/publish/)、[`retain`](/zh/docs/command/retain/)、[`gc`](/zh/docs/command/gc/) 与 [`export`](/zh/docs/command/export/) —— 交付生命周期命令
- [退出码](/zh/docs/reference/exit-codes/) —— 这里的 `2` 与 `6` 分别意味着什么
