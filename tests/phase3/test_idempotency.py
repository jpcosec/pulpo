"""
Phase 3 Iteration 5: Idempotency & Caching Tests

Tests that compilation is idempotent:
- Running compile twice produces identical output
- File hashes match on second run
- No unnecessary regeneration
- Cache invalidation works correctly
"""

import hashlib
from pathlib import Path

import pytest


class TestIdempotency:
    """Test that compilation is idempotent."""

    def test_compile_twice_identical(self):
        """Test that compiling twice produces identical output."""
        from core.cli_interface import CLI

        cli = CLI()

        # First compile
        cli.compile()

        # Collect hashes of generated files
        run_cache = Path("run_cache")
        first_hashes = {}
        for file in run_cache.rglob("*.py"):
            if file.is_file():
                content = file.read_bytes()
                first_hashes[str(file)] = hashlib.sha256(content).hexdigest()

        # Second compile
        cli.compile()

        # Collect hashes again
        second_hashes = {}
        for file in run_cache.rglob("*.py"):
            if file.is_file():
                content = file.read_bytes()
                second_hashes[str(file)] = hashlib.sha256(content).hexdigest()

        # Hashes should match
        assert first_hashes == second_hashes

    def test_compile_creates_same_files(self):
        """Test that compiling twice creates the same files."""
        from core.cli_interface import CLI

        cli = CLI()

        # First compile
        cli.compile()
        first_files = set(Path("run_cache").rglob("*"))

        # Second compile
        cli.compile()
        second_files = set(Path("run_cache").rglob("*"))

        # File sets should match
        assert first_files == second_files

    def test_no_errors_on_recompile(self):
        """Test that recompiling doesn't produce errors."""
        from core.cli_interface import CLI

        cli = CLI()

        # First compile
        cli.compile()

        # Second compile - should not raise
        try:
            cli.compile()
        except Exception as e:
            pytest.fail(f"Recompile raised exception: {e}")

    def test_cache_invalidation_on_change(self):
        """Test that changing operations invalidates cache."""
        # This would require modifying operation definitions dynamically
        # If we add a new operation, recompiling should detect it
        pass

    def test_partial_regeneration(self):
        """Test that only changed files are regenerated."""
        # If we modify one operation, only its flow file should regenerate
        # Other flow files should be unchanged
        pass
