---
title: "JSON 输出"
linkTitle: "JSON 输出"
description: "sow.cli/v1 Envelope、字段含义与主要命令族的 Result 形态。"
url: "/zh/docs/reference/json/"
weight: 600
icon: fa-solid fa-code
---

所有产出数据的命令都接受 `--json`。输出是 stdout 上的**一行**版本化信封 ——
不管是哪条命令产生的,都能直接管道给 `jq`。

```bash
sow status --json
```

```json
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"pigsty","operation":null,
 "result":{"repository":"pigsty","status":"clean","ready_to_copy":true,"desired_revision":4,
 "built_generation":"00000000000000000004","dirty_dists":[],"dirty_reasons":[],"pending":{"count":0,"bytes":0},
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
 "created_at":"2026-08-04T04:07:17.665377Z","updated_at":"2026-08-04T04:07:18.293848Z"},
 "repository_locked":false},"errors":[]}
```

(此处为便于阅读做了折行,实际输出是一行。)

## 信封结构

| 字段 | 类型 | 含义 |
|---|---|---|
| `schema` | string | 恒为 `sow.cli/v1`。解析其他字段前先检查它。 |
| `command` | string | 实际调用的命令,含子命令:`add`、`repo ls`、`config show`。 |
| `ok` | bool | `errors` 为空时为 `true`,等价于退出码 `0`。 |
| `repository` | string 或 null | 选定的仓库;工作区级与 Plain 模式命令为 `null`。 |
| `operation` | string 或 null | 写命令的 Operation ID,只读命令为 `null`。 |
| `result` | object 或 null | 命令专属载荷,详见下文。 |
| `errors` | array | 零个或多个 `{code, class, message}` 对象。 |

七个字段**永远存在**。只有命令在产出任何东西之前就失败时(比如未知参数),
`result` 才是 `null`。

### errors

```json
"errors":[{"code":3,"class":"partial","message":"managed: batch partially succeeded"}]
```

| 字段 | 含义 |
|---|---|
| `code` | 进程[退出码](/zh/docs/reference/exit-codes/) —— `1` 到 `6`。 |
| `class` | `runtime`、`usage`、`partial`、`lock`、`integrity`、`rejected` 之一。 |
| `message` | 与写到 stderr 的文本相同。 |

请对 `class` 做分支判断,不要匹配 message 文本。message 里含路径和包名,会变;class 不会。

{{% alert title="非零退出仍然返回 result" color="info" %}}
批次部分成功时,`ok` 是 `false`,**同时** `result` 会完整列出已提交的内容。
不要因为退出码非零就丢掉载荷 —— 对 `add` 来说,那正是你了解"哪些包落地了"的唯一途径。
{{% /alert %}}

### Operation ID 是字符串

```json
"operation":"8632724976452398569"
```

Operation ID 是 64 位值,序列化为十进制**字符串**,因为它经常超出 IEEE 754 双精度
能精确表示的范围。在 JavaScript 里,`JSON.parse` 处理裸数字会静默损坏它们。
请保持字符串形态;`jq` 原样处理即可。

### Generation ID 是固定宽度字符串

```json
"built_generation":"00000000000000000004"
```

Generation ID 覆盖完整的无符号 64 位范围，并固定序列化为 20 位、左侧补零的十进制字符串。
`generation`、`built_generation`、`base_generation` 以及表示 Generation 的 `base` 字段都应
按字符串处理；固定宽度也能保持普通字节序比较与数值顺序一致。

### stdout 与 stderr

结果和 JSON 信封写 stdout;警告与错误诊断写 stderr,**同时**也出现在 `errors` 数组里。
所以这样写是可行的:

```bash
sow check --json 2>/dev/null | jq -e '.ok'
```

## 各命令的 result 形态

### create

```bash
sow create /srv/offline --json
```

```json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,
 "result":{"dir":"/srv/offline","rpm":4,"deb":3,
 "kept":["blackbox_exporter-0.28.0-1.aarch64.rpm","blackbox_exporter-0.28.0-1.x86_64.rpm",
 "libpq5_18.2-1.pgdg12+1_amd64.deb","pev2-1.23.0-1.noarch.rpm"],
 "removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

| 字段 | 含义 |
|---|---|
| `dir` | 被索引的绝对目录 |
| `rpm`、`deb` | 各格式的包数量 |
| `kept` | 进入索引的文件名,已排序 |
| `removed` | 被 `--pigsty` 清理删除的包;否则为空 |
| `marker` | 是否写入了 `repo_complete` |
| `marker_sha256` | marker 文件的摘要;仅 `--pigsty` 时出现 |
| `noop` | 索引本来就正确、什么都没改时为 `true` |
| `recovered` | 本次运行完成了上一次被中断的操作时为 `true` |
| `signed` | 被重签的文件名;仅 `--sign-with` 时出现 |

### init

```json
"result":{"workspace":"/srv/repo","config_created":true,
 "repositories_initialized":0,"dists_initialized":0,"existing":[]}
```

对已存在的工作区重跑时,计数为 `0`,`existing` 说明找到了什么:

```json
"result":{"workspace":"/srv/repo","config_created":false,
 "repositories_initialized":0,"dists_initialized":0,"existing":["sow.yml"]}
```

### config check 与 config show

```json
"result":{"workspace":"/srv/repo","repositories":1,"dists":2}
```

`config show` 返回有效配置本身,形态与规范化之后的
[`sow.yml`](/zh/docs/reference/config/) 一致:

```json
"result":{"schema":"sow/v3","architectures":["x86_64","aarch64"],
 "repos":{"pigsty":{"protected":false,
 "signing":{"rpm":{"packages":{"mode":"never"}}},
 "dists":{"el9":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":0,"exclude":null},
          "trixie":{"format":"deb","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}}}}
```

带 `--all` 时,签名条目会额外携带 `key_fingerprint`。私钥内容与口令永不出现。

### repo ls / repo new / repo show

`repo ls` 返回数组;`repo new` 与 `repo show` 返回同一形态的单个对象。

```json
"result":{"repositories":[{"name":"pigsty","path":"/srv/repo/pigsty","protected":false,
 "dists":2,"generation":"00000000000000000004","desired_revision":4,"status":"clean","packages":7,"memberships":7,
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
  "created_at":"2026-08-04T04:07:17.665377Z","updated_at":"2026-08-04T04:07:18.293848Z"},
 "config":{"protected":false,"signing":{...},"dists":{...}}}]}
```

`packages` 统计包池中不同的包对象数;`memberships` 统计 Dist 成员关系数 ——
同一个包出现在两个 Dist 里,前者计一次,后者计两次。

`repo rm` 只返回结果:

```json
"result":{"name":"demo","noop":false,"removed":true}
```

### dist ls / dist new / dist show

```json
"result":{"dists":[{"name":"el9","format":"rpm",
 "architectures":[{"family":"x86_64","ecosystem_arch":"x86_64"},
                  {"family":"aarch64","ecosystem_arch":"aarch64"}],
 "desired_members":4,"built_members":4,"generation":"00000000000000000003","dirty":false,"status":"clean",
 "effective_config_sha256":"39913af601d10d4d4033b0c29e8d66df385f8a6eb22f45219773a7fc170d4243",
 "config":{"format":"rpm","architectures":["x86_64","aarch64"],"limit":0,"exclude":null}}]}
```

每个架构条目同时给出两个名字:`family` 是配置里用的规范名,
`ecosystem_arch` 是发布树里出现的名字 —— RPM 两者相同,DEB 分别是 `amd64`/`arm64`。

`desired_members` 大于 `built_members`,或 `dirty: true`,都表示还欠一次 `sow build`。
`effective_config_sha256` 是所有喂给渲染器的输入的摘要;它一变,该 Dist 就变 dirty。

`dist rm` 与 `repo rm` 一致:`{"name":"el9","noop":false,"removed":true}`。

### add

```json
"result":{"operation":"320653458389425222","repository":"demo",
 "desired_revision":2,"built_generation":"00000000000000000002","dirty":false,
 "accepted":1,"failed":0,"memberships_added":1,"memberships_removed":0,
 "items":[{"input":"/incoming/pev2-1.23.0-1.noarch.rpm","status":"accepted","format":"rpm",
 "coordinate":"pev2-0:1.23.0-1.noarch",
 "sha256":"d06d7f23b9cfc6aedaab7b60c8e890cda020efe84f1f246243414862b98b1229",
 "dists":{"el9":"accepted"}}]}
```

每个输入路径对应一条 `items`,顺序稳定。`status` 是该项的总体结果,
`dists` 给出**逐 Dist** 的裁决:

| `status` | 含义 |
|---|---|
| `accepted` | 新包对象,已建立成员关系 |
| `reused` | 完全相同的对象已存在;可能仍为其他 Dist 新增成员关系 |
| `excluded` | 被策略挡下 —— 看 `dists` 区分是 `excluded` 还是 `limited` |
| `failed` | 未被接纳;`error` 给出原因 |

逐 Dist 的取值是 `accepted`、`excluded`、`limited`。同一条命令里,
一个包可以被某个 Dist 接受、被另一个 Dist 限流:

```json
"items":[{"input":".../libpq5_18.2-1.pgdg12+1_amd64.deb","status":"excluded","format":"deb",
 "coordinate":"libpq5=18.2-1.pgdg12+1:amd64","sha256":"310611d0...","dists":{"trixie":"limited"}}]
```

失败项携带 `error`,不带包字段:

```json
{"input":"/incoming/broken-1.0-1.x86_64.rpm","status":"failed",
 "error":"invalid RPM package: parse RPM reader: unexpected EOF"}
```

`memberships_added` 与 `memberships_removed` 双向计数,因为 `limit` 可能在接纳新版本的
同一个操作里淘汰旧版本。

### rm

```json
"result":{"operation":"3422380511083828695","repository":"pigsty",
 "desired_revision":5,"built_generation":"00000000000000000005","dirty":false,"check":false,
 "removed":[{"dist":"el9","sha256":"45171966...",
   "coordinate":"rpm:pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64","name":"pgbouncer_fdw_18"}],
 "dists":["el9"],
 "changes":[{"op":"add","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz",
   "phase":"metadata","size":382,"sha256":"1a57aa2f..."},
  {"op":"update","path":"dists/el9/x86_64/repodata/repomd.xml","phase":"pointer",
   "size":1510,"sha256":"f28ffe14..."},
  {"op":"delete","path":"dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz","phase":"delete"}]}
```

带 `-c/--check` 运行时 `check` 为 `true`,此时**什么都没写**,`changes` 是一份预测。
注意 `removed` 只列出成员关系的移除 —— `rm` 永远不删除包池字节。

### build

```json
"result":{"operation":"3701044631565986409","repository":"pigsty",
 "dists":["el9","trixie"],"desired_revision":5,"built_generation":"00000000000000000005",
 "noop":true,"dirty":false}
```

`noop: true` 表示期望状态已经与已构建的树一致,没有产生新的代。
`dists` 列的是被纳入考量的 Dist,不一定是真正重建了的那些。

### status

```json
"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,
 "desired_revision":4,"built_generation":"00000000000000000004","dirty_dists":[],"dirty_reasons":[],
 "pending":{"count":0,"bytes":0},
 "recent_operation":{"id":"8632724976452398569","kind":"add","state":"done",
  "created_at":"...","updated_at":"..."},
 "repository_locked":false}
```

`status` 取值为 `clean`、`dirty`、`recovering`、`error`。部署脚本该读的字段是
`ready_to_copy` —— 但记住 `status` 在任何状态下都返回 `0`,所以要判断**字段**,不是退出码:

```bash
sow status --json | jq -e '.result.ready_to_copy' >/dev/null || exit 1
```

`pending` 统计 `add --skip` 之后私有保存、尚未发布的包体。
`repository_locked` 报告当前是否有其他进程持有写锁。

### check

```json
"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,
 "built_generation":"00000000000000000004","desired_revision":4,
 "layers":[{"name":"config","ok":true,"checked":5,"issues":[]},
  {"name":"retained","ok":true,"checked":0,"issues":[]},
  {"name":"state","ok":true,"checked":1,"issues":[]},
  {"name":"public-modes","ok":true,"checked":72,"issues":[]},
  {"name":"package-bytes","ok":true,"checked":7,"issues":[]},
  {"name":"desired-membership","ok":true,"checked":7,"issues":[]},
  {"name":"index","ok":true,"checked":2,"issues":[]},
  {"name":"signature","ok":true,"checked":11,"issues":[]},
  {"name":"generation-manifest","ok":true,"checked":4,"issues":[]}]}
```

终态九层按固定顺序报告,每层给出检查了多少项以及发现的问题。dirty 仓库可以各层全部
`ok: true`,但仍以退出码 `5` 失败 —— 因为层校验的是**自洽性**,
而 `ready_to_copy` 报告的是**时效性**:

```json
{...,"ok":false,"result":{"status":"dirty","ready_to_copy":false,...},
 "errors":[{"code":5,"class":"integrity",
  "message":"integrity or recovery error: managed: repository is not ready to copy: repository status is dirty"}]}
```

### changes

```json
"result":{"repository":"pigsty","base":"00000000000000000004","generation":"00000000000000000005","dirty":false,
 "changes":[{"op":"add","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz",
   "phase":"metadata","size":382,"sha256":"1a57aa2f..."},
  {"op":"update","path":"dists/el9/x86_64/repodata/repomd.xml","phase":"pointer",
   "size":1510,"sha256":"f28ffe14..."},
  {"op":"delete","path":"dists/el9/x86_64/repodata/0df96f0b...-primary.xml.gz","phase":"delete"}]}
```

| 字段 | 取值 |
|---|---|
| `op` | `add`、`update`、`delete` |
| `phase` | `payload`、`metadata`、`pointer`、`delete` |
| `path` | 永远相对仓库根,永远用 `/` 分隔 |
| `size`、`sha256` | `add` 与 `update` 有;`delete` 没有 |

按这个 phase 顺序施加变更,客户端永远不会取到悬空引用:先包体,
再校验和命名的元数据,然后是协议指针(`repomd.xml`、`Release`),最后才删除被取代的文件。

`sow changes 0` 把当前整棵树作为一个 `add` 集合给出 —— 也就是一份完整交付清单。

### ls / show / where

`ls` 返回包对象数组;`show` 在 `package` 下返回恰好一个。

```json
"result":{"repository":"pigsty","dists":["el9"],"dirty":false,
 "packages":[{"sha256":"d06d7f23...","format":"rpm","coordinate":"pev2-0:1.23.0-1.noarch",
 "architecture":"noarch","canonical_arch":"neutral",
 "pool_path":"pool/p/pev2/pev2-1.23.0-1.noarch.rpm","filename":"pev2-1.23.0-1.noarch.rpm",
 "size":316372,"name":"pev2","source":"pev2","version":"1.23.0","epoch":"0","release":"1",
 "kind":"main","payload_sha256":"0413d629...","signature_key":"E7935D8DB9BD8B20",
 "storage":"pool","created_revision":3,"dists":["el9"],"built_dists":["el9"]}]}
```

值得关注的字段:

| 字段 | 含义 |
|---|---|
| `architecture` | 包头里的原始写法:`x86_64`、`noarch`、`amd64`、`all` |
| `canonical_arch` | SOW 用于分组的族:`x86_64`、`aarch64` 或 `neutral` |
| `payload_sha256` | 仅 RPM —— 签名无关摘要,用于识别同一包的重签副本 |
| `signature_key` | 包内嵌签名的 key ID(包带签名时) |
| `storage` | 已发布为 `pool`,`--skip` 加入的为 `pending` |
| `dists` / `built_dists` | 期望成员集 与 上一次构建实际发布的集合 |

`dists` 比 `built_dists` 长,是判断"还欠一次 build"的另一种方式。

`where` 搜索整个工作区,返回位置而不是完整对象:

```json
"result":{"reference":"pev2","locations":[{"repository":"pigsty","dists":["el9"],
 "built_dists":["el9"],"sha256":"d06d7f23...","coordinate":"rpm:pev2-0:1.23.0-1.noarch"}]}
```

### publish、retain、gc、export

v0.2.0 生命周期命令使用同一 envelope,数字 Generation 仍序列化为 JSON 字符串:

| 命令 | 重要 `result` 字段 |
|---|---|
| `publish` | `repository`、`target`、`provider`、`generation`、`attempt`、`checkpoint`、`phase`、`objects`、`noop` |
| `publish --abort` | `repository`、`target`、`provider`、`attempt`、`phase`、`objects` |
| `retain add` / `retain rm` | `repository`、`record`、`record_identity`、`path` |
| `retain ls` | `repository`、`generations[]`,元素使用同一 retained record 形态 |
| 本地 `gc` | `operation`、`repository`、`base_generation`、`generation`、`objects`、`bytes`、`noop` |
| 目标 `gc` | `repository`、`target`、`provider`、`phase`、`reports`、`candidates`、`deleted_objects`、`deleted_bytes`、`retained_objects`、`pending_grace`、`completed_attempts`、`noop` |
| `export rpm-leaf` | `repository`、`repository_id`、`generation`、`dist`、`arch`、`directory`、`method`、`signed`、`signer_identity`、`packages`、`files`、`manifest_sha256` |

`attempt`、`checkpoint` 或本地 GC `operation` 等可选 identity 没有值时直接省略。
R2 目标 GC 会把候选计入 retained,SOW 从不报告自己执行了远端删除。

### log

`sow log` 返回操作账本,由新到旧:

```json
"result":{"repository":"pigsty","operations":[{"id":"3701044631565986409","kind":"build",
 "state":"done",
 "payload_json":"{\"version\":2,\"repository\":\"pigsty\",\"kind\":\"build\",\"config_sha256\":\"37eb6dcf...\",\"skip\":false,\"noop\":true,\"dists\":[\"el9\",\"trixie\"],\"build_dists\":[],\"manifest_sha256\":\"125d7266...\"}",
 "result_json":"{\"dists\":2,\"dropped_pending\":[]}",
 "created_at":"2026-08-04T04:08:08.691678Z","updated_at":"2026-08-04T04:08:08.763019Z"}]}
```

`payload_json` 与 `result_json` 是**内含 JSON 的字符串**,不是对象。
它们原样保存以保证审计记录字节稳定;需要二次解析:

```bash
sow log --json | jq -r '.result.operations[] | .payload_json | fromjson | .config_sha256'
```

传入 Operation ID 会返回完整细节 —— 状态迁移、包、成员关系与每一个文件动作:

```json
"result":{"repository":"pigsty","detail":{"operation":{...},"duration_ms":598,
 "events":[{"sequence":0,"state":"planned","detail_json":"{}","occurred_at":"..."},
  {"sequence":1,"state":"staged",...},{"sequence":2,"state":"applied",...},
  {"sequence":3,"state":"built",...},{"sequence":4,"state":"done",...}],
 "packages":[{"sequence":0,"input_path":"pgbouncer_fdw_18","package_sha256":"45171966...",
  "coordinate":"rpm:pgbouncer_fdw_18-0:1.4.0-1PGDG.rhel9.8.x86_64","disposition":"removed"}],
 "memberships":[{"sequence":0,"dist":"el9","package_sha256":"45171966...","action":"remove"}],
 "files":[{"sequence":0,"action":"add","phase":"metadata","path":"dists/el9/x86_64/repodata/1a57aa2f...-filelists.xml.gz","size":382,"sha256":"1a57aa2f..."}]}}
```

`sow log prune` 返回它清理了什么:

```json
"result":{"operation":"7140280533435786353","repository":"demo",
 "before":"2026-01-01T00:00:00+08:00","pruned":0}
```

注意 `before` 会回显裸日期在本地时区解析出的绝对时间戳。

### log export 不是信封

`sow log export` 输出 **JSON Lines** —— 每行一条完整的 Operation 记录,
没有信封,也没有 `--json` 参数。它是给归档用的,不是给单条命令脚本用的:

```bash
sow log export - | head -1
sow log export operations.jsonl
```

它拒绝覆盖已存在的文件,也拒绝父目录是符号链接的目标。

## 一个完整例子

仓库既自洽又最新时才允许部署,然后列出该复制哪些文件:

```bash
#!/usr/bin/env bash
set -euo pipefail

if ! sow check -r pigsty --json 2>/dev/null | jq -e '.ok' >/dev/null; then
  echo "仓库不可交付" >&2
  exit 1
fi

# 当前发布树的完整清单,按交付顺序排列
sow changes 0 -r pigsty --json \
  | jq -r '.result.changes[] | [.phase, .op, .path] | @tsv'
```

## 延伸阅读

- [退出码](/zh/docs/reference/exit-codes/) —— `errors` 里的 `code` 与 `class` 取值
- [命令行](/zh/docs/reference/cli/) —— 哪些命令接受 `--json`
- [可观测与审计](/zh/docs/feature/audit/) —— 操作账本记录了什么
