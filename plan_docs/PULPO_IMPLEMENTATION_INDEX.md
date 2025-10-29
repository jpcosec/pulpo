# PulpoCore Implementation Index

**Overview:** Complete documentation for transforming framework into reusable PulpoCore library with Extended Proposal C orchestration

**Status:** Planning phase complete with Extended Proposal C, ready for execution
**Total Pages:** 3 comprehensive documents + Extended Proposal C features
**Total Content:** ~120 KB
**Architecture:** Hierarchical naming → auto-generated DAG → Prefect orchestration

---

## 🎯 Extended Proposal C Summary

**What is Extended Proposal C?**

A brilliant architectural innovation that eliminates the need for users to write orchestration code. Instead:

1. **Hierarchical Naming Convention** - Operations named like "scraping.stepstone.fetch" create automatic DAG structure
2. **Auto-Generated Prefect Flows** - Framework generates valid Prefect @flow and @task decorators from naming
3. **Automatic Parallelization** - Same-level operations (e.g., multiple "scraping.*.fetch") run in parallel with asyncio.gather()
4. **Sync/Async Transparency** - Sync functions automatically wrapped with run_in_executor()
5. **Multi-Level Hierarchy** - Creates nested flows for complex workflows (e.g., "scraping.stepstone.parse")
6. **Sub-Flow Reuse** - Operations can invoke entire flows as internal steps via invoke_flow()

**Zero-Boilerplate Orchestration:**
```python
# User writes decorators
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(): ...

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(): ...

@operation(name="scraping.merge")
async def merge(stepstone, linkedin): ...

# Framework auto-generates Prefect flows with:
# - Parallel execution of fetch operations
# - Automatic dependency injection
# - Valid @flow/@task decorators in run_cache/orchestration/
```

---

## 📋 Document Overview

### 1. **PULPO_INSTRUCTIONS_SUMMARY.md** (5 KB)
**Start here to understand the vision**

**Contains:**
- New architecture overview
- Import pattern changes (from relative to `from pulpo import ...`)
- Framework agnosticism principle
- Generated artifacts folder change (.run_cache → run_cache)
- Three-part plan overview
- Success criteria

**Best For:**
- Understanding new direction
- Quick reference of requirements
- Executive briefing

**Read Time:** 10 minutes

---

### 2. **PULPO_TESTING_PLAN.md** (35 KB)
**Complete testing guide for framework modifications**

**Contains:**
- 5 independent testing phases
- 12 detailed testing steps
- Each step has:
  - Clear objective
  - Detailed test commands (copy-paste ready)
  - Acceptance criteria (testable)
  - Expected output

**Phases:**
1. **Framework Structure Validation** - Package structure, imports
2. **CLI Interface Validation** - CLI methods, registries, commands
3. **Run Cache Generation** - folder creation, artifacts, idempotency
4. **Framework Agnosticism** - different project structures
5. **Example Validation** - tar example testing

**Best For:**
- Testing framework changes
- Separate test instance execution
- Validating requirements
- Copy-paste command reference

**Read Time:** 20 minutes | **Execution Time:** 2-3 hours

---

### 3. **PULPO_RESTRUCTURING_PLAN.md** (40 KB)
**Complete restructuring guide for production repository**

**Contains:**
- 5 implementation phases
- 13 detailed restructuring steps
- Each step has:
  - Clear objective
  - Bash commands (copy-paste ready)
  - Acceptance criteria
  - Verification procedures
  - Rollback instructions

**Phases:**
1. **Comprehensive Backup** - Full backups, recovery scripts
2. **Deduplication** - Identify and remove duplicates
3. **Core to PulpoCore** - Reorganize framework
4. **Jobhunter Migration** - Update to use PulpoCore
5. **Verification & Cleanup** - Test and commit

**Best For:**
- Production restructuring
- Risk mitigation (full backups)
- Step-by-step execution
- Rollback capability

**Read Time:** 25 minutes | **Execution Time:** 3-4 hours

---

## 🎯 Execution Roadmap

### Week 1: Planning & Testing

**Day 1-2: Review Plans**
```
1. Read: PULPO_INSTRUCTIONS_SUMMARY.md (10 min)
2. Review: PULPO_TESTING_PLAN.md (20 min)
3. Review: PULPO_RESTRUCTURING_PLAN.md (25 min)
Total: ~1 hour
```

**Day 3-4: Test in Isolated Instance**
```
1. Set up test environment
2. Execute PULPO_TESTING_PLAN.md
3. Verify all 5 phases pass
4. Document any issues
Total: ~4 hours
```

### Week 2: Production Restructuring

**Day 1: Pre-restructuring**
```
1. Review PULPO_RESTRUCTURING_PLAN.md
2. Verify backups exist
3. Create full backup (Phase 1)
Total: ~1 hour
```

**Day 2-3: Execute Restructuring**
```
1. Deduplication (Phase 2)
2. Core → PulpoCore (Phase 3)
3. Migrate Jobhunter (Phase 4)
4. Verification (Phase 5)
Total: ~4 hours
```

**Day 4: Verification**
```
1. Run full test suite
2. Verify all imports work
3. Test make commands
4. Document any changes
Total: ~2 hours
```

---

## 🗂️ Document Reading Paths

### Path 1: "I Just Want to Understand" (45 minutes)

1. **PULPO_INSTRUCTIONS_SUMMARY.md** - New architecture (10 min)
2. **PULPO_TESTING_PLAN.md** - Intro + Phase 1 (15 min)
3. **PULPO_RESTRUCTURING_PLAN.md** - Overview + Phase 1 (20 min)

**Result:** High-level understanding of direction

---

### Path 2: "I'm Testing in Separate Instance" (3+ hours)

1. **PULPO_INSTRUCTIONS_SUMMARY.md** - Requirements (10 min)
2. **PULPO_TESTING_PLAN.md** - Complete document (20 min)
3. Set up test environment (30 min)
4. Execute all 5 testing phases (2-3 hours)
5. Document results

**Result:** Framework validated, requirements confirmed

---

### Path 3: "I'm Restructuring Production" (7+ hours)

1. All three documents (1 hour total)
2. **PULPO_RESTRUCTURING_PLAN.md** - Complete implementation (6+ hours)
   - Phase 1: Backup (30 min)
   - Phase 2: Deduplication (30 min)
   - Phase 3: Core migration (1 hour)
   - Phase 4: Jobhunter migration (1 hour)
   - Phase 5: Verification (1 hour)

**Result:** Production repository restructured, tested, committed

---

## ✅ Success Criteria by Document

### PULPO_INSTRUCTIONS_SUMMARY.md
- ✅ Understand new architecture
- ✅ Know import pattern change (from pulpo import ...)
- ✅ Understand framework agnosticism
- ✅ Know folder structure changes (run_cache/ not .run_cache/)
- ✅ Understand Extended Proposal C concepts

### PULPO_TESTING_PLAN.md (Extended with Proposal C)
- ✅ Phase 1: Framework structure valid + Hierarchy parser works
- ✅ Phase 2: CLI interface works + Orchestration compilation works
- ✅ Phase 3: run_cache/ folder + orchestration/ folder with Prefect flows
- ✅ Phase 4: Framework agnostic + Sync/async handling + Hierarchy examples
- ✅ Phase 5: Example validates + Demonstrates Extended Proposal C features

### PULPO_RESTRUCTURING_PLAN.md (Extended with Proposal C)
- ✅ Phase 1: Full backup created
- ✅ Phase 2: No duplicates remain
- ✅ Phase 3: PulpoCore ready with orchestration modules + Extended Proposal C
- ✅ Phase 4: Jobhunter migrated to use pulpocore
- ✅ Phase 5: Verified and committed with new architecture

---

## 🔑 Key Requirements Summary

### Framework Agnosticism
```
✓ Doesn't care about project structure
✓ Only requires decorators + main entrypoint
✓ Works with any folder organization
✓ CLI acts as universal interface
✓ Works with hierarchical or flat operation names
```

### Import Pattern
```
OLD: from core.decorators import datamodel
NEW: from pulpo import datamodel, operation, CLI
     from pulpo.core.hierarchy import HierarchyParser
     from pulpo.core.orchestration import OrchestrationCompiler
```

### Generated Artifacts
```
OLD: .run_cache/ (hidden folder)
NEW: run_cache/ (visible folder)
     run_cache/orchestration/ (Prefect flows - Extended Proposal C)
```

### Extended Proposal C Requirements
```
✓ Hierarchical naming creates DAG structure automatically
✓ HierarchyParser converts "flow.step.substep" → nested flows
✓ OrchestrationCompiler generates Prefect @flow/@task code
✓ SyncAsyncDetector wraps sync with run_in_executor
✓ Automatic parallelization for same-level operations
✓ Multi-level hierarchy support (3+ levels)
✓ Sub-flow reuse via invoke_flow()
✓ Dependencies inferred from operation input/output types
```

### Three Phases
```
Phase 1: Test in isolated instance (with Extended Proposal C validation)
Phase 2: Backup production
Phase 3: Restructure live repository (with orchestration modules)
```

---

## 📊 Progress Tracking

Use this checklist to track progress:

### Planning Phase
- [ ] Read PULPO_INSTRUCTIONS_SUMMARY.md
- [ ] Read PULPO_TESTING_PLAN.md
- [ ] Read PULPO_RESTRUCTURING_PLAN.md
- [ ] Understand all requirements
- [ ] Identify test instance
- [ ] Confirm backup location

### Testing Phase
- [ ] Set up test environment
- [ ] Execute Phase 1: Structure validation
- [ ] Execute Phase 2: CLI interface
- [ ] Execute Phase 3: Run cache generation
- [ ] Execute Phase 4: Agnosticism
- [ ] Execute Phase 5: Examples
- [ ] All tests pass ✅

### Production Phase
- [ ] Create full backup
- [ ] Execute Phase 1: Deduplication
- [ ] Execute Phase 2: Core migration
- [ ] Execute Phase 3: Jobhunter migration
- [ ] Execute Phase 4: Verification
- [ ] All tests pass ✅
- [ ] Commit changes
- [ ] Archive old code

---

## 🎓 Key Concepts

| Concept | Meaning |
|---------|---------|
| **Agnostic** | Framework doesn't care about project structure |
| **Decorators** | @datamodel and @operation register with framework |
| **CLI** | Command-line interface that provides all functionality |
| **PulpoCore** | Reusable framework library with Extended Proposal C orchestration |
| **Main Entrypoint** | Single entry point that instantiates CLI |
| **run_cache** | Generated artifacts folder (visible, not hidden) |
| **Deduplication** | Removing duplicate folder instances |
| **Hierarchical Naming** | "flow.step.substep" naming creates automatic DAG structure |
| **HierarchyParser** | Parses operation names into hierarchy components |
| **OrchestrationCompiler** | Generates Prefect flows from operation hierarchy |
| **SyncAsyncDetector** | Detects and wraps sync functions with run_in_executor |
| **Parallelization** | Same-level operations automatically run concurrently |
| **Prefect Integration** | Auto-generated @flow and @task decorators in orchestration/ |
| **Sub-Flow Reuse** | Operations can invoke entire flows as internal steps |

---

## 📁 Related Documentation

**Already Created:**
- CLAUDE.md - Global project guide
- MIGRATION_PLAN.md - Monorepo to separate repos migration
- GIT_ANALYSIS_REPORT.md - Git structure analysis

**Part of This Set:**
- PULPO_INSTRUCTIONS_SUMMARY.md
- PULPO_TESTING_PLAN.md
- PULPO_RESTRUCTURING_PLAN.md

---

## 🚀 Quick Links to Key Sections

### Testing Quick Start
See: **PULPO_TESTING_PLAN.md**
- Step 1.1: Framework structure validation
- Step 3.1: Run cache folder creation
- All copy-paste commands provided

### Restructuring Quick Start
See: **PULPO_RESTRUCTURING_PLAN.md**
- Step 1.1: Create full backup
- Step 2.1: Identify duplicates
- Step 3.1: Reorganize core framework
- All bash commands provided

### Import Pattern
See: **PULPO_INSTRUCTIONS_SUMMARY.md**
- "Import Pattern Change" section
- Shows before/after examples

---

## 🆘 Support & Troubleshooting

### Testing Issues
→ See PULPO_TESTING_PLAN.md section "Acceptance Criteria" for each step

### Restructuring Issues
→ See PULPO_RESTRUCTURING_PLAN.md section "Rollback Procedure"

### Import Problems
→ See PULPO_INSTRUCTIONS_SUMMARY.md section "Import Pattern Change"

### Understanding Architecture
→ Read PULPO_INSTRUCTIONS_SUMMARY.md completely

---

## ✨ Expected Outcomes

After all documentation is followed with Extended Proposal C:

### Immediate
- ✅ Framework tested and validated
- ✅ All Extended Proposal C features confirmed (hierarchy, parallelization, sync/async)
- ✅ Orchestration modules working correctly
- ✅ Production ready

### Short-term (Week 1)
- ✅ Repository restructured with orchestration modules
- ✅ No duplicates remaining
- ✅ Imports updated (from pulpo import ...)
- ✅ Extended Proposal C modules integrated
- ✅ Changes committed with new architecture

### Medium-term (Week 2-4)
- ✅ Publish pulpocore to PyPI (with Prefect integration)
- ✅ Separate GitHub repo created (/pulpo)
- ✅ Update external projects to use pulpocore with hierarchical naming
- ✅ Old repository archived
- ✅ Documentation updated with Extended Proposal C examples

### Long-term
- ✅ Reusable framework for future projects (with zero-boilerplate orchestration)
- ✅ Clean separation of concerns
- ✅ Easier to maintain and test (orchestration auto-generated)
- ✅ Industry-standard architecture
- ✅ Users write only decorators, framework handles orchestration
- ✅ Auto-parallelization for improved performance

---

## 📝 Document Status

| Document | Status | Completeness | Extended Proposal C |
|----------|--------|--------------|-----|
| PULPO_INSTRUCTIONS_SUMMARY.md | ✅ Complete | 100% | Base concepts |
| PULPO_TESTING_PLAN.md | ✅ Updated | 100% | Full coverage (5 phases, 16 steps) |
| PULPO_RESTRUCTURING_PLAN.md | ✅ Updated | 100% | Orchestration modules included |

**Overall Status:** Ready for Execution with Extended Proposal C ✅

**Extended Proposal C Coverage:**
- ✅ Hierarchical naming convention documented
- ✅ Auto-generated orchestration explained
- ✅ Prefect integration included
- ✅ Sync/async handling covered
- ✅ Parallelization detection detailed
- ✅ Multi-level hierarchy supported
- ✅ Testing plan includes validation steps
- ✅ Restructuring plan includes orchestration modules

---

## 🎯 Next Actions

**Immediate (Today):**
1. Read PULPO_INSTRUCTIONS_SUMMARY.md
2. Review Extended Proposal C summary (at top of this document)
3. Decide on test instance timeline

**Short-term (This Week):**
1. Review all three documents (now with Extended Proposal C)
2. Execute PULPO_TESTING_PLAN.md with all Extended Proposal C validations
3. Document testing results

**Medium-term (Next Week):**
1. Execute PULPO_RESTRUCTURING_PLAN.md with orchestration modules
2. Verify all Extended Proposal C features working
3. Commit to git with new architecture

**Long-term (After Restructuring):**
1. Publish pulpocore to PyPI with Prefect integration
2. Create separate /pulpo GitHub repository
3. Document Extended Proposal C for users
4. Update external projects to use pulpocore

---

**Generated:** 2025-10-29
**Last Updated:** 2025-10-29 with Extended Proposal C
**Author:** Claude Code
**Status:** Complete and Ready for Extended Proposal C Execution ✅

All documentation is cross-referenced and self-contained. You can start with any document based on your immediate needs. Extended Proposal C provides zero-boilerplate orchestration with hierarchical naming and auto-generated Prefect flows.
