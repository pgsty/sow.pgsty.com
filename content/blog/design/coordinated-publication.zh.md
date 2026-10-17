---
title: "协同发布决策记录"
linkTitle: "发布决策"
date: 2026-08-14
lastmod: 2026-10-13
authors: [Vonng]
description: "SOW v0.4.0 为什么保留原生发布后端，没有采用早期的 rclone 提案。"
categories: [Design]
tags: [publish, transaction, object-storage, decision]
url: "/zh/blog/design/coordinated-publication/"
aliases:
  - "/docs/design/coordinated-publication/"
weight: 10
icon: fa-solid fa-cloud-arrow-up
draft: false
---

<span id="最终决策" data-td-print-local></span>

SOW 0.4.0 保留了原生 `filesystem` 与 `r2` 发布后端。早期提案曾计划使用 rclone，并增加远端审计和预览命令。
最终选择原生后端，是因为 SOW 需要逐项记录条件写入及其结果。

当前命令语法见 [`sow publish`](/zh/docs/command/publish/)。

<span id="为什么没有采用-executor-提案" data-td-print-local></span>
<span id="040-实际交付" data-td-print-local></span>

## 为什么保留原生后端

发布计划为每个文件记录预期 SHA-256 和操作。后端需要创建不可变对象，避免覆盖已有内容，并按条件更新可变入口文件。
SOW 记录操作结果，用于中断后继续发布。

批量复制工具需要额外的身份与检查点模型才能保留这些规则。0.4 选择改进已有后端：

- 支持条件式分段上传；
- 分别设置响应头和响应体空闲超时；
- 对可重复执行的操作重试；
- 通过公共 URL 校验变化的文件。

这保留了已有发布状态，也省去了传输工具的迁移。

<span id="原生增量发布" data-td-print-local></span>
<span id="强化公共可见性" data-td-print-local></span>
<span id="操作者流程" data-td-print-local></span>

## 发布流程

原生后端先上传软件包与不可变元数据，再更新仓库索引。
随后检查公开文件，并为目标记录发布检查点。下次发布以该检查点为基准，计算需要更新的文件。

<span id="操作者确认的-rebind" data-td-print-local></span>

## 修改目标设置

目标名称、公共 URL 或缓存时间的变化记录在绑定修订中，原发布历史继续保留。
使用不同存储位置时，需要配置新目标。

<span id="恢复决策" data-td-print-local></span>

## 继续中断的发布

SOW 为每次发布保存计划与进度。作出提交决定前，确认索引未变化后即可放弃该次发布。
作出提交决定后，恢复流程完成已保存的计划。
上传、校验和恢复因此可以使用同一份发布历史。

<span id="明确边界" data-td-print-local></span>

## 单独配置访问服务

运维人员配置 HTTP 访问、缓存与客户端信任。SOW 通过配置的公共端点检查发布结果。

<span id="参考资料" data-td-print-local></span>

完整执行顺序见[发布与恢复](/zh/blog/design/publication/)，配置与命令见
[`sow publish`](/zh/docs/command/publish/)。
