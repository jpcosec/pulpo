# Pulpo Core: Architecture Decisions & Rationale

**Date:** 2025-10-29
**Version:** 0.6.0 (First iteration)
**Status:** Documented - Ready for implementation alignment

---

## Overview

This document explains the key architectural decisions made for Pulpo Core and the rationale behind them.

---

## Decision 1: No TaskRun Observability - Use Prefect Instead

### Decision
**Remove TaskRun model entirely. Use Prefect for all observability, tracking, and orchestration.**

### Rationale
1. **Prefect is industry standard** - Provides production-grade task/flow tracking
2. **Eliminates duplication** - TaskRun was duplicating Prefect functionality
3. **Simpler code** - No custom observability infrastructure needed
4. **Better user experience** - Prefect UI is superior to custom dashboards
5. **Zero-boilerplate** - Users don't write TaskRun code; Prefect handles it automatically

### Impact
- **Removed:** `create_taskrun` parameter from `@operation` decorator
- **Removed:** TaskRun model references and imports
- **Removed:** TODO comments about TaskRun implementation
- **Updated:** Docstrings to reference Prefect instead
- **Architecture:** Prefect is now the single source of truth for execution tracking

### Benefits
- Operations don't need manual observability code
- Full execution lineage in Prefect UI
- Built-in logging, error handling, retries
- Hierarchical naming enables automatic parallelization
- Zero additional setup for observability

---

## Decision 2: Dynamic CLI with Smart run_cache Creation

### Decision
**CLI discovers decorators dynamically on each instantiation. run_cache created on-demand only when needed.**

### Rationale
1. **Flexibility** - Framework works with or without full stack
2. **User-friendly** - No manual "compile first" step
3. **Smart defaults** - Auto-compile when needed, don't force it
4. **Inspection-first** - Can inspect decorators without compilation
5. **Separation of concerns** - Compilation is optional, discovery is always available

### Implementation Pattern
```python
cli = CLI()  # Fresh discovery on each instantiation

# These work immediately (no run_cache needed):
cli.list_models()
cli.list_operations()
cli.draw_graphs()
cli.docs()

# These auto-create run_cache if missing:
cli.api()
cli.prefect()
cli.compile()  # Idempotent
```

### run_cache Behavior
- **Created on-demand** - When first operation requiring it is called
- **Idempotent** - Safe to call compile() multiple times
- **Visible** - Folder is `run_cache/` not `.run_cache/` (visible in listings)
- **Contents** - All generated artifacts: API, UI config, Prefect flows, graphs, docs

### Benefits
- Users can inspect models/operations immediately
- No "build before use" friction
- Framework works for lightweight projects (just decorators + introspection)
- Works for heavy projects (full API + Prefect + Docker)
- Flexible integration - use as much or as little as needed

---

## Decision 3: Hierarchical Naming for Automatic Orchestration

### Decision
**Operation names use dot-notation (e.g., "scraping.stepstone.fetch") to automatically generate Prefect flows.**

### Rationale
1. **Zero boilerplate** - No users write orchestration code
2. **Self-documenting** - Naming convention makes structure obvious
3. **Auto-parallelization** - Same-level operations run in parallel automatically
4. **Type-safe dependencies** - Inferred from operation input/output types
5. **Nestable flows** - Multi-level hierarchies create nested Prefect flows

### Naming Convention
```
flow.step.substep.operation

Examples:
- scraping.stepstone.fetch      (level 3)
- scraping.linkedin.fetch       (level 3, parallel to stepstone.fetch)
- scraping.merge                (level 2, depends on fetches)
- parsing.clean_text            (level 2, independent flow)
- validate                       (level 1, root operation)
```

### Generated Prefect Structures
```
@flow
def scraping_flow():
    # Parallelizes level-2 operations
    stepstone, linkedin = await asyncio.gather(
        fetch_stepstone(),
        fetch_linkedin(),
    )
    # Depends on fetch results
    return await merge(stepstone, linkedin)
```

### Benefits
- Users just name operations hierarchically
- Framework generates valid Prefect code
- Parallelization happens automatically
- Dependency injection from operation signatures
- Flow visualization in Prefect UI

---

## Decision 4: Framework Agnosticism

### Decision
**Framework makes no assumptions about project structure. Only requires decorators + main entrypoint.**

### Rationale
1. **Universal applicability** - Works with any project layout
2. **Simple onboarding** - No rigid directory structure required
3. **Flexibility** - Teams use their own conventions
4. **Testability** - Easy to test in various environments
5. **Reusability** - Framework works for any domain

### Valid Project Structures
```
# Flat
app.py                    # All decorators in one file

# Organized
src/models/...
src/operations/...
src/main.py

# Nested non-standard
internal/domain/models/
internal/domain/ops/
main.py

# Deep hierarchical
app/
  ├── models/
  │   ├── users.py
  │   ├── jobs.py
  ├── operations/
  │   ├── scraping/
  │   ├── parsing/
  └── main.py
```

All work exactly the same - framework finds decorators regardless of structure.

### Benefits
- No boilerplate structure required
- Teams use familiar conventions
- Easier migration from other frameworks
- Simpler to understand and debug
- Works with existing projects

---

## Decision 5: Version Strategy - First Iteration

### Decision
**Current version 0.6.0 represents first iteration toward pip-installable library. Not "full" 1.0.**

### Rationale
1. **Core features work** - Decorators, registries, API generation stable
2. **Still refactoring** - Import patterns, documentation, structure being finalized
3. **Prefect integration new** - Hierarchical orchestration being implemented
4. **Path to 1.0 clear** - Feature-complete after testing and restructuring
5. **Honest about maturity** - 0.x signifies not production-guaranteed yet

### Versioning Path
```
0.6.0 (current)  - Core framework + early Prefect integration
0.7.0 (after testing) - Framework validated, Prefect flows working
0.8.0 (after restructuring) - Separate repo, pip-installable
1.0.0 (future) - Production-grade, stable API, PyPI published
```

### Benefits
- Honest about current state
- Clear roadmap to 1.0
- Users know framework is evolving
- Doesn't claim stability it doesn't have yet

---

## Decision 6: Remove core/examples Directory

### Decision
**No example code in core/. Use demo-project.tar.gz for testing reference.**

### Rationale
1. **Framework is reusable** - Examples belong in users' projects, not core
2. **Reduce maintenance** - Don't maintain example code alongside framework
3. **Testing leverage** - tar.gz already contains working example
4. **Clear boundaries** - Core contains only framework, not sample apps
5. **Users write examples** - Framework enables them, doesn't prescribe them

### Where Examples Go
- **Development testing:** Use demo-project.tar.gz (extract, test, remove)
- **Documentation:** Code snippets in docs/
- **User projects:** Users create their own examples
- **Integration tests:** Framework tests use generated code

### Benefits
- Core stays focused and minimal
- Easy to maintain and test
- Users see real project patterns, not toy examples
- Framework doesn't bloat with example code

---

## Decision 7: Documentation Structure

### Decision
**Organize docs hierarchically: concepts, integration guides, reference.**

### Rationale
1. **Clear navigation** - Users find what they need quickly
2. **Multiple audiences** - Beginners, integrators, reference users
3. **Cross-referencing** - Related docs link to each other
4. **API documentation** - Separate reference from tutorials

### Documentation Organization
```
docs/
├── README.md                    # Docs overview
├── ARCHITECTURE_OVERVIEW.md     # System design
├── CLI_ARCHITECTURE.md          # NEW: CLI behavior
├── HOW_CORE_WORKS.md           # Implementation details
├── ORCHESTRATION.md             # Prefect + hierarchy
├── DATAMODEL_DECORATOR.md       # @datamodel reference
├── OPERATION_DECORATOR.md       # @operation reference
├── externals/
│   ├── FRONTEND_INTEGRATION.md
│   ├── CLI_INTEGRATION.md
│   └── PREFECT_INTEGRATION.md
└── development/                 # Internal dev docs
    ├── TESTING_PATTERNS.md
    ├── CODE_GENERATION.md
    └── LINTER_GUIDE.md
```

### Key Documents Added
- **CLI_ARCHITECTURE.md** - Complete CLI behavior and methods
- Explains dynamic discovery and smart run_cache
- Lists all CLI methods with requirements

### Benefits
- Documentation matches actual implementation
- Clear separation of concerns
- Easy to update individual sections
- Good for new contributors

---

## Decision 8: Git Repository Strategy

### Decision
**Initialize git locally first. Test and develop locally before pushing to GitHub.**

### Rationale
1. **Safe experimentation** - Local changes don't affect public
2. **Testing first** - Validate before public visibility
3. **Clean history** - One initial commit with clean state
4. **Future flexibility** - Can change repo strategy if needed

### Git Plan
```
Phase 1 (now):     Local git init + development
Phase 2 (testing): Run test suite in isolated instance
Phase 3 (ready):   Restructure locally with tests passing
Phase 4 (publish): Push to github.com when ready
Phase 5 (pip):     Publish to PyPI
```

### Benefits
- Low risk of breaking public repo
- Can iterate freely locally
- Clean final history
- Ready for collaboration when ready

---

## Decision 9: Prefect as Core Orchestration

### Decision
**Prefect is the orchestration layer. Not optional, integrated at framework level.**

### Rationale
1. **Industry standard** - Prefect 3.0 is mature and capable
2. **Saves work** - Don't reinvent workflow orchestration
3. **Better UX** - Prefect UI is excellent for debugging
4. **Automatic** - Framework generates Prefect code from hierarchy
5. **Scales well** - Works from local dev to cloud deployments

### Integration Level
- **Decorator level** - `@operation` aware of orchestration requirements
- **Compiler level** - Code generation creates valid Prefect @flow/@task
- **CLI level** - `cli.prefect()` starts Prefect with auto-generated flows
- **Optional consumption** - Users can ignore if not using orchestration

### Benefits
- Framework handles orchestration complexity
- Users just write business logic
- Automatic parallelization
- Execution history and debugging built-in
- Works with Prefect Cloud for production

---

## Decision 10: No Dual Import Patterns

### Decision
**Single import pattern: `from pulpo import ...` not relative imports.**

### Rationale
1. **Simplicity** - One way to do it
2. **Clarity** - Clear that items come from framework
3. **Consistency** - Same pattern everywhere
4. **Flexibility** - Framework can be installed anywhere (local, PyPI, git)
5. **Future-proof** - Prepared for pip install

### Import Pattern
```python
# Standard
from pulpo import CLI, datamodel, operation
from pulpo.core import registries
from pulpo.core.hierarchy import HierarchyParser
from pulpo.core.orchestration import OrchestrationCompiler

# NOT (relative imports deprecated)
# from core.decorators import datamodel  # Don't do this
# from core import CLI                   # Don't do this
```

### Benefits
- Consistent across codebases
- Works whether installed or local
- Prepares for PyPI publication
- Clear dependencies
- Easier to mock/test

---

## Summary of Key Decisions

| Decision | What | Why |
|----------|------|-----|
| 1 | No TaskRun - use Prefect | Industry standard, simpler code |
| 2 | Dynamic CLI + smart run_cache | Flexible, user-friendly |
| 3 | Hierarchical naming for orchestration | Zero-boilerplate orchestration |
| 4 | Framework agnostic to structure | Works with any project layout |
| 5 | Version 0.6.0 (first iteration) | Honest about maturity |
| 6 | No core/examples | Keep core focused |
| 7 | Documentation hierarchy | Clear navigation |
| 8 | Local git first | Safe experimentation |
| 9 | Prefect core orchestration | Industry standard, built-in |
| 10 | Single import pattern | Simplicity and clarity |

---

## Next Steps

1. **Align Implementation** - Update CLI class to match described behavior
2. **Test Integration** - Run test suite with all decisions implemented
3. **Restructure** - Move to separate /pulpo directory with orchestration modules
4. **Validate** - Ensure all decisions hold up in practice
5. **Document** - Keep this file and docs in sync

---

## Related Documents

- **README.md** - Public overview (updated with new decisions)
- **docs/CLI_ARCHITECTURE.md** - Detailed CLI behavior
- **docs/ORCHESTRATION.md** - Hierarchical orchestration details
- **CHANGELOG.md** - What changed and why (in plan_docs)

---

**Status:** Documented and ready for implementation
**Last Updated:** 2025-10-29
**Author:** Claude Code with user feedback
