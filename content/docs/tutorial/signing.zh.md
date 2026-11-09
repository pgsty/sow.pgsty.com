---
title: "仓库签名"
linkTitle: "仓库签名"
description: "签署 RPM 与 APT 元数据，可选签署 RPM 包体，并启用客户端验签。"
categories: [Tutorial]
tags: [signing, apt, yum]
url: "/zh/docs/tutorial/signing/"
weight: 300
icon: fa-solid fa-key
---

仓库签名分为元数据签名与 RPM 软件包签名两层，需要分别配置：

| 路径 | 产物 | 客户端开关 |
|---|---|---|
| RPM 元数据 | `repodata/repomd.xml.asc` | `repo_gpgcheck=1` |
| APT 元数据 | `InRelease` 与 `Release.gpg` | `Signed-By` |
| RPM 包体 | RPM 内嵌签名 | `gpgcheck=1` |
{.wide .expand}

APT 通过签名的 `Release` 文件验证包哈希，因此 DEB 不需要单独的包签名。先配置元数据签名；客户端要求 `gpgcheck=1` 时，再配置 RPM 软件包签名。

本教程使用 [YUM](/zh/docs/tutorial/yum-repo/) 或 [APT](/zh/docs/tutorial/apt-repo/) 教程中的 `pigsty` 仓库。只执行你已创建的格式与 Dist 所对应的命令。

## 1. 创建专用密钥 {#1-create-a-dedicated-key}

先安装 GPG。下面生成一把无口令的测试密钥，并导出到私有目录。已有带口令密钥时，按下文配置 `passfile`。

```bash
SIGNING_UID='SOW Repository <repo@example.com>'
gpg --batch --pinentry-mode loopback --passphrase '' \
  --quick-generate-key "$SIGNING_UID" rsa3072 sign 2y

FPR="$(gpg --batch --with-colons --list-secret-keys "$SIGNING_UID" \
  | awk -F: '$1 == "fpr" {print $10; exit}')"
test -n "$FPR"

sudo install -d -m 0700 /srv/sow-secrets
sudo chown "$(id -u):$(id -g)" /srv/sow-secrets
gpg --batch --pinentry-mode loopback --passphrase '' --armor \
  --export-secret-keys "$FPR" > /srv/sow-secrets/repo-signing.asc
gpg --armor --export "$FPR" > /srv/sow-secrets/repo-signing.pub
chmod 600 /srv/sow-secrets/repo-signing.asc
```

SOW 从公共仓库目录之外的 `/srv/sow-secrets` 读取私钥。如果 SOW 服务账户不同于当前用户，给该账户目录访问权限。向客户端分发 `repo-signing.pub`。

## 2. 配置元数据签名 {#2-configure-metadata-signing}

在 `/srv/sow/sow.yml` 中，将以下元数据配置合并到仓库已有的 `signing` 块。保留包签名策略与 Dist 定义，只加入使用的格式：

```yaml
repos:
  pigsty:
    signing:
      rpm:
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
      deb:
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
    dists:
      # 保留已有 Dist 定义
```

带口令的密钥应先配置口令来源，再检查或构建。可在 `key` 旁增加
`passfile: /run/secrets/gpg-password`，或执行
`export SOW_GPG_PASSFILE=/run/secrets/gpg-password`。单次执行可以使用
`sow build -r pigsty --passfile /run/secrets/gpg-password`，`agent://FINGERPRINT` 密钥同样支持。
口令文件放在仓库之外，权限建议为 `0600`。内容就是口令：非空 UTF-8 单行，可以带一个
末尾 LF 或 CRLF。SOW 保留空格与制表符，且不自动搜索默认文件。
优先级和完整格式见[口令文件](/zh/docs/reference/config/#passfile)。
旧 `passphrase` 引用继续兼容。配置只保存引用，不保存秘密值。

校验配置、重新构建并检查：

```bash
cd /srv/sow
sow config check
sow build -r pigsty
sow check -r pigsty
```

<span id="3-手工验证元数据" data-td-print-local></span>

## 3. 可选：查看元数据签名者 {#3-verify-metadata-manually}

前面的 `sow check` 已验证元数据签名。需要用 GPG 查看签名者时，执行对应 Dist 的命令：

```bash
gpg --verify \
  pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
  pigsty/dists/el9/x86_64/repodata/repomd.xml

gpg --verify pigsty/dists/trixie/InRelease
gpg --verify \
  pigsty/dists/trixie/Release.gpg \
  pigsty/dists/trixie/Release
```

将显示的指纹与分发给客户端的公钥指纹比较。

## 4. 可选：签署 RPM 包体 {#4-optional-sign-rpm-package-bodies}

新仓库应在导入 RPM 前配置包签名。在已有 `signing.rpm` 下增加以下配置：

```yaml
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: fill
          key: agent://REPLACE_WITH_THE_FINGERPRINT
        metadata:
          key: file:///srv/sow-secrets/repo-signing.asc
```

将占位符替换为 `$FPR` 中的 40 位十六进制指纹。安装 `rpm` 与 `gpg`，
并将私钥放在 `rpm` 使用的 GPG 密钥环中。

`fill` 会签署新导入的包；如果已有签名能通过配置密钥或 `trusted_keys` 验证，则保留原签名。SOW 支持验证 RSA、DSA、ECDSA 与 EdDSA RPM 签名，包括保存在 RPM 签名头 tag 267（`RPMSIGTAG_DSA`）中的纯头签名。
其他模式见 [RPM 签名策略](/zh/docs/reference/config/)。

包签名密钥带口令时，在 `signing.rpm.packages` 下配置 `passfile`，或使用
`SOW_GPG_PASSFILE`。`metadata` 下的 `passfile` 只适用于对应的元数据密钥。
`config check` 会校验包签名前置条件，但不会通过签包来测试口令。下面的 `add`
必须实际遇到需要签名的包，才会验证这条路径。

SOW 在 `add` 时签署私有副本，输入文件保持不变。`build` 检查包池中的 RPM 是否满足策略，不会重签它们。

已有 RPM 时，先检查签名再启用 `fill`。把信任的上游公钥保留在 `trusted_keys` 中。对于包池中未签名或不受信任的包，准备使用新版本、新文件名且签名正确的包；也可以先配置签名，再把原始包导入新仓库。

配置策略后，导入新包并检查结果：

```bash
sow config check
sow add /path/to/new.rpm -r pigsty -d el9
sow check -r pigsty
```

需要独立查看包签名时，对 `pigsty/pool/` 中的包文件执行 `rpmkeys --checksig`。

## 5. 启用 DNF 验签 {#5-enable-dnf-verification}

先[发布已签名仓库](/zh/docs/tutorial/serving/)，再通过可信通道把公钥传到客户端：

```bash
sudo install -m 0644 /path/to/repo-signing.pub /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
```

再打开与你实际签名范围对应的检查：

```ini
[pigsty-el9]
name=Pigsty EL9
baseurl=https://repo.example.com/pigsty/dists/el9/$basearch/
enabled=1
repo_gpgcheck=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-pigsty
```

只签名元数据时，使用 `repo_gpgcheck=1` 与 `gpgcheck=0`。启用包验签时，除了自己的公钥，也要安装所信任的上游包签名公钥。随后执行 `sudo dnf makecache --refresh` 并安装一个包。

## 6. 启用 APT 验签 {#6-enable-apt-verification}

[发布已签名仓库](/zh/docs/tutorial/serving/)后，在客户端将公钥安装为独立密钥环：

```bash
sudo gpg --dearmor --yes \
  --output /usr/share/keyrings/pigsty-archive-keyring.gpg /path/to/repo-signing.pub
sudo chmod 0644 /usr/share/keyrings/pigsty-archive-keyring.gpg
```

在 deb822 配置中引用它，且不要设置 `Trusted: yes`：

```ini
Types: deb
URIs: https://repo.example.com/pigsty
Suites: trixie
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/pigsty-archive-keyring.gpg
```

执行 `sudo apt update` 并安装一个包。验签失败时，核对客户端公钥环指纹与 `gpg --verify` 显示的签名者是否一致。ARM64 客户端将 `Architectures` 改为 `arm64`。

## Plain 模式 RPM 签名 {#plain-mode-rpm-signing}

Plain 模式可以签署 RPM 包体，但不会签署仓库元数据，也不会生成 APT `Release`：

```bash
sow create /srv/flat --sign-with 0123456789ABCDEF
```

将 `0123456789ABCDEF` 换成你的密钥 ID 或指纹，匹配的私钥必须能被 `rpm` 与 GPG 使用。
SOW 保留已有签名（包括上游签名），并识别 RPM 签名头 tag 267（`RPMSIGTAG_DSA`）中的 RSA、DSA、ECDSA 与 EdDSA 纯头签名。需要全部换成自己的密钥时，在独立工作副本上使用 `--overwrite`。
密钥格式见 [`sow create`](/zh/docs/command/create/#signing-rpms)。

使用带口令的密钥时，增加 `--passfile /run/secrets/gpg-password`，或将
`SOW_GPG_PASSFILE` 设置为该路径。这些选项只为 SOW 签名提供口令；单独执行的
`gpg` 命令需要自己的凭据配置。

已有 YUM 仓库按[迁移指南](/zh/docs/tutorial/yum-migration/)保留发布时间，
并在最后一次 `create` 完成后签署 `repomd.xml`。

## 更换密钥 {#key-changes}

轮换元数据密钥时，先分发新公钥，再更新密钥引用，执行 `build`、`check` 与 `publish`。引用或解析出的指纹变化后，相关 Dist 会变为 dirty。

轮换 RPM 包密钥时，使用 `fill`，并在 `trusted_keys` 中保留旧公钥，直到旧密钥签署的软件包已撤下或替换。在此期间，也保留客户端对应的公钥。已有包对象保持不变。

用用户实际使用的 DNF 或 APT 版本测试最终仓库。自动化覆盖见[平台与集成](/zh/docs/reference/compatibility/)。
