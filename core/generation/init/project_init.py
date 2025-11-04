#!/usr/bin/env python3
"""Initialize a new JobHunter project.

Creates project structure with configuration, Makefile, docker-compose.yml,
and .run_cache directories. Automatically detects available ports.

Usage:
    python init_project.py [project_name] [options]

Options:
    --force         Skip confirmation prompts and overwrite existing files
    --dry-run       Show what would be created without creating files
    --port-base N   Use specific port base (default: auto-detect)
    --all           Initialize + compile + build + up
    --reset         Clean everything (prompt for each), then run --all
    --clean         Clean all (no prompt)
    --demo          Copy examples, then run --all
    --help, -h      Show this help message

Examples:
    # Initialize current directory
    python init_project.py

    # Initialize with specific name
    python init_project.py my-project

    # Force overwrite existing files
    python init_project.py --force

    # Dry run to preview
    python init_project.py --dry-run

    # Use specific port base
    python init_project.py --port-base 10020

    # Full setup (init + compile + build + up)
    python init_project.py --all
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager


class ProjectInitializer:
    """Initialize a JobHunter project."""

    TEMPLATES = {
        "Makefile": """{makefile_content}""",
        "docker-compose.yml": """{docker_compose_content}""",
    }

    def __init__(
        self,
        project_root: Path | None = None,
        project_name: str | None = None,
        port_base: int | None = None,
        force: bool = False,
        dry_run: bool = False,
    ):
        """Initialize project initializer.

        Args:
            project_root: Project root directory. Defaults to cwd.
            project_name: Project name. Defaults to directory name.
            port_base: Base port number. If None, auto-detect.
            force: Skip confirmation prompts.
            dry_run: Show what would be created without creating files.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # Get project name: from arg, or prompt if not in dry_run/force mode, or use dir name
        if project_name:
            self.project_name = project_name
        elif not dry_run and not force:
            # Prompt user for project name
            default_name = self.project_root.name or "my-project"
            self.project_name = self._prompt_for_project_name(default_name)
        else:
            self.project_name = self.project_root.name or "my-project"

        self.port_base = port_base
        self.force = force
        self.dry_run = dry_run
        self.config_path = self.project_root / ".jobhunter.yml"

    def initialize(self) -> None:
        """Initialize project with config, Makefile, docker-compose."""
        print()
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║          JobHunter Project Initialization                      ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print()
        print(f"📁 Project directory: {self.project_root}")
        print(f"📝 Project name:      {self.project_name}")

        if self.dry_run:
            print("🔍 Mode:              DRY RUN (no files will be created)")
        elif self.force:
            print("⚡ Mode:              FORCE (overwriting existing files)")
        print()

        # Check for existing files before starting
        if not self.dry_run and not self.force:
            existing = self._check_existing_files()
            if existing:
                print()
                print("⚠️  Warning: The following files already exist:")
                for f in existing:
                    print(f"  - {f.name}")
                print()
                if not self._prompt_yes_no("Overwrite these files"):
                    print()
                    print("❌ Initialization cancelled.")
                    print()
                    print("Use --force to skip confirmation, or --dry-run to preview.")
                    return
                print()

        # Detect or use provided port base
        if self.port_base is None:
            print("🔍 Detecting available ports...")
            self.port_base = ConfigManager.find_available_port_base()
            print(f"✅ Found available port base: {self.port_base}")
        else:
            print(f"🔌 Using specified port base: {self.port_base}")

        # Calculate port mapping
        ports = {
            "api": self.port_base + ConfigManager.PORT_OFFSETS["api"],
            "ui": self.port_base + ConfigManager.PORT_OFFSETS["ui"],
            "mongodb": self.port_base + ConfigManager.PORT_OFFSETS["mongodb"],
            "prefect_server": self.port_base + ConfigManager.PORT_OFFSETS["prefect_server"],
            "prefect_ui": self.port_base + ConfigManager.PORT_OFFSETS["prefect_ui"],
        }

        print()
        print("📡 Port allocation:")
        for service, port in ports.items():
            print(f"  {service:20s} → {port}")
        print()

        # Create files
        print("📦 Creating project structure...")
        print()

        # Create config
        self._create_config()

        # Create .env
        self._create_env_file()

        # Create Makefile
        self._create_makefile()

        # Create docker-compose
        self._create_docker_compose()

        # Create .gitignore
        self._create_gitignore()

        # Create directories
        self._create_directories()

        # Create example files
        self._create_example_files()

        # Create docs directory
        docs_dir = self.project_root / "docs"
        if self.dry_run:
            print(f"  [DRY RUN] Would create: {docs_dir}/README.md")
        else:
            docs_dir.mkdir(exist_ok=True)
            (docs_dir / "README.md").write_text(
                "# Architecture Documentation\n\nAuto-generated graphs will appear here after running `make compile`.\n"
            )
            print(f"  ✅ Created: {docs_dir}/README.md")

        print()

        if self.dry_run:
            print("✅ Dry run complete! No files were created.")
            print()
            print("Run without --dry-run to actually create the files.")
        else:
            print("✅ Project initialized successfully!")
            print()
            print("📋 Created files:")
            print("  ├── .jobhunter.yml         (Project configuration)")
            print("  ├── .env                   (Environment variables)")
            print("  ├── .gitignore             (Git ignore patterns)")
            print("  ├── Makefile               (Build commands)")
            print("  ├── docker-compose.yml     (Docker configuration)")
            print("  ├── models/                (Data models directory)")
            print("  │   ├── __init__.py")
            print("  │   └── README.md")
            print("  ├── operations/            (Operations directory)")
            print("  │   ├── __init__.py")
            print("  │   └── README.md")
            print("  ├── docs/                  (Documentation)")
            print("  │   └── README.md")
            print("  └── .run_cache/            (Generated code)")
            print("      ├── generated_api/")
            print("      └── generated_frontend/")
            print()
            print("🚀 Next steps:")
            print("  1. Define your data models in models/")
            print("  2. Define your operations in operations/")
            print("  3. Run 'make compile' to generate API, UI, and CLI")
            print("  4. Run 'make build' to build Docker images")
            print("  5. Run 'make up' to start all services")
            print("  6. Visit:")
            print(f"     • API Docs:  http://localhost:{ports['api']}/docs")
            print(f"     • UI:        http://localhost:{ports['ui']}")
            print(f"     • Prefect:   http://localhost:{ports['prefect_ui']}")
            print()
            print("📚 More help:")
            print("  make help               - Show all available commands")
        print()

    def _create_config(self) -> None:
        """Create .jobhunter.yml config file."""
        if self.dry_run:
            print(f"  [DRY RUN] Would create: {self.config_path}")
            config = ConfigManager.create_default_config(
                project_name=self.project_name,
                port_base=self.port_base,
                models_dirs=["models"],
                operations_dirs=["operations"],
            )
            # Show preview
            try:
                import yaml

                yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
                print("  Content:")
                for line in yaml_content.splitlines()[:10]:
                    print(f"    {line}")
                if len(yaml_content.splitlines()) > 10:
                    print("    ...")
            except ImportError:
                print("  Content: (YAML preview unavailable)")
            return

        # Create config
        config = ConfigManager.create_default_config(
            project_name=self.project_name,
            port_base=self.port_base,
            models_dirs=["models"],
            operations_dirs=["operations"],
        )

        # Save config
        config_manager = ConfigManager(self.config_path)
        config_manager.save(config)

        print(f"  ✅ Created: {self.config_path}")

    def _create_env_file(self) -> None:
        """Create .env file with project configuration."""
        env_path = self.project_root / ".env"

        content = f"""# JobHunter Project Configuration
PROJECT_NAME={self.project_name}
IMAGE_VERSION=latest

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE={self.project_name}

# Environment
ENVIRONMENT=development
"""

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {env_path}")
            print("  Content (preview):")
            for line in content.splitlines()[:5]:
                print(f"    {line}")
            print("    ...")
            return

        env_path.write_text(content)
        print(f"  ✅ Created: {env_path}")

    def _create_gitignore(self) -> None:
        """Create .gitignore file."""
        gitignore_path = self.project_root / ".gitignore"

        content = """# Generated code
.run_cache/
cli/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Node (for generated frontend)
node_modules/
"""

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {gitignore_path}")
            return

        gitignore_path.write_text(content)
        print(f"  ✅ Created: {gitignore_path}")

    def _create_example_files(self) -> None:
        """Create README files in model and operation directories."""
        models_dir = self.project_root / "models"
        operations_dir = self.project_root / "operations"

        # README for models
        models_readme = '''# Data Models

Define your data models here using the `@datamodel` decorator from Beanie and the core framework.

## Example:

```python
from beanie import Document
from pydantic import Field
from core.decorators import datamodel

@datamodel(
    name="MyModel",
    description="A sample data model",
    tags=["sample"],
)
class MyModel(Document):
    """My data model."""

    name: str = Field(..., description="Name")
    email: str = Field(..., description="Email")

    class Settings:
        name = "my_models"
```

## Parameters:
- `name`: Unique identifier for the model
- `description`: Human-readable description
- `tags`: Optional tags for categorization
- `ui`: Optional UI hints (dict)
- `indexes`: Documentation for database indexes
- `relations`: Relationships to other models

For more details, see the framework documentation.
'''

        # README for operations
        operations_readme = '''# Operations

Define your operations here using the `@operation` decorator with typed input/output schemas.

## Example:

```python
from pydantic import BaseModel
from core.decorators import operation


class GreetInput(BaseModel):
    """Input for greet operation."""
    name: str


class GreetOutput(BaseModel):
    """Output for greet operation."""
    message: str


@operation(
    name="greet",
    description="Greet a person by name",
    category="greeting",
    inputs=GreetInput,
    outputs=GreetOutput,
)
async def greet(input_data: GreetInput) -> GreetOutput:
    """Greet someone by name."""
    return GreetOutput(message=f"Hello, {input_data.name}!")
```

## Parameters:
- `name`: Unique identifier for the operation
- `description`: Human-readable description
- `category`: Logical category for grouping
- `inputs`: Pydantic model for input validation
- `outputs`: Pydantic model for output definition
- `tags`: Optional tags for categorization
- `permissions`: Optional permission requirements
- `async_enabled`: Whether to enable async execution
- `create_taskrun`: Whether to create TaskRun records

For more details, see the framework documentation.
'''

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {models_dir}/README.md")
            print(f"  [DRY RUN] Would create: {operations_dir}/README.md")
            return

        # Create README files
        (models_dir / "README.md").write_text(models_readme)
        (operations_dir / "README.md").write_text(operations_readme)

        print(f"  ✅ Created: {models_dir}/README.md")
        print(f"  ✅ Created: {operations_dir}/README.md")

    def _check_existing_files(self) -> list[Path]:
        """Check for existing files that would be overwritten.

        Returns:
            List of existing file paths
        """
        files_to_check = [
            self.project_root / ".jobhunter.yml",
            self.project_root / "Makefile",
            self.project_root / "docker-compose.yml",
            self.project_root / ".env",
            self.project_root / ".gitignore",
        ]

        return [f for f in files_to_check if f.exists()]

    def _create_makefile(self) -> None:
        """Create Makefile wrapper."""
        makefile_path = self.project_root / "Makefile"

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {makefile_path}")
            print("  Content: (Makefile wrapper to core framework)")
            return

        # Find core directory (go up from project root to find core)
        core_dir = self._find_core_directory()
        if not core_dir:
            raise RuntimeError("Could not find core/ directory")

        # Create wrapper Makefile
        content = self._generate_makefile(core_dir)
        makefile_path.write_text(content)
        print(f"  ✅ Created: {makefile_path}")

    def _create_docker_compose(self) -> None:
        """Create docker-compose.yml."""
        compose_path = self.project_root / "docker-compose.yml"

        # Calculate ports
        ports = {
            "api": self.port_base + ConfigManager.PORT_OFFSETS["api"],
            "ui": self.port_base + ConfigManager.PORT_OFFSETS["ui"],
            "mongodb": self.port_base + ConfigManager.PORT_OFFSETS["mongodb"],
            "prefect_server": self.port_base + ConfigManager.PORT_OFFSETS["prefect_server"],
            "prefect_ui": self.port_base + ConfigManager.PORT_OFFSETS["prefect_ui"],
        }

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {compose_path}")
            print("  Content: (Docker Compose configuration with ports)")
            for service, port in ports.items():
                print(f"    {service}: {port}")
            return

        # Create docker-compose
        content = self._generate_docker_compose(self.project_name, ports)
        compose_path.write_text(content)
        print(f"  ✅ Created: {compose_path}")

    def _create_directories(self) -> None:
        """Create project directories."""
        dirs = [
            self.project_root / "models",
            self.project_root / "operations",
            self.project_root / ".run_cache",
            self.project_root / ".run_cache" / "generated_api",
            self.project_root / ".run_cache" / "generated_frontend",
        ]

        if self.dry_run:
            print("  [DRY RUN] Would create directories:")
            for d in dirs:
                print(f"    {d}")
                if d.name in ("models", "operations"):
                    print(f"    {d}/__init__.py")
            return

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            # Create __init__.py for Python packages
            if d.name in ("models", "operations"):
                (d / "__init__.py").write_text('"""Auto-generated package."""\n')

        print("  ✅ Created: directories (models, operations, .run_cache)")

    def clean(self, prompt: bool = True) -> None:
        """Clean all project files.

        Args:
            prompt: Whether to prompt before deleting each file
        """
        print()
        print("🧹 Cleaning project files...")
        print()

        files_to_clean = [
            (".jobhunter.yml", "Config file"),
            ("Makefile", "Makefile"),
            ("docker-compose.yml", "Docker Compose"),
            (".run_cache", ".run_cache/"),
        ]

        for filename, display_name in files_to_clean:
            path = self.project_root / filename
            if path.exists():
                if prompt:
                    if not self._prompt_yes_no(f"Delete {display_name}"):
                        print(f"   Skipped: {display_name}")
                        continue

                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

                print(f"   ✅ Deleted: {display_name}")

        print()

    def reset(self) -> None:
        """Reset project (clean with prompts, then initialize)."""
        print()
        print("⚠️  WARNING: This will reset your project configuration.")
        print()

        if not self._prompt_yes_no("Continue"):
            print("Cancelled.")
            return

        self.clean(prompt=True)
        self.initialize()

    def add_demo(self) -> None:
        """Note: Demo examples are now only provided via tarball (make demo).

        core/examples/ was removed - only the tarball Pokemon demo is supported.
        Run 'make demo' from the framework root to unpack the demo project.
        """
        print()
        print("ℹ️  Demo examples are provided via tarball only")
        print()
        print("To use the demo project:")
        print("  1. cd <jobhunter-core-minimal>")
        print("  2. make demo  (unpacks test-project-demo/)")
        print("  3. cd test-project-demo")
        print()
        print("No examples copied to this project.")
        print()

    def run_all(self) -> None:
        """Run full setup: compile → build → up."""
        print()
        print("🚀 Running full setup...")
        print()

        commands = [
            ("compile", "make compile"),
            ("build", "make build"),
            ("up", "make up"),
        ]

        for name, cmd in commands:
            print(f"Running: {cmd}")
            result = subprocess.run(cmd, shell=True, cwd=self.project_root)
            if result.returncode != 0:
                print(f"❌ Failed: {cmd}")
                sys.exit(1)
            print()

        print("✅ Full setup complete!")

    @staticmethod
    def _find_core_directory() -> Path | None:
        """Find the core/ directory.

        Search strategies:
        1. Check JOBHUNTER_CORE environment variable
        2. Look up from cwd
        3. Check common locations

        Returns:
            Path to core directory, or None if not found
        """
        import os

        # Strategy 1: Environment variable
        env_core = os.getenv("JOBHUNTER_CORE")
        if env_core:
            core_path = Path(env_core)
            if (core_path / "core").exists():
                return core_path
            if core_path.name == "core" and core_path.exists():
                return core_path.parent

        # Strategy 2: Look up from cwd
        current = Path.cwd()
        for _ in range(15):  # Increase search depth
            if (current / "core" / "core").exists():
                return current / "core"
            current = current.parent

        # Strategy 3: Check absolute path to this script
        script_dir = Path(__file__).parent.parent
        if (script_dir / "core").exists():
            return script_dir

        return None

    @staticmethod
    def _prompt_yes_no(message: str) -> bool:
        """Prompt user for yes/no.

        Args:
            message: Prompt message

        Returns:
            True if user says yes
        """
        response = input(f"   {message}? [y/N] ").strip().lower()
        return response in ("y", "yes")

    @staticmethod
    def _prompt_for_project_name(default_name: str) -> str:
        """Prompt user for project name.

        Args:
            default_name: Default project name (shown as suggestion)

        Returns:
            Project name entered by user or default
        """
        print()
        print("📝 Project Configuration")
        print("─" * 50)
        response = input(f"   Project name [{default_name}]: ").strip()

        if not response:
            return default_name

        # Sanitize name (lowercase, hyphens only)
        sanitized = response.lower().replace(" ", "-").replace("_", "-")
        if sanitized != response:
            print(f"   ℹ️  Sanitized to: {sanitized}")

        return sanitized

    @staticmethod
    def _generate_makefile(core_dir: Path) -> str:
        """Generate wrapper Makefile.

        Args:
            core_dir: Path to core directory

        Returns:
            Makefile content
        """
        # Use absolute path to core directory
        abs_core_dir = Path(core_dir).resolve()

        content = dedent(f"""\
            # Auto-generated Makefile for JobHunter project
            # This delegates to {abs_core_dir}/Makefile

            CORE_MAKEFILE := {abs_core_dir}/Makefile
            PROJECT_DIR := $(shell pwd)
            CONFIG_FILE := $(PROJECT_DIR)/.jobhunter.yml

            .PHONY: help setup discover compile build up down logs health where where-all is-up

            help:
            \t@$(MAKE) -f $(CORE_MAKEFILE) help

            setup:
            \t@python {abs_core_dir}/scripts/init_project.py

            setup-all:
            \t@python {abs_core_dir}/scripts/init_project.py --all

            setup-reset:
            \t@python {abs_core_dir}/scripts/init_project.py --reset

            setup-clean:
            \t@python {abs_core_dir}/scripts/init_project.py --clean

            setup-demo:
            \t@python {abs_core_dir}/scripts/init_project.py --demo

            discover:
            \t@$(MAKE) -f $(CORE_MAKEFILE) discover CONFIG_FILE=$(CONFIG_FILE)

            compile:
            \t@$(MAKE) -f $(CORE_MAKEFILE) compile CONFIG_FILE=$(CONFIG_FILE)

            build:
            \t@$(MAKE) -f $(CORE_MAKEFILE) build CONFIG_FILE=$(CONFIG_FILE)

            up:
            \t@$(MAKE) -f $(CORE_MAKEFILE) up CONFIG_FILE=$(CONFIG_FILE)

            down:
            \t@$(MAKE) -f $(CORE_MAKEFILE) down

            logs:
            \t@$(MAKE) -f $(CORE_MAKEFILE) logs

            health:
            \t@python {abs_core_dir}/scripts/service_manager.py health

            where:
            \t@python {abs_core_dir}/scripts/service_manager.py where $(SERVICE)

            where-all:
            \t@python {abs_core_dir}/scripts/service_manager.py where-all

            is-up:
            \t@python {abs_core_dir}/scripts/service_manager.py is-up $(SERVICE)

            %:
            \t@$(MAKE) -f $(CORE_MAKEFILE) $@ CONFIG_FILE=$(CONFIG_FILE)
            """)

        return content

    @staticmethod
    def _generate_docker_compose(project_name: str, ports: dict) -> str:
        """Generate docker-compose.yml from template.

        Args:
            project_name: Project name
            ports: Port mapping from config

        Returns:
            docker-compose.yml content
        """
        try:
            from jinja2 import Template
        except ImportError:
            # Fallback if Jinja2 not available
            return ProjectInitializer._generate_docker_compose_fallback(project_name, ports)

        # Find the template
        template_path = Path(__file__).parent.parent / "docker" / "docker-compose.yml.template"

        if not template_path.exists():
            # Fallback to inline generation
            return ProjectInitializer._generate_docker_compose_fallback(project_name, ports)

        # Read and render template
        template_content = template_path.read_text()
        template = Template(template_content)

        content = template.render(
            project_name=project_name,
            ports=ports,
        )

        return content

    @staticmethod
    def _generate_docker_compose_fallback(project_name: str, ports: dict) -> str:
        """Fallback docker-compose generation (inline).

        Args:
            project_name: Project name
            ports: Port mapping from config

        Returns:
            docker-compose.yml content
        """
        api_port = ports.get("api", 8001)
        ui_port = ports.get("ui", 3001)
        mongodb_port = ports.get("mongodb", 27017)
        prefect_server_port = ports.get("prefect_server", 4200)

        content = dedent(f"""\
            version: "3.9"

            services:
              api:
                container_name: ${{PROJECT_NAME}}-api
                image: ${{PROJECT_NAME}}-api:${{VERSION}}
                ports:
                  - "{api_port}:8000"
                environment:
                  - MONGODB_URL=mongodb://mongodb:27017
                  - MONGODB_DATABASE=${{PROJECT_NAME}}
                volumes:
                  - ./.run_cache:/app/.run_cache:rw
                depends_on:
                  - mongodb

              mongodb:
                container_name: ${{PROJECT_NAME}}-mongodb
                image: mongo:7.0
                ports:
                  - "{mongodb_port}:27017"
                environment:
                  - MONGO_INITDB_DATABASE=${{PROJECT_NAME}}
                volumes:
                  - ${{PROJECT_NAME}}-mongo-data:/data/db
                healthcheck:
                  test: mongosh --quiet --eval 'db.runCommand("ping")'
                  interval: 10s
                  timeout: 5s
                  retries: 3

              ui:
                container_name: ${{PROJECT_NAME}}-ui
                build:
                  context: ./.run_cache/generated_frontend
                  dockerfile: Dockerfile
                ports:
                  - "{ui_port}:3000"
                environment:
                  - REACT_APP_API_URL=http://localhost:{api_port}
                depends_on:
                  - api

              prefect-server:
                container_name: ${{PROJECT_NAME}}-prefect-server
                image: prefecthq/prefect:2-latest
                entrypoint: /opt/prefect/entrypoint.sh prefect server start --host 0.0.0.0
                ports:
                  - "{prefect_server_port}:4200"
                environment:
                  - PREFECT_API_URL=http://0.0.0.0:4200/api
                volumes:
                  - ${{PROJECT_NAME}}-prefect-data:/root/.prefect

            volumes:
              ${{PROJECT_NAME}}-mongo-data:
              ${{PROJECT_NAME}}-prefect-data:

            networks:
              default:
                name: ${{PROJECT_NAME}}-network
            """)

        return content


def has_flag(flag: str) -> bool:
    """Check if a flag is present in command line arguments."""
    return flag in sys.argv


def get_flag_value(flag: str) -> str | None:
    """Get value for a flag (e.g., --port-base 10020)."""
    try:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv) and not sys.argv[idx + 1].startswith("--"):
            return sys.argv[idx + 1]
    except ValueError:
        pass
    return None


def get_positional_arg() -> str | None:
    """Get first positional argument (project name)."""
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            # Check if it's a flag value
            for i, a in enumerate(sys.argv[1:], 1):
                if a.startswith("--") and i + 1 < len(sys.argv) and sys.argv[i + 1] == arg:
                    continue
            if arg not in ["--help", "-h", "--force", "--dry-run", "--all", "--reset", "--clean", "--demo"]:
                return arg
    return None


def show_help():
    """Display help message."""
    print(__doc__)
    sys.exit(0)


def main():
    """Command-line entry point."""
    # Check for help flag first
    if has_flag("--help") or has_flag("-h"):
        show_help()

    # Parse command-line arguments
    project_name = get_positional_arg()
    port_base_str = get_flag_value("--port-base")
    force = has_flag("--force")
    dry_run = has_flag("--dry-run")

    # Parse port base if provided
    port_base = None
    if port_base_str:
        try:
            port_base = int(port_base_str)
        except ValueError:
            print(f"❌ Error: Invalid port base: {port_base_str}")
            print("Port base must be an integer.")
            sys.exit(1)

    # Create initializer
    initializer = ProjectInitializer(
        project_name=project_name,
        port_base=port_base,
        force=force,
        dry_run=dry_run,
    )

    # Handle special modes
    if has_flag("--all"):
        initializer.initialize()
        if not dry_run:
            initializer.run_all()
    elif has_flag("--reset"):
        initializer.reset()
        if not dry_run:
            initializer.run_all()
    elif has_flag("--clean"):
        initializer.clean(prompt=not force)
    elif has_flag("--demo"):
        initializer.initialize()
        if not dry_run:
            initializer.add_demo()
            initializer.run_all()
    else:
        # Default: just initialize
        initializer.initialize()


if __name__ == "__main__":
    main()
