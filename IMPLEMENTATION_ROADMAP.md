# Pulpo Core: Implementation Roadmap

**Current Status:** Architecture documented, git initialized, ready for implementation alignment
**Date:** 2025-10-29
**Branch:** lib_refactorization

---

## What Was Just Done ✅

### 1. Architecture & Vision Established
- **ARCHITECTURE_DECISIONS.md** - 10 key decisions with rationale
- **docs/CLI_ARCHITECTURE.md** - Complete CLI behavior specification
- **README.md** - Updated with accurate framework description
- **decorators.py** - Removed TaskRun references

### 2. Git Repository Initialized
- `git init` on branch `lib_refactorization`
- `.gitignore` created (Python/Docker/IDE standards)
- Initial commit with clean state

### 3. Documentation Updated
- Removed all TaskRun promises
- Added Prefect as core orchestration
- Clarified dynamic CLI behavior
- Documented smart run_cache creation
- Added CLI method specifications

---

## What Still Needs Implementation 🔨

### Phase 1: Align CLI Implementation

**Goal:** Make CLI class match documented behavior

**Tasks:**
1. **Review `core/cli/main.py`** - Current implementation
   - Check if `CLI()` discovers decorators automatically
   - Verify methods match spec: `list_models()`, `list_operations()`, `inspect_operation()`, etc.
   - Check run_cache creation logic

2. **Implement missing methods** (if needed):
   - `list_models()` - Return list of model names
   - `list_operations()` - Return list of operation names
   - `inspect_model(name)` - Return model metadata
   - `inspect_operation(name)` - Return operation metadata
   - `draw_graphs()` / `draw_dataflow()` - Generate diagrams
   - `draw_operationflow()` / `draw_flowgraph()` - Operation flow graphs
   - `docs()` - Generate documentation
   - `check_version()` - Check version compatibility
   - `get_model_registry()` / `get_operation_registry()` - Return registries

3. **Implement run_cache logic:**
   - Auto-create `run_cache/` when needed
   - Make operations that need it call `compile()` first
   - Ensure idempotency

4. **Update method signatures** to match CLI_ARCHITECTURE.md spec

5. **Add error handling** for missing operations, invalid states, etc.

### Phase 2: Implement Extended Proposal C (Prefect Integration)

**Goal:** Auto-generate Prefect flows from hierarchical operation names

**Tasks:**
1. **Create hierarchy parser** - Parse "flow.step.substep" naming
   - `core/hierarchy.py` with `HierarchyParser` class
   - Parse names into components
   - Group by level for parallelization detection

2. **Create orchestration compiler** - Generate Prefect code
   - `core/orchestration/compiler.py` with `OrchestrationCompiler`
   - Parse operation registry
   - Generate `@flow` and `@task` decorators
   - Create dependency graph from input/output types
   - Implement parallelization for same-level operations

3. **Sync/async handling** - Wrap sync functions
   - `core/orchestration/sync_async.py` with `SyncAsyncDetector`
   - Detect async functions
   - Wrap sync functions with `run_in_executor`
   - Create awaitable versions

4. **Code generation templates** - Generate Prefect files
   - Create Jinja2 templates for @flow code
   - Generate to `run_cache/orchestration/`
   - Ensure valid, executable Python

5. **Update `cli.compile()`** to generate Prefect flows
   - Call orchestration compiler
   - Create orchestration/ folder
   - Generate flow files

6. **Update `cli.prefect()`** to use generated flows
   - Import generated flows
   - Start Prefect server
   - Register generated flows

### Phase 3: Testing & Validation

**Goal:** Ensure framework works as documented

**Tests needed:**
1. **CLI methods work** - All documented methods callable
2. **Discovery works** - Decorators found automatically
3. **run_cache creation** - Auto-created, contains correct files
4. **Hierarchy parsing** - Names parsed correctly
5. **Orchestration generation** - Valid Prefect code created
6. **Sync/async wrapping** - Sync functions wrapped correctly
7. **Parallelization detection** - Same-level operations recognized
8. **Framework agnosticism** - Works with various project structures

**Test plan location:** `plan_docs/PULPO_TESTING_PLAN.md` (already detailed)

### Phase 4: Restructuring

**Goal:** Move to separate /pulpo directory, prepare for PyPI

**Tasks:**
1. Create `/pulpo` subdirectory structure
2. Move framework code to `/pulpo/pulpo/`
3. Remove duplicate instances
4. Update imports to `from pulpo import ...`
5. Update pyproject.toml for pip installation
6. Commit restructuring

**Restructuring plan location:** `plan_docs/PULPO_RESTRUCTURING_PLAN.md` (already detailed)

---

## Quick Reference: Key Files

| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE_DECISIONS.md` | 10 key decisions + rationale | ✅ Done |
| `docs/CLI_ARCHITECTURE.md` | CLI behavior specification | ✅ Done |
| `README.md` | Public overview | ✅ Updated |
| `core/decorators.py` | @datamodel, @operation | ✅ Cleaned (TaskRun removed) |
| `core/cli/main.py` | CLI class | 🔨 Needs alignment |
| `core/hierarchy.py` | Hierarchical naming parser | 🔨 Needs implementation |
| `core/orchestration/` | Prefect code generation | 🔨 Needs implementation |
| `.gitignore` | Git ignore rules | ✅ Done |
| `plan_docs/` | Planning documents | ✅ Existing |

---

## Decision Summary for Implementation

### Core Principles
1. **CLI discovers at instantiation** - Fresh discovery every time `CLI()` created
2. **Inspection without compilation** - Can list/inspect models without run_cache
3. **Smart run_cache** - Create only when needed, idempotent
4. **Prefect orchestration** - Auto-generated from hierarchy
5. **Framework agnostic** - Works with any project structure

### Import Pattern
```python
from pulpo import CLI, datamodel, operation
from pulpo.core.hierarchy import HierarchyParser
from pulpo.core.orchestration import OrchestrationCompiler
```

### CLI Usage Pattern
```python
cli = CLI()  # Fresh discovery

# Inspection (no compilation)
cli.list_operations()
cli.draw_graphs()

# Full stack (auto-compiles if needed)
cli.api()     # or
cli.prefect() # or
cli.compile() # explicit
```

### Hierarchical Naming
```python
@operation(name="scraping.stepstone.fetch")  # level 3
@operation(name="scraping.linkedin.fetch")   # level 3, parallel
@operation(name="scraping.merge")            # level 2, depends on fetches
```

---

## Next Steps for User

1. **Review architecture** - Read `ARCHITECTURE_DECISIONS.md`
2. **Understand CLI** - Read `docs/CLI_ARCHITECTURE.md`
3. **Decide implementation order** - Phase 1 → 2 → 3 → 4
4. **Align CLI first** - Get current CLI matching documented behavior
5. **Add Prefect integration** - Implement hierarchy parser and orchestration compiler
6. **Test thoroughly** - Run PULPO_TESTING_PLAN.md test suite
7. **Restructure** - Move to /pulpo, update imports, commit

---

## Questions to Answer Before Phase 1

1. **Current CLI methods** - What methods exist in core/cli/main.py already?
2. **Current registries** - Do they have get_all() methods?
3. **Existing run_cache** - How is it currently created/managed?
4. **Prefect dependency** - Is prefect already in pyproject.toml?
5. **Code generation** - What code generators exist in core/codegen.py?

---

## Success Criteria

✅ Phase 1 Complete:
- [ ] CLI methods match CLI_ARCHITECTURE.md specification
- [ ] Discovery works automatically on CLI() instantiation
- [ ] run_cache created on-demand, not at startup
- [ ] All inspection methods work without compilation
- [ ] All full-stack methods auto-compile if needed

✅ Phase 2 Complete:
- [ ] HierarchyParser parses operation names correctly
- [ ] OrchestrationCompiler generates valid Prefect code
- [ ] SyncAsyncDetector wraps sync functions
- [ ] Generated Prefect flows in run_cache/orchestration/
- [ ] `cli.prefect()` starts with auto-generated flows

✅ Phase 3 Complete:
- [ ] All test phases in PULPO_TESTING_PLAN.md pass
- [ ] Framework works with various project structures
- [ ] Generated code is valid and executable

✅ Phase 4 Complete:
- [ ] Separate /pulpo directory created
- [ ] All imports updated to `from pulpo import ...`
- [ ] pyproject.toml configured for pip install
- [ ] Changes committed to git

---

## Current Git Status

```
Branch: lib_refactorization
Status: Clean (100 files committed)
Last commit: Architecture documentation
```

To continue:
```bash
cd /home/jp/pulpo
git status  # Should show clean
git log     # Should show documentation commit
```

---

## Resources

**Plan documents** (in `plan_docs/`):
- `PULPO_TESTING_PLAN.md` - Comprehensive test suite
- `PULPO_RESTRUCTURING_PLAN.md` - Step-by-step restructuring guide
- `PULPO_IMPLEMENTATION_INDEX.md` - Index of all planning documents

**Architecture docs** (in `docs/`):
- `CLI_ARCHITECTURE.md` - Complete CLI specification
- `ARCHITECTURE_OVERVIEW.md` - System design
- `ORCHESTRATION.md` - Prefect integration details

**Decision documents**:
- `ARCHITECTURE_DECISIONS.md` - Rationale for each decision
- `README.md` - Public overview

---

**Status:** Ready for implementation alignment
**Estimated effort:** 15-20 hours (including testing)
**Next milestone:** CLI implementation aligned with docs

---

Generated: 2025-10-29
Last updated: 2025-10-29
Author: Claude Code + User feedback
