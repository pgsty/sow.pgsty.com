---
title: 发布注记
linkTitle: 发布注记
description: SOW 发布注记，涵盖功能、性能、正确性、打包与验证。
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
  # OINK 0.6 renders it behind the article header at a tenth of its opacity,
  # masked out before the text starts -- a post takes a colour from its subject
  # without spending any contrast on it.
  featured_image: wash
---

查看各版 SOW 的变化和升级步骤，版本按从新到旧排列。

[SOW 0.6.0](/zh/blog/release/sow-v0.6.0/) 保留上一轮 Plain RPM 索引，并记录 Managed 发布时间。
它强化文件校验与恢复，减少重复 I/O。已使用 0.5.0 的工作区无需迁移数据库，详见[升级说明](/zh/docs/start/install/#升级到-060)。
