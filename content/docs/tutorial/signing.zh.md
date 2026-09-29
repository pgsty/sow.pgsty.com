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

SOW 提供两条互相独立的签名路径：

| 路径 | 产物 | 客户端开关 |
|---|---|---|
| RPM 元数据 | `repodata/repomd.xml.asc` | `repo_gpgcheck=1` |
| APT 元数据 | `InRelease` 与 `Release.gpg` | `Signed-By` |
| RPM 包体 | RPM 内嵌签名 | `gpgcheck=1` |

APT 通过签名的 `Release` 信任包哈希；SOW 不重签 DEB 包体。先配置元数据签名；只有当你负责
这些 RPM 字节的签名策略时，再启用包体签名。

## 1. 创建专用密钥

下面生成一把无口令的示例密钥。生产环境应使用受保护密钥并配置 `passphrase` 引用，详见
[配置参考](/zh/docs/reference/config/#passphrase-引用)。

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

私钥必须放在 Workspace 公共 Repository 树与所有 Web Root 之外。若 SOW 由专用服务账户运行，
目录 owner 应是该账户，而不是交互用户。只向客户端分发 `repo-signing.pub`。

## 2. 配置元数据签名

在 `/srv/sow/sow.yml` 的 Repository 下添加所需配置；未使用的包生态可以省略：

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

解析密钥引用、重建并执行发布门禁：

```bash
cd /srv/sow
sow config check
sow build -r pigsty
sow check -r pigsty
```

受口令保护的密钥可在 `key` 旁增加 `passphrase: env://SOW_METADATA_PASSPHRASE`，或使用
有界文件引用。SOW 不会把密钥或口令内容写入配置、SQLite、JSON 或日志。

## 3. 手工验证元数据

按实际 Dist 与架构调整路径：

```bash
gpg --verify \
  pigsty/dists/el9/x86_64/repodata/repomd.xml.asc \
  pigsty/dists/el9/x86_64/repodata/repomd.xml

gpg --verify pigsty/dists/trixie/InRelease
gpg --verify \
  pigsty/dists/trixie/Release.gpg \
  pigsty/dists/trixie/Release
```

`sow check` 会在深度一致性校验中检查配置的签名身份。建立客户端信任根时，仍应手工验证一次。

## 4. 可选：签署 RPM 包体

只有客户端要求内嵌包签名时，才添加 `rpm.packages`：

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

将占位符替换为 `$FPR` 中的 40 位十六进制指纹。该操作要求：

- 安装 `rpm` 与 `gpg`；
- 匹配的私钥存在于 `rpm` 使用的环境 GPG Keyring 中；
- `fill` 保留已经由配置 key 或 `trusted_keys` 签好的包；
- `always` 重签所有未由配置身份签好的包；
- `never` 保持输入字节不变。

SOW 只会对私有 staged 副本调用 `rpm --addsign` 或 `rpm --resign`，不会修改输入文件。
这些规则适用于新导入的包；`build` 不会重签已有的不可变包对象。在启用 `fill` 或更换
key 前，确认 **所有已有 RPM** 都由配置 key 或受信任身份签署。只检查 `signature_key`
是否为空还不够：已有的第三方签名也可能不受新策略信任。若确实信任该签名身份，可将其
公钥加入 `trusted_keys`；否则先在仓库外准备正确签名的包，使用新的包版本与文件名导入，或从
原始包重建新仓库。准备完成前保留旧策略。策略拒绝会保留已有 Desired 状态。

确认已有包兼容后，再校验并构建：

```bash
sow config check
sow build -r pigsty
sow check -r pigsty
```

用 `rpmkeys --checksig /path/to/package.rpm` 检查结果。

## 5. 启用 dnf 验签

通过可信通道把公钥传到客户端：

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

没有配置包体签名时，将 `gpgcheck` 设为 `0`；既然已经配置元数据签名，就不要关闭
`repo_gpgcheck`。

## 6. 启用 APT 验签

将公钥安装为独立 Keyring：

```bash
sudo gpg --dearmor --yes \
  --output /usr/share/keyrings/pigsty-archive-keyring.gpg /path/to/repo-signing.pub
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

执行 `apt update`。任何签名错误都应视为部署失败，不能靠削弱客户端配置绕过。

## Plain 模式 RPM 签名

Plain 模式可以签署 RPM 包体，但不会签署仓库元数据，也不会生成 APT `Release`：

```bash
sow create /srv/flat --sign-with 0123456789ABCDEF
```

key 去掉可选的 `0x` 或 `0X` 前缀后，必须是恰好 16、40 或 64 位十六进制字符；SOW 会去掉
前缀并规范化为大写。匹配私钥必须能被环境中的
`rpm`/GPG 使用。不带 `--overwrite` 时，已有签名的 RPM 保持字节不变；带上该参数则显式重签
所有 RPM。SOW 先签署私有 staged 副本，再替换包体与元数据。

已有签名并不等于由 `--sign-with` 指定的密钥签署。如果要求全部 RPM 都使用自己的密钥，
应逐包验证，在候选副本上选择性重签不匹配的包；也可以明确使用 `--overwrite` 重签全部包。

已有在线 YUM 仓库还应保留发布时间。SOW 0.5.0 新增 `--metadata-timestamp`；最后一次
`create` 完成后，发布前应单独签署并验证新的 `repomd.xml`。包签名与索引签名是两项独立
检查。完整顺序及带缓存客户端验收见 [YUM 迁移指南](/zh/docs/tutorial/yum-migration/)。

## 更换密钥

在 Managed 模式中，改变 key 引用或解析出的指纹会让相关 Dist 变为 dirty。元数据 key 可以先分发新公钥，再重建、
校验并切换客户端。RPM 包 key 必须分阶段轮换：Package Object 不可变，`build` 遇到不满足新策略的
既有 RPM 会拒绝，而不是原地重签。旧软件包坐标尚未下架或由新 Release 替代前，应使用 `fill`
并把旧公钥保留在 `trusted_keys`。最后在目标环境做真实客户端验收。

最后应使用生产中的确切 dnf/APT 版本与信任策略验收签名仓库。自动化覆盖见
[平台与集成](/zh/docs/reference/compatibility/)。
