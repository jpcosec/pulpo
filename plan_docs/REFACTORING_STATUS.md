# Pulpo Core - Refactoring to Library Status

**Status:** 🔄 **IN PROGRESS** - Active Refactoring Phase

**Date Started:** October 2024
**Current Phase:** Removing Domain-Specific Code & Establishing Core Library Semantics

---

## Objective

Transform Pulpo Core from a project-specific codebase (JobHunter) into a **domain-agnostic, importable library** that:

- Can be used independently of any specific project domain
- Provides metadata-driven code generation for ANY full-stack application
- Acts as the orchestration backbone for peripheral services (API, UI, CLI, etc.)
- Uses three fundamental graphs to drive all code generation
- Can be installed via pip and used in any Python project

---

## What's Being Changed

### ✅ Completed

#### 1. **Removed Domain-Specific Language**
   - Removed all hardcoded "JobHunter" references
   - Removed all "Job", "User", "Match" domain concepts from core code
   - Removed Pokemon demo examples
   - Replaced with generic "Item", "Process" patterns

#### 2. **Made Container Names Dynamic**
   - `docker-compose.yml` now uses `${PROJECT_NAME}` environment variables
   - Container names: `${PROJECT_NAME}-api`, `${PROJECT_NAME}-mongodb`, etc.
   - Volume names: `${PROJECT_NAME}-mongo-data`
   - Database names: `${MONGODB_DATABASE}`

#### 3. **Renamed Core Exception Class**
   - `JobHunterException` → `PulpoException`
   - All subclasses updated to be domain-agnostic
   - Updated `core/utils/exceptions.py` and `__init__.py`

#### 4. **Updated Configuration Management**
   - Config files: `.jobhunter.yml` → `.pulpo.yml` (in code comments/docs)
   - `core/config_manager.py` updated to reference generic config
   - All hardcoded defaults removed

#### 5. **Cleaned All Documentation**
   - `README.md`: Examples now use generic Item/Process operations
   - `CLAUDE.md`: All examples are domain-agnostic
   - Makefile: Removed JobHunter branding
   - Code comments: Updated to reference Pulpo Core framework

### 🔄 In Progress

#### 1. **Graph-Driven Architecture Documentation**
   - Document the 3 fundamental graphs (See below)
   - Show how graphs drive API, UI, CLI, Prefect flow generation
   - Create visual representations

#### 2. **Library API Stabilization**
   - Ensure decorators work with any domain model
   - Verify registries are truly domain-agnostic
   - Test with multiple project examples

#### 3. **Installation & Distribution**
   - Verify `pip install -e .` works correctly
   - Test imports: `from core import datamodel, operation`
   - Ensure no hardcoded paths or assumptions

### 📋 Planned

#### 1. **Example Projects**
   - Create multiple starter projects (not in core)
   - Show Pulpo Core used with different domains
   - Document best practices for project structure

#### 2. **Integration Tests**
   - Test core with mock projects
   - Verify code generation works across domains
   - Test CLI generation

#### 3. **Performance & Scalability**
   - Benchmark graph analysis
   - Optimize registry operations
   - Test with large numbers of models/operations

---

## The Three Fundamental Graphs

The entire framework is built on three interconnected graphs that drive all code generation:

### 1. **Model Composition Graph** (Data Models)
**Nodes:** `@datamodel` definitions
**Edges:** Relationships (foreign keys, references, hierarchies)
**Purpose:** Drive CRUD API generation, database schema, UI data models

### 2. **Operation Hierarchy Graph** (Workflows)
**Nodes:** `@operation` definitions
**Edges:** Hierarchical dependencies (dot-separated names create parent-child relationships)
**Purpose:** Drive Prefect flow generation, CLI command organization, task orchestration

### 3. **Data Flow Graph** (Transformation Pipeline)
**Nodes:** Data models
**Edges:** Operations (directed edges from input models to output models)
**Purpose:** Drive data transformation logic, dependency analysis, impact analysis

### **Graph-Driven Code Generation**
```
Model Composition Graph  ──┐
Operation Hierarchy Graph ─┼─→ Code Generators ─→ FastAPI Routes
Data Flow Graph          ──┤                   ├→ React UI
                            └─→ Analyzers      └→ Prefect Flows
                                               ├→ CLI Commands
                                               └→ Documentation
```

**This graph-driven approach ensures:**
- All generated code is consistent and synchronized
- Changes to models/operations automatically propagate
- Circular dependencies can be detected
- Data lineage can be traced
- Optimization opportunities can be found

---

## Documentation Structure

### `docs/` - Actual Implementation State
Contains documentation of the **current, working implementation**:
- Architecture overview
- API reference
- CLI usage
- Decorator specifications
- Integration guides

### `plan_docs/` - Refactoring & Design Documentation
Contains documentation being **created during this refactoring**:
- Refactoring status (this file)
- Graph-driven architecture design
- Library API specifications
- Installation & distribution plan
- Example projects & patterns
- Migration guides for existing projects

---

## How to Help with This Refactoring

### For Developers

1. **Testing the Library**
   ```bash
   # Install locally
   pip install -e .

   # Test imports
   python -c "from core import datamodel, operation; print('OK')"

   # Run tests
   make test-unit
   ```

2. **Creating Test Projects**
   - Create simple test projects in different domains
   - Document what works and what doesn't
   - Report issues with domain-specific assumptions

3. **Code Review**
   - Look for remaining hardcoded assumptions
   - Check for hidden dependencies on specific domains
   - Verify configuration is truly dynamic

### For Documentation

1. **Graph Documentation**
   - Help visualize the 3 fundamental graphs
   - Create examples showing how graphs drive generation
   - Document graph analysis algorithms

2. **Example Projects**
   - Create starter projects in different domains
   - Document best practices
   - Show how to extend the framework

3. **API Documentation**
   - Document decorator parameters
   - Document registry APIs
   - Document code generator APIs

---

## Success Criteria

### Phase 1: Core Library (Current)
- ✅ Remove all domain-specific code
- ✅ Make container names dynamic
- 🔄 Stabilize public API
- 📋 Comprehensive documentation of graphs

### Phase 2: Installability
- 📋 `pip install pulpocore` works
- 📋 Works in multiple environments (Linux, macOS, Windows)
- 📋 No hardcoded paths or assumptions

### Phase 3: Example Projects
- 📋 Minimum 3 example projects (different domains)
- 📋 Each with complete documentation
- 📋 Each demonstrating different features

### Phase 4: Production Ready
- 📋 1.0.0 release
- 📋 Stable API guarantees
- 📋 Full test coverage
- 📋 Community examples

---

## Known Issues & Limitations (Being Addressed)

### 1. **Config File Naming**
Currently, the framework refers to `.pulpo.yml` but the actual implementation may still reference `.jobhunter.yml` in some places.
- **Status:** Being updated
- **Action:** Grep codebase for remaining references

### 2. **Python Code Comments**
Some Python files still have domain-specific comments or examples.
- **Status:** Partially complete
- **Action:** Continue updating file by file

### 3. **Documentation Graphs**
The 3 fundamental graphs are not yet visually documented.
- **Status:** Planned
- **Action:** Create Mermaid diagrams and descriptions

### 4. **Example Projects**
No example projects yet to demonstrate library usage.
- **Status:** Not started
- **Action:** Create starter projects in different domains

---

## Next Steps

### Immediate (This Week)
1. [ ] Create comprehensive graph documentation
2. [ ] Create visual diagrams of the 3 graphs
3. [ ] Update `docs/README.md` to indicate refactoring
4. [ ] Audit remaining domain-specific code

### Short Term (Next Sprint)
1. [ ] Create first example project
2. [ ] Test pip installation
3. [ ] Full grep for remaining hardcoded references
4. [ ] API stabilization pass

### Medium Term (Month)
1. [ ] Multiple example projects (3-5)
2. [ ] Performance optimization
3. [ ] Comprehensive test suite
4. [ ] Integration tests with real projects

---

## References

- **Graph-Driven Code Generation**: See `plan_docs/GRAPH_DRIVEN_ARCHITECTURE.md`
- **Decorator Specifications**: See `docs/DATAMODEL_DECORATOR.md` and `docs/OPERATION_DECORATOR.md`
- **Architecture Overview**: See `docs/ARCHITECTURE_OVERVIEW.md`

---

## Questions & Discussions

This refactoring is ongoing. If you encounter:
- Hardcoded domain assumptions → Document them here
- API unclear → Add to clarification list
- Better approaches → Create issue/discussion

**This is a collaborative process to make Pulpo Core the best metadata-driven framework possible.**
