---
title: "仓库签名"
linkTitle: "仓库签名"
description: "生成专用 GPG 签名钥,为仓库元数据与 RPM 包签名,并配置客户端拒绝一切未签名内容。"
url: "/zh/docs/tutorial/signing/"
weight: 300
icon: fa-solid fa-key
---

没签名的仓库,链路上任何人都能改写。这篇教程把这个洞堵上:生成签名钥、配置 SOW 对发布内容签名、
手工验证签名,再打开客户端强制校验,让 `dnf` 与 `apt` 拒绝一切校验不过的东西。

预计二十分钟。

## 两条互相独立的信任链

软件仓库里有两样东西值得签名,而它们不是一回事。

**仓库元数据**回答"这份索引是不是发布者产出的那份?"。RPM 侧是对 `repomd.xml` 的分离签名,
发布为 `repodata/repomd.xml.asc`;APT 侧是 `InRelease`(`Release` 正文带内联签名)与
`Release.gpg`(对同一份 `Release` 的分离签名)。SOW 用 Go 的 OpenPGP 实现在进程内完成元数据签名
——除非你指向 GPG agent,否则不需要外部 `gpg` 二进制。

**包体**回答"这个 `.rpm` 是不是它声称的那家做的?"。这个签名嵌在 RPM 包头里,随文件走,因此
在镜像和离线拷贝之后依然有效。SOW 对私有 stage 副本调用 `rpm --addsign` / `rpm --resign` 来签
RPM 包,所以环境里必须有 `rpm` 可执行文件。

DEB 包在通用实践中没有等价的带内签名;APT 的信任来自已签名的 `Release`,它覆盖索引,索引又覆盖
每个包的 SHA-256。

| | 签什么 | 产出 | 需要外部工具 |
|---|---|---|---|
| RPM 元数据 | `repomd.xml` | `repodata/repomd.xml.asc` | 否(除非用 `agent://`) |
| APT 元数据 | `Release` | `InRelease`、`Release.gpg` | 否(除非用 `agent://`) |
| RPM 包体 | `.rpm` 包头 | 重写后的包字节 | 是——`rpm` 及其 GPG 环境 |

两者独立配置。先做元数据签名:成本低、不需要额外工具,而且 `repo_gpgcheck` 与 `Signed-By`
验的就是它。

## 第 1 步:生成专用签名钥

不要复用个人密钥。仓库密钥会被拷到构建机上、活好几年;给它独立身份,吊销时才不会殃及其他。

写一份 batch 参数文件:

```bash
mkdir -p ~/secure && chmod 700 ~/secure
cat > ~/secure/keyparams <<'EOF'
%no-protection
Key-Type: RSA
Key-Length: 4096
Key-Usage: sign
Name-Real: Pigsty Repository Signing Key
Name-Email: repo@example.com
Expire-Date: 0
%commit
EOF
gpg --batch --gen-key ~/secure/keyparams
```

```console
gpg: keybox '/home/you/.gnupg/pubring.kbx' created
gpg: /home/you/.gnupg/trustdb.gpg: trustdb created
gpg: directory '/home/you/.gnupg/openpgp-revocs.d' created
gpg: revocation certificate stored as '/home/you/.gnupg/openpgp-revocs.d/C811FBFBFE4031E5E2D7047904DD7F129A7B65E7.rev'
```

`Key-Usage: sign` 生成只用于签名的密钥,不带加密子钥——这里没有要加密的东西。`Expire-Date: 0`
表示不过期;如果你希望有轮换节奏,写成 `2y` 之类,并规划好[第 8 步](#step-8-rotate-the-key)。

`%no-protection` 生成不带 passphrase 的密钥,适合无人值守构建——此时文件权限就是保护。想用
passphrase 的话把那行换成 `Passphrase: 你的口令`,并看[第 6 步](#step-6-key-references)。

查指纹:

```bash
gpg --list-keys --keyid-format=long repo@example.com
```

```console
pub   rsa4096/04DD7F129A7B65E7 2026-08-04 [SC]
      C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
uid                 [ultimate] Pigsty Repository Signing Key <repo@example.com>
```

{{% alert title="保存吊销证书" color="warning" %}}
`gpg --gen-key` 把吊销证书写到了 `~/.gnupg/openpgp-revocs.d/`。把它拷到一个即使这台主机没了也能
拿到的地方。没有它,你没办法告诉客户端这把钥匙作废了。
{{% /alert %}}

## 第 2 步:导出密钥的两半

SOW 读 ASCII-armored **私钥**来签名,客户端需要 armored **公钥**来验签。

```bash
FPR=C811FBFBFE4031E5E2D7047904DD7F129A7B65E7

gpg --armor --export-secret-keys "$FPR" > ~/secure/repo-signing.asc
chmod 600 ~/secure/repo-signing.asc

gpg --armor --export "$FPR" > ~/secure/RPM-GPG-KEY-pigsty
```

```bash
ls -l ~/secure
```

```console
-rw-------  1 you you  3457 Aug  4 12:25 repo-signing.asc
-rw-r--r--  1 you you  1709 Aug  4 12:25 RPM-GPG-KEY-pigsty
```

`repo-signing.asc` 是秘密;`RPM-GPG-KEY-pigsty` 是给人下载的,放在仓库旁边让客户端能取到。
同一个文件两套生态通用,`RPM-GPG-KEY-` 前缀只是 Enterprise Linux 的命名习惯。

## 第 3 步:配置元数据签名

签名按仓库配置在 `sow.yml` 里。没有命令行覆盖——用什么签了这棵树是配置的属性,而且会记进操作日志。

```yaml
schema: sow/v3
architectures:
  - x86_64
  - aarch64

repos:
  pigsty:
    signing:
      rpm:
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
      deb:
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
    dists:
      el9:
        format: rpm
        limit: 1
        exclude:
          - kind: [debuginfo, debugsource]
      trixie:
        format: deb
```

`file://` 后面接绝对路径,所以是三条斜杠:`file://` 加上 `/home/...`。

构建之前先校验密钥能否解析、能否用于签名:

```bash
sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=2
```

`sow config show --all` 展开默认值并报出 SOW 解析到的指纹——绝不输出密钥内容:

```bash
sow config show --all
```

```console
schema: sow/v3
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    protected: false
    signing:
      rpm:
        packages:
          mode: never
        metadata:
          key: file:///home/you/secure/repo-signing.asc
          key_fingerprint: C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
      deb:
        metadata:
          key: file:///home/you/secure/repo-signing.asc
          key_fingerprint: C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 1
        exclude:
          - kind:
              - debuginfo
              - debugsource
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

秘密内容永远不会进入配置输出、SQLite、操作日志、JSON 或错误文本。如果你在 SOW 的任何输出里看见了
密钥字节,那是个值得上报的 bug。

## 第 4 步:构建已签名的树

签名身份是"已构建代"定义的一部分,所以改签名配置会让相关 Dist 全部变 dirty:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=6 dirty_dists=el9,trixie pending=0/0 locked=false
```

```bash
sow build
```

```console
{"operation":"5414596509861246745","repository":"pigsty","dists":["el9","trixie"],"desired_revision":6,"built_generation":7,"noop":false,"dirty":false}
```

```bash
find pigsty/dists \( -name "*.asc" -o -name "InRelease" -o -name "Release.gpg" \) | sort
```

```console
pigsty/dists/el9/aarch64/repodata/repomd.xml.asc
pigsty/dists/el9/x86_64/repodata/repomd.xml.asc
pigsty/dists/trixie/InRelease
pigsty/dists/trixie/Release.gpg
```

每个 RPM 架构视图一份 `.asc`,DEB Dist 两种 APT 签名形式都有。`Release` 仍然与 `InRelease`
并存——有些工具还在读它,而 `Release.gpg` 正好覆盖它。

## 第 5 步:自己验一遍签名

别只听构建过程的一面之词,三个都验:

```bash
gpg --verify pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
             pigsty/dists/el9/x86_64/repodata/repomd.xml
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

```bash
gpg --verify pigsty/dists/trixie/InRelease
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

```bash
gpg --verify pigsty/dists/trixie/Release.gpg pigsty/dists/trixie/Release
```

```console
gpg: Signature made Tue Aug  4 12:25:13 2026 CST
gpg:                using RSA key C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
gpg: Good signature from "Pigsty Repository Signing Key <repo@example.com>" [ultimate]
```

`InRelease` 是 clearsign 文档——`Release` 正文原样在里面:

```bash
head -13 pigsty/dists/trixie/InRelease
```

```console
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

Origin: SOW
Label: trixie
Suite: trixie
Codename: trixie
Date: Tue, 04 Aug 2026 04:25:13 UTC
X-SOW-Generation: 7
Architectures: amd64 arm64
Components: main
Acquire-By-Hash: yes
Description: SOW managed distribution
```

`sow check` 的完整校验里包含所有声明签名的验证,所以在 CI 里这一步是白送的:

```bash
sow check
```

```console
repository=pigsty status=clean ready_to_copy=true revision=6 generation=7
config	ok=true	checked=5
state	ok=true	checked=1
public-modes	ok=true	checked=99
package-bytes	ok=true	checked=18
desired-membership	ok=true	checked=15
index	ok=true	checked=2
signature	ok=true	checked=20
generation-manifest	ok=true	checked=7
```

## 第 6 步:密钥引用与 passphrase {#step-6-key-references}

`key:` 接受三种引用形态。

`file:///绝对路径` 从磁盘读 armored 私钥,在进程内签名。这是默认选择:不需要外部工具、不需要
agent,Linux 与 macOS 行为一致。

`env://变量名` 从环境变量读 armored 私钥。适合密钥由 secret manager 在运行时注入、你又不想落盘的
场景。变量里放的是密钥本身,不是路径:

```yaml
key: "env://SOW_METADATA_KEY"
```

```bash
sow config check
```

```console
operation rejected: managed: operation rejected: repository "pigsty" signing: rpm metadata key: environment key reference SOW_METADATA_KEY is unset
```

退出码 `6`。设上变量之后:

```bash
SOW_METADATA_KEY="$(cat ~/secure/repo-signing.asc)" sow config check
```

```console
configuration valid: /home/you/repo repositories=1 dists=2
```

`agent://指纹` 委托给正在运行的 `gpg-agent`,私钥不出 agent——密钥在智能卡或 YubiKey 上时应该选它。
这种形态会调用环境里的 `gpg`,并且不能配 passphrase 引用:解锁是 agent 的事,走 pinentry 或预置。

### 带 passphrase 的密钥

对受保护的 `file://` 与 `env://` 密钥,在 `key:` 旁边加 `passphrase:`。它用同一套引用文法,
所以口令本身可以不进配置文件:

```yaml
signing:
  rpm:
    metadata:
      key: "file:///home/you/secure/repo-signing-2027.asc"
      passphrase: "env://SOW_METADATA_PASSPHRASE"
  deb:
    metadata:
      key: "file:///home/you/secure/repo-signing-2027.asc"
      passphrase: "env://SOW_METADATA_PASSPHRASE"
```

缺失时失败关闭,而不是产出一棵未签名的树:

```bash
sow config check
```

```console
operation rejected: managed: operation rejected: repository "pigsty" signing: managed: resolve RPM metadata passphrase: environment passphrase reference is unset
```

```bash
SOW_METADATA_PASSPHRASE='...' sow build
```

## 第 7 步:给 RPM 包签名

元数据签名证明索引是你的;包签名证明每个 `.rpm` 是你的——别人镜像你的仓库、或从里面单独拷走一个
文件之后,这层结论依然成立。客户端 `gpgcheck=1` 验的就是它。

配置在 `signing.rpm.packages` 下:

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: fill
          key: "agent://C811FBFBFE4031E5E2D7047904DD7F129A7B65E7"
          trusted_keys: [keys/pgdg.asc]
        metadata:
          key: "file:///home/you/secure/repo-signing.asc"
```

三种模式:

| 模式 | 行为 |
|---|---|
| `never` | 原样保留输入字节;没有 key 时唯一可用的模式,也是默认值 |
| `fill` | 无签名或签名不受信任时用配置 key 签;已有签名能被 `trusted_keys` 验证通过则保留 |
| `always` | 确保最终包由配置 key 有效签名;已经是就保留字节,否则重签 |

混合上游包与自研包的仓库通常选 `fill`:列在 `trusted_keys` 里的上游签名保留,其余全部换成你的。
配置 key 自己的公钥半边总是自动包含在 `trusted_keys` 里,不必手写。

实践中有两点要注意。包签名会重写字节,所以进入仓库的对象是签名后的包而不是输入文件。另外它要求
环境里装了 `rpm`,并且 GPG 环境确实能用那把私钥;缺少任一条件时命令会在发布任何东西之前失败,
而不是悄悄退回未签名。

你的输入文件永远不会被修改。签名发生在私有 stage 副本上,结果会被重新解析并验证——签名存在、
NEVRA 未变、最终 SHA-256 已记录——之后才允许进入包池。

即使签名嵌了时间戳、字节不可复现,重复 add 同一个未签名 RPM 仍是 no-op:SOW 另存一份对不可变
header 与 payload 计算的 signature-neutral 摘要,据此识别出这是同一次重试,复用已经签过的对象
而不是再造一个。

### Plain 平面模式签名

Plain 模式没有配置文件,所以授权必须显式写在命令行上:

```bash
sow create /srv/repo --sign-with C811FBFBFE4031E5E2D7047904DD7F129A7B65E7
```

`--sign-with` 只签当前未签名的包。加 `--overwrite` 用 `rpm --resign` 全量重签:

```bash
sow create /srv/repo --sign-with C811FBFBFE4031E5E2D7047904DD7F129A7B65E7 --overwrite
```

KEY 必须是 16、40 或 64 位十六进制 GPG key ID 或指纹,并且私钥在该环境里必须已经能被 `rpm` 使用
——SOW 通过 `_gpg_name` macro 传递身份,从不经手你的 passphrase。在没装 `rpm` 的主机上,命令在
碰目录之前就停下:

```console
plain: sign rpm pev2-1.22.0-1.noarch.rpm: rpm executable is required for --sign-with
```

两个值得知道的参数错误:

```bash
sow create /srv/repo --sign-with ABC123
```

```console
usage error: --sign-with must be a 16, 40, or 64 hexadecimal GPG key ID/fingerprint
```

```bash
sow create /srv/repo --overwrite
```

```console
usage error: --overwrite requires --sign-with
```

两者都是退出码 `2`。签名与元数据在发布前一起验证:任一签名失败,目录保持原状。

## 第 8 步:轮换密钥 {#step-8-rotate-the-key}

改动密钥引用或它的指纹会让相关 Dist 全部变 dirty,因为签名者是"已构建代"定义的一部分:

```bash
sow status
```

```console
repository=pigsty status=dirty ready_to_copy=false revision=6 generation=7 dirty_dists=el9,trixie pending=0/0 locked=false
```

```bash
sow build
```

```console
{"operation":"3752151705135652397","repository":"pigsty","dists":["el9","trixie"],"desired_revision":6,"built_generation":8,"noop":false,"dirty":false}
```

```bash
gpg --verify pigsty/dists/trixie/InRelease
```

```console
gpg: Signature made Tue Aug  4 12:25:43 2026 CST
gpg:                using RSA key D856A1034A0B8BCDC20FA54F63E1D670C57DB46A
gpg: Good signature from "Pigsty Repository Signing Key <repo-2027@example.com>" [ultimate]
```

元数据轮换之所以这么简单,是因为元数据每次 build 都重新生成。轮换**包**签名钥则不然:重签会改变
包字节,而仓库不允许同一坐标下存在两份不同字节。想重签的包应当提高 release 号,或者把新钥作为
额外受信任密钥发布、让它从此对新包生效。

新公钥要与旧的并行发布一段时间,给客户端留出导入的时间,再下线旧的。

## 第 9 步:在客户端强制校验

签名只有在客户端真去验的时候才有意义。

### dnf 与 yum

把 armored 公钥发布到仓库旁边,然后:

{{< tabpane persist="header" >}}
{{< tab header="EL8 / EL9 / EL10" lang="ini" >}}
[pigsty-el9]
name=Pigsty EL9 - $basearch
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
{{< /tab >}}
{{< tab header="导入密钥" lang="bash" >}}
curl -fsSL https://repo.example.com/RPM-GPG-KEY-pigsty \
  -o /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
rpm -q gpg-pubkey --qf '%{name}-%{version}-%{release} %{summary}\n'
{{< /tab >}}
{{< /tabpane >}}

这两个开关验的是不同东西,两个都要开:

- `repo_gpgcheck=1` 验 `repodata/repomd.xml.asc`,也就是第 4 步那条元数据链。不开它,能改写索引的
  攻击者就能藏包或把你降级到旧版本。
- `gpgcheck=1` 验每个 `.rpm` 内部的签名,也就是第 7 步那条包体链。这要求包签名已经配好;
  在 `mode: never` 下,你的包带着进来时是什么签名就是什么签名,未签名的会被拒绝。

元数据签名一上线就把 `repo_gpgcheck` 打开;包签名到位、或者你发布的每个包本来就带着客户端信任的
签名之后,再打开 `gpgcheck`。

已在 AlmaLinux 8/9/10 上双开实测通过。

### apt

APT 验的是已签名的 `Release`;逐包信任由索引里的 SHA-256 推导而来。

{{< tabpane persist="header" >}}
{{< tab header="deb822" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.sources
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Signed-By: /etc/apt/keyrings/pigsty.asc
{{< /tab >}}
{{< tab header="传统 sources.list" lang="ini" >}}
# /etc/apt/sources.list.d/pigsty.list
deb [signed-by=/etc/apt/keyrings/pigsty.asc] https://repo.example.com/pigsty trixie main
{{< /tab >}}
{{< tab header="安装密钥" lang="bash" >}}
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://repo.example.com/RPM-GPG-KEY-pigsty \
  -o /etc/apt/keyrings/pigsty.asc
chmod 0644 /etc/apt/keyrings/pigsty.asc
apt update
{{< /tab >}}
{{< /tabpane >}}

`Signed-By` 把密钥限定到这一个仓库,这也是它取代 `apt-key add` 的原因——全局添加的密钥可以为系统上
任何源背书。直接用 armored `.asc` 即可,现代 APT 不需要你先 dearmor。

已在 Debian 13(apt 3.0.3)与 Debian 12(apt 2.6.1)上实测通过。

{{% alert title="把逃生口拆掉" color="warning" %}}
如果你按[搭建 APT 仓库](/zh/docs/tutorial/apt-repo/)写过 `Trusted: yes` 或 `trusted=yes`,现在删掉。
它们会完全关闭校验,留一条就把这整篇教程的效果悄悄抵消了。
{{% /alert %}}

## 下一步去哪

{{< doc-cards cols="2" >}}
{{< doc-card title="签名模型" link="/zh/docs/feature/signing/" >}}
两条信任链的实现方式、签名者为什么进入 Built 配置摘要,以及重签对包身份意味着什么。
{{< /doc-card >}}
{{< doc-card title="对外服务" link="/zh/docs/tutorial/serving/" >}}
发布已签名的树,并拷到够不着构建机的主机上。
{{< /doc-card >}}
{{< doc-card title="配置参考" link="/zh/docs/reference/config/" >}}
全部签名字段、密钥引用文法与完整配置 schema。
{{< /doc-card >}}
{{< doc-card title="可观测与审计" link="/zh/docs/feature/audit/" >}}
哪次构建签了哪一代,以及怎么把这份记录导出来。
{{< /doc-card >}}
{{< /doc-cards >}}
