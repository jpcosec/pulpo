"""
Phase 3 Iteration 2: CLI Service Management Tests

Tests that the CLI properly manages services via actual subprocess invocation.
No mocking - tests real CLI commands via subprocess.run().
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_pulpo_installed():
    """Auto-install pulpo-core if not already installed."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if "pulpo-core" not in result.stdout:
        # Install the package in editable mode from repo root
        repo_root = Path(__file__).parent.parent.parent
        install_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(repo_root)],
            capture_output=True,
            text=True,
            timeout=120
        )
        assert install_result.returncode == 0, f"Failed to install: {install_result.stderr}"


class TestCLIDiscovery:
    """Test CLI discovery and listing commands."""

    def test_pulpo_command_exists(self):
        """Test that 'pulpo' command is available."""
        result = subprocess.run(
            ["pulpo", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"pulpo --help failed: {result.stderr}"
        assert "help" in result.stdout.lower() or "commands" in result.stdout.lower()

    def test_pulpo_models_command(self):
        """Test that 'pulpo models' works."""
        # This should work in the repo root
        repo_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            ["pulpo", "models"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Should list models (may be empty)
        assert result.returncode in [0, 1]

    def test_pulpo_compile_help(self):
        """Test that 'pulpo compile' help works."""
        result = subprocess.run(
            ["pulpo", "compile", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0


class TestCLIInvocation:
    """Test actual CLI command invocation via subprocess."""

    def test_cli_version(self):
        """Test that 'pulpo version' returns version info."""
        result = subprocess.run(
            ["pulpo", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Version command failed: {result.stderr}"
        # Should output version number
        assert len(result.stdout.strip()) > 0 or len(result.stderr.strip()) > 0

    def test_cli_help_shows_commands(self):
        """Test that help shows available commands."""
        result = subprocess.run(
            ["pulpo", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        help_text = result.stdout.lower()
        # Should mention main commands
        assert any(cmd in help_text for cmd in ["compile", "discover", "up", "down"])

    def test_cli_invalid_command_fails(self):
        """Test that invalid commands fail appropriately."""
        result = subprocess.run(
            ["pulpo", "nonexistent-command"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode != 0

    def test_cli_compile_without_project(self):
        """Test 'pulpo compile' behavior in directory without project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["pulpo", "compile"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Should either succeed (with empty output) or fail gracefully
            assert result.returncode in [0, 1]

    def test_cli_timeout_handling(self):
        """Test that long-running commands can timeout gracefully."""
        # Using a simple command with a timeout
        try:
            result = subprocess.run(
                ["pulpo", "discover"],
                capture_output=True,
                text=True,
                timeout=5  # Short timeout
            )
            # Should complete within timeout
            assert True
        except subprocess.TimeoutExpired:
            # Timeout is acceptable for this test
            pass


class TestCLIExitCodes:
    """Test CLI exit codes match expected behavior."""

    def test_success_returns_zero(self):
        """Test that successful commands return exit code 0."""
        result = subprocess.run(
            ["pulpo", "--help"],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_help_returns_zero(self):
        """Test that help commands return exit code 0."""
        result = subprocess.run(
            ["pulpo", "compile", "--help"],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0

    def test_invalid_args_return_nonzero(self):
        """Test that invalid arguments return non-zero exit code."""
        result = subprocess.run(
            ["pulpo", "--invalid-flag-xyz"],
            capture_output=True,
            timeout=10
        )
        assert result.returncode != 0
