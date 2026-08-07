---
title: "Quick Start"
linkTitle: "Quick Start"
description: "Turn a directory of packages into a servable repository, then install from it with dnf or apt."
url: "/docs/start/quickstart/"
weight: 200
icon: fa-solid fa-bolt
---

This page takes about five minutes. You will put some packages in a directory, run one
command, serve the directory over HTTP, and install from it with `dnf` or `apt`. No
configuration file, no workspace, no database — plain mode writes indexes next to your
packages and nothing else.

## 1. Collect the packages

Any directory containing `.rpm` or `.deb` files works. The files stay where they are;
SOW never moves or renames them.

```bash
mkdir -p /srv/repo
cp ~/downloads/*.rpm /srv/repo/
ls /srv/repo
```

```console
blackbox_exporter-0.28.0-1.aarch64.rpm
blackbox_exporter-0.28.0-1.x86_64.rpm
pev2-1.23.0-1.noarch.rpm
pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

## 2. Build the indexes

```bash
sow create /srv/repo
```

```console
created /srv/repo: rpm=4 deb=0 signed=0 removed=0 marker=false noop=false recovered=false
```

That is the whole build step. Four packages took 0.35 seconds; a 2.9 GB directory of 87
RPMs takes about 11 seconds, most of it spent hashing.

SOW read every RPM header, computed SHA-256 for each payload, and wrote a `repodata/`
directory beside the packages:

```console
/srv/repo
├── blackbox_exporter-0.28.0-1.aarch64.rpm
├── blackbox_exporter-0.28.0-1.x86_64.rpm
├── pev2-1.23.0-1.noarch.rpm
├── pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
└── repodata
    ├── 2eda195ef4ce04cc2df3548bb056e3588b6c872c5333305ae108b26bcacdb558-other.xml.gz
    ├── 78b24c2413c1f60dd7871bf7c05834d0c363d2b4742b13da115565f23e0d41bd-filelists.xml.gz
    ├── 996f7947874e8c1ced323dcaae26e4ec20d4f7844701a8ef1cce0dc93631b6f7-primary.xml.gz
    └── repomd.xml
```

This is the same `primary` / `filelists` / `other` layout `createrepo_c` produces, with
checksum-named files and `repomd.xml` as the entry point every YUM client reads first.

## 3. Serve it

Any static web server will do. For a quick check, Python's built-in server is enough:

```bash
cd /srv/repo
python3 -m http.server 8080
```

Confirm the entry point is reachable:

```bash
curl -s http://localhost:8080/repodata/repomd.xml | head -3
```

```console
<?xml version="1.0" encoding="UTF-8"?>
<repomd xmlns="http://linux.duke.edu/metadata/repo" xmlns:rpm="http://linux.duke.edu/metadata/rpm">
  <revision>0</revision>
```

For anything longer-lived, put Nginx in front of the directory instead — see
[Serve Repositories](/docs/tutorial/serving/).

## 4. Install from it

Point a client at the directory URL. The packages here are unsigned, so signature
checking is off; [Sign Your Repository](/docs/tutorial/signing/) shows how to turn it on.

{{< tabpane persist="header" >}}
{{< tab header="dnf / yum" lang="bash" >}}
sudo tee /etc/yum.repos.d/quickstart.repo <<'EOF'
[quickstart]
name=SOW Quick Start
baseurl=http://10.0.0.1:8080/
enabled=1
gpgcheck=0
EOF

sudo dnf makecache
sudo dnf install pgbouncer
{{< /tab >}}
{{< tab header="apt" lang="bash" >}}
echo 'deb [trusted=yes] http://10.0.0.1:8080/ ./' | \
  sudo tee /etc/apt/sources.list.d/quickstart.list

sudo apt update
sudo apt install pev2
{{< /tab >}}
{{< /tabpane >}}

The trailing `./` in the APT line is what tells `apt` this is a flat repository — packages
and indexes in one directory, no `dists/` hierarchy. `[trusted=yes]` is required because
there is no `Release` signature yet.

A `file://` URL works too, which is handy for offline installs from a mounted disk:
`baseurl=file:///srv/repo` for `dnf`, or `deb [trusted=yes] file:///srv/repo ./` for `apt`.

## 5. Add more packages

Copy new files in and run the same command again:

```bash
cp ~/downloads/more/*.rpm /srv/repo/
sow create /srv/repo
```

SOW rescans the directory and rewrites the indexes. Nothing is remembered between runs —
the directory contents *are* the state.

Running it twice on an unchanged directory is a no-op, and says so:

```console
created /srv/repo: rpm=4 deb=0 signed=0 removed=0 marker=false noop=true recovered=false
```

The output is deterministic: same packages in, byte-identical indexes out. `repomd.xml`
carries `<revision>0</revision>` and zero timestamps precisely so that a rebuild does not
churn checksums and force every client to redownload metadata.

## 6. One directory, both formats

RPMs and DEBs can live side by side. A single `sow create` indexes both and reports them
separately:

```bash
ls /srv/mixed
```

```console
libpq5_18.3-1.pgdg12+1_amd64.deb
pev2_1.23.0_all.deb
pev2-1.23.0-1.noarch.rpm
pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm
```

```bash
sow create /srv/mixed
```

```console
created /srv/mixed: rpm=2 deb=2 signed=0 removed=0 marker=false noop=false recovered=false
```

You get `repodata/` for the RPM side and `Packages` plus `Packages.gz` for the DEB side,
in the same directory. Either format failing to parse aborts the whole command before
anything is published — the two sides commit together or not at all.

## Want machine-readable output?

Add `--json` to any command for a versioned envelope:

```bash
sow create /srv/repo --json
```

```json
{"schema":"sow.cli/v1","command":"create","ok":true,"repository":null,"operation":null,"result":{"dir":"/srv/repo","rpm":4,"deb":0,"kept":["blackbox_exporter-0.28.0-1.aarch64.rpm","blackbox_exporter-0.28.0-1.x86_64.rpm","pev2-1.23.0-1.noarch.rpm","pgbouncer-1.25.2-43PGDG.rhel9.8.x86_64.rpm"],"removed":[],"marker":false,"noop":true,"recovered":false},"errors":[]}
```

The envelope shape is the same for every command; see [JSON Output](/docs/reference/json/).

## Next steps

Plain mode is the right tool when the directory already contains exactly what you want to
publish — a build output, a directory pulled down from an upstream mirror, an offline
bundle. When you need to decide
*which* packages belong in a repository, keep several distributions in one tree, split by
architecture, or sign and audit your changes, move to a managed workspace.

- [First Workspace](/docs/start/workspace/) — the managed path, end to end.
- [Core Concepts](/docs/start/concepts/) — how the two modes differ and when to pick which.
- [Plain Flat Repositories](/docs/feature/plain/) — what `sow create` guarantees.
- [`sow create` reference](/docs/reference/cli/create/) — every flag and exit code.
