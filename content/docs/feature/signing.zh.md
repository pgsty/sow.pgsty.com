---
title: "签名模型"
linkTitle: "签名模型"
description: "两条独立信任链、四种密钥引用形态、进程内与外部签名的分工，以及安全换钥方式。"
url: "/zh/docs/feature/signing/"
weight: 600
icon: fa-solid fa-key
---

客户端会对一个仓库提两个不同的问题,SOW 用两套彼此独立的机制分别回答。把它们混为一谈,是"我明明签了名,`dnf` 还是报错"这类问题最常见的来源 —— 所以本页先把两者拆开。

## 两条独立的信任链

| | 元数据签名 | RPM 包体签名 |
|---|---|---|
| 回答的问题 | "这份索引真是你出的、没被改过吗?" | "这个 `.rpm` 文件真是你出的吗?" |
| 配置项 | `signing.rpm.metadata`、`signing.deb.metadata` | `signing.rpm.packages` |
| 产出 | `repodata/repomd.xml.asc`、`InRelease`、`Release.gpg` | 嵌入包内的 OpenPGP 签名 |
| 是否改变包字节 | 否 | 是 |
| 客户端配置 | dnf `repo_gpgcheck=1`、apt `Signed-By` | dnf `gpgcheck=1` |
| Plain 模式可用 | 否 | 是,通过 `create -S KEY` |

二者分别配置、可分别使用。通常正确的起点是只做元数据签名:它在一个地方为整份索引背书,而且完全不需要改动你从上游拿到的那些包。

Managed 的元数据签名完全由 `sow.yml` 控制。没有 CLI 覆盖开关,`build` 上没有 `--sign` 参数,也没有办法让这次构建和下次构建签得不一样。这是刻意的 —— 仓库的签名身份是仓库的属性,不是"碰巧更新了它的那条命令"的属性。

## 配置

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never              # never | fill | always
        metadata:
          key: "file:///secure/repo-signing.asc"
      deb:
        metadata:
          key: "file:///secure/repo-signing.asc"
```

RPM 与 DEB 的元数据密钥分开声明,所以你可以像上面这样两边共用同一把钥匙,也可以拆开用。每个 metadata 块除 `key` 外还接受可选的 `passphrase` 引用。

配了元数据密钥之后,每次构建都会产出签名文件 —— 空 Dist 也不例外:

- RPM,每个架构视图:`repodata/repomd.xml` 加一份 ASCII-armored 的 `repodata/repomd.xml.asc`
- DEB,每个 Dist:`Release` 加一份 clearsigned 的 `InRelease` 与一份分离式 armored 的 `Release.gpg`

`InRelease` 的 clearsign 正文与 `Release` 完全一致。没有配元数据密钥时,这两个签名文件根本不会生成 —— 你只会得到 `repomd.xml` 和 `Release`。

## 四种密钥引用形态

密钥引用是一个 URI,scheme 决定由谁来签:

| 引用 | 含义 | 签名者 |
|---|---|---|
| `keys/repo-signing.asc` | 相对 Workspace Root 的 ASCII-armored 密钥路径 | 进程内 Go signer |
| `file:///绝对路径.asc` | 磁盘上的 ASCII-armored 私钥 | 进程内 Go signer |
| `env://VAR_NAME` | 环境变量里的 armored 密钥材料 | 进程内 Go signer |
| `agent://<fingerprint>` | 由环境中 GPG agent 持有的密钥 | 外部 `gpg` |

`file://` 与 `env://` 不需要装任何东西 —— SOW 自己签元数据,这也是为什么用 `file://` 元数据密钥的仓库在 macOS 和最小化容器里能构建出一致的结果。`agent://` 把签名委托给你的 GPG agent,适合私钥在智能卡上、或绝不能落盘的场景。`agent://` 不能与 `passphrase` 引用同时使用,因为那次交互归 agent 管。

`passphrase` 引用接受相对 Workspace Root 的路径、`file://` 或 `env://`，不接受 `agent://`。

**任何秘密都不会被持久化。** 配置、SQLite、日志、JSON 输出和错误文本里,只有引用字符串、fingerprint 和公钥验证证书。`config show --all` 打印引用与 fingerprint,绝不打印密钥材料。如果某个密钥引用无法解析或不可用于签名,`config check` 会在你执行 build 之前就告诉你。

## RPM 包体签名

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      trusted_keys: [keys/pgdg.asc]
```

三种模式:

| 模式 | 行为 |
|---|---|
| `never` | 原样保留输入字节 |
| `fill` | 包未签名、或签名不受信任时用配置的 key 签;已有签名能被 `trusted_keys` 验证通过则保持字节不变 |
| `always` | 确保最终包由配置的 key 有效签名;已经是了就保持字节,否则重签 |

`trusted_keys` 自动包含配置 `key` 的公钥部分。没有 key 时只能用 `never`;有 key 时默认 `fill`。

包体签名总是对私有 staged 副本调用环境中的 `rpm --addsign` 或 `rpm --resign`，不会就地
修改输入文件。签完后 SOW 会重新解析结果，要求嵌入签名存在、signature-neutral digest 与
NEVRA 不变，并且签名身份与配置完全一致。`fill` 与 `always` 必须有 `rpm`、`gpg`，且匹配私钥
必须存在于 `rpm` 使用的 GPG 环境中。key 引用用于标识并验证签名者，不会把私钥自动导入该环境。

由于签名里嵌入了时间戳,签名过程不可复现 —— 同一个未签名 RPM 签两次会得到不同字节。于是重复 add 一个已经加过的包看起来就像内容冲突。SOW 用 **signature-neutral payload digest** 解决这个问题:对不可变的 header 与 payload(排除 RPM signature header)计算 SHA-256。如果逻辑坐标已存在、neutral digest 相同,且既有对象满足当前策略,SOW 就复用既有的最终字节而不再签名。重复 add 同一个包是稳定的空操作。

这种复用的口子刻意开得很窄。`never` 模式要求完整字节一致,因为该模式承诺保留输入字节。如果 payload digest 不同,或既有对象不满足当前签名策略,那就是硬冲突 —— `add` 不会悄悄地在既有坐标上就地重签一个包。这里没有 `--replace`;如果重签导致字节变化,请提高 release,或专门规划一次密钥轮换流程。

## 更换密钥会让 Dist 变 dirty

一个 Dist 的 Built 配置摘要覆盖它的 format、canonical 架构、`limit`、`exclude`,以及**已冻结的签名身份**。改动密钥引用或 fingerprint 会改变这个摘要,于是所有受影响的 Dist 变 dirty:

```console
$ sow status
repository=pigsty status=dirty ready_to_copy=false revision=5 generation=4 dirty_dists=el9,trixie pending=0/0 locked=false
```

更换**元数据** key 后，`sow build` 会用新身份签署索引并产生新 Generation。

RPM 包体是不可变 Package Object；`build` 不会在同一坐标下静默重签既有对象。如果当前 Desired
RPM 不满足新的包签名策略，`build` 会拒绝。分阶段轮换通常使用 `fill`：将新 key 设为当前 key，
同时把旧公钥保留在 `trusted_keys`；旧 key 软件包保持字节不变，新加入的软件包使用新 key。
只有当旧坐标已下架或被新 Release 替代后，才移除旧信任。直接切到新 key 的 `always`，要求
每个 Desired RPM 已经由新 key 签名。

当前 Built 元数据的精确公钥证书身份按 Dist 记录,同一 primary fingerprint 的多个证书版本可以共存 —— 所以延长有效期或增加子钥,不会让已经发布出去的东西失效。

## Plain 模式

```bash
sow create /srv/repo --sign-with 6D5C5A26C36B1F73
sow create /srv/repo --sign-with 6D5C5A26C36B1F73 --overwrite
```

Plain 模式只签 RPM 包体,没有元数据签名。`KEY` 必须是恰好 16、40 或 64 位十六进制 GPG key ID/fingerprint，不接受 `0x` 前缀；规范化为大写后作为 `_gpg_name` macro 传给 `rpm`。不带 `--overwrite` 时只签没有可解析嵌入签名的 RPM;带上则对全部保留的 RPM 重签。

`--sign-with` 要求目录里至少有一个顶层 RPM。纯 DEB 目录、缺少 `rpm` 可执行文件、密钥不可用,都在任何公开变更之前失败。签名运行的崩溃恢复要求给出完全相同的授权参数,见 [Plain 平面仓库](/zh/docs/feature/plain/)。

## 客户端验证什么

```ini
[pigsty-el9]
name=Pigsty EL9
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch/
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://repo.example.com/keys/repo-signing.asc
```

```text
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Signed-By: /etc/apt/keyrings/repo-signing.asc
```

`repo_gpgcheck=1` 让 dnf 验证 `repomd.xml.asc`；`gpgcheck=1` 让它验证每个包的嵌入签名。
APT 侧的 `Signed-By` 让 apt 验证 `InRelease`。当前测试套件会直接校验生成的签名，但尚未
提供完整的签名 Managed dnf/APT 验收门禁。请在目标环境执行真实客户端测试；确切证据见
[兼容性](/zh/docs/reference/compatibility/)。

`sow check` 在常规运行中就会校验全部已声明的签名与文件哈希,所以签名配置出错会在发货之前暴露,而不是在客户机器上暴露。

## 继续阅读

- [仓库签名](/zh/docs/tutorial/signing/) —— 生成专用密钥并把两条链都接起来
- [`sow.yml` 配置参考](/zh/docs/reference/config/) —— 完整签名 schema 与密钥引用文法
- [可观测与审计](/zh/docs/feature/audit/) —— `check` 如何证明这些签名
