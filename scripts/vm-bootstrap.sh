#!/usr/bin/env bash
# ============================================================
# FLUX VM Bootstrap Script
# Initializes the FLUX VM runtime environment
# ============================================================
set -euo pipefail

FLUX_VM_HOME="${FLUX_VM_HOME:-/opt/flux-vm}"
LOG_DIR="${FLUX_VM_HOME}/logs"
AGENT_DIR="${FLUX_VM_HOME}/agents"

log() {
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [BOOT] $*"
}

log "FLUX VM Bootstrap starting..."

# --- Create directory structure ---
mkdir -p "${LOG_DIR}" "${AGENT_DIR}" "${FLUX_VM_HOME}/data"

# --- Initialize runtime state ---
cat > "${FLUX_VM_HOME}/data/runtime-state.json" <<EOF
{
    "vm_id": "${FLUX_VM_ID:-local}",
    "status": "initializing",
    "started_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
    "agents_registered": 0
}
EOF

# --- Load agent configurations ---
if [[ -d "${AGENT_DIR}" ]]; then
    for agent_config in "${AGENT_DIR}"/*.yml "${AGENT_DIR}"/*.yaml; do
        [[ -f "${agent_config}" ]] || continue
        log "Loading agent config: $(basename "${agent_config}")"
    done
fi

log "FLUX VM Bootstrap complete — runtime ready"
