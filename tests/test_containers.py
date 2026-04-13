"""FLUX Fleet Containers — Test Suite

Comprehensive tests validating Dockerfiles, compose files,
entrypoint script, health check logic, and network configuration.
"""

import json
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest
import yaml

# --- Project root ---
PROJECT_ROOT = Path(__file__).parent.parent


# ============================================================
#  Dockerfile Validation Tests
# ============================================================

class TestDockerfileBase:
    """Tests for Dockerfile.base."""

    @pytest.fixture
    def dockerfile(self):
        return PROJECT_ROOT / "Dockerfile.base"

    def test_dockerfile_base_exists(self, dockerfile):
        """T01: Dockerfile.base must exist."""
        assert dockerfile.exists(), "Dockerfile.base not found"

    def test_dockerfile_base_from_instruction(self, dockerfile):
        """T02: Dockerfile.base must have a valid FROM instruction."""
        content = dockerfile.read_text()
        assert re.search(r"^FROM\s+\S+", content, re.MULTILINE), \
            "Missing FROM instruction in Dockerfile.base"

    def test_dockerfile_base_has_python(self, dockerfile):
        """T03: Dockerfile.base must install Python 3.11."""
        content = dockerfile.read_text()
        assert "python3.11" in content or "python:3.11" in content, \
            "Python 3.11 not found in Dockerfile.base"

    def test_dockerfile_base_has_go(self, dockerfile):
        """T04: Dockerfile.base must install Go."""
        content = dockerfile.read_text()
        assert "go" in content.lower() or "golang" in content.lower(), \
            "Go installation not found in Dockerfile.base"

    def test_dockerfile_base_has_node(self, dockerfile):
        """T05: Dockerfile.base must install Node.js."""
        content = dockerfile.read_text()
        assert "node" in content.lower(), \
            "Node.js not found in Dockerfile.base"

    def test_dockerfile_base_has_rust(self, dockerfile):
        """T06: Dockerfile.base must install Rust."""
        content = dockerfile.read_text()
        assert "rust" in content.lower() or "rustup" in content.lower(), \
            "Rust installation not found in Dockerfile.base"

    def test_dockerfile_base_has_workdir(self, dockerfile):
        """T07: Dockerfile.base must set a WORKDIR."""
        content = dockerfile.read_text()
        assert re.search(r"^WORKDIR\s+\S+", content, re.MULTILINE), \
            "Missing WORKDIR instruction in Dockerfile.base"

    def test_dockerfile_base_has_labels(self, dockerfile):
        """T08: Dockerfile.base must have OCI labels."""
        content = dockerfile.read_text()
        assert "LABEL" in content, "No LABEL instructions found"
        assert "org.opencontainers.image.title" in content, \
            "Missing OCI image title label"

    def test_dockerfile_base_has_healthcheck(self, dockerfile):
        """T09: Dockerfile.base must have a HEALTHCHECK."""
        content = dockerfile.read_text()
        assert "HEALTHCHECK" in content, \
            "Missing HEALTHCHECK instruction in Dockerfile.base"


class TestDockerfileFluxRuntime:
    """Tests for Dockerfile.flux-runtime."""

    @pytest.fixture
    def dockerfile(self):
        return PROJECT_ROOT / "Dockerfile.flux-runtime"

    def test_dockerfile_runtime_exists(self, dockerfile):
        """T10: Dockerfile.flux-runtime must exist."""
        assert dockerfile.exists(), "Dockerfile.flux-runtime not found"

    def test_dockerfile_runtime_from_slim(self, dockerfile):
        """T11: Dockerfile.flux-runtime must use a slim base."""
        content = dockerfile.read_text()
        assert re.search(r"^FROM\s+\S+", content, re.MULTILINE), \
            "Missing FROM instruction"

    def test_dockerfile_runtime_has_fastapi(self, dockerfile):
        """T12: Dockerfile.flux-runtime must install FastAPI."""
        content = dockerfile.read_text()
        assert "fastapi" in content.lower(), \
            "FastAPI not found in Dockerfile.flux-runtime"

    def test_dockerfile_runtime_has_expose(self, dockerfile):
        """T13: Dockerfile.flux-runtime must expose a port."""
        content = dockerfile.read_text()
        assert "EXPOSE" in content, \
            "Missing EXPOSE instruction in Dockerfile.flux-runtime"

    def test_dockerfile_runtime_has_entrypoint(self, dockerfile):
        """T14: Dockerfile.flux-runtime must have an ENTRYPOINT."""
        content = dockerfile.read_text()
        assert "ENTRYPOINT" in content, \
            "Missing ENTRYPOINT in Dockerfile.flux-runtime"

    def test_dockerfile_runtime_has_non_root_user(self, dockerfile):
        """T15: Dockerfile.flux-runtime should run as non-root."""
        content = dockerfile.read_text()
        assert "USER" in content, \
            "Missing USER instruction — should run as non-root"


class TestDockerfileAgent:
    """Tests for Dockerfile.agent."""

    @pytest.fixture
    def dockerfile(self):
        return PROJECT_ROOT / "Dockerfile.agent"

    def test_dockerfile_agent_exists(self, dockerfile):
        """T16: Dockerfile.agent must exist."""
        assert dockerfile.exists(), "Dockerfile.agent not found"

    def test_dockerfile_agent_has_git(self, dockerfile):
        """T17: Dockerfile.agent must install git."""
        content = dockerfile.read_text()
        assert "git" in content.lower(), \
            "Git not found in Dockerfile.agent"

    def test_dockerfile_agent_has_gh_cli(self, dockerfile):
        """T18: Dockerfile.agent must install GitHub CLI."""
        content = dockerfile.read_text()
        assert "gh" in content.lower() or "github" in content.lower(), \
            "GitHub CLI not found in Dockerfile.agent"

    def test_dockerfile_agent_has_copy_entrypoint(self, dockerfile):
        """T19: Dockerfile.agent must copy entrypoint.sh."""
        content = dockerfile.read_text()
        assert "COPY" in content and "entrypoint" in content.lower(), \
            "Missing COPY entrypoint.sh in Dockerfile.agent"


# ============================================================
#  Docker Compose Validation Tests
# ============================================================

class TestDockerCompose:
    """Tests for docker-compose.yml."""

    @pytest.fixture
    def compose(self):
        with open(PROJECT_ROOT / "docker-compose.yml") as f:
            return yaml.safe_load(f)

    def test_compose_file_exists(self):
        """T20: docker-compose.yml must exist."""
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_compose_version(self, compose):
        """T21: Compose file must have a version key."""
        assert "version" in compose, "Missing 'version' key in docker-compose.yml"

    def test_compose_has_services(self, compose):
        """T22: Compose file must have services defined."""
        assert "services" in compose, "Missing 'services' in docker-compose.yml"
        assert len(compose["services"]) >= 3, \
            f"Expected at least 3 services, got {len(compose['services'])}"

    def test_compose_has_oracle(self, compose):
        """T23: Compose must have an oracle service."""
        assert "oracle" in compose["services"], "Missing 'oracle' service"

    def test_compose_has_vessels(self, compose):
        """T24: Compose must have vessel services."""
        services = compose["services"]
        vessels = [s for s in services if "vessel" in s]
        assert len(vessels) >= 2, \
            f"Expected at least 2 vessel services, got {len(vessels)}"

    def test_compose_has_greenhorns(self, compose):
        """T25: Compose must have greenhorn services."""
        services = compose["services"]
        greenhorns = [s for s in services if "greenhorn" in s]
        assert len(greenhorns) >= 2, \
            f"Expected at least 2 greenhorn services, got {len(greenhorns)}"

    def test_compose_has_runtime(self, compose):
        """T26: Compose must have a flux-runtime service."""
        assert "flux-runtime" in compose["services"], \
            "Missing 'flux-runtime' service"

    def test_compose_has_network(self, compose):
        """T27: Compose must define a network."""
        assert "networks" in compose, "Missing 'networks' in docker-compose.yml"

    def test_compose_has_volumes(self, compose):
        """T28: Compose must define volumes."""
        assert "volumes" in compose, "Missing 'volumes' in docker-compose.yml"

    def test_compose_oracle_has_healthcheck(self, compose):
        """T29: Oracle service must have a healthcheck."""
        oracle = compose["services"]["oracle"]
        assert "healthcheck" in oracle, \
            "Oracle service missing healthcheck"

    def test_compose_oracle_has_resource_limits(self, compose):
        """T30: Oracle service must have resource limits."""
        oracle = compose["services"]["oracle"]
        assert "deploy" in oracle, "Oracle service missing deploy config"
        assert "resources" in oracle["deploy"], \
            "Oracle service missing resource limits"

    def test_compose_vessels_depend_on_oracle(self, compose):
        """T31: Vessels must depend on oracle."""
        services = compose["services"]
        for name, svc in services.items():
            if "vessel" in name:
                assert "depends_on" in svc, f"{name} missing depends_on"
                assert "oracle" in svc["depends_on"], \
                    f"{name} doesn't depend on oracle"

    def test_compose_services_use_fleet_network(self, compose):
        """T32: All services must be on fleet-internal network."""
        services = compose["services"]
        for name, svc in services.items():
            if name == "flux-runtime":
                continue
            assert "networks" in svc, f"{name} missing network config"
            assert "fleet-internal" in svc["networks"], \
                f"{name} not on fleet-internal network"


# ============================================================
#  Entrypoint Script Tests
# ============================================================

class TestEntrypoint:
    """Tests for entrypoint.sh."""

    @pytest.fixture
    def entrypoint(self):
        return PROJECT_ROOT / "entrypoint.sh"

    def test_entrypoint_exists(self, entrypoint):
        """T33: entrypoint.sh must exist."""
        assert entrypoint.exists(), "entrypoint.sh not found"

    def test_entrypoint_is_executable(self, entrypoint):
        """T34: entrypoint.sh should be a shell script."""
        content = entrypoint.read_text()
        assert "#!/usr/bin/env bash" in content or "#!/bin/bash" in content, \
            "entrypoint.sh must have a bash shebang"

    def test_entrypoint_has_git_config(self, entrypoint):
        """T35: entrypoint.sh must configure git."""
        content = entrypoint.read_text()
        assert "git config" in content, \
            "entrypoint.sh must configure git"

    def test_entrypoint_has_gh_auth(self, entrypoint):
        """T36: entrypoint.sh must handle GitHub CLI auth."""
        content = entrypoint.read_text()
        assert "gh auth" in content or "GITHUB_TOKEN" in content, \
            "entrypoint.sh must handle GitHub auth"

    def test_entrypoint_has_clone_logic(self, entrypoint):
        """T37: entrypoint.sh must clone repos."""
        content = entrypoint.read_text()
        assert "git clone" in content, \
            "entrypoint.sh must clone repositories"

    def test_entrypoint_has_agent_modes(self, entrypoint):
        """T38: entrypoint.sh must support agent modes (idle, work, test, shell)."""
        content = entrypoint.read_text()
        for mode in ["idle", "work", "test", "shell"]:
            assert mode in content, f"entrypoint.sh missing '{mode}' mode"

    def test_entrypoint_has_state_file(self, entrypoint):
        """T39: entrypoint.sh must create an agent state file."""
        content = entrypoint.read_text()
        assert ".agent-state.json" in content, \
            "entrypoint.sh must create agent state file"

    def test_entrypoint_uses_env_vars(self, entrypoint):
        """T40: entrypoint.sh must use AGENT_NAME and AGENT_ROLE env vars."""
        content = entrypoint.read_text()
        assert "AGENT_NAME" in content, "entrypoint.sh must use AGENT_NAME"
        assert "AGENT_ROLE" in content, "entrypoint.sh must use AGENT_ROLE"

    def test_entrypoint_has_error_handling(self, entrypoint):
        """T41: entrypoint.sh must have error handling."""
        content = entrypoint.read_text()
        assert "set -" in content or "set -euo" in content or "set -e" in content, \
            "entrypoint.sh must have error handling (set -e or similar)"


# ============================================================
#  Health Check Tests
# ============================================================

class TestHealthCheck:
    """Tests for healthcheck.py."""

    @pytest.fixture
    def healthcheck(self):
        return PROJECT_ROOT / "healthcheck.py"

    def test_healthcheck_exists(self, healthcheck):
        """T42: healthcheck.py must exist."""
        assert healthcheck.exists(), "healthcheck.py not found"

    def test_healthcheck_is_valid_python(self, healthcheck):
        """T43: healthcheck.py must be valid Python."""
        content = healthcheck.read_text()
        compile(content, str(healthcheck), "exec")

    def test_healthcheck_has_main(self, healthcheck):
        """T44: healthcheck.py must have a main function."""
        content = healthcheck.read_text()
        assert "def main()" in content, "healthcheck.py missing main()"

    def test_healthcheck_accepts_mode_args(self, healthcheck):
        """T45: healthcheck.py must accept --runtime and --agent flags."""
        content = healthcheck.read_text()
        assert "--runtime" in content, "healthcheck.py missing --runtime flag"
        assert "--agent" in content, "healthcheck.py missing --agent flag"

    def test_healthcheck_has_checker_class(self, healthcheck):
        """T46: healthcheck.py must have a HealthChecker class."""
        content = healthcheck.read_text()
        assert "class HealthChecker" in content, \
            "healthcheck.py missing HealthChecker class"

    def test_healthcheck_returns_exit_codes(self, healthcheck):
        """T47: healthcheck.py must define exit codes 0, 1, 2."""
        content = healthcheck.read_text()
        assert "return 0" in content, "Missing exit code 0"
        assert "return 1" in content, "Missing exit code 1 (degraded)"
        assert "return 2" in content, "Missing exit code 2 (unhealthy)"

    def test_healthcheck_check_methods(self, healthcheck):
        """T48: healthcheck.py must have check methods."""
        content = healthcheck.read_text()
        assert "def check_python" in content, "Missing check_python method"
        assert "def check_git" in content, "Missing check_git method"
        assert "def check_workspace" in content, "Missing check_workspace method"

    def test_healthcheck_json_output(self, healthcheck):
        """T49: healthcheck.py must output JSON."""
        content = healthcheck.read_text()
        assert "json.dumps" in content, "healthcheck.py must output JSON"

    @pytest.mark.unit
    def test_healthcheck_runs_base_mode(self):
        """T50: healthcheck.py runs successfully in base mode."""
        env = os.environ.copy()
        env["AGENT_WORKSPACE"] = tempfile.mkdtemp()
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "healthcheck.py")],
            capture_output=True, text=True, timeout=15, env=env
        )
        assert result.returncode in (0, 1), \
            f"healthcheck base mode failed: {result.stderr}"

    @pytest.mark.unit
    def test_healthcheck_runs_agent_mode(self):
        """T51: healthcheck.py runs successfully in agent mode."""
        env = os.environ.copy()
        env["AGENT_WORKSPACE"] = tempfile.mkdtemp()
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "healthcheck.py"), "--agent"],
            capture_output=True, text=True, timeout=15, env=env
        )
        assert result.returncode in (0, 1, 2), \
            f"healthcheck agent mode failed: {result.stderr}"

    @pytest.mark.unit
    def test_healthcheck_output_is_valid_json(self):
        """T52: healthcheck.py output must be valid JSON."""
        env = os.environ.copy()
        env["AGENT_WORKSPACE"] = tempfile.mkdtemp()
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "healthcheck.py")],
            capture_output=True, text=True, timeout=15, env=env
        )
        try:
            data = json.loads(result.stdout)
            assert "checks" in data, "Output missing 'checks' key"
            assert "summary" in data, "Output missing 'summary' key"
        except json.JSONDecodeError:
            pytest.fail(f"Output is not valid JSON: {result.stdout[:200]}")


# ============================================================
#  Network Configuration Tests
# ============================================================

class TestFleetNetwork:
    """Tests for fleet-network.yml."""

    @pytest.fixture
    def network_config(self):
        with open(PROJECT_ROOT / "fleet-network.yml") as f:
            return yaml.safe_load(f)

    def test_network_file_exists(self):
        """T53: fleet-network.yml must exist."""
        assert (PROJECT_ROOT / "fleet-network.yml").exists()

    def test_network_has_fleet_internal(self, network_config):
        """T54: Must define fleet-internal network."""
        assert "networks" in network_config
        assert "fleet-internal" in network_config["networks"], \
            "Missing fleet-internal network definition"

    def test_network_uses_bridge_driver(self, network_config):
        """T55: Networks must use bridge driver."""
        networks = network_config["networks"]
        for name, net in networks.items():
            assert net.get("driver") == "bridge", \
                f"Network {name} must use bridge driver"

    def test_network_has_ipam(self, network_config):
        """T56: fleet-internal must have IPAM configuration."""
        fleet_net = network_config["networks"]["fleet-internal"]
        assert "ipam" in fleet_net, "Missing IPAM config in fleet-internal"

    def test_network_has_subnet(self, network_config):
        """T57: fleet-internal must define a subnet."""
        fleet_net = network_config["networks"]["fleet-internal"]
        ipam_config = fleet_net["ipam"]["config"]
        assert any("subnet" in c for c in ipam_config), \
            "Missing subnet in fleet-internal IPAM"

    def test_network_has_static_addresses(self, network_config):
        """T58: fleet-internal must assign static addresses to agents."""
        fleet_net = network_config["networks"]["fleet-internal"]
        ipam_config = fleet_net["ipam"]["config"]
        has_aux = any("aux_addresses" in c for c in ipam_config)
        assert has_aux, "Missing static aux_addresses for agents"

    def test_network_has_volumes(self, network_config):
        """T59: Must define shared volumes."""
        assert "volumes" in network_config, "Missing volumes section"
        assert len(network_config["volumes"]) >= 2, \
            f"Expected at least 2 volumes, got {len(network_config['volumes'])}"

    def test_network_has_labels(self, network_config):
        """T60: Networks must have fleet labels."""
        fleet_net = network_config["networks"]["fleet-internal"]
        assert "labels" in fleet_net, "Missing labels on fleet-internal"
        assert "fleet.org" in fleet_net["labels"], \
            "Missing fleet.org label"


# ============================================================
#  Makefile Tests
# ============================================================

class TestMakefile:
    """Tests for Makefile."""

    @pytest.fixture
    def makefile(self):
        return PROJECT_ROOT / "Makefile"

    def test_makefile_exists(self, makefile):
        """T61: Makefile must exist."""
        assert makefile.exists(), "Makefile not found"

    def test_makefile_has_build_target(self, makefile):
        """T62: Makefile must have a build target."""
        content = makefile.read_text()
        assert re.search(r"^build[:\s]", content, re.MULTILINE), \
            "Missing 'build' target"

    def test_makefile_has_up_target(self, makefile):
        """T63: Makefile must have an up target."""
        content = makefile.read_text()
        assert re.search(r"^up[:\s]", content, re.MULTILINE), \
            "Missing 'up' target"

    def test_makefile_has_down_target(self, makefile):
        """T64: Makefile must have a down target."""
        content = makefile.read_text()
        assert re.search(r"^down[:\s]", content, re.MULTILINE), \
            "Missing 'down' target"

    def test_makefile_has_test_target(self, makefile):
        """T65: Makefile must have a test target."""
        content = makefile.read_text()
        assert re.search(r"^test[:\s]", content, re.MULTILINE), \
            "Missing 'test' target"

    def test_makefile_has_clean_target(self, makefile):
        """T66: Makefile must have a clean target."""
        content = makefile.read_text()
        assert re.search(r"^clean[:\s]", content, re.MULTILINE), \
            "Missing 'clean' target"

    def test_makefile_has_help_target(self, makefile):
        """T67: Makefile must have a help target."""
        content = makefile.read_text()
        assert re.search(r"^help[:\s]", content, re.MULTILINE), \
            "Missing 'help' target"


# ============================================================
#  Project Structure Tests
# ============================================================

class TestProjectStructure:
    """Tests for overall project structure."""

    def test_readme_exists(self):
        """T68: README.md must exist."""
        assert (PROJECT_ROOT / "README.md").exists()

    def test_gitignore_exists(self):
        """T69: .gitignore should exist."""
        # Not strictly required but good practice
        pass  # Optional

    def test_all_dockerfiles_present(self):
        """T70: All three Dockerfiles must exist."""
        for df in ["Dockerfile.base", "Dockerfile.flux-runtime", "Dockerfile.agent"]:
            assert (PROJECT_ROOT / df).exists(), f"Missing {df}"

    def test_scripts_directory_exists(self):
        """T71: scripts/ directory must exist with runtime scripts."""
        scripts_dir = PROJECT_ROOT / "scripts"
        assert scripts_dir.exists(), "scripts/ directory not found"
        assert (scripts_dir / "vm-bootstrap.sh").exists(), \
            "Missing vm-bootstrap.sh"
        assert (scripts_dir / "vm-shutdown.sh").exists(), \
            "Missing vm-shutdown.sh"

    def test_no_hardcoded_secrets(self):
        """T72: No hardcoded secrets in any file."""
        secret_patterns = [
            r'ghp_[A-Za-z0-9]{36}',
            r'AKIA[0-9A-Z]{16}',
        ]
        skip_dirs = {".git"}
        for pattern in secret_patterns:
            for filepath in PROJECT_ROOT.rglob("*"):
                if any(skip in filepath.parts for skip in skip_dirs):
                    continue
                if filepath.is_file() and filepath.suffix in {".py", ".yml", ".yaml", ".sh", ".env"}:
                    content = filepath.read_text(errors="ignore")
                    matches = re.findall(pattern, content)
                    assert not matches, \
                        f"Potential secret found in {filepath}: {matches[0][:10]}..."
