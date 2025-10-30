# Plan Docs - Pulpo Core Library Refactoring

**This folder contains design and planning documentation created during the refactoring of Pulpo Core into an importable library.**

---

## What's in Here?

This folder documents the **ongoing transformation** of Pulpo Core from a monolithic project-specific codebase (JobHunter) into a **domain-agnostic, modular, importable library**.

### Key Documents

#### 1. **REFACTORING_STATUS.md** ⭐ START HERE
Current status of the refactoring effort:
- What's been completed
- What's in progress
- What's planned
- Success criteria for each phase
- Known issues and limitations

#### 2. **GRAPH_DRIVEN_ARCHITECTURE.md** 🔑 CORE CONCEPT
Deep dive into the three fundamental graphs that power the entire framework:
- **Model Composition Graph (MCG)** - Data structure relationships
- **Operation Hierarchy Graph (OHG)** - Workflow organization
- **Data Flow Graph (DFG)** - Data transformation pipeline

This is the architectural foundation for understanding how code generation works.

#### 3. Other Documents
Additional planning documents created during refactoring phases.

---

## How This Differs from `docs/`

### `docs/` Folder
✅ **For actual, working implementation**
- Describes current state of the code
- API reference
- How to use the framework
- Decorator specifications
- Integration guides
- Assumes core is working and stable

### `plan_docs/` Folder
📋 **For design, planning, and refactoring documentation**
- Design decisions and rationale
- Refactoring progress and status
- Architecture of the library itself
- What we're building toward
- How to help with refactoring
- Known issues being addressed

---

## Refactoring Phases

### Phase 1: Remove Domain-Specific Code ✅ ACTIVE
Current phase. Making the codebase generic.

**Status**: ~80% complete
- Removed JobHunter branding
- Made container names dynamic
- Renamed core exception classes
- Updated all examples to generic patterns
- Documented the 3 fundamental graphs

**What's Left**:
- Audit remaining hardcoded references
- Complete documentation updates
- Stabilize library API

### Phase 2: Library Installability 📋 PLANNED
Make it installable via pip and usable independently.

**Goals**:
- `pip install pulpocore` works
- No hardcoded paths or assumptions
- Cross-platform compatibility (Linux, macOS, Windows)

### Phase 3: Example Projects 📋 PLANNED
Demonstrate library usage in different domains.

**Goals**:
- 3-5 example projects
- Different domains (not job hunting)
- Complete documentation for each
- Best practices guide

### Phase 4: Production Ready 📋 FUTURE
Full 1.0.0 release.

**Goals**:
- Stable API with guarantees
- Full test coverage
- Community contributions
- Production deployments

---

## Key Architectural Insights

### The 3 Graphs (CRITICAL)

The entire framework is built on 3 graphs that drive ALL code generation:

```
┌──────────────────────┐
│ Model Composition    │──┐
│ Graph (MCG)          │  │
│                      │  │
│ Nodes: @datamodels   │  │
│ Edges: Relationships │  │
└──────────────────────┘  │
                          │
┌──────────────────────┐  │
│ Operation Hierarchy  │──┼─→ CODE GENERATORS ──→ API/CLI/UI/Prefect
│ Graph (OHG)          │  │
│                      │  │
│ Nodes: @operations   │  │
│ Edges: Hierarchy     │  │
└──────────────────────┘  │
                          │
┌──────────────────────┐  │
│ Data Flow Graph      │──┘
│ (DFG)                │
│                      │
│ Nodes: Data models   │
│ Edges: Operations    │
└──────────────────────┘
```

**These graphs are the key to understanding:**
- How API endpoints are generated
- How CLI commands are organized
- How Prefect flows are created
- How UI is structured
- Why changes propagate automatically

See `GRAPH_DRIVEN_ARCHITECTURE.md` for complete details.

---

## Refactoring Progress Checklist

### Phase 1 Progress: Remove Domain-Specific Code
- [x] Remove "JobHunter" references from comments
- [x] Remove "Job/User/Match" concepts from examples
- [x] Make container names dynamic (${PROJECT_NAME})
- [x] Rename JobHunterException → PulpoException
- [x] Update config file references
- [x] Update README with generic examples
- [x] Update CLAUDE.md with generic examples
- [ ] Audit all remaining hardcoded references
- [ ] Update all Python file docstrings
- [ ] Complete graph documentation

### Phase 2 Progress: Installability
- [ ] Test `pip install -e .` works
- [ ] Remove all hardcoded paths
- [ ] Test cross-platform compatibility
- [ ] Document installation process

### Phase 3 Progress: Example Projects
- [ ] Create first example project (auth/permissions)
- [ ] Create second example project (ecommerce)
- [ ] Create third example project (content management)
- [ ] Document best practices from examples

### Phase 4 Progress: Production Ready
- [ ] 1.0.0 API defined and stable
- [ ] Full test coverage (unit + integration)
- [ ] Performance benchmarks established
- [ ] Production deployment guide

---

## How to Help

### For Developers
1. Read `REFACTORING_STATUS.md`
2. Review changes in this branch
3. Help audit remaining hardcoded references
4. Test core library with mock projects
5. Report issues or missing pieces

### For Documentation
1. Understand the 3 graphs in `GRAPH_DRIVEN_ARCHITECTURE.md`
2. Create visual diagrams (Mermaid/ASCII art)
3. Document example projects
4. Help with API documentation

### For Testing
1. Create test projects in different domains
2. Test `pip install` and basic usage
3. Verify code generation works
4. Document any breaking issues

---

## Important Notes

### This Codebase is Currently Being Refactored
- Some documentation may be out of date
- Some code may have hardcoded assumptions (being fixed)
- API may change during this phase (documented in REFACTORING_STATUS.md)
- See `REFACTORING_STATUS.md` for known issues

### We're Building Toward
A domain-agnostic library that can be installed via pip and used to build full-stack applications in ANY domain with metadata-driven code generation.

### The Vision
```python
# User should be able to do:
pip install pulpocore

# Then in their project:
from pulpo import datamodel, operation

@datamodel(name="MyEntity")
class MyEntity(Document):
    name: str

@operation(name="process_entity", ...)
async def process_entity(...): ...

# Generate and deploy
from pulpo.codegen import generate_all
generate_all()

# Everything else is auto-generated (API, CLI, UI, Prefect flows)
```

---

## Questions & Discussion

This refactoring is collaborative. If you have:
- **Questions** about the architecture → See `GRAPH_DRIVEN_ARCHITECTURE.md`
- **Progress updates** → Update `REFACTORING_STATUS.md`
- **Issues found** → Add to `REFACTORING_STATUS.md` Known Issues section
- **Suggestions** → Create discussion or PR

---

## References

**In This Folder**:
- `REFACTORING_STATUS.md` - Current status & next steps
- `GRAPH_DRIVEN_ARCHITECTURE.md` - Core architectural concept

**In `docs/` Folder**:
- `ARCHITECTURE_OVERVIEW.md` - Current implementation architecture
- `HOW_CORE_WORKS.md` - How the framework currently works
- `DATAMODEL_DECORATOR.md` - @datamodel decorator reference
- `OPERATION_DECORATOR.md` - @operation decorator reference

**In Code**:
- `core/registries.py` - Graph storage (MCG, OHG)
- `core/codegen.py` - Code generators (graph consumers)
- `core/decorators.py` - Decorator implementations

---

**Last Updated**: October 2024
**Status**: 🔄 **IN PROGRESS** - Refactoring Phase 1
