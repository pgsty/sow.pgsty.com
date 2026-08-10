---
title: "Serve and Publish Repositories"
linkTitle: "Serve Repositories"
description: "Serve a public Repository with Nginx and publish verified Generations to a filesystem target."
url: "/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW writes static files; it is not an HTTP server. This guide keeps the writable Workspace
separate from the path Nginx serves.

## Public and private paths

| Mode | Public unit | Never serve |
|---|---|---|
| Plain | the directory passed to `sow create` | transient `.sow-plain-stage-*` output; no durable journal |
| Managed | one Repository's complete `pool/ + dists/` tree | Workspace `sow.yml`, `.sow/`, SQLite, locks, journals, staging |

For the workspace in [First Workspace](/docs/start/workspace/), the source Repository is
`/srv/sow/local`. Do not make `/srv/sow` the document root.

## 1. Gate the source Generation

```bash
cd /srv/sow
sow build -r local
sow check -r local
```

Continue only when `check` returns `0`. `status` is useful for diagnosis, but `check` is
the full read-only delivery proof.

## 2. Configure a filesystem target

Create the endpoint directory first. It must be a real, canonical directory, not a symlink;
SOW refuses to create a missing endpoint for you.

```bash
sudo install -d -m 0755 /srv/repo-public
sudo chown "$(id -u):$(id -g)" /srv/repo-public
```

The second command gives the current operator write access; use the account that will run
`sow publish` if publication runs under a dedicated service user.

Add a target to `/srv/sow/sow.yml`:

```yaml
targets:
  public:
    repository: local
    provider: filesystem
    endpoint: file:///srv/repo-public
    prefix: local
    public_endpoint: file:///srv/repo-public/local/
    max_cache_ttl: 0s
    authoritative_workspace: true
    single_writer: true
    exclusive_write_authority: true
```

The three booleans are mandatory safety acknowledgements. The endpoint and prefix combine
to `/srv/repo-public/local`; SOW creates and owns the prefix below the pre-existing endpoint.

Validate and publish:

```bash
sow config check
sow publish public
```

Publication copies immutable payloads and metadata before mutable protocol pointers,
verifies the result, and records a target checkpoint. Repeating the command for an
unchanged Generation is an idempotent no-op.

Do not let another tool write into the same target prefix. The target contract is
single-writer and exclusive.

## 3. Serve the target with Nginx

```nginx
server {
    listen 80;
    server_name repo.example.com;

    root /srv/repo-public;
    autoindex off;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ (^|/)\. {
        deny all;
    }
}
```

Reload Nginx after validating its configuration. The client URLs are:

```text
DNF baseurl: http://repo.example.com/local/dists/el9/x86_64/
APT source:  deb http://repo.example.com/local bookworm main
```

If metadata or packages are signed, publish the corresponding public key separately and
configure `gpgkey`/`Signed-By`; private keys never belong under the document root.

## 4. Verify the served entry points

```bash
curl --fail --head \
  http://repo.example.com/local/dists/el9/x86_64/repodata/repomd.xml

curl --fail --head \
  http://repo.example.com/local/dists/bookworm/Release

curl --fail --head \
  http://repo.example.com/local/dists/bookworm/main/binary-amd64/Packages.gz
```

Then run the actual package manager from a client host. HTTP reachability is not package
client verification; both checks matter.

The complete Repository prefix must have one access policy. RPM metadata may resolve a
package through `../../../pool/...`, and APT `Filename` fields point to `pool/...` directly.
Protecting `dists/` while accidentally exposing or blocking `pool/` breaks the repository.

## Manual and air-gapped delivery

If `sow publish` cannot reach the destination:

1. run `sow check` on the source;
2. copy the complete Repository into a new, non-live staging or release directory;
3. verify transport checksums against `sow changes 0` or an archive manifest;
4. atomically switch an operator-owned parent reference to the new directory;
5. keep the previous release until clients and caches have moved past it.

Do **not** run an unordered `rsync --delete` directly against a live Repository root. That
does not preserve SOW's pointer ordering, target checkpoint, cache grace, or recovery state.
`sow changes` describes Generation differences; it is not an authorization to mutate a
live target without those controls.

## R2 targets

The configuration parser and current implementation support `provider: r2`, with
S3-compatible publication and report-only target GC. Current real CLI-to-R2 end-to-end
evidence is not complete; validate credentials, bucket policy, public endpoint, cache,
replay, and recovery in a nonproduction prefix before relying on it. See
[Compatibility](/docs/reference/compatibility/).

## Next

- [`sow publish`](/docs/command/publish/) and [`sow gc`](/docs/command/gc/)
- [Publication design](/docs/design/publication/)
- [Signing tutorial](/docs/tutorial/signing/)
