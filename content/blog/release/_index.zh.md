---
title: 发布注记
linkTitle: 发布注记
description: 各版本 SOW 的主要变更与升级说明。
url: "/zh/blog/release/"
weight: 20
icon: fa-solid fa-tag
sidebar_expanded: true
categories: [Release]
tags: [release]
images: [/images/blog/sow-release.webp]
featured_image: wash
cascade:
  # The purpose-made release banner, not the generic social card: it is the
  # image the index cards crop to 16:9 and the one every release note carries.
  images: [/images/blog/sow-release.webp]
  # OINK 1.5.1 renders it behind the article header at a tenth of its opacity,
  # masked out before the text starts -- a post takes a colour from its subject
  # without spending any contrast on it.
  featured_image: wash
---

查看各版 SOW 的变化和升级步骤，版本按从新到旧排列。

[SOW 0.9.0](/zh/blog/release/sow-v0.9.0/) 让平面 `create` 与 `prune` 默认容错并提供 `--strict` 选项，新增 RPM 格式 v6 与原生 OPENPGP 多签名验签，同时支持 `sow.yml` 与 `sow.yaml`，支持 ECDSA/DSA 元数据签名与 FIFO 口令文件，并使目标 GC 宽限期直接遵循 `max_cache_ttl`。0.5.0 至 0.8.0 的工作区保持 schema v13；升级前请检查配置为 `max_cache_ttl: 0s` 的发布目标，详见 [0.9.0 升级说明](/zh/docs/start/install/#upgrade-to-090)。

[SOW 0.8.0](/zh/blog/release/sow-v0.8.0/) 新增按需 R2 条件删除（`sow gc TARGET --delete`），支持工作区外的外部密钥与口令文件符号链接挂载，移除 `.deb` 的 `control.tar.lzma` 支持，加固 DEB/RPM 校验，并提升大型仓库发布与 GC 性能。0.5.0 至 0.7.1 的工作区保持 schema v13，升级前需先完成中断的 0.7.1 本地 GC，详见 [0.8.0 升级说明](/zh/docs/start/install/#upgrade-to-080)。

[SOW 0.7.1](/zh/blog/release/sow-v0.7.1/) 升级到 Go 1.27.4，更新依赖，并修复恢复、输入校验和 S3/R2 处理。0.5.0 至 0.7.0 的工作区无需迁移数据库，详见 [0.7.1 升级说明](/zh/docs/start/install/#upgrade-to-071)。

[SOW 0.7.0](/zh/blog/release/sow-v0.7.0/) 新增平面 RPM 仓库裁剪与口令文件签名，修复迁移和恢复缺陷并更新依赖。0.5.0 至 0.6.1 的工作区无需迁移数据库，详见 [0.7.0 升级说明](/zh/docs/start/install/#升级到-070)。

[SOW 0.6.1](/zh/blog/release/sow-v0.6.1/) 升级到 Go 1.27.3，更新依赖，并修复无效输入的错误信息。
已使用 0.5.0 或 0.6.0 的工作区无需迁移数据库，详见[升级说明](/zh/docs/start/install/#升级到-061)。
