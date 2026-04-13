#!/usr/bin/env bash
# ============================================================
# FLUX VM Shutdown Script
# Gracefully shuts down the FLUX VM runtime
# ============================================================
set -euo pipefail

FLUX_VM_HOME="${FLUX_VM_HOME:-/opt/flux-vm}"
STATE_FILE="${FLUX_VM_HOME}/data/runtime-state.json"

log() {
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [SHUTDOWN] $*"
}

log "FLUX VM Shutdown initiated..."

# --- Update state ---
if [[ -f "${STATE_FILE}" ]]; then
    python3 -c "
import json, pathlib
state = json.loads(pathlib.Path('${STATE_FILE}').read_text())
state['status'] = 'shutting_down'
state['stopped_at'] = '$(date -u '+%Y-%m-%dT%H:%M:%SZ')'
pathlib.Path('${STATE_FILE}').write_text(json.dumps(state, indent=2))
"
fi

# --- Wait for agents to finish (grace period) ---
GRACE_PERIOD="${GRACE_PERIOD:-10}"
log "Waiting ${GRACE_PERIOD}s for agents to finish..."
sleep "${GRACE_PERIOD}"

log "FLUX VM Shutdown complete"
