"""Re-export decorators for convenience.

This module provides easy access to Pulpo decorators without needing to know
the internal module structure. Users can import directly:

    from core.decorators import datamodel, operation
"""

from .analysis.decorators import datamodel, operation

__all__ = ["datamodel", "operation"]
