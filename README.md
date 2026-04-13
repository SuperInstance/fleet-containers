# 🐳 FLUX Fleet Containers

> Docker-based agent containerization for the FLUX Fleet — reproducible deployments, isolated execution, standardized tooling.

[![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)](tests/)

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLUX FLEET NETWORK                        │
│                  (172.28.0.0/16 — bridge)                      │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────┐      │
│  │   ORACLE-1   │    │        FLUX RUNTIME              │      │
│  │  (coordinator)│    │   FastAPI / Uvicorn :8080       │      │
│  │  172.28.0.10 │    │   172.28.0.20                   │      │
│  │  CPU: 2.0     │    │   Health: 15s interval          │      │
│  │  MEM: 2G      │    └──────────────┬───────────────────┘      │
│  └──────┬───────┘                   │                          │
│         │                           │                          │
│    depends_on                  runtime API                     │
│         │                           │                          │
│  ┌──────┴───────────────────────────┴──────────────────┐       │
│  │              AGENT LAYER                             │       │
│  │                                                      │       │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐     │       │
│  │  │ VESSEL-1 │  │ VESSEL-2 │  │  GREENHORN-1  │     │       │
│  │  │ .31      │  │ .32      │  │  .41          │     │       │
│  │  │ 1.5 CPU  │  │ 1.5 CPU  │  │  1.0 CPU      │     │       │
│  │  │ 1G MEM   │  │ 1G MEM   │  │  1G MEM       │     │       │
│  │  └──────────┘  └──────────┘  └───────────────┘     │       │
│  │                                    ┌───────────────┐│       │
│  │                                    │ GREENHORN-2   ││       │
│  │                                    │ .42           ││       │
│  │                                    │ 1.0 CPU       ││       │
│  │                                    │ 1G MEM        ││       │
│  │                                    └───────────────┘│       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  SHARED VOLUMES                                       │       │
│  │  📁 fleet-data  │  📁 fleet-logs  │  🔐 secrets     │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘

Image Hierarchy:
  ┌─────────────┐
  │ Dockerfile  │  ← Python 3.11 + Go 1.21 + Node 20 + Rust
  │   .base     │
  └──────┬──────┘
         │
    ┌────┴─────────────┐
    ▼                  ▼
┌──────────┐    ┌──────────────┐
│Dockerfile│    │ Dockerfile   │
│.flux-    │    │ .agent       │
│ runtime  │    │ + git + gh   │
└──────────┘    └──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose v2+
- Python 3.11+ (for tests)
- GitHub PAT (for agent git operations)

### 1. Clone & Configure

```bash
git clone https://github.com/SuperInstance/fleet-containers.git
cd fleet-containers

# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"
```

### 2. Run Tests

```bash
make test
```

### 3. Build Images

```bash
make build-all
```

### 4. Launch the Fleet

```bash
make up
```

### 5. Monitor

```bash
make logs     # Stream all fleet logs
make ps       # Show running containers
make health   # Check health status
```

### 6. Stop

```bash
make down
```

---

## 📦 Docker Images

| Image | Dockerfile | Purpose | Base |
|-------|-----------|---------|------|
| `fleet/base` | `Dockerfile.base` | Multi-language runtime | ubuntu:22.04 |
| `fleet/runtime` | `Dockerfile.flux-runtime` | FLUX VM execution | python:3.11-slim |
| `fleet/agent` | `Dockerfile.agent` | Generic agent with git/gh | python:3.11-slim |

### Base Image Includes
- **Python 3.11** — Agent scripting, health checks, testing
- **Go 1.21** — High-performance fleet tooling
- **Node.js 20** — JavaScript/TypeScript agent tasks
- **Rust (stable)** — Systems-level agent components

### Agent Image Includes
- Git, GitHub CLI (`gh`)
- Python packages: `requests`, `pyyaml`, `pytest`, `docker`, `gitpython`, `rich`, `click`, `pydantic`
- Entrypoint with agent bootstrap logic

---

## 🔧 Environment Variables

### Common Variables (all containers)

| Variable | Default | Description |
|----------|---------|-------------|
| `FLEET_ORG` | `SuperInstance` | GitHub organization for fleet repos |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `GIT_USER_NAME` | `Super Z` | Git commit author name |
| `GIT_USER_EMAIL` | `superz@flux.fleet` | Git commit author email |

### Agent Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_NAME` | `flux-agent` | Unique agent identifier |
| `AGENT_ROLE` | `greenhorn` | Agent role (oracle, vessel, greenhorn) |
| `GITHUB_TOKEN` | _(empty)_ | GitHub PAT for git operations |
| `AGENT_REPOS` | _(empty)_ | Comma-separated list of repos to clone |
| `AGENT_WORKSPACE` | `/home/agent/workspace` | Agent working directory |

### Runtime Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLUX_RUNTIME_PORT` | `8080` | Runtime API port |
| `FLUX_LOG_LEVEL` | `info` | Runtime-specific log level |
| `FLUX_VM_HOME` | `/opt/flux-vm` | VM installation directory |
| `GRACE_PERIOD` | `10` | Shutdown grace period (seconds) |

---

## 🛠 Make Targets

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets |
| `make build-all` | Build all Docker images |
| `make up` | Start the full fleet |
| `make down` | Stop the fleet |
| `make restart` | Restart the fleet |
| `make test` | Run all tests |
| `make health` | Check container health |
| `make shell` | Shell into running agent |
| `make clean-all` | Remove containers, images, and volumes |
| `make lint` | Lint Dockerfiles and compose file |

---

## 🧪 Tests

The test suite contains **72 tests** covering:

- **Dockerfile validation** (T01–T19) — Syntax, instructions, labels, security
- **Compose validation** (T20–T32) — Services, networks, dependencies, resources
- **Entrypoint validation** (T33–T41) — Git config, auth, agent modes, error handling
- **Health check validation** (T42–T52) — Script execution, modes, JSON output
- **Network validation** (T53–T60) — Driver, IPAM, subnets, labels
- **Makefile validation** (T61–T67) — Build targets, clean, test
- **Project structure** (T68–T72) — File existence, no secrets

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Verbose output
make test-verbose
```

---

## 🔐 Security Considerations

### Token Handling
- **Never** commit GitHub PATs to the repository
- Pass tokens via environment variables or Docker secrets
- The `.gitignore` excludes `.env` files
- Tests verify no hardcoded secrets (T72)

### Container Isolation
- Runtime containers run as non-root (`flux` / `agent` users)
- Each agent has its own container with resource limits
- Inter-agent communication only via `fleet-internal` bridge network
- No host port exposure except runtime API (8080)

### Network Security
- Bridge network isolates fleet from host network
- Static IP assignment prevents address hijacking
- DNS resolution is verified by health checks
- No privileged mode or capabilities granted

### Image Security
- Use `slim` variants where possible
- Pin language versions to prevent supply-chain drift
- Layer caching optimized with proper ordering
- No build-time secrets in image layers

### Supply Chain
- Base images from official Docker Hub libraries
- PPA/deb repos from trusted sources only
- `rustup` verified via TLS (`https://sh.rustup.rs`)

---

## 📁 Project Structure

```
fleet-containers/
├── Dockerfile.base           # Multi-language base image
├── Dockerfile.flux-runtime   # FLUX VM runtime container
├── Dockerfile.agent          # Generic agent container
├── docker-compose.yml        # Multi-agent fleet orchestration
├── fleet-network.yml         # Network and volume configuration
├── entrypoint.sh             # Agent bootstrap script
├── healthcheck.py            # Container health monitoring
├── Makefile                  # Build, run, test targets
├── README.md                 # This file
├── scripts/
│   ├── vm-bootstrap.sh       # VM initialization
│   └── vm-shutdown.sh        # VM graceful shutdown
└── tests/
    └── test_containers.py    # 72 test cases
```

---

## 📜 License

FLUX Fleet — SuperInstance

Built with 🚀 by Super Z
