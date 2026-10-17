---
title: "Serve and Publish Repositories"
linkTitle: "Serve Repositories"
description: "Serve a public Repository with Nginx and publish verified Generations to a filesystem target."
categories: [Tutorial]
tags: [publish, filesystem, managed]
url: "/docs/tutorial/serving/"
weight: 400
icon: fa-solid fa-server
---

SOW generates static repository files. This guide publishes a Managed Repository to a separate directory, then serves that directory with Nginx. It continues from [First Workspace](/docs/start/workspace/).

<span id="public-and-private-paths" data-td-print-local></span>

The source is `/srv/sow/local`; the public copy will be `/srv/repo-public/local`.
Both contain the complete `pool/` and `dists/` tree. The workspace configuration and
private state stay outside the server root.

<span id="1-gate-the-source-generation" data-td-print-local></span>

## 1. Build and check

```bash
cd /srv/sow
sow build -r local
sow check -r local
```

Continue when `check` succeeds.

<span id="2-configure-a-filesystem-target" data-td-print-local></span>

## 2. Add a filesystem target

Create the target's parent directory and give the SOW operator write access:

```bash
sudo install -d -m 0755 /srv/repo-public
sudo chown "$(id -u):$(id -g)" /srv/repo-public
```

Use the account that runs `sow publish` if it differs from your current user. The endpoint must already exist at its physical path; use no symlink components.

Add this target to `/srv/sow/sow.yml`:

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

SOW creates `/srv/repo-public/local` from `endpoint` and `prefix`. The three required booleans declare that this workspace is the source of truth and the only writer for that target. Use a separate prefix for other tools.

This example checks the published files through `file://` and declares no intermediary cache. If you later add a proxy or CDN, use its public Repository URL for `public_endpoint`
and its longest cache lifetime for `max_cache_ttl`. Apply these changes through
[`publish --rebind`](/docs/command/publish/). SOW uses them to check delivery and decide
when old files can be removed.

Publish the Repository:

```bash
sow publish public
```

SOW copies package files and immutable metadata first, then updates client entry points. It checks the result and records the published generation. Repeating publication without changes reports a no-op.

<span id="3-serve-the-target-with-nginx" data-td-print-local></span>

## 3. Configure Nginx

Install Nginx and add a server configuration like this. Replace `repo.example.com` with your hostname:

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

Check and reload the configuration:

```bash
sudo nginx -t
sudo nginx -s reload
```

These commands assume Nginx is already running. If this is a new installation, start it through your operating system's service manager after `nginx -t` succeeds.

The client addresses are:

| Client | Address |
|---|---|
| DNF `baseurl` | `http://repo.example.com/local/dists/el9/$basearch/` |
| APT `URIs` | `http://repo.example.com/local` |
| APT `Suites` / `Components` | `bookworm` / `main` |

Use the [YUM](/docs/tutorial/yum-repo/) or [APT](/docs/tutorial/apt-repo/) tutorial for the full source configuration. To verify signatures, distribute the public key and follow [Sign Your Repository](/docs/tutorial/signing/).

<span id="4-verify-the-served-entry-points" data-td-print-local></span>

## 4. Check client access

Configure a client with the addresses above. Refresh its indexes and install a package.
This checks access to both `dists/` and `pool/`. Apply the same access rules to both
directories.

<span id="next" data-td-print-local></span>

## Publish an update

After changing membership or configuration, build any pending changes and publish again:

```bash
sow build -r local
sow check -r local
sow publish public
```

If publication stops, rerun `sow publish public` to resume it. See [`sow publish`](/docs/command/publish/) for recovery and target changes, and [`sow gc`](/docs/command/gc/) for cleanup after the cache grace period.

<span id="manual-and-air-gapped-delivery" data-td-print-local></span>

## Deliver to an isolated host

When SOW cannot reach the destination, stop source writers while creating and checking
the copy:

1. Run `sow check` on the source.
2. Copy the complete Repository to a new release directory on the destination. Preserve hard links, for example with `rsync -aH` or `tar`.
3. Verify transferred files against `sow changes 0` or an archive checksum manifest.
4. Switch the server's path to the new release directory.
5. Keep package and immutable metadata URLs referenced by old indexes reachable until the maximum cache lifetime expires, then clean up the old release.

For paths absent from the new release, the HTTP server can fall back to the previous
release directory during that interval.

Copying directly over a live tree can expose indexes before their package files arrive. Prepare the new directory first and switch it as a unit.

## Serve a Plain repository

For Plain mode, serve the directory passed to `sow create`. Keep temporary hidden files
inaccessible; the Nginx dotfile rule above does this.

<span id="r2-targets" data-td-print-local></span>

## Publish to R2

Use `provider: r2` for Cloudflare R2. Configure its endpoint, bucket, credential reference, public URL, and cache lifetime; see the [target configuration reference](/docs/reference/config/). Run an initial publication to a test prefix and check it from your package clients.

R2 target garbage collection reports deletion candidates; SOW does not delete those objects. See [Platforms & Integrations](/docs/reference/compatibility/) for tested storage operations.
