"""DataModel and Operation linter for catching orthographic and semantic errors.

Checks for:
1. Type annotation anti-patterns (list[str] when should be list[Model])
2. Field naming vs type mismatches (plural names with non-list types, etc.)
3. Documentation/spelling errors
4. Missing references to other models
5. Unused models and orphaned operations
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..registries import ModelRegistry, OperationRegistry


@dataclass
class LintError:
    """A linting error with context and suggestions."""

    level: str  # "error", "warning", "info"
    model_or_op: str  # Name of model or operation
    field: str | None  # Field name (if applicable)
    code: str  # Error code (e.g., "TYPE_MISMATCH")
    message: str  # Human-readable message
    suggestion: str | None = None  # How to fix it
    context: str | None = None  # Code context

    def __str__(self) -> str:
        """Format as readable error message."""
        level_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[self.level]
        location = f"{self.model_or_op}"
        if self.field:
            location += f".{self.field}"

        msg = f"{level_icon} [{self.code}] {location}: {self.message}"
        if self.suggestion:
            msg += f"\n   💡 Suggestion: {self.suggestion}"
        if self.context:
            msg += f"\n   Context: {self.context}"
        return msg


class DataModelLinter:
    """Lints datamodels and operations for semantic errors."""

    # Common typos and misspellings
    COMMON_MISSPELLINGS = {
        "pokemons": "pokemon",  # Plural of pokemon is pokemon, not pokemons
        "trainers": "trainer",  # Use singular
        "battels": "battles",
        "experiance": "experience",
        "intialize": "initialize",
        "occurence": "occurrence",
        "seperator": "separator",
    }

    # Common field name patterns and their expected types
    FIELD_NAME_PATTERNS = {
        # Pattern: (regex, expected_type_pattern, error_message)
        (r"^(\w+)_ids?$", "should be reference to model"): (
            r"^list\[",
            "collection reference",
        ),
        (r"^(\w+)_list$", "should be reference to model"): (
            r"^list\[",
            "collection reference",
        ),
        (r"^(\w+)s$", "plural names should be collections"): (
            r"^list\[",
            "collection type",
        ),
    }

    def __init__(self):
        """Initialize linter."""
        self.errors: list[LintError] = []
        self.model_registry = ModelRegistry()
        self.operation_registry = OperationRegistry()

    def lint(self) -> list[LintError]:
        """Run all linting checks.

        Returns:
            List of linting errors found
        """
        self.errors = []

        # Get all registered models
        models = self.model_registry.list_all()
        model_names = {m.name for m in models}

        # Check each model
        for model in models:
            self._check_model(model, model_names)

        # Check operations
        operations = self.operation_registry.list_all()
        self._check_operations(operations, model_names)

        # Check for orphaned models/operations
        self._check_usage(models, operations)

        return self.errors

    def _check_model(self, model: Any, all_model_names: set[str]) -> None:
        """Check a single model for errors."""
        model_name = model.name
        doc_cls = getattr(model, "document_cls", None)

        if not doc_cls:
            return

        # Check model has description
        description = getattr(model, "description", "")
        if not description or len(description) < 10:
            self.errors.append(
                LintError(
                    level="warning",
                    model_or_op=model_name,
                    field=None,
                    code="DOC_MISSING",
                    message="Model lacks proper description",
                    suggestion="Add detailed description to @datamodel decorator",
                )
            )

        # Check fields
        if hasattr(doc_cls, "model_fields"):
            for field_name, field_info in doc_cls.model_fields.items():
                self._check_field(model_name, field_name, field_info, all_model_names)

    def _check_field(
        self,
        model_name: str,
        field_name: str,
        field_info: Any,
        all_model_names: set[str],
    ) -> None:
        """Check a single field for type/naming mismatches."""
        field_type_str = str(field_info.annotation)
        field_desc = getattr(field_info, "description", "")

        # Skip private fields and standard MongoDB fields
        if field_name in ("id", "revision_id") or field_name.startswith("_"):
            return

        # Check 1: Detect list[str] that should be list[Model]
        if "list[str]" in field_type_str.lower():
            # Check if field name suggests a model relationship AND a matching model exists
            if self._looks_like_relationship(field_name):
                suggested_model = self._guess_model_name(field_name, all_model_names)
                # Only error if we found a matching model - otherwise it's probably legitimate string data
                if suggested_model:
                    self.errors.append(
                        LintError(
                            level="error",
                            model_or_op=model_name,
                            field=field_name,
                            code="TYPE_MISMATCH",
                            message=f"Field '{field_name}' uses list[str] but a '{suggested_model}' model exists",
                            suggestion=f"Change to: {field_name}: list[{suggested_model}]",
                            context=f"Current: list[str] | Suggested: list[{suggested_model}]",
                        )
                    )

        # Check 2: Detect str fields that might be foreign keys
        if field_type_str == "<class 'str'>" and field_name.endswith("_id"):
            suggested_model = self._guess_model_name(field_name.replace("_id", ""), all_model_names)
            if suggested_model:
                self.errors.append(
                    LintError(
                        level="warning",
                        model_or_op=model_name,
                        field=field_name,
                        code="FK_AS_STRING",
                        message=f"Foreign key '{field_name}' stored as string",
                        suggestion=f"Consider: {field_name.replace('_id', '')}: {suggested_model}",
                        context="String FKs prevent relationship detection in diagrams",
                    )
                )

        # Check 3: Plural field names should have list types (only for strong relationship patterns)
        # Skip common stat/property fields that naturally end in 's'
        plural_exceptions = {
            "status",
            "address",
            "class",
            "stats",
            "gains",
            "losses",
            "wins",
            "turns",
            "bytes",
            "access",
            "progress",
            "success",
            "results",
            "bounds",
            "basis",
            "compass",
            "focus",
            "radius",
            "lens",
            "axis",
        }

        if (
            field_name.endswith("s")
            and "list" not in field_type_str.lower()
            and field_name not in plural_exceptions
        ):
            # Only warn if field name STRONGLY suggests a relationship
            if self._looks_like_strong_relationship(field_name):
                suggested_model = self._guess_model_name(field_name.rstrip("s"), all_model_names)
                self.errors.append(
                    LintError(
                        level="warning",
                        model_or_op=model_name,
                        field=field_name,
                        code="PLURAL_NOT_LIST",
                        message=f"Plural field '{field_name}' is not a collection",
                        suggestion=f"Change to: {field_name}: list[{suggested_model}]",
                        context=f"Current type: {field_type_str}",
                    )
                )

        # Check 4: Check description for common misspellings
        if field_desc:
            misspellings = self._find_misspellings(field_desc)
            for wrong, correct in misspellings:
                self.errors.append(
                    LintError(
                        level="info",
                        model_or_op=model_name,
                        field=field_name,
                        code="SPELLING",
                        message=f"Possible misspelling in description: '{wrong}'",
                        suggestion=f"Did you mean '{correct}'?",
                        context=f"Description: {field_desc}",
                    )
                )

        # Check 5: Missing field description
        if not field_desc or len(field_desc) < 5:
            self.errors.append(
                LintError(
                    level="warning",
                    model_or_op=model_name,
                    field=field_name,
                    code="DOC_MISSING_FIELD",
                    message="Field lacks description",
                    suggestion="Add description: Field(..., description='...')",
                )
            )

    def _check_operations(self, operations: list[Any], all_model_names: set[str]) -> None:
        """Check operations for errors."""
        for op in operations:
            op_name = op.name
            models_in = getattr(op, "models_in", [])
            models_out = getattr(op, "models_out", [])

            # Check 1: Referenced models exist
            for model_name in models_in + models_out:
                if model_name not in all_model_names:
                    self.errors.append(
                        LintError(
                            level="error",
                            model_or_op=op_name,
                            field=None,
                            code="MODEL_NOT_FOUND",
                            message=f"Operation references unknown model '{model_name}'",
                            suggestion=f"Available models: {', '.join(sorted(all_model_names))}",
                        )
                    )

            # Check 2: Operations have description
            description = getattr(op, "description", "")
            if not description or len(description) < 10:
                self.errors.append(
                    LintError(
                        level="warning",
                        model_or_op=op_name,
                        field=None,
                        code="DOC_MISSING_OP",
                        message="Operation lacks proper description",
                        suggestion="Add description to @operation decorator",
                    )
                )

    def _check_usage(self, models: list[Any], operations: list[Any]) -> None:
        """Check for orphaned models and unused operations."""
        model_names = {m.name for m in models}
        used_models = set()

        # Collect used models from operations
        for op in operations:
            used_models.update(getattr(op, "models_in", []))
            used_models.update(getattr(op, "models_out", []))

        # Check for orphaned models
        orphaned = model_names - used_models
        for model_name in orphaned:
            self.errors.append(
                LintError(
                    level="info",
                    model_or_op=model_name,
                    field=None,
                    code="ORPHANED_MODEL",
                    message="Model is not used by any operation",
                    suggestion="Either use this model in an operation or remove it",
                )
            )

    @staticmethod
    def _looks_like_relationship(field_name: str) -> bool:
        """Check if field name suggests a relationship to another model."""
        # Patterns that suggest relationships
        relationship_patterns = [
            r"^([a-z_]+)_(id|ids)$",  # trainer_id, pokemon_ids
            r"^([a-z_]+)_(list|set)$",  # pokemon_list
            r"^([a-z_]+)s$",  # trainers, pokemons
            r"^(\w+)_team$",  # pokemon_team
            r"^(\w+)_members$",  # team_members
            r"^captured_(\w+)s?$",  # captured_pokemon
            r"^has_(\w+)s?$",  # has_pokemon
            r"^belongs_to_(\w+)$",  # belongs_to_trainer
        ]

        return any(re.match(pattern, field_name) for pattern in relationship_patterns)

    @staticmethod
    def _looks_like_strong_relationship(field_name: str) -> bool:
        """Check if field name STRONGLY suggests a relationship (stricter than _looks_like_relationship)."""
        # Only these patterns are STRONG indicators of relationships
        strong_patterns = [
            r"^([a-z_]+)_(id|ids)$",  # trainer_id, pokemon_ids
            r"^([a-z_]+)_(list|set)$",  # pokemon_list
            r"^(\w+)_team$",  # pokemon_team
            r"^(\w+)_members$",  # team_members
            r"^captured_(\w+)s?$",  # captured_pokemon
            r"^has_(\w+)s?$",  # has_pokemon
            r"^belongs_to_(\w+)$",  # belongs_to_trainer
        ]

        return any(re.match(pattern, field_name) for pattern in strong_patterns)

    @staticmethod
    def _guess_model_name(field_name: str, all_models: set[str]) -> str | None:
        """Try to guess the model name from field name."""
        # Remove common suffixes
        candidates = [
            field_name.rstrip("s"),  # pokemons -> pokemon
            field_name.replace("_id", ""),  # pokemon_id -> pokemon
            field_name.replace("_ids", ""),  # pokemon_ids -> pokemon
            field_name.replace("_list", ""),  # pokemon_list -> pokemon
            field_name.replace("_team", ""),  # pokemon_team -> pokemon
            field_name.replace("captured_", ""),  # captured_pokemon -> pokemon
        ]

        # Try to find matching model (case-insensitive)
        for candidate in candidates:
            # Exact match
            if candidate in all_models:
                return candidate
            # Case-insensitive match
            for model in all_models:
                if model.lower() == candidate.lower():
                    return model

        return None

    @staticmethod
    def _find_misspellings(text: str) -> list[tuple[str, str]]:
        """Find common misspellings in text."""
        misspellings = []
        text_lower = text.lower()

        for wrong, correct in DataModelLinter.COMMON_MISSPELLINGS.items():
            if wrong in text_lower:
                misspellings.append((wrong, correct))

        return misspellings

    def report(self, format: str = "text") -> str:
        """Generate a report of linting errors.

        Args:
            format: Output format ("text", "json", "summary")

        Returns:
            Formatted report
        """
        if format == "text":
            return self._report_text()
        elif format == "summary":
            return self._report_summary()
        elif format == "json":
            return self._report_json()
        else:
            raise ValueError(f"Unknown format: {format}")

    def _report_text(self) -> str:
        """Generate text report."""
        if not self.errors:
            return "✅ No linting errors found!"

        errors_by_level = {}
        for error in self.errors:
            if error.level not in errors_by_level:
                errors_by_level[error.level] = []
            errors_by_level[error.level].append(error)

        lines = ["📋 DataModel Linting Report\n"]

        for level in ["error", "warning", "info"]:
            if level in errors_by_level:
                level_label = {
                    "error": "❌ Errors",
                    "warning": "⚠️ Warnings",
                    "info": "ℹ️ Info",
                }[level]
                lines.append(f"\n{level_label} ({len(errors_by_level[level])}):")
                lines.append("-" * 60)
                for error in errors_by_level[level]:
                    lines.append(str(error))
                    lines.append("")

        # Summary
        total = len(self.errors)
        errors = len(errors_by_level.get("error", []))
        warnings = len(errors_by_level.get("warning", []))
        info = len(errors_by_level.get("info", []))

        lines.append("=" * 60)
        lines.append(f"Total: {total} issues ({errors} errors, {warnings} warnings, {info} info)")

        return "\n".join(lines)

    def _report_summary(self) -> str:
        """Generate summary report."""
        if not self.errors:
            return "✅ All good!"

        errors = sum(1 for e in self.errors if e.level == "error")
        warnings = sum(1 for e in self.errors if e.level == "warning")
        info = sum(1 for e in self.errors if e.level == "info")

        return f"🔍 Lint: {errors} errors, {warnings} warnings, {info} info"

    def _report_json(self) -> str:
        """Generate JSON report."""
        import json

        error_dicts = [
            {
                "level": e.level,
                "code": e.code,
                "model_or_op": e.model_or_op,
                "field": e.field,
                "message": e.message,
                "suggestion": e.suggestion,
            }
            for e in self.errors
        ]

        return json.dumps(error_dicts, indent=2)


def run_linter(
    registry_models: list[Any] | None = None,
    registry_ops: list[Any] | None = None,
) -> None:
    """Run linter and print report."""
    linter = DataModelLinter()

    # Override registries if provided
    if registry_models is not None:
        linter.model_registry.models = {m.name: m for m in registry_models}
    if registry_ops is not None:
        linter.operation_registry.operations = {op.name: op for op in registry_ops}

    errors = linter.lint()
    print(linter.report(format="text"))

    # Return exit code based on error count
    error_count = sum(1 for e in errors if e.level == "error")
    return 0 if error_count == 0 else 1
