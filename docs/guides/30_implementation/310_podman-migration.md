---
title: Docker to Podman Migration Guide
version: 1.0
updated: 2026-02-01
parent: ./CLAUDE.md
target_audience: developers
related:
  - ./31_paradigm-shift.md
  - ./35_project-template.md
changelog:
  - Initial Docker to Podman migration guide
---

# Docker to Podman Migration Guide

Practical guide for developers migrating from Docker to Podman. This project uses Podman as the default container runtime (see `Containerfile` and `podman-compose.yml` at the repo root).

## Why Podman

### Rootless by Default

Podman runs containers without requiring root privileges. The Docker daemon (`dockerd`) runs as root, meaning any container escape potentially grants full host access. Podman eliminates this attack surface entirely.

**Key security benefits:**
- No persistent daemon process running as root
- Containers run under your user's UID/GID
- User namespace isolation prevents privilege escalation
- Compatible with enterprise environments that restrict root access

### Daemonless Architecture

Docker requires a long-running background daemon. Podman launches containers directly via `fork/exec`, which means:
- No single point of failure (a daemon crash does not kill all containers)
- Lower resource usage when containers are not running
- Simpler systemd integration for production workloads

## Command Mapping Quick Reference

Most Docker commands translate directly to Podman by replacing `docker` with `podman`.

| Docker Command | Podman Equivalent | Notes |
|---|---|---|
| `docker build` | `podman build` | Identical usage |
| `docker run` | `podman run` | Identical flags |
| `docker ps` | `podman ps` | Identical output |
| `docker images` | `podman images` | Identical output |
| `docker pull` | `podman pull` | Identical usage |
| `docker push` | `podman push` | Identical usage |
| `docker exec` | `podman exec` | Identical usage |
| `docker stop` | `podman stop` | Identical usage |
| `docker rm` | `podman rm` | Identical usage |
| `docker rmi` | `podman rmi` | Identical usage |
| `docker logs` | `podman logs` | Identical usage |
| `docker inspect` | `podman inspect` | Identical usage |
| `docker-compose` | `podman-compose` | Separate install required |
| `docker volume` | `podman volume` | Identical subcommands |
| `docker network` | `podman network` | Identical subcommands |

### Compose Tools

| Docker Compose | Podman Compose | Notes |
|---|---|---|
| `docker-compose up -d` | `podman-compose up -d` | Same flags |
| `docker-compose down` | `podman-compose down` | Same flags |
| `docker-compose exec dev bash` | `podman-compose exec dev bash` | Same flags |
| `docker-compose run --rm dev pytest` | `podman-compose run --rm dev pytest` | Same flags |
| `docker compose` (v2 plugin) | `podman-compose` | Podman uses standalone binary |

Install `podman-compose` via pip:

```bash
pip install podman-compose
# or
uv pip install podman-compose
```

## Before and After Examples

### Building a Container Image

**Docker (before):**
```bash
docker build -t stharrold-templates .
```

**Podman (after):**
```bash
podman build -t stharrold-templates .
```

Note: Podman uses `Containerfile` by default (as in this repo) but also accepts `Dockerfile`. No renaming is required if you still have a `Dockerfile`.

### Running a Development Container

**Docker (before):**
```bash
docker run --rm -v .:/app stharrold-templates bash
docker run --rm -it -v .:/app stharrold-templates bash
```

**Podman (after):**
```bash
podman run --rm -v .:/app stharrold-templates bash
podman run --rm -it -v .:/app stharrold-templates bash
```

### Using Compose for Development

**Docker (before):**
```bash
docker-compose up -d
docker-compose exec dev bash
docker-compose run --rm dev pytest
docker-compose down
```

**Podman (after):**
```bash
podman-compose up -d
podman-compose exec dev bash
podman-compose run --rm dev pytest
podman-compose down
```

### Secrets Management

**Docker (before):**
```bash
docker run -e DB_PASSWORD="$DB_PASSWORD" -e API_KEY="$API_KEY" \
           -v .:/app stharrold-templates uv run scripts/run.py pytest
```

**Podman (after, using secrets store):**
```bash
# Create secrets
echo "$DB_PASSWORD" | podman secret create db_pass -
echo "$API_KEY" | podman secret create api_key -

# Run with secrets (recommended approach)
podman run --secret db_pass,type=env,target=DB_PASSWORD \
           --secret api_key,type=env,target=API_KEY \
           -v .:/app stharrold-templates uv run scripts/run.py pytest
```

The environment variable approach also works with Podman if you prefer simplicity:

```bash
podman run -e DB_PASSWORD="$DB_PASSWORD" -e API_KEY="$API_KEY" \
           -v .:/app stharrold-templates uv run scripts/run.py pytest
```

## Common Pitfalls

### 1. SELinux Volume Mount Flags (`:Z`)

On SELinux-enabled systems (RHEL, Fedora, CentOS), bind mounts require the `:Z` flag so that the container process can read and write to the mounted directory.

**Problem:**
```bash
# Permission denied when accessing /app inside the container
podman run -v .:/app stharrold-templates ls /app
```

**Solution:**
```bash
# Add :Z to relabel the volume for the container's SELinux context
podman run -v .:/app:Z stharrold-templates ls /app
```

This project's `podman-compose.yml` already includes the `:Z` flag:

```yaml
volumes:
  - .:/app:Z
```

**When to use `:Z` vs `:z`:**
- `:Z` (uppercase) — private unshared label; only this container can access the volume
- `:z` (lowercase) — shared label; multiple containers can access the volume
- On macOS, the `:Z` flag is accepted but has no effect (SELinux is Linux-only)

### 2. Docker Socket Path Differences

Tools that communicate with the Docker daemon via its socket need path updates.

**Docker socket:**
```
/var/run/docker.sock
```

**Podman socket (rootless):**
```
/run/user/$(id -u)/podman/podman.sock
# or via XDG_RUNTIME_DIR
$XDG_RUNTIME_DIR/podman/podman.sock
```

If a tool requires the Docker socket, you can enable the Podman socket service:

```bash
# Enable and start the Podman socket (rootless, user-level)
systemctl --user enable --now podman.socket

# Verify it is running
podman info
```

Some tools accept the `DOCKER_HOST` environment variable:

```bash
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
```

### 3. Image Registry Defaults

Docker defaults to `docker.io` for unqualified image names. Podman may prompt you to choose a registry.

**Docker:**
```bash
docker pull python:3.11-slim
# Automatically resolves to docker.io/library/python:3.11-slim
```

**Podman:**
```bash
podman pull python:3.11-slim
# May prompt: "? Please select an image:" with multiple registries
```

**Solution** — use fully qualified image names:
```bash
podman pull docker.io/library/python:3.11-slim
```

Or configure default registries in `/etc/containers/registries.conf`:

```toml
unqualified-search-registries = ["docker.io"]
```

### 4. Rootless Port Binding

Rootless Podman cannot bind to ports below 1024 by default.

**Problem:**
```bash
podman run -p 80:80 nginx
# Error: rootlessport cannot expose privileged port 80
```

**Solution — use a high port:**
```bash
podman run -p 8080:80 nginx
```

**Or allow low ports (Linux):**
```bash
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

### 5. Docker Compose v2 Plugin vs Podman Compose

Docker Compose v2 is a plugin (`docker compose` with a space). Podman uses the standalone `podman-compose` binary. If you have scripts that reference `docker compose` (with a space), update them to `podman-compose` (with a hyphen).

## Migration Checklist

Use this checklist when migrating a project from Docker to Podman.

### Installation

- [ ] Install Podman (`brew install podman` on macOS, `dnf install podman` on Fedora/RHEL)
- [ ] Install podman-compose (`pip install podman-compose` or `uv pip install podman-compose`)
- [ ] Initialize a Podman machine on macOS (`podman machine init && podman machine start`)
- [ ] Verify installation (`podman info`)

### File Updates

- [ ] Rename `Dockerfile` to `Containerfile` (optional but recommended for clarity)
- [ ] Update `docker-compose.yml` to `podman-compose.yml` (optional; Podman reads both)
- [ ] Add `:Z` suffix to bind-mount volumes if targeting SELinux systems
- [ ] Use fully qualified image names (e.g., `docker.io/library/python:3.11-slim`)

### Script and CI Updates

- [ ] Replace `docker` with `podman` in shell scripts
- [ ] Replace `docker-compose` with `podman-compose` in shell scripts
- [ ] Replace `docker compose` (v2 plugin syntax) with `podman-compose`
- [ ] Update socket paths from `/var/run/docker.sock` to Podman socket
- [ ] Update `DOCKER_HOST` environment variable if used
- [ ] Update CI/CD pipelines (GitHub Actions, GitLab CI) to use Podman

### Testing

- [ ] Build the container image (`podman build -t <name> .`)
- [ ] Run the test suite inside the container (`podman-compose run --rm dev pytest`)
- [ ] Verify volume mounts work correctly
- [ ] Verify secrets/environment variables are passed correctly
- [ ] Verify networking (port mapping, inter-container communication)

### Cleanup

- [ ] Remove Docker daemon dependency if no longer needed
- [ ] Update project documentation to reference Podman commands
- [ ] Update onboarding guides for new developers

## Repo-Specific Reference

This repository already uses Podman. Key files:

- **`Containerfile`** — Multi-stage build with Python 3.11 + uv. Build with `podman build -t stharrold-templates .`
- **`podman-compose.yml`** — Development service definition with `:Z` volume mounts. Run with `podman-compose run --rm dev <command>`

Common development commands:

```bash
# Build the image
podman build -t stharrold-templates .

# Run tests
podman-compose run --rm dev pytest

# Run linting
podman-compose run --rm dev uv run ruff check .

# Interactive shell
podman-compose run --rm dev bash

# Start in background
podman-compose up -d

# Stop
podman-compose down
```

## Further Reading

- [Podman documentation](https://docs.podman.io/)
- [Podman Compose documentation](https://github.com/containers/podman-compose)
- [Rootless containers overview](https://rootlesscontaine.rs/)

---

*This guide covers the practical steps for migrating from Docker to Podman. For broader development workflow patterns, see [32_workflow-patterns.md](./32_workflow-patterns.md).*
