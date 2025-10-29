# PulpoCore - New Instructions Summary

**Date:** 2025-10-29
**Status:** Planning Phase
**Goal:** Transform framework into reusable PulpoCore library with agnostic architecture

---

## 📋 New Instructions Overview

### 1. **Repository Structure Change**

**OLD:**
```
postulator3000/
├── jobhunter-core-minimal/     ← Part of monorepo
├── Jobhunter/
└── jobhunter-scraping-applying/
```

**NEW:**
```
Separate Repositories:

/pulpo/                          ← NEW GitHub repo
├── pulpo/                       ← Package folder
│   ├── core/
│   │   ├── decorators.py
│   │   ├── registries.py
│   │   ├── codegen.py
│   │   ├── cli/
│   │   └── ...
│   └── __init__.py
├── pyproject.toml
└── examples/                    ← Example from tar

/postulator3000/
├── Jobhunter/                   ← Uses "from pulpo import ..."
├── jobhunter-scraping-applying/ ← Only this folder remains (deduplicated)
└── (core-minimal removed/archived)
```

### 2. **Import Pattern Change**

**OLD (Relative Imports):**
```python
from core.decorators import datamodel, operation
from core.registries import ModelRegistry
from core.cli import CLI
```

**NEW (Package Imports):**
```python
from pulpo import datamodel, operation, ModelRegistry
from pulpo.core import cli
from pulpo.core.cli import CLI
```

### 3. **Framework Architecture Principle**

**Core Concept:** Framework is **AGNOSTIC** to the outer layer

**Only Two Requirements:**
1. **Main Entrypoint** - Project must have a single entry point that:
   - Imports PulpoCore: `from pulpo import ...`
   - Instantiates a CLI object
   - Passes the imports to CLI for mapping

2. **Decorators** - Models and operations must use:
   - `@datamodel` - For data models
   - `@operation` - For business logic

**Example Structure:**
```python
# main.py or main entrypoint
from pulpo import datamodel, operation, CLI

# Your decorators are here (can be in same file or imported)
@datamodel(name="Job")
class Job: ...

@operation(name="search")
async def search(): ...

# Instantiate CLI
cli = CLI(
    models=[Job],  # Discovered models
    operations=[search]  # Discovered operations
)

# CLI is the interface
if __name__ == "__main__":
    cli.run()
```

### 4. **Generated Artifacts Folder**

**CHANGE:** Remove hidden property from `.run_cache` → `run_cache`

**OLD:**
```
.run_cache/                      ← Hidden folder (starts with dot)
├── generated_api.py
├── cli/
└── ...
```

**NEW:**
```
run_cache/                       ← Visible folder (no dot)
├── generated_api.py
├── cli/
└── ...
```

**Why:** Makes it obvious this is generated code, easier to see in directory listings, clearer for CI/CD

### 5. **PulpoCore Features**

The framework provides:

✅ **Decorators System:**
- `@datamodel` - Registers data models
- `@operation` - Registers operations

✅ **CLI Interface:**
- Auto-discovers models and operations
- Provides `make` commands (init, compile, build)
- Maps data/operations graph

✅ **Code Generation:**
- FastAPI endpoints
- CLI commands
- React UI config
- Docker setup

✅ **Registries:**
- ModelRegistry - All @datamodel classes
- OperationRegistry - All @operation functions

---

## 🎯 Three-Part Plan

### **PART 1: Test PulpoCore Framework**
- Create testing/modification plan
- Use example from tar file
- Verify framework works agnostically
- Test CLI interface
- Validate code generation (run_cache folder)

### **PART 2: Backup Current State**
- Full backup of postulator3000
- Preserve git history
- Save migration baseline
- Create rollback point

### **PART 3: Restructure Repository**
- Move jobhunter-core-minimal → /pulpo (separate repo)
- Remove duplicate folders (only jobhunter-scraping-applying remains)
- Update imports in Jobhunter
- Prepare for pulpo as external dependency
- Update documentation

---

## 📊 Detailed Requirements

### Requirement 1: Framework Agnosticism

```
Current: Framework assumes specific project structure (models/, operations/, etc.)
New: Framework doesn't care about project structure

How it works:
1. Project has decorators anywhere (models/job.py, src/ops/search.py, etc.)
2. Main entrypoint discovers and imports them
3. Passes to CLI for mapping
4. CLI doesn't care where they came from
```

### Requirement 2: Main Entrypoint Pattern

```python
# Every project using PulpoCore needs:

from pulpo import datamodel, operation, CLI

# 1. Define models (can be in any file)
@datamodel(...)
class MyModel: ...

# 2. Define operations (can be in any file)
@operation(...)
async def my_operation(): ...

# 3. Create CLI at entrypoint
cli = CLI()

# 4. Discover from decorators
cli.discover_from_decorators()

# 5. Entrypoint runs CLI
if __name__ == "__main__":
    cli.run()
```

### Requirement 3: Make Commands

```bash
make init      # Initialize project structure
make compile   # Generate code (creates run_cache/)
make build     # Build Docker images
```

**Changes:**
- Generated folder is `run_cache/` (not `.run_cache/`)
- Folder is visible in directory listings
- Same contents as before

### Requirement 4: CLI as Main Interface

```python
# CLI object provides:
cli.discover()              # Find models/operations
cli.compile()               # Generate code
cli.run()                   # Start application
cli.show_graph()            # Display dependency graph

# Users interact through CLI, not directly with framework
```

---

## ✅ Success Criteria for Testing

### Part 1: Framework Testing
- [ ] Example from tar unpacks successfully
- [ ] `from pulpo import ...` works correctly
- [ ] CLI object instantiates
- [ ] Decorators are discovered
- [ ] `make compile` generates run_cache/ (not .run_cache/)
- [ ] Generated code works
- [ ] Framework works with any project structure

### Part 2: Backup Phase
- [ ] Full backup created with timestamp
- [ ] Git bundle saved
- [ ] Baseline documented
- [ ] Rollback verified

### Part 3: Restructuring
- [ ] jobhunter-core-minimal moved to /pulpo
- [ ] Duplicate folders removed
- [ ] Imports updated in Jobhunter
- [ ] jobhunter-scraping-applying remains (deduplicated)
- [ ] All tests pass

---

## 📁 File Organization After Restructuring

```
BEFORE:
/home/jp/postulator3000/
├── jobhunter-core-minimal/        ← To be moved
├── jobhunter-core-minimal/ (in Jobhunter worktree)  ← Duplicate
├── Jobhunter/
├── jobhunter-scraping-applying/   ← Keep (one copy)
└── jobhunter-scraping-applying/ (in worktree)  ← Duplicate - remove

AFTER:
/pulpo/                            ← Separate GitHub repo
├── pulpo/
│   └── core/
├── examples/
└── pyproject.toml

/home/jp/postulator3000/
├── Jobhunter/                     ← Uses: from pulpo import ...
├── jobhunter-scraping-applying/   ← Single copy (no duplicate)
└── (core-minimal archived or deleted)
```

---

## 🚀 Execution Order

1. **SUMMARY & REVIEW** (This document)
   - Understand new architecture
   - Confirm requirements

2. **CREATE TESTING PLAN** (Next document)
   - Detailed testing phases
   - Example setup instructions
   - Verification tests

3. **CREATE RESTRUCTURING PLAN** (Third document)
   - Backup procedures
   - Deduplication steps
   - Import updates
   - Verification

4. **EXECUTE IN ORDER:**
   - Part 1: Test framework (in another instance)
   - Part 2: Backup current state
   - Part 3: Restructure repository

---

## 🎓 New Architecture Model

### Old Model (Current)
```
postulator3000/ (monorepo)
├── Core Framework (jobhunter-core-minimal)
├── Production App (Jobhunter)
├── Scraping Module (jobhunter-scraping-applying)
└── Test Setup (jobhunter-test)

Problem: Everything in one repo, duplication, coupling
```

### New Model (Target)
```
/pulpo/                            Framework library
├── Agnostic to outer layer
├── Only cares about decorators + main entrypoint
└── Used by any project

/postulator3000/
├── Jobhunter/                    Application using pulpo
├── jobhunter-scraping-applying/  Specialized module
└── (Clean, no framework code)

Problem Solved:
✅ Framework reusable
✅ No duplication
✅ Clear boundaries
✅ Easier testing
```

---

## 📝 Key Terminology

| Term | Meaning |
|------|---------|
| **PulpoCore** | The reusable framework library (in /pulpo repo) |
| **Agnostic** | Framework doesn't care about project structure, only decorators |
| **Main Entrypoint** | Single entry point that instantiates CLI and runs app |
| **Decorators** | @datamodel and @operation that register with framework |
| **CLI** | Command-line interface that framework provides |
| **run_cache** | Generated artifacts folder (visible, not hidden) |
| **Deduplication** | Removing duplicate folders (core-minimal in two places) |

---

## 🔄 Next Steps

1. **Read This Document** - Understand new architecture
2. **Review Testing Plan** - How to test framework changes
3. **Review Restructuring Plan** - How to backup and reorganize
4. **Execute Testing** - Test in separate instance first
5. **Execute Restructuring** - Only after testing succeeds
6. **Migrate Jobhunter** - Update to use pulpo from PyPI
7. **Archive Old Code** - Keep backups, clean up workspace

---

**Status:** ✅ Instructions Summarized | 📋 Ready for Planning Phase

**Next Document:** Create detailed testing plan with example setup and verification steps.
