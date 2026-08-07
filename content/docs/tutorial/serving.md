---
title: "Serve Repositories"
linkTitle: "Serve Repositories"
description: "Publish a repository over HTTP with Nginx, preview it locally, and copy it to an air-gapped host without losing deduplication."
url: "/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW builds a static directory. Anything that can serve static files can serve it — there is no
daemon, no application server, and no runtime component. This tutorial covers what to point a
web server at, a tested Nginx configuration, a one-command local preview, and how to move the
tree to a host that cannot reach your build machine.

Plan for about fifteen minutes.

## What you actually serve

For a managed workspace, the document root is the **repository** directory:

```console
~/repo/                  <- workspace: do not serve this
├── sow.yml              <- configuration
├── .sow/                <- SQLite, locks, staging, recovery
└── pigsty/              <- serve this
    ├── pool/
    └── dists/
```

The repository directory contains exactly two entries, `pool/` and `dists/`, and both are meant
to be public. State that must never be published — the database, locks, staging areas, pending
payloads — lives in `.sow/` at the workspace root, one level above. Pointing a web server at
`~/repo/pigsty` cannot leak it, whatever you get wrong in the server configuration.

For Plain mode there is no workspace: the directory you ran `sow create` in is the document root,
with `repodata/` and `Packages` sitting next to the package files.

Serve over HTTPS. APT and DNF verify signatures, so plaintext HTTP does not let an attacker
forge packages, but it does let anyone on the path see exactly which packages each host installs.

## Step 1: Preview locally

Before touching a real web server, check the tree serves at all:

```bash
cd ~/repo/pigsty
python3 -m http.server 8080
```

From another terminal:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  http://127.0.0.1:8080/dists/el9/x86_64/repodata/repomd.xml
```

```console
200
```

That is enough to point a test VM at `http://YOUR_IP:8080/` and run a real `dnf makecache`. It is
not enough for production — single-threaded, no caching, no TLS — but it removes the web server
from the list of suspects when something does not work.

## Step 2: Serve with Nginx

This configuration has been tested end to end against a repository with both an RPM and a DEB
Dist, signed metadata included.

```nginx
server {
    listen 443 ssl;
    server_name repo.example.com;

    ssl_certificate     /etc/ssl/certs/repo.example.com.crt;
    ssl_certificate_key /etc/ssl/private/repo.example.com.key;

    root /home/you/repo/pigsty;

    autoindex on;
    autoindex_exact_size off;
    autoindex_localtime on;

    # Never serve dotfiles, whatever the root ends up being.
    location ~ /\. { deny all; }

    # Package payloads are immutable: their path contains their exact version.
    location ~ \.(rpm|deb)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Indexes and pointers change on every build.
    location ~ /(repodata|dists)/ {
        add_header Cache-Control "no-cache";
    }
}
```

Four things are worth explaining.

`root` points at the repository, not the workspace. Combined with the dotfile rule, `.sow/` is
unreachable twice over.

The cache split matters more than it looks. A file in `pool/` never changes content — its name
contains its version — so it can be cached forever. `repomd.xml`, `Release` and `InRelease` are
pointers that flip on every build; a CDN or proxy that holds a stale one sends clients to
metadata files that have already been deleted. `no-cache` here means "revalidate", not "do not
store", so you keep the bandwidth savings without the staleness.

`autoindex` is optional. It is genuinely useful for humans browsing the pool, and it exposes
nothing a client could not already enumerate from the indexes. Turn it off if you prefer.

There is no `try_files`, no rewrite, and no MIME special-casing. APT and DNF ask for exact paths
and care about bytes, not `Content-Type`.

Check and reload:

```bash
nginx -t
```

```console
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

```bash
systemctl reload nginx
```

## Step 3: Verify every entry point

Fetch one file of each kind. All five must return `200`:

```bash
for u in /dists/el9/x86_64/repodata/repomd.xml \
         /dists/el9/x86_64/repodata/repomd.xml.asc \
         /dists/trixie/InRelease \
         /dists/trixie/Release.gpg \
         /pool/p/pev2/pev2-1.22.0-1.noarch.rpm; do
  printf "%-52s %s\n" "$u" \
    "$(curl -sS -o /dev/null -w '%{http_code} %{size_download}' https://repo.example.com$u)"
done
```

```console
/dists/el9/x86_64/repodata/repomd.xml                200 1517
/dists/el9/x86_64/repodata/repomd.xml.asc            200 832
/dists/trixie/InRelease                              200 1498
/dists/trixie/Release.gpg                            200 832
/pool/p/pev2/pev2-1.22.0-1.noarch.rpm                200 325925
```

Then check the `by-hash` path APT actually uses, taking the hash straight from `Release`:

```bash
HASH=$(grep -m1 " main/binary-arm64/Packages$" \
        ~/repo/pigsty/dists/trixie/Release | awk '{print $1}')
curl -sS -o /dev/null -w "%{http_code} %{size_download}\n" \
  "https://repo.example.com/dists/trixie/main/binary-arm64/by-hash/SHA256/$HASH"
```

```console
200 3846
```

A `404` here means the server is rewriting or normalizing paths — `by-hash` directories look
unusual and some configurations mangle them. Fix that before clients hit it, because APT will
fall back to fetching by name and you lose the protection against fetching across a rebuild.

## Step 4: Serving several repositories at once

If a workspace holds more than one repository, you can root the server at the workspace instead.
Now the dotfile rule is doing real work, and you need a second rule for `sow.yml`:

```nginx
server {
    listen 443 ssl;
    server_name repo.example.com;

    ssl_certificate     /etc/ssl/certs/repo.example.com.crt;
    ssl_certificate_key /etc/ssl/private/repo.example.com.key;

    root /home/you/repo;

    autoindex on;

    location ~ /\.       { deny all; }   # blocks /.sow/
    location = /sow.yml  { deny all; }

    location ~ \.(rpm|deb)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
    location ~ /(repodata|dists)/ {
        add_header Cache-Control "no-cache";
    }
}
```

Verify both denials and one real path:

```console
GET /.sow/pigsty.db                    -> 403
GET /sow.yml                           -> 403
GET /pigsty/dists/trixie/InRelease     -> 200
```

Client URLs gain the repository name: `https://repo.example.com/pigsty/dists/el9/$basearch`.

{{% alert title="Prefer one server block per repository" color="info" %}}
Rooting at the workspace works, but it puts your configuration file and state directory one
misconfiguration away from being public. If you can spare the server blocks, root each one at its
own repository directory — then no denial rule has anything to protect.
{{% /alert %}}

## Step 5: Copy the tree to another host

The whole repository is the two directories `pool/` and `dists/`. Copying them anywhere produces
a working repository — no import step, no database to move.

Check the tree is deliverable first. This is the whole point of `sow check`:

```bash
sow check
```

Exit code `0` means every layer verified and the tree is coherent. Exit code `5` means it is not
ready — usually because the repository is dirty and a `sow build` is pending. Never copy a tree
that did not pass; you would be shipping indexes that do not match their payloads.

Scripts can read the same fact from `status`:

```bash
sow status --json
```

```console
{"schema":"sow.cli/v1","command":"status","ok":true,"repository":"pigsty","operation":null,"result":{"repository":"pigsty","status":"clean","ready_to_copy":true,"desired_revision":6,"built_generation":9,"dirty_dists":[],"dirty_reasons":[],"pending":{"count":0,"bytes":0},"recent_operation":{"id":"2579903513812731490","kind":"build","state":"done","created_at":"2026-08-04T04:25:47.526819Z","updated_at":"2026-08-04T04:25:48.505935Z"},"repository_locked":false},"errors":[]}
```

Gate on `.result.ready_to_copy`.

### rsync, with hardlinks preserved

```bash
rsync -aH --delete ~/repo/pigsty/ user@mirror:/srv/www/pigsty/
```

`-H` is the flag that matters. Architecture views are hardlinks into the pool, so a `noarch` or
`all` package occupies one inode no matter how many views list it. Without `-H`, rsync writes
each name as an independent file:

```bash
du -sh pigsty
rsync -aH --delete pigsty/ /srv/mirror-hardlink/ && du -sh /srv/mirror-hardlink
rsync -a  --delete pigsty/ /srv/mirror-plain/    && du -sh /srv/mirror-plain
```

```console
187M	pigsty
187M	/srv/mirror-hardlink
223M	/srv/mirror-plain
```

```bash
stat -c "%h %n" /srv/mirror-hardlink/pool/p/pev2/pev2-1.22.0-1.noarch.rpm \
                /srv/mirror-plain/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
```

```console
3 /srv/mirror-hardlink/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
1 /srv/mirror-plain/pool/p/pev2/pev2-1.22.0-1.noarch.rpm
```

19% more disk on this small repository, and the gap widens with the proportion of `noarch` and
`all` packages. Both copies work identically for clients — losing hardlinks costs space, not
correctness — so if your transport cannot preserve them, that is a budget question rather than a
blocker.

The result is byte-for-byte the source:

```bash
diff -r --brief ~/repo/pigsty /srv/mirror-hardlink && echo "trees identical"
```

```console
trees identical
```

### Air-gapped media

Same idea, one hop at a time:

```bash
sow check                                    # gate
tar -C ~/repo -cf /mnt/usb/pigsty.tar pigsty # tar preserves hardlinks by default
# carry the media across
tar -C /srv/www -xf /mnt/usb/pigsty.tar
```

`tar` detects and records hardlinks without a flag. `cp -a` preserves them too. Anything that
does not — most object-storage sync tools, for instance — produces the larger independent-file
copy from the previous section, which still serves correctly.

## Step 6: Ship only what changed

For a large repository, re-copying everything on each build is wasteful. `sow changes` reports
the exact file-level difference between any past generation and the current one.

`changes 0` is the full delivery set — everything a fresh mirror needs:

```bash
sow changes 0 | head -3
sow changes 0 | wc -l
```

```console
base=0 generation=9 dirty=false
add	payload	dists/el9/aarch64/pool/b/blackbox_exporter/blackbox_exporter-0.28.0-1.aarch64.rpm	15289542	ceb1b8660f8bc1fe59fb7a28e750e19a1ccd010a254a50e82328adb5818a5943
add	payload	dists/el9/aarch64/pool/p/patroni/patroni-4.1.4-1PGDG.rhel9.6.noarch.rpm	1451117	077938eac0fae939368887e4f20e55e2af7dfb9f0e885869df8841213bd97fd6
      49
```

Passing the generation your mirror already has gives the incremental set. After adding one
package to a repository that was at generation 9:

```bash
sow changes 9
```

```console
base=9 generation=10 dirty=false
add	payload	dists/el9/x86_64/pool/g/gdal311-devel/gdal311-devel-3.11.0-2.rhel9.x86_64.rpm	251366	0663e42e48207189e5dde643fc779de022ade1e3ddd87519009d484bfd2d05fc
add	payload	pool/g/gdal311-devel/gdal311-devel-3.11.0-2.rhel9.x86_64.rpm	251366	0663e42e48207189e5dde643fc779de022ade1e3ddd87519009d484bfd2d05fc
add	metadata	dists/el9/x86_64/repodata/6439665d77d7129eb17c4775148fb2ab918b00525d0012572863fedbf2eb2ff9-filelists.xml.gz	4765	6439665d77d7129eb17c4775148fb2ab918b00525d0012572863fedbf2eb2ff9
add	metadata	dists/el9/x86_64/repodata/90965c9a2093e32fb6e9a42a701a0be80510fd55a58ae8c4b7e78ccc95d3c79e-primary.xml.gz	3750	90965c9a2093e32fb6e9a42a701a0be80510fd55a58ae8c4b7e78ccc95d3c79e
add	metadata	dists/el9/x86_64/repodata/e3fb8c08073e38e189d995817588e0990db1f0b7a1b77e1a1606ac3fa9ff5e45-other.xml.gz	1917	e3fb8c08073e38e189d995817588e0990db1f0b7a1b77e1a1606ac3fa9ff5e45
update	pointer	dists/el9/aarch64/repodata/repomd.xml	1520	114f79dade90f77d11b3c452d8d59654917683f59f196c7098e68449c361f0ae
update	pointer	dists/el9/aarch64/repodata/repomd.xml.asc	832	48d7c114f84876c1247444b3792f549e9da3c775fe4d46a384839b8b37121237
update	pointer	dists/el9/x86_64/repodata/repomd.xml	1521	c67ab04efe06c1ff2a55a3c8fecc15405346471de8ca77f76915797fa81d3a4c
update	pointer	dists/el9/x86_64/repodata/repomd.xml.asc	832	d0de8d66071a1fb6ecc1ff8a34e8b0d84689ed886169b6ea3fa696ab169e05aa
```

The columns are operation, phase, repository-relative path, size, and SHA-256. The `phase` column
is the constraint you must respect when applying this by hand or with your own tooling:

1. `payload` — package files. Copy these first; nothing points at them yet.
2. `metadata` — checksum-named indexes and `by-hash` copies. Still unreferenced.
3. `pointer` — `repomd.xml`, `Release`, `InRelease`, and their signatures. This is the
   commit: the moment a pointer lands, clients see the new generation.
4. `delete` — files the previous generation referenced and this one does not. Only safe once
   every pointer has flipped.

Apply them out of order and a client mid-fetch gets a dangling reference. Follow the order and
readers always see a coherent tree, because they either read the old pointer or the new one, and
both resolve.

`changes` produces a plan, not a transfer. SOW has no endpoint configuration, no credentials, and
calls no sync tool — feed the paths to `rsync --files-from`, or to whatever your environment
already uses.

{{% alert title="A dirty repository has no plan" color="warning" %}}
`changes` refuses to answer while the repository is dirty, recovering, or in error. There is no
coherent physical tree to describe. Run `sow build`, confirm `sow check` passes, then ask again.
{{% /alert %}}

## Where to go next

{{< doc-cards cols="2" >}}
{{< doc-card title="Sign Your Repository" link="/docs/tutorial/signing/" >}}
Do this before you publish anything clients will trust.
{{< /doc-card >}}
{{< doc-card title="Observability & Audit" link="/docs/feature/audit/" >}}
`status`, `check`, `changes` and `log` — what each one costs and what each one proves.
{{< /doc-card >}}
{{< doc-card title="Repository Layout" link="/docs/reference/layout/" >}}
Every path in the tree, and what must never reach a document root.
{{< /doc-card >}}
{{< doc-card title="Compatibility" link="/docs/reference/compatibility/" >}}
Which clients were tested, and the hardlink and filesystem requirements.
{{< /doc-card >}}
{{< /doc-cards >}}
