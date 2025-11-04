"""Configuration management for Pulpo Core projects.

Handles YAML config file parsing, validation, port management, and detection
of corrupted configs or containers.
"""

from __future__ import annotations

import socket
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


class ConfigManager:
    """Manage project configuration and port allocation."""

    DEFAULT_CONFIG_NAME = ".pulpo.yml"
    DEFAULT_PORT_BASE = 10010

    # Port offset mapping
    PORT_OFFSETS = {
        "api": 0,
        "ui": 1,
        "mongodb": 2,
        "prefect_server": 3,
        "prefect_ui": 4,
    }

    def __init__(
        self, config_path: Path | str | None = None, project_root: Path | str | None = None
    ):
        """Initialize config manager.

        Args:
            config_path: Path to .pulpo.yml. If None, looks in pwd.
            project_root: Root directory for relative paths. Defaults to config directory.
        """
        if config_path is None:
            config_path = Path.cwd() / self.DEFAULT_CONFIG_NAME
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.project_root = Path(project_root) if project_root else config_path.parent
        self._config: dict[str, Any] | None = None

    @staticmethod
    def create_default_config(
        project_name: str = "my-project",
        port_base: int | None = None,
        models_dirs: list[str] | None = None,
        operations_dirs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a default configuration dictionary.

        Args:
            project_name: Project name
            port_base: Base port number. If None, finds next available.
            models_dirs: List of model directories (relative to pwd)
            operations_dirs: List of operation directories (relative to pwd)

        Returns:
            Configuration dictionary
        """
        if port_base is None:
            port_base = ConfigManager.find_available_port_base()

        if models_dirs is None:
            models_dirs = ["models"]

        if operations_dirs is None:
            operations_dirs = ["operations"]

        return {
            "project_name": project_name,
            "version": "1.0",
            "port_base": port_base,
            "ports": {
                "api": port_base + ConfigManager.PORT_OFFSETS["api"],
                "ui": port_base + ConfigManager.PORT_OFFSETS["ui"],
                "mongodb": port_base + ConfigManager.PORT_OFFSETS["mongodb"],
                "prefect_server": port_base + ConfigManager.PORT_OFFSETS["prefect_server"],
                "prefect_ui": port_base + ConfigManager.PORT_OFFSETS["prefect_ui"],
            },
            "discovery": {
                "models_dirs": models_dirs,
                "operations_dirs": operations_dirs,
            },
            "docker": {
                "image_version": "latest",
                "base_image": project_name,
            },
        }

    @staticmethod
    def find_available_port_base(start: int = 10010, step: int = 10) -> int:
        """Find next available port base.

        Tries to bind to all ports in the range [base, base+4].

        Args:
            start: Starting port base (default 10010)
            step: Increment for each attempt (default 10)

        Returns:
            First available port base
        """
        current = start
        while True:
            if ConfigManager._is_port_range_available(current):
                return current
            current += step

    @staticmethod
    def _is_port_range_available(port_base: int) -> bool:
        """Check if all ports in range [base, base+4] are available."""
        for offset in ConfigManager.PORT_OFFSETS.values():
            port = port_base + offset
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", port))
                sock.close()
            except OSError:
                return False
        return True

    def load(self) -> dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: Config file not found
            ValueError: Invalid YAML or missing required fields
        """
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install pyyaml")

        try:
            content = self.config_path.read_text()
            self._config = yaml.safe_load(content) or {}
            self._validate_config(self._config)
            return self._config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.config_path}: {e}") from e

    def save(self, config: dict[str, Any]) -> None:
        """Save configuration to file.

        Args:
            config: Configuration dictionary
        """
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install pyyaml")

        self._validate_config(config)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        self._config = config

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:
        """Validate configuration structure.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If config is invalid
        """
        required_keys = {"project_name", "version", "port_base", "ports", "discovery", "docker"}
        missing = required_keys - set(config.keys())

        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

        # Validate ports
        required_ports = set(ConfigManager.PORT_OFFSETS.keys())
        config_ports = set(config.get("ports", {}).keys())
        if required_ports != config_ports:
            raise ValueError(
                f"Port config mismatch. Expected: {required_ports}, got: {config_ports}"
            )

        # Validate discovery paths
        discovery = config.get("discovery", {})
        if not isinstance(discovery.get("models_dirs"), list):
            raise ValueError("discovery.models_dirs must be a list")
        if not isinstance(discovery.get("operations_dirs"), list):
            raise ValueError("discovery.operations_dirs must be a list")

    def get_port(self, service: str) -> int:
        """Get port for a service.

        Args:
            service: Service name (api, ui, mongodb, prefect_server, prefect_ui)

        Returns:
            Port number

        Raises:
            ValueError: If service not found in config
        """
        config = self.load()
        port = config.get("ports", {}).get(service)

        if port is None:
            raise ValueError(f"Service '{service}' not found in config")

        return int(port)

    def get_port_base(self) -> int:
        """Get port base."""
        config = self.load()
        return int(config.get("port_base", self.DEFAULT_PORT_BASE))

    def get_discovery_dirs(self) -> tuple[list[str], list[str]]:
        """Get model and operation discovery directories.

        Returns:
            Tuple of (models_dirs, operations_dirs) - paths relative to pwd
        """
        config = self.load()
        discovery = config.get("discovery", {})
        return (
            discovery.get("models_dirs", ["models"]),
            discovery.get("operations_dirs", ["operations"]),
        )

    def get_project_name(self) -> str:
        """Get project name."""
        config = self.load()
        return config.get("project_name", "pulpo-app")

    def get_version(self) -> str:
        """Get project version."""
        config = self.load()
        return config.get("version", "1.0")

    def get_image_version(self) -> str:
        """Get Docker image version."""
        config = self.load()
        return config.get("docker", {}).get("image_version", "latest")

    def is_valid(self) -> bool:
        """Check if config file is valid.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.load()
            return True
        except (FileNotFoundError, ValueError, ImportError):
            return False

    def check_corruption(self) -> list[str]:
        """Check for corrupted configuration.

        Returns:
            List of issues found (empty if all good)
        """
        issues = []

        # Check file exists
        if not self.config_path.exists():
            issues.append(f"Config file missing: {self.config_path}")
            return issues

        # Check valid YAML
        try:
            self.load()
        except ValueError as e:
            issues.append(f"Invalid YAML: {e}")
            return issues

        # Check ports are available (warning only)
        config = self._config
        if config:
            port_base = config.get("port_base")
            if port_base and not self._is_port_range_available(port_base):
                issues.append(f"Port range {port_base}-{port_base+4} not available")

        return issues
