---
title: "签名模型"
linkTitle: "签名模型"
description: "配置元数据与 RPM 包签名、引用密钥，并轮换签名身份。"
categories: [Feature]
tags: [signing, rpm, apt]
url: "/zh/docs/feature/signing/"
weight: 600
icon: fa-solid fa-key
---

配置元数据签名，让客户端验证仓库索引。需要客户端验证 RPM 文件内嵌签名时，
另行配置 RPM 包签名。

<span id="两条独立的信任链" data-td-print-local></span>
<span id="客户端验证什么" data-td-print-local></span>

## 签名对象

| 配置 | 签名内容 | 输出 | 客户端设置 |
|---|---|---|---|
| `signing.rpm.metadata` | RPM 索引清单 | `repodata/repomd.xml.asc` | DNF `repo_gpgcheck=1` |
| `signing.deb.metadata` | APT 发布清单 | `InRelease`、`Release.gpg` | APT `Signed-By` |
| `signing.rpm.packages` | RPM 包 | 内嵌 OpenPGP 签名 | DNF `gpgcheck=1` |

元数据签名不改变包字节。RPM 包签名会改变包字节及 SHA-256。
SOW 不给 DEB 包文件增加签名。

<span id="配置" data-td-print-local></span>

## 配置元数据签名

```yaml
repos:
  demo:
    signing:
      rpm:
        metadata:
          key: file:///secure/repo-signing.asc
      deb:
        metadata:
          key: file:///secure/repo-signing.asc
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

RPM 与 DEB 可使用相同或不同密钥。文件或环境变量中的密钥已加密时，增加 `passphrase` 引用。
先检查配置，再构建：

```bash
sow config check
sow build -r demo
sow check -r demo
```

已配置签名的空 Dist 与非空 Dist 生成相同种类的签名文件。`InRelease` 的签名正文与
`Release` 一致。未配置密钥时，SOW 生成未签名索引。
Managed 签名设置来自 `sow.yml`，`build` 没有单次覆盖签名设置的选项。

<span id="四种密钥引用形态" data-td-print-local></span>

## 密钥与口令引用

| 元数据密钥引用 | 含义 | 签名实现 |
|---|---|---|
| `keys/repo.asc` | 相对于工作区根的 OpenPGP 密钥文件 | 进程内 |
| `file:///secure/repo.asc` | 绝对路径的 OpenPGP 密钥文件 | 进程内 |
| `env://SOW_METADATA_KEY` | ASCII 装甲格式密钥、文件路径或 GPG 密钥标识 | 取决于变量值 |
| `agent://KEY_ID_OR_FINGERPRINT` | 本地 GPG 环境可用的密钥 | 外部 `gpg` |

密钥文件支持 ASCII 装甲格式和二进制 OpenPGP 数据。GPG 密钥标识可以是 16 位 key ID，
或 40、64 位指纹。引用解析为 GPG 密钥标识时，使用外部 `gpg` 访问私钥和处理口令。

提供私钥内容时，口令支持路径、`file://` 或 `env://` 引用。GPG 密钥标识由 GPG 处理口令，
不能另配 `passphrase` 字段。路径和大小限制见[密钥引用](/zh/docs/reference/config/#密钥引用)。

`config show` 显示引用和解析出的公钥身份，不显示私钥或口令内容。
`config check` 解析引用并检查用途。创建新元数据签名时，选中的签名密钥需要在发布时间和
当前时间都可用。历史验证使用保留的证书。

新 APT 签名使用 SHA-256。新的发布尝试要求两份 APT 签名都使用 SHA-256、SHA-384 或 SHA-512。
升级包含 SHA-1 元数据签名的工作区后，先运行 `build`，再开始新发布。
已有发布尝试继续使用其记录的文件。

<span id="rpm-包体签名" data-td-print-local></span>
<span id="信任环彼此独立验证" data-td-print-local></span>

## 配置 RPM 包签名

```yaml
signing:
  rpm:
    packages:
      mode: fill
      key: agent://7F721C4AD40F4A9D8CA578BFAC7E4690B50CCF3B
      trusted_keys: [keys/upstream.asc]
```

| 模式 | 行为 |
|---|---|
| `never` | 原样保存输入字节 |
| `fill` | 已有签名可由当前密钥或受信密钥验证时保留原包，其余包签名 |
| `always` | 已由当前密钥签名的包保留原样，其余包重签 |

没有密钥时默认 `never`，有密钥时默认 `fill`。`fill` 和 `always` 都必须配置密钥。

包签名在私有副本上调用主机的 `rpm --addsign` 或 `rpm --resign`。
安装 `rpm`、`gpg`，并确保 `rpm` 使用的 GPG 环境中有对应私钥。
密钥引用只标识签名者，不会把私钥导入该环境。原始输入文件保持不变。

SOW 检查签名结果、包坐标及排除签名头后的包体摘要。已有对象的坐标和包体相同、
且符合当前策略时，可复用已有签名字节。`never` 模式要求字节完全相同才能复用。

包签名工作流请使用 RPM 格式 v4。SOW 不支持 RPM 格式 v6 使用的签名标签。
这与 OpenPGP 签名报文版本不同；历史 CentOS 的 OpenPGP v3、v4 签名受支持。

<span id="更换密钥会让-dist-变-dirty" data-td-print-local></span>

## 更换密钥

签名身份变化会使相关 Dist 变脏。更换元数据密钥后，运行 `build` 生成新签名，
并在发布新元数据前把新公钥分发给客户端。

已有包池对象不可变，修改 RPM 包签名策略不会原地重签这些对象。
逐步轮换包签名密钥时：

1. 将新密钥设为当前密钥，使用 `mode: fill`。
2. 旧包仍为成员时，在 `trusted_keys` 中保留旧公钥。
3. 加入由新密钥签名的新版本包。
4. 旧签名包退出成员集合或被新版本替代后，再移除旧信任。

直接换新密钥并使用 `always`，要求所有期望成员 RPM 已符合新密钥策略。
若重签会使同一包 URL 对应不同字节，应使用新的包发行版本和文件名。

RPM 验证按包的签名时间检查证书和签名子钥是否有效。证书保留了所需历史自签名与子钥绑定时，
续期本身不会使旧包签名失效。导出续期公钥时保留这些历史公钥信息。

<span id="plain-模式" data-td-print-local></span>

## Plain 签名

```bash
sow create /srv/offline --sign-with 6D5C5A26C36B1F73
sow create /srv/offline --sign-with 6D5C5A26C36B1F73 --overwrite
```

Plain 模式只签 RPM 包文件。不带 `--overwrite` 时，为没有可解析内嵌签名的包签名；
带该选项时，重签全部保留的 RPM。密钥标识为 16、40 或 64 位十六进制字符，
可带 `0x` 前缀。执行 `--pigsty` 清理后，至少需要剩余一个 RPM。

客户端配置见[仓库签名](/zh/docs/tutorial/signing/)，完整字段见
[配置参考](/zh/docs/reference/config/)。

<span id="继续阅读" data-td-print-local></span>
