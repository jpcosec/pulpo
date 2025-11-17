"""Init phase - Initial project setup.

Handles:
- CLI generation (if not exists)
- Configuration file generation (.pulpo.yml)
- Graph visualization generation
"""

from .cli_generator import generate_cli_script
from .project_init import init_project

__all__ = [
    "generate_cli_script",
    "init_project",
]
