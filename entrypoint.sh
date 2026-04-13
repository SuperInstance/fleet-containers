#!/usr/bin/env bash
# ============================================================
# FLUX Fleet — Agent Bootstrap Entrypoint
# Clones repos, sets up git config, and starts agent work
# ============================================================
set -euo pipefail

# --- Configuration from environment ---
AGENT_NAME="${AGENT_NAME:-flux-agent}"
AGENT_ROLE="${AGENT_ROLE:-greenhorn}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_USER="${GITHUB_USER:-SuperInstance}"
WORKSPACE="${AGENT_WORKSPACE:-/home/agent/workspace}"
FLEET_ORG="${FLEET_ORG:-SuperInstance}"
REPOS="${AGENT_REPOS:-}"
GIT_USER_NAME="${GIT_USER_NAME:-Super Z}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-superz@flux.fleet}"
LOG_LEVEL="${LOG_LEVEL:-info}"

log() {
    local level="$1"; shift
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "[${ts}] [${level^^}] [${AGENT_NAME}] $*"
}

log_info()  { log "info"  "$@"; }
log_warn()  { log "warn"  "$@"; }
log_error() { log "error" "$@"; }

# --- Banner ---
log_info "============================================"
log_info "FLUX Fleet Agent Bootstrap"
log_info "Agent : ${AGENT_NAME}"
log_info "Role  : ${AGENT_ROLE}"
log_info "============================================"

# --- Setup workspace ---
mkdir -p "${WORKSPACE}"
cd "${WORKSPACE}"

# --- Git configuration ---
log_info "Configuring git identity..."
git config --global user.name "${GIT_USER_NAME}"
git config --global user.email "${GIT_USER_EMAIL}"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global fetch.prune true

# --- GitHub CLI auth (if token provided) ---
if [[ -n "${GITHUB_TOKEN}" ]]; then
    log_info "Authenticating GitHub CLI..."
    echo "${GITHUB_TOKEN}" | gh auth login --with-token 2>/dev/null || {
        log_warn "GitHub CLI auth failed, continuing without gh"
    }
    gh config set git_protocol https
fi

# --- Clone fleet repos ---
if [[ -n "${REPOS}" ]]; then
    log_info "Cloning fleet repositories..."
    IFS=',' read -ra REPO_LIST <<< "${REPOS}"
    for repo in "${REPO_LIST[@]}"; do
        repo_name=$(basename "${repo}" .git)
        if [[ -d "${WORKSPACE}/${repo_name}" ]]; then
            log_info "Repo ${repo_name} already exists, pulling latest..."
            cd "${WORKSPACE}/${repo_name}" && git pull --ff-only && cd "${WORKSPACE}"
        else
            log_info "Cloning ${repo_name}..."
            git clone "https://github.com/${FLEET_ORG}/${repo_name}.git" "${WORKSPACE}/${repo_name}" 2>/dev/null || {
                log_warn "Failed to clone ${repo_name}, skipping"
            }
        fi
    done
fi

# --- Create agent state file ---
cat > "${WORKSPACE}/.agent-state.json" <<EOF
{
    "agent_name": "${AGENT_NAME}",
    "agent_role": "${AGENT_ROLE}",
    "workspace": "${WORKSPACE}",
    "fleet_org": "${FLEET_ORG}",
    "booted_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "status": "ready"
}
EOF

# --- Agent mode ---
COMMAND="${1:-idle}"
case "${COMMAND}" in
    idle)
        log_info "Agent entering idle mode (waiting for tasks)..."
        tail -f /dev/null
        ;;
    work)
        log_info "Agent entering work mode..."
        shift
        exec "$@"
        ;;
    test)
        log_info "Running agent tests..."
        shift
        exec pytest "$@"
        ;;
    shell)
        log_info "Dropping into interactive shell..."
        exec /bin/bash
        ;;
    *)
        log_info "Executing: $*"
        exec "$@"
        ;;
esac
