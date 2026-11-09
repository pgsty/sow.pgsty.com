---
title: "sow config"
linkTitle: "config"
description: "Validate sow.yml and inspect the effective configuration."
categories: [Command]
tags: [cli, config]
url: "/docs/command/config/"
aliases: ["/docs/reference/cli/config/"]
weight: 300
icon: fa-solid fa-file-code
---

Use `sow config check` after editing `sow.yml`. It validates the configuration, signing references, and compatibility with existing Repository state. Use `sow config show` to inspect resolved defaults and inherited settings. Both commands are read-only.

## Synopsis

```text
sow config check [-C DIR] [--json] [--passfile PATH]
sow config show [--all] [-C DIR] [-r NAME] [-d NAME]... [--json]
```

`config check` accepts `--passfile PATH` for signing preflights. Priority is CLI, per-key config, then `SOW_GPG_PASSFILE`. `config show` does not read password files. See [Password files](/docs/reference/config/#passfile).

## sow config check

`sow config check` parses and validates the complete `sow.yml`: schema version, names, path collisions, the architecture
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
| `--passfile PATH` | [Password file for this invocation](/docs/reference/config/#passfile) | per-key config, then `SOW_GPG_PASSFILE` |
| `--json` | Output JSON | false |
| `-h, --help` | Show help | — |
{.wide .expand}

### Strict field rejection

Unknown keys produce a configuration error:

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": parse sow.yml: yaml: unmarshal errors:
  line 8: field bogus_field not found in type config.DistConfig
```

Use `schema: sow/v3`:

```console
sow config check
configuration error: load config "/srv/repo/sow.yml": config schema must be "sow/v3", got "invalid"
```

Signing checks depend on the signer:

- SOW unlocks metadata key files and checks them for signing suitability. External GPG
  metadata keys also perform a small noninteractive signing probe.
- Active RPM package signing checks the selected password file's format, `rpm`/GPG,
  and secret-key availability. It does not sign a package or prove that the password
  is correct. RPM macros can affect authentication; an actual package-signing call
  and verification of its output are the final check.

Before removing an architecture from the Workspace list, remove its use from Dist
configuration, membership, and Built state.

## sow config show

`sow config show` prints the effective configuration as YAML for the currently selected scope.

```console
sow config show
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
schema: sow/v3
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
`exclude` list. Architectures use canonical family names: `x86_64` and `aarch64`. The corresponding DEB names are `amd64` and `arm64`.

### Options

| Flag | Description | Default |
|---|---|---|
| `--all` | Expand defaults and normalized architectures across the whole Workspace | off |
| `-C, --workdir DIR` | Workspace discovery start directory | current directory |
| `-r, --repo NAME` | Select a repository | selection rules |
| `-d, --dist NAME` | Select a distribution; repeatable | selection rules |
| `--json` | Output JSON | false |
| `-h, --help` | Show help | — |
{.wide .expand}

### Select configuration with -r and -d {#scope-projection-with--r-and--d}

`-r` and `-d` narrow the output to the selected objects. This is the fast way to answer "what policy
is actually in effect for this one Dist":

```console
sow config show -r pigsty -d el9
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
    dists:
      el9:
        format: rpm
        architectures:
          - x86_64
          - aarch64
        limit: 0
        exclude: []
```

Without `--all`, normal Repository selection applies. If the discovery start directory is inside a Dist, SOW selects that Dist unless you provide `-d`. Otherwise, SOW shows all Dists of the selected Repository. `--all` shows the entire Workspace and ignores `-r` and `-d`.

### Signing references {#secrets-are-never-printed}

The output contains key references and resolved fingerprints. SOW omits private key contents and passphrases.
Configured `passfile` paths remain visible. SOW does not add the `SOW_GPG_PASSFILE` runtime fallback to the displayed configuration.

## Examples

Validate before a build in CI:

```bash
sow config check -C /srv/repo || exit 1
sow build -C /srv/repo -r pgsql
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
| `1` | Runtime or key-resolution failure |
| `2` | Usage or discovery error, invalid YAML, unknown field, or unsupported schema |
| `5` | Existing state, controlled paths, or recovery records are inconsistent |
| `6` | Unknown selection, unusable signing configuration, or configuration incompatible with existing state |
{.wide .expand}

`config check` validates both the YAML file and its compatibility with existing Repository state.

## See also

- [sow.yml Reference](/docs/reference/config/) — every key, with a complete example file
- [Membership Policy](/docs/feature/policy/) — how `exclude` and `limit` are evaluated
- [Signing Model](/docs/feature/signing/) — key reference grammar and the two trust chains
- [sow init](/docs/command/init/) — create objects declared in a hand-written config
- [sow check](/docs/command/check/) — the runtime counterpart that verifies bytes on disk
