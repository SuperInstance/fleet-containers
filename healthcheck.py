#!/usr/bin/env python3
# ============================================================
# FLUX Fleet — Container Health Check Monitor
# Verifies container health for base, runtime, and agent modes
# ============================================================
"""
Health check script for FLUX Fleet containers.

Usage:
    healthcheck.py                 # Base health check
    healthcheck.py --runtime       # Runtime-specific checks
    healthcheck.py --agent         # Agent-specific checks

Exit codes:
    0 = healthy
    1 = degraded
    2 = unhealthy
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class HealthChecker:
    """FLUX Fleet container health checker."""

    def __init__(self, mode: str = "base"):
        self.mode = mode
        self.checks = []
        self.start_time = datetime.now(timezone.utc)

    def record(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({
            "name": name,
            "passed": passed,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def check_python(self):
        """Verify Python runtime is available."""
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip()
            passed = result.returncode == 0
            self.record("python_available", passed, version)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.record("python_available", False, str(e))

    def check_git(self):
        """Verify git is installed."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip()
            passed = result.returncode == 0
            self.record("git_available", passed, version)
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.record("git_available", False, str(e))

    def check_workspace(self):
        """Verify workspace directory exists and is writable."""
        workspace = os.environ.get("AGENT_WORKSPACE", "/fleet")
        path = Path(workspace)
        if path.exists():
            writable = os.access(workspace, os.W_OK)
            self.record("workspace_exists", True, workspace)
            self.record("workspace_writable", writable, workspace)
        else:
            self.record("workspace_exists", False, f"{workspace} not found")
            self.record("workspace_writable", False, f"{workspace} not found")

    def check_agent_state(self):
        """Verify agent state file exists and is valid JSON."""
        workspace = os.environ.get("AGENT_WORKSPACE", "/fleet")
        state_file = Path(workspace) / ".agent-state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                status = data.get("status", "unknown")
                passed = status == "ready"
                self.record("agent_state", passed, f"status={status}")
            except (json.JSONDecodeError, OSError) as e:
                self.record("agent_state", False, str(e))
        else:
            self.record("agent_state", False, "state file not found")

    def check_network(self):
        """Verify network connectivity (DNS resolution)."""
        try:
            import socket
            socket.setdefaulttimeout(5)
            ip = socket.gethostbyname("github.com")
            self.record("dns_resolution", True, f"github.com -> {ip}")
        except (socket.gaierror, socket.timeout) as e:
            self.record("dns_resolution", False, str(e))

    def check_gh_cli(self):
        """Verify GitHub CLI is installed (agent mode only)."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True, timeout=10
            )
            passed = result.returncode == 0
            self.record("gh_cli_available", passed, result.stdout.strip().split("\n")[0])
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            self.record("gh_cli_available", False, str(e))

    def check_runtime_port(self):
        """Verify runtime port is bound (runtime mode only)."""
        port = int(os.environ.get("FLUX_RUNTIME_PORT", "8080"))
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            listening = result == 0
            self.record("runtime_port", listening, f"port {port}")
        except OSError as e:
            self.record("runtime_port", False, str(e))

    def run(self) -> int:
        """Execute all health checks and return exit code."""
        # Base checks
        self.check_python()

        if self.mode == "base":
            self.check_workspace()
            self.check_network()

        elif self.mode == "agent":
            self.check_git()
            self.check_gh_cli()
            self.check_workspace()
            self.check_agent_state()
            self.check_network()

        elif self.mode == "runtime":
            self.check_network()
            self.check_runtime_port()

        # Report
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c["passed"])
        failed = total - passed

        report = {
            "mode": self.mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": self.checks,
            "summary": {"total": total, "passed": passed, "failed": failed},
        }

        print(json.dumps(report, indent=2))

        # Exit codes: 0=healthy, 1=degraded, 2=unhealthy
        if failed == 0:
            return 0
        elif passed > 0:
            return 1
        else:
            return 2


def main():
    parser = argparse.ArgumentParser(description="FLUX Fleet Health Check")
    parser.add_argument("--runtime", action="store_true", help="Runtime-specific checks")
    parser.add_argument("--agent", action="store_true", help="Agent-specific checks")
    args = parser.parse_args()

    if args.runtime:
        mode = "runtime"
    elif args.agent:
        mode = "agent"
    else:
        mode = "base"

    checker = HealthChecker(mode=mode)
    sys.exit(checker.run())


if __name__ == "__main__":
    main()
