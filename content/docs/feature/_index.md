---
title: "Features"
linkTitle: "Features"
description: "How SOW works and why it is built this way: execution paths, pool projection, policy, signing, transactions, and audit."
url: "/docs/feature/"
weight: 300
icon: fa-solid fa-cubes
---

This section explains the machinery. The [Getting Started](/docs/start/) pages show you which commands to type and the [Tutorials](/docs/tutorial/) walk through complete scenarios; the pages here answer the next question — *what is actually happening on disk, and why was it designed that way*.

Every page opens with the invariants it protects, then shows the mechanism that enforces them. If you only need syntax, go to the [Command manual](/docs/command/) instead.

## Which page answers which question

| Question | Page |
|---|---|
| What can SOW do, and how does it compare to `createrepo_c` and `reprepro`? | [Capability Overview](/docs/feature/overview/) |
| What exactly does `sow create` write, and what does it refuse to touch? | [Plain Flat Repositories](/docs/feature/plain/) |
| How do Workspace, Repository and Dist relate, and how does SOW find them? | [Managed Workspaces](/docs/feature/managed/) |
| How does one pool feed several metadata-only architecture views? | [Pool & Architecture Views](/docs/feature/views/) |
| Why did my package come back as `excluded` or `limited`? | [Membership Policy](/docs/feature/policy/) |
| Which key signs what, and what happens when I rotate it? | [Signing Model](/docs/feature/signing/) |
| What happens if the machine dies mid-`add`? | [Transactions & Recovery](/docs/feature/transactions/) |
| How do I prove the tree is safe to ship? | [Observability & Audit](/docs/feature/audit/) |
