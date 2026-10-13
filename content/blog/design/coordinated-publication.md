---
title: "Coordinated Publication Decision"
linkTitle: "Publication Decision"
date: 2026-08-14
lastmod: 2026-10-13
authors: [Vonng]
description: "The v0.4.0 decision to keep SOW's native publication providers, and the earlier rclone proposal that did not ship."
categories: [Design]
tags: [publish, transaction, object-storage, decision]
url: "/blog/design/coordinated-publication/"
aliases:
  - "/docs/design/coordinated-publication/"
weight: 10
icon: fa-solid fa-cloud-arrow-up
draft: false
---

<span id="decision"></span>

SOW 0.4.0 kept the native `filesystem` and `r2` publication backends. An earlier proposal
used rclone and added remote audit and preview commands. The native design was selected
because SOW needs to track each conditional write and its result.

Current command syntax is in [`sow publish`](/docs/command/publish/).

<span id="why-the-executor-proposal-was-not-adopted"></span>
<span id="what-040-shipped"></span>

## Why keep native backends

A publication plan binds each file to an expected SHA-256 and operation. The backend must
create immutable objects without overwriting existing content and update mutable pointers
conditionally. SOW records the result so it can resume after an interruption.

A bulk-copy tool would need another identity and checkpoint model to preserve these rules.
The 0.4 work instead improved the existing backend:

- conditional multipart uploads;
- separate response-header and body-idle timeouts;
- retries for operations that can be repeated;
- verification of changed files through the public URL.

This retained the existing publication state and avoided a transport migration.

<span id="native-incremental-publication"></span>
<span id="hardened-public-visibility"></span>
<span id="operator-workflow"></span>

## Publication workflow

The native backend uploads packages and immutable metadata before updating the repository indexes.
It then checks the public files and records a checkpoint for the target.
The next publication compares the current build with that checkpoint.

<span id="operator-confirmed-rebind"></span>

## Change target settings

A binding revision records changes to the target name, public URL, or cache lifetime.
The target keeps its publication history. A different storage location requires a new target.

<span id="recovery-decision"></span>

## Resume an interrupted publication

SOW saves the plan and progress for each attempt.
Before the commit decision, it can abandon the attempt after checking that the indexes have not changed.
After that decision, recovery completes the saved plan.
This gives each target one history for upload, verification, and recovery.

<span id="explicit-boundaries"></span>

## Configure serving separately

The operator configures HTTP access, caching, and client trust.
SOW verifies publication through the configured public endpoint.

<span id="references"></span>

See [Publication and recovery](/blog/design/publication/) for the complete sequence.
Use [`sow publish`](/docs/command/publish/) for configuration and commands.
