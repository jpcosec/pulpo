"""
Hierarchy Parser for Pulpo Operations

Parses hierarchical operation names (e.g., "scraping.stepstone.fetch") into
structured components for flow composition and dependency analysis.

The hierarchy defines:
- Operation scope and grouping
- Flow composition (each hierarchical level becomes a subflow)
- Dependency relationships (implicit in data flow)
- Parallelization opportunities (operations at same level with same I/O)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedName:
    """Represents a parsed hierarchical operation name."""

    full_name: str  # e.g., "scraping.stepstone.fetch"
    hierarchy: list[str]  # e.g., ["scraping", "stepstone", "fetch"]
    level: int  # e.g., 3 (number of components)
    step: str  # e.g., "fetch" (last component)
    parent: Optional[str]  # e.g., "scraping.stepstone"
    is_standalone: bool  # True if no parent (single component)

    @property
    def all_parents(self) -> list[str]:
        """Return all parent levels in order.

        Example: "scraping.stepstone.fetch" returns:
        ["scraping", "scraping.stepstone"]
        """
        if self.is_standalone:
            return []
        return [".".join(self.hierarchy[: i + 1]) for i in range(len(self.hierarchy) - 1)]

    @property
    def root(self) -> str:
        """Return the topmost parent level.

        Example: "scraping.stepstone.fetch" returns "scraping"
        """
        return self.hierarchy[0] if self.hierarchy else ""

    def is_child_of(self, potential_parent: str) -> bool:
        """Check if this operation is a child of the given parent.

        Args:
            potential_parent: Parent name to check (e.g., "scraping")

        Returns:
            True if this operation is under that parent
        """
        if potential_parent == "":
            return not self.is_standalone
        return self.full_name.startswith(potential_parent + ".")

    def is_sibling_of(self, other_name: str) -> bool:
        """Check if this operation is at same level with same parent.

        Args:
            other_name: Other operation name to check

        Returns:
            True if both have same parent
        """
        parsed_other = HierarchyParser.parse(other_name)
        return self.parent == parsed_other.parent


class HierarchyParser:
    """Parses and analyzes hierarchical operation names."""

    SEPARATOR = "."
    MIN_LEVEL = 1
    MAX_LEVEL = 10  # Prevent excessively deep hierarchies

    @staticmethod
    def parse(name: str) -> ParsedName:
        """Parse a hierarchical operation name.

        Args:
            name: Operation name (e.g., "scraping.stepstone.fetch")

        Returns:
            ParsedName with full structure

        Raises:
            ValueError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Operation name must be non-empty string")

        if not name.replace(".", "").replace("_", "").isalnum():
            raise ValueError(
                f"Operation name must contain only alphanumeric, dots, "
                f"and underscores: {name}"
            )

        parts = name.split(HierarchyParser.SEPARATOR)

        # Remove empty parts
        parts = [p for p in parts if p]

        if not parts:
            raise ValueError(f"Operation name cannot be empty or only dots: {name}")

        if len(parts) > HierarchyParser.MAX_LEVEL:
            raise ValueError(
                f"Operation hierarchy too deep (max {HierarchyParser.MAX_LEVEL} "
                f"levels): {name}"
            )

        level = len(parts)
        step = parts[-1]
        is_standalone = level == 1
        parent = HierarchyParser.SEPARATOR.join(parts[:-1]) if not is_standalone else None

        return ParsedName(
            full_name=name,
            hierarchy=parts,
            level=level,
            step=step,
            parent=parent,
            is_standalone=is_standalone,
        )

    @staticmethod
    def get_parent(name: str) -> Optional[str]:
        """Get the parent of an operation.

        Args:
            name: Operation name

        Returns:
            Parent name or None if standalone
        """
        return HierarchyParser.parse(name).parent

    @staticmethod
    def get_level(name: str) -> int:
        """Get the hierarchy level (depth) of an operation.

        Args:
            name: Operation name

        Returns:
            Number of hierarchy components
        """
        return HierarchyParser.parse(name).level

    @staticmethod
    def is_standalone(name: str) -> bool:
        """Check if operation is standalone (no parent).

        Args:
            name: Operation name

        Returns:
            True if operation has no parent
        """
        return HierarchyParser.parse(name).is_standalone

    @staticmethod
    def is_leaf(name: str) -> bool:
        """Check if operation is a leaf node.

        A leaf node has no children (can't determine without seeing all operations,
        so this always returns True for individual parsing). More useful with
        group_by_hierarchy().

        Args:
            name: Operation name

        Returns:
            True (individual names are always leaf nodes)
        """
        return True  # A single name is always a leaf node

    @staticmethod
    def get_root(name: str) -> str:
        """Get the topmost parent of an operation.

        Args:
            name: Operation name (e.g., "scraping.stepstone.fetch")

        Returns:
            Root name (e.g., "scraping")
        """
        return HierarchyParser.parse(name).root

    @staticmethod
    def get_all_parents(name: str) -> list[str]:
        """Get all parent levels of an operation.

        Args:
            name: Operation name (e.g., "scraping.stepstone.fetch")

        Returns:
            List of all parents (e.g., ["scraping", "scraping.stepstone"])
        """
        return HierarchyParser.parse(name).all_parents

    @staticmethod
    def group_by_parent(names: list[str]) -> dict[Optional[str], list[str]]:
        """Group operation names by their parent.

        Args:
            names: List of operation names

        Returns:
            Dictionary mapping parent (or None for standalones) to operation list

        Example:
            >>> names = [
            ...     "scraping.fetch",
            ...     "scraping.merge",
            ...     "parsing.clean",
            ...     "validate"
            ... ]
            >>> result = HierarchyParser.group_by_parent(names)
            >>> result["scraping"]
            ["scraping.fetch", "scraping.merge"]
            >>> result["parsing"]
            ["parsing.clean"]
            >>> result[None]  # Standalone operations
            ["validate"]
        """
        groups: dict[Optional[str], list[str]] = {}

        for name in names:
            parsed = HierarchyParser.parse(name)
            parent = parsed.parent

            if parent not in groups:
                groups[parent] = []

            groups[parent].append(name)

        return groups

    @staticmethod
    def group_by_root(names: list[str]) -> dict[str, list[str]]:
        """Group operation names by their root (topmost parent).

        Args:
            names: List of operation names

        Returns:
            Dictionary mapping root to operation list

        Example:
            >>> names = [
            ...     "scraping.stepstone.fetch",
            ...     "scraping.linkedin.fetch",
            ...     "parsing.clean",
            ...     "validate"
            ... ]
            >>> result = HierarchyParser.group_by_root(names)
            >>> result["scraping"]
            ["scraping.stepstone.fetch", "scraping.linkedin.fetch"]
            >>> result["parsing"]
            ["parsing.clean"]
            >>> result["validate"]  # Standalone has root = itself
            ["validate"]
        """
        groups: dict[str, list[str]] = {}

        for name in names:
            root = HierarchyParser.get_root(name)

            if root not in groups:
                groups[root] = []

            groups[root].append(name)

        return groups

    @staticmethod
    def group_by_level(names: list[str]) -> dict[int, list[str]]:
        """Group operation names by their hierarchy level.

        Args:
            names: List of operation names

        Returns:
            Dictionary mapping level to operation list

        Example:
            >>> names = [
            ...     "scraping.stepstone.fetch",  # level 3
            ...     "parsing.clean",              # level 2
            ...     "validate"                    # level 1
            ... ]
            >>> result = HierarchyParser.group_by_level(names)
            >>> result[1]
            ["validate"]
            >>> result[2]
            ["parsing.clean"]
            >>> result[3]
            ["scraping.stepstone.fetch"]
        """
        groups: dict[int, list[str]] = {}

        for name in names:
            level = HierarchyParser.get_level(name)

            if level not in groups:
                groups[level] = []

            groups[level].append(name)

        return groups

    @staticmethod
    def find_siblings(name: str, all_names: list[str]) -> list[str]:
        """Find all siblings of an operation (operations with same parent).

        Args:
            name: Operation name
            all_names: All operation names to search in

        Returns:
            List of sibling names (including the operation itself)
        """
        parsed = HierarchyParser.parse(name)
        parent = parsed.parent

        return [n for n in all_names if HierarchyParser.get_parent(n) == parent]

    @staticmethod
    def find_children(parent_name: str, all_names: list[str]) -> list[str]:
        """Find all direct children of a parent operation.

        Args:
            parent_name: Parent operation name
            all_names: All operation names to search in

        Returns:
            List of direct children (one level deeper)
        """
        parent_prefix = parent_name + HierarchyParser.SEPARATOR
        parent_level = HierarchyParser.get_level(parent_name)
        children = []

        for name in all_names:
            if not name.startswith(parent_prefix):
                continue

            child_level = HierarchyParser.get_level(name)
            # Only direct children (one level deeper)
            if child_level == parent_level + 1:
                children.append(name)

        return children

    @staticmethod
    def build_hierarchy_tree(names: list[str]) -> dict:
        """Build a tree structure representing the operation hierarchy.

        Args:
            names: List of operation names

        Returns:
            Nested dictionary representing the hierarchy tree

        Example:
            >>> names = [
            ...     "scraping.stepstone.fetch",
            ...     "scraping.linkedin.fetch",
            ...     "scraping.merge",
            ...     "parsing.clean"
            ... ]
            >>> tree = HierarchyParser.build_hierarchy_tree(names)
            >>> tree
            {
                "scraping": {
                    "stepstone": {"fetch": None},
                    "linkedin": {"fetch": None},
                    "merge": None
                },
                "parsing": {
                    "clean": None
                }
            }
        """
        tree: dict = {}

        for name in names:
            parts = name.split(HierarchyParser.SEPARATOR)
            current = tree

            for part in parts:
                if part not in current:
                    current[part] = {}

                current = current[part]

        return tree

    @staticmethod
    def validate_names(names: list[str]) -> tuple[bool, str]:
        """Validate a list of operation names.

        Args:
            names: List of operation names

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            for name in names:
                HierarchyParser.parse(name)
            return True, ""
        except ValueError as e:
            return False, str(e)
