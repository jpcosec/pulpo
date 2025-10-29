"""Service discovery and health checking for JobHunter projects.

Provides commands to:
- Find where services are running
- Check if services are up
- Perform full system health checks
- Validate configuration and containers
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager


class ServiceManager:
    """Manage service discovery and health checks."""

    SERVICE_NAMES = {
        "api": "API Server",
        "ui": "UI (Refine.dev)",
        "mongodb": "MongoDB",
        "prefect_server": "Prefect Server",
        "prefect_ui": "Prefect UI",
    }

    def __init__(self, config_path: Path | str | None = None):
        """Initialize service manager.

        Args:
            config_path: Path to .jobhunter.yml
        """
        try:
            self.config = ConfigManager(config_path)
            self.config.load()
        except Exception:
            self.config = None

    def where(self, service: str) -> None:
        """Show where a service is running.

        Args:
            service: Service name (api, ui, mongodb, prefect_server, prefect_ui)
        """
        if not self.config:
            print("❌ No config found. Run 'make setup' first.")
            return

        try:
            port = self.config.get_port(service)
            service_display = self.SERVICE_NAMES.get(service, service)

            print()
            print(f"🔍 {service_display}:")
            print(f"   Config: {self.config.config_path}")
            print(f"   Port: {port}")
            print(f"   URL: http://localhost:{port}")

            # Check if port is listening
            if self._is_port_listening(port):
                print("   Status: ✅ Running")
            else:
                print("   Status: ❌ Not running")

            print()
        except ValueError as e:
            print(f"❌ {e}")

    def where_all(self) -> None:
        """Show where all services are running."""
        if not self.config:
            print("❌ No config found. Run 'make setup' first.")
            return

        print()
        print("📊 All Services:")
        print()

        # Build table data
        services_data = []
        for service_key, service_name in self.SERVICE_NAMES.items():
            try:
                port = self.config.get_port(service_key)
                url = f"http://localhost:{port}"
                is_up = self._is_port_listening(port)
                status = "✅ Up" if is_up else "❌ Down"

                services_data.append({
                    "name": service_name,
                    "port": str(port),
                    "url": url,
                    "status": status,
                })
            except ValueError:
                pass

        # Print table
        if services_data:
            self._print_table(
                ["Service", "Port", "URL", "Status"],
                [[d["name"], d["port"], d["url"], d["status"]] for d in services_data],
            )
        else:
            print("❌ No services configured")

        print()

    def is_up(self, service: str) -> int:
        """Check if a service is up.

        Args:
            service: Service name

        Returns:
            Exit code (0 = up, 1 = down)
        """
        if not self.config:
            print("❌ No config found. Run 'make setup' first.")
            return 1

        try:
            port = self.config.get_port(service)
            service_display = self.SERVICE_NAMES.get(service, service)

            if self._is_port_listening(port):
                print(f"✅ {service_display} is up (port {port})")
                return 0
            else:
                print(f"❌ {service_display} is down (port {port})")
                return 1
        except ValueError as e:
            print(f"❌ {e}")
            return 1

    def health(self) -> int:
        """Perform full system health check.

        Returns:
            Exit code (0 = healthy, 1 = issues found)
        """
        if not self.config:
            print("❌ No config found. Run 'make setup' first.")
            return 1

        issues = []
        warnings = []

        print()
        print("🏥 System Health Check:")
        print()

        # Check Configuration
        print("━" * 50)
        print("📋 CONFIGURATION")
        print("━" * 50)

        config_issues = self.config.check_corruption()
        if config_issues:
            for issue in config_issues:
                print(f"  ❌ {issue}")
                issues.append(issue)
        else:
            print(f"  ✅ {self.config.config_path}: Valid")

        # Check Makefile
        makefile_path = self.config.project_root / "Makefile"
        if makefile_path.exists():
            print("  ✅ Makefile: Exists")
        else:
            print("  ⚠️  Makefile: Missing (run 'make setup')")
            warnings.append("Makefile missing")

        # Check docker-compose
        docker_compose_path = self.config.project_root / "docker-compose.yml"
        if docker_compose_path.exists():
            print("  ✅ docker-compose.yml: Exists")
        else:
            print("  ⚠️  docker-compose.yml: Missing")
            warnings.append("docker-compose.yml missing")

        # Check .run_cache
        run_cache_path = self.config.project_root / ".run_cache"
        if run_cache_path.exists():
            print("  ✅ .run_cache/: Exists")
            # Check for generated files
            if (run_cache_path / "generated_api.py").exists():
                print("     ✅ generated_api.py: Present")
            else:
                print("     ⚠️  generated_api.py: Missing (run 'make compile')")
                warnings.append("generated_api.py missing")
        else:
            print("  ⚠️  .run_cache/: Missing (run 'make compile')")
            warnings.append(".run_cache missing")

        print()

        # Check Docker Containers
        print("━" * 50)
        print("🐳 DOCKER CONTAINERS")
        print("━" * 50)

        container_status = self._check_containers()
        if container_status:
            for container, status in container_status.items():
                symbol = "✅" if status["healthy"] else "⚠️ " if status["restarting"] else "❌"
                print(f"  {symbol} {container}: {status['message']}")
                if not status["healthy"] and not status["restarting"]:
                    issues.append(f"Container {container} not healthy")
        else:
            print("  ℹ️  No containers running")

        print()

        # Check Services
        print("━" * 50)
        print("🔌 SERVICES")
        print("━" * 50)

        for service_key, service_name in self.SERVICE_NAMES.items():
            try:
                port = self.config.get_port(service_key)
                if self._is_port_listening(port):
                    print(f"  ✅ {service_name} ({port}): Up")
                else:
                    print(f"  ❌ {service_name} ({port}): Down")
                    issues.append(f"{service_name} not responding")
            except ValueError:
                pass

        print()

        # Check .run_cache integrity
        print("━" * 50)
        print("💾 RUN CACHE")
        print("━" * 50)

        cache_status = self._check_run_cache()
        if cache_status:
            for item, status in cache_status.items():
                symbol = "✅" if status["valid"] else "❌"
                print(f"  {symbol} {item}: {status['message']}")
                if not status["valid"]:
                    issues.append(f"{item} corrupted or invalid")
        else:
            print("  ⚠️  .run_cache/ not found")

        print()

        # Summary
        print("━" * 50)
        if not issues:
            print("✅ Overall Status: Healthy")
            return 0
        else:
            print(f"⚠️  Overall Status: {len(issues)} issue(s) found")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            return 1

    @staticmethod
    def _is_port_listening(port: int) -> bool:
        """Check if a port is listening.

        Args:
            port: Port number

        Returns:
            True if port is listening
        """
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result == 0
        except Exception:
            return False

    @staticmethod
    def _check_containers() -> dict[str, dict]:
        """Check Docker container status.

        Returns:
            Dict of container statuses
        """
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            containers = {}
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) == 2:
                    name, status = parts
                    if "jobhunter" in name:
                        containers[name] = {
                            "healthy": "Up" in status and "Healthy" in status,
                            "restarting": "Restarting" in status,
                            "message": status,
                        }

            return containers
        except Exception:
            return {}

    @staticmethod
    def _check_run_cache() -> dict[str, dict]:
        """Check .run_cache/ integrity.

        Returns:
            Dict of cache item statuses
        """
        cache_dir = Path(".run_cache")
        if not cache_dir.exists():
            return {}

        items = {
            "generated_api.py": cache_dir / "generated_api.py",
            "generated_frontend/": cache_dir / "generated_frontend",
            "cli/jobhunter": cache_dir / "cli" / "jobhunter",
        }

        status = {}
        for name, path in items.items():
            if path.exists():
                status[name] = {
                    "valid": True,
                    "message": f"Present ({'executable' if path.is_file() and path.stat().st_mode & 0o111 else 'readable'})",
                }
            else:
                status[name] = {
                    "valid": False,
                    "message": "Missing",
                }

        return status

    @staticmethod
    def _print_table(headers: list[str], rows: list[list[str]]) -> None:
        """Print formatted table.

        Args:
            headers: Column headers
            rows: Table rows
        """
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        # Print header
        header_line = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐"
        print(header_line)

        header = "│" + "│".join(f" {h:<{w}} " for h, w in zip(headers, widths, strict=False)) + "│"
        print(header)

        sep_line = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"
        print(sep_line)

        # Print rows
        for row in rows:
            row_line = "│" + "│".join(f" {cell:<{w}} " for cell, w in zip(row, widths, strict=False)) + "│"
            print(row_line)

        # Print footer
        footer_line = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘"
        print(footer_line)


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print("Usage: python service_manager.py [where|where-all|is-up|health] [args]")
        sys.exit(1)

    command = sys.argv[1]
    manager = ServiceManager()

    if command == "where" and len(sys.argv) > 2:
        manager.where(sys.argv[2])
    elif command == "where-all":
        manager.where_all()
    elif command == "is-up" and len(sys.argv) > 2:
        sys.exit(manager.is_up(sys.argv[2]))
    elif command == "health":
        sys.exit(manager.health())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
