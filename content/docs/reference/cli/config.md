---
title: "sow config"
linkTitle: "sow config"
description: "Validate sow.yml without touching anything, and print the effective configuration for any scope."
url: "/docs/reference/cli/config/"
weight: 300
icon: fa-solid fa-file-code
---

`sow config` has two read-only subcommands. `config check` is the full preflight over `sow.yml` —
run it after every hand edit and in CI. `config show` prints the configuration SOW actually computed,
which is where you confirm that defaults, inherited architectures and normalized aliases resolved the
way you expected.

Neither subcommand creates directories, touches a database, or corrects your file.

## Synopsis

```text
sow config check [-C DIR] [--json]
sow config show [--all] [-C DIR] [-r NAME] [-d NAME]... [--json]
```

`sow help config` lists both.

## sow config check

Parses and validates the complete `sow.yml`: schema version, names, path collisions, the architecture
permit list, Dist formats, membership policy and signing key references. It reports the Workspace it
resolved and how much it validated.

```console
sow config check
configuration valid: /srv/repo repositories=1 dists=2
```

```console
sow config check --json
{"schema":"sow.cli/v1","command":"config check","ok":true,"repository":null,"operation":null,"result":{"workspace":"/srv/repo","repositories":1,"dists":2},"errors":[]}
```

### Options

| Flag | Description | Default |
|---|---|---|
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `--json` | Emit the versioned JSON envelope | false |
| `-h, --help` | Show help | — |

### Strict field rejection

Unknown keys are errors, not warnings. A typo can't silently disable a policy:

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 8: field bogus_field not found in type config.DistConfig
```

The schema version is pinned:

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": config schema must be "sow/v2", got "sow/v1"
```

`check` also verifies that every declared signing key reference resolves and is usable for signing —
without ever printing key material. If you remove an architecture from the permit list while a Dist
config, Membership or Built Generation still uses it, `config check` rejects the configuration.

## sow config show

Prints the effective configuration as YAML for the currently selected scope.

```console
sow config show
schema: sow/v2
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
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
      trixie:
        format: deb
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

Compare that with the file on disk, which carries only what you wrote:

```console
cat sow.yml
schema: sow/v2
architectures:
  - x86_64
  - aarch64
repos:
  pigsty:
    signing:
      rpm:
        packages:
          mode: never
    dists:
      el9:
        format: rpm
      trixie:
        format: deb
```

`show` filled in `protected: false`, the inherited per-Dist `architectures`, `limit: 0` and an empty
`exclude` list. Architectures are always printed as canonical families (`x86_64`, `aarch64`), never
as ecosystem aliases — `amd64` and `arm64` are the DEB spellings of the same two families.

### Options

| Flag | Description | Default |
|---|---|---|
| `--all` | Expand defaults and normalized architectures across the whole Workspace | off |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | selection rules |
| `--json` | Emit the versioned JSON envelope | false |
| `-h, --help` | Show help | — |

### Scope projection with -r and -d

`-r` and `-d` narrow the output to the selected objects. This is the fast way to answer "what policy
is actually in effect for this one Dist":

```console
sow config show -r pigsty -d el9
schema: sow/v2
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
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

`--all` goes the other way: it expands the entire Workspace regardless of where you are standing.

### Secrets are never printed

Key material and passphrases never appear in `config show`, in JSON, in the operation log, or in
error text. Only the reference (`file://…`, `env://…`, `agent://…`) and fingerprint are shown.

## Examples

Validate before a build in CI:

```bash
sow config check -C /srv/repo || exit 1
sow build -r pgsql
```

Diff effective policy across two Dists:

```bash
sow config show -r pgsql -d el9 > /tmp/el9.yml
sow config show -r pgsql -d el9-beta > /tmp/beta.yml
diff -u /tmp/el9.yml /tmp/beta.yml
```

## Exit codes

| Code | Trigger |
|---|---|
| `0` | Configuration valid, or output printed |
| `1` | Runtime I/O error reading the config file |
| `2` | Usage error, Workspace not found, unknown field, wrong schema, or any validation failure |
| `6` | A named Repository or Dist does not exist |

`config check` reports validation failures as exit `2`, not `6`: an invalid `sow.yml` is a
configuration error, not a rejected operation.

## See also

- [sow.yml Reference](/docs/reference/config/) — every key, with a complete example file
- [Membership Policy](/docs/feature/policy/) — how `exclude` and `limit` are evaluated
- [Signing Model](/docs/feature/signing/) — key reference grammar and the two trust chains
- [sow init](/docs/reference/cli/init/) — converging a hand-written config
- [sow check](/docs/reference/cli/build/) — the runtime counterpart that verifies bytes on disk
