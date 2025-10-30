# Pulpo Core Refactoring Checklist

**Status**: 🔄 Phase 1 - ~85% Complete

---

## Phase 1: Remove Domain-Specific Code ✅ ACTIVE

### Code Cleanup
- [x] Remove "JobHunter" from Makefile
- [x] Remove "JobHunter" from docker-compose.yml comments
- [x] Rename `JobHunterException` → `PulpoException`
- [x] Update `core/config_manager.py` docstrings
- [x] Update `core/utils/exceptions.py` docstrings
- [x] Update `core/utils/__init__.py` exports
- [ ] Audit and fix remaining Python file docstrings
- [ ] Full codebase grep for hardcoded references

### Documentation Updates
- [x] README.md - Replace Job/User/Match examples with generic Item/Process
- [x] CLAUDE.md - Update all code examples to be domain-agnostic
- [x] Makefile - Remove JobHunter branding and examples
- [x] docs/README.md - Add refactoring status notice
- [x] Create `plan_docs/REFACTORING_STATUS.md`
- [x] Create `plan_docs/GRAPH_DRIVEN_ARCHITECTURE.md`
- [x] Create `plan_docs/README.md`

### Configuration
- [x] Make docker-compose container names dynamic (${PROJECT_NAME})
- [x] Make volume names dynamic
- [x] Make database names dynamic (${MONGODB_DATABASE})
- [x] Update config_manager.py to reference .pulpo.yml
- [ ] Test configuration with actual project setup

### Examples & Code
- [x] README.md examples use generic Item model
- [x] README.md examples use generic process_item operation
- [x] CLAUDE.md examples use pipeline naming instead of scraping
- [x] Operation examples use generic names
- [ ] Create first test project to validate everything works

---

## Phase 2: Library Installability 📋 PLANNED

### Installation Testing
- [ ] `pip install -e .` works in clean environment
- [ ] `pip install .` works in clean environment
- [ ] All imports work: `from core import datamodel, operation`
- [ ] No hardcoded paths break installation

### Cross-Platform Testing
- [ ] Linux (verified)
- [ ] macOS (needs testing)
- [ ] Windows (needs testing)

### Configuration Validation
- [ ] PROJECT_NAME environment variable is used correctly
- [ ] MONGODB_DATABASE environment variable is used correctly
- [ ] docker-compose works with environment variables
- [ ] No hardcoded "jobhunter" strings remain

---

## Phase 3: Example Projects 📋 PLANNED

### First Example: Basic Todo App
- [ ] Create separate project repo (not in core)
- [ ] Document project structure
- [ ] Show how to define models
- [ ] Show how to define operations
- [ ] Document generated API usage
- [ ] Document CLI usage

### Second Example: E-commerce System
- [ ] Create separate project repo
- [ ] More complex data model relationships
- [ ] Complex operation hierarchies
- [ ] Document best practices

### Third Example: Content Management
- [ ] Create separate project repo
- [ ] Demonstrate relationship complexity
- [ ] Show advanced operation hierarchies
- [ ] Performance considerations

### Documentation from Examples
- [ ] Best practices guide
- [ ] Project structure recommendations
- [ ] Deployment guide

---

## Phase 4: Production Ready 📋 FUTURE

### API Stability
- [ ] Define public API (decorators, registries, generators)
- [ ] Write API contracts
- [ ] Backward compatibility guarantees

### Testing
- [ ] Unit test coverage > 80%
- [ ] Integration tests for all generators
- [ ] E2E tests with example projects
- [ ] Performance benchmarks established

### Documentation
- [ ] Complete API reference
- [ ] Deployment guides
- [ ] Troubleshooting guide
- [ ] Migration guides for existing projects

### Release
- [ ] Version 1.0.0 on PyPI
- [ ] Release notes
- [ ] Community communication

---

## Known Issues Being Addressed

### In Codebase
- [ ] Possible remaining hardcoded "jobhunter" strings in other files
- [ ] Some Python docstrings may still reference old domain
- [ ] Config file naming may not be fully consistent

### In Documentation
- [ ] Some old docs may reference JobHunter
- [ ] Graph diagrams need visual representations
- [ ] Example projects not yet created

### In Testing
- [ ] No E2E tests with pip installation
- [ ] No cross-platform tests
- [ ] No performance benchmarks

---

## How to Help

### Developers
- [ ] Review code for remaining hardcoded assumptions
- [ ] Test `pip install -e .` in clean environment
- [ ] Create test projects with different domains
- [ ] Run full test suite: `make test-all`

### Documentation
- [ ] Create visual diagrams for the 3 graphs
- [ ] Review GRAPH_DRIVEN_ARCHITECTURE.md for clarity
- [ ] Document example projects
- [ ] Create migration guides

### Testers
- [ ] Test on macOS and Windows
- [ ] Test with Docker
- [ ] Test configuration options
- [ ] Report any issues

---

## References

**Current Status**:
- [`plan_docs/REFACTORING_STATUS.md`](plan_docs/REFACTORING_STATUS.md) - Detailed status
- [`plan_docs/GRAPH_DRIVEN_ARCHITECTURE.md`](plan_docs/GRAPH_DRIVEN_ARCHITECTURE.md) - Architecture

**Implementation Guidance**:
- [`CLAUDE.md`](CLAUDE.md) - Development guide
- [`docs/ARCHITECTURE_OVERVIEW.md`](docs/ARCHITECTURE_OVERVIEW.md) - Current implementation

---

**Last Updated**: October 2024
**Status**: 🔄 Refactoring Phase 1
