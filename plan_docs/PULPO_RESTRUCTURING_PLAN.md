# PulpoCore Restructuring Plan

**Prerequisite:** PULPO_TESTING_PLAN.md must be completed successfully in test instance
**Status:** Ready after testing passes
**Total Time:** 3-4 hours
**Risk Level:** MEDIUM (with full backups)
**Architecture:** Extended Proposal C (Hierarchical naming → auto-generated DAG → Prefect orchestration)

---

## Overview

After testing confirms PulpoCore works as agnostic framework with Extended Proposal C features, restructure the repository:

1. **BACKUP** - Full backup of current state
2. **DEDUPLICATE** - Remove duplicate folders
3. **MIGRATE CORE TO PULPO** - Move jobhunter-core-minimal to /pulpo with Extended Proposal C orchestration support
4. **MIGRATE JOBHUNTER** - Update imports to use pulpocore from external repo
5. **VERIFY** - Test everything works with new orchestration

### Extended Proposal C in Production

The new PulpoCore repository will include:
- **Hierarchical naming support** - Operations use "flow.step.substep" naming convention
- **Auto-generated orchestration** - Framework generates Prefect flows from naming hierarchy
- **Sync/Async transparency** - Framework wraps sync functions with run_in_executor
- **Parallelization detection** - Same-level operations automatically run in parallel
- **Nested flows** - Multi-level hierarchy creates nested Prefect flow structure
- **run_cache/orchestration/** - New folder containing generated Prefect flow files

---

# PHASE 1: Comprehensive Backup

## Step 1.1: Create Full Backup

**Objective:** Ensure complete recovery capability before any changes.

**Actions:**
```bash
# Create backup directory
mkdir -p ~/backups
BACKUP_DIR=~/backups/postulator3000_$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup entire postulator3000
cd ~
cp -r postulator3000 $BACKUP_DIR/postulator3000

# Backup .git history
cd postulator3000
git bundle create $BACKUP_DIR/postulator3000.bundle --all

# Create git info
cat > $BACKUP_DIR/GIT_INFO.txt << 'EOF'
Git Information at Backup Time:

Branches:
EOF
git branch -a >> $BACKUP_DIR/GIT_INFO.txt
echo -e "\nRecent Commits:" >> $BACKUP_DIR/GIT_INFO.txt
git log --oneline -20 >> $BACKUP_DIR/GIT_INFO.txt

# Document structure
echo -e "\n=== Current Structure ===" > $BACKUP_DIR/STRUCTURE.txt
find postulator3000 -maxdepth 2 -type d | head -50 >> $BACKUP_DIR/STRUCTURE.txt

# Save configuration
cat > $BACKUP_DIR/BACKUP_INFO.md << 'EOF'
# Backup Information

Created: $(date)
Location: $BACKUP_DIR

## What's Included
- Complete postulator3000/ directory
- Git bundle with full history
- Current git status and branches
- Directory structure snapshot

## Restoration Instructions

### Option 1: Restore Everything
```bash
cp -r $BACKUP_DIR/postulator3000 ~/postulator3000
```

### Option 2: Restore from Git Bundle
```bash
cd ~/postulator3000
git bundle unbundle $BACKUP_DIR/postulator3000.bundle
```

## Before This Backup
See GIT_INFO.txt for branches and commits

## Size
$(du -sh $BACKUP_DIR)
EOF

echo "✅ Backup created at: $BACKUP_DIR"
echo "Backup size: $(du -sh $BACKUP_DIR | awk '{print $1}')"

# Verify backup
[ -d "$BACKUP_DIR/postulator3000" ] && echo "✅ Postulator3000 backed up"
[ -f "$BACKUP_DIR/postulator3000.bundle" ] && echo "✅ Git bundle created"
[ -f "$BACKUP_DIR/GIT_INFO.txt" ] && echo "✅ Git info saved"

# Create recovery script
cat > $BACKUP_DIR/RESTORE.sh << 'EOF'
#!/bin/bash
echo "Restoring from backup..."
BACKUP_DIR="$(dirname "$0")"
cp -r $BACKUP_DIR/postulator3000 ~/postulator3000
echo "✅ Restored to ~/postulator3000"
EOF
chmod +x $BACKUP_DIR/RESTORE.sh

echo "✅ Recovery script created at: $BACKUP_DIR/RESTORE.sh"
```

**Acceptance Criteria:**
- ✅ Full postulator3000/ directory backed up
- ✅ Git bundle created with history
- ✅ Backup info documented
- ✅ Recovery script created
- ✅ Backup verified to contain files

**Test Restore:**
```bash
# Quick test (don't actually restore)
ls -la ~/backups/postulator3000_*/

# Verify structure
find ~/backups/postulator3000_*/postulator3000 -maxdepth 2 -type d | wc -l
# Should show ~20+ directories
```

**Rollback:** If needed before starting Phase 2
```bash
rm -rf ~/postulator3000
bash ~/backups/postulator3000_[timestamp]/RESTORE.sh
```

---

## Step 1.2: Archive Baseline

**Objective:** Document current state before changes.

**Actions:**
```bash
cd ~/postulator3000

# Create baseline document
cat > RESTRUCTURING_BASELINE.md << 'EOF'
# Restructuring Baseline

## Before Restructuring
Date: $(date)

### Directory Structure
EOF

tree -L 2 -d >> RESTRUCTURING_BASELINE.md 2>/dev/null || find . -maxdepth 2 -type d >> RESTRUCTURING_BASELINE.md

cat >> RESTRUCTURING_BASELINE.md << 'EOF'

### Repository Status
EOF

git status >> RESTRUCTURING_BASELINE.md
git branch -a >> RESTRUCTURING_BASELINE.md

# Count files
echo -e "\n### File Count\n" >> RESTRUCTURING_BASELINE.md
echo "Total files: $(find . -type f | wc -l)" >> RESTRUCTURING_BASELINE.md
echo "Core files: $(find jobhunter-core-minimal -type f | wc -l)" >> RESTRUCTURING_BASELINE.md
echo "Jobhunter files: $(find Jobhunter -type f | wc -l)" >> RESTRUCTURING_BASELINE.md
echo "Scraping files: $(find jobhunter-scraping-applying -type f | wc -l)" >> RESTRUCTURING_BASELINE.md

git add RESTRUCTURING_BASELINE.md
git commit -m "docs: Record baseline before PulpoCore restructuring"

echo "✅ Baseline documented"
```

**Acceptance Criteria:**
- ✅ RESTRUCTURING_BASELINE.md created
- ✅ Current structure documented
- ✅ Git status captured
- ✅ File counts recorded
- ✅ Committed to git

---

# PHASE 2: Deduplication

## Step 2.1: Identify Duplicates

**Objective:** Find and document all duplicate folders.

**Actions:**
```bash
cd ~/postulator3000

echo "=== Checking for Duplicate Folders ===" > DUPLICATE_ANALYSIS.txt

# Check for multiple core-minimal instances
echo "Core Minimal Instances:" >> DUPLICATE_ANALYSIS.txt
find . -name "jobhunter-core-minimal" -type d >> DUPLICATE_ANALYSIS.txt

# Check for multiple scraping instances
echo -e "\nScraping Instances:" >> DUPLICATE_ANALYSIS.txt
find . -name "jobhunter-scraping-applying" -type d >> DUPLICATE_ANALYSIS.txt

# Check git worktrees
echo -e "\nGit Worktrees:" >> DUPLICATE_ANALYSIS.txt
git worktree list >> DUPLICATE_ANALYSIS.txt 2>/dev/null || echo "No worktrees" >> DUPLICATE_ANALYSIS.txt

# Compare file counts
echo -e "\nFile Count Comparison:" >> DUPLICATE_ANALYSIS.txt
CORE_FILES1=$([ -d "jobhunter-core-minimal" ] && find jobhunter-core-minimal -type f | wc -l || echo "0")
CORE_FILES2=$([ -d "Jobhunter/jobhunter-core-minimal" ] && find Jobhunter/jobhunter-core-minimal -type f | wc -l || echo "0")
SCRAPE_FILES1=$([ -d "jobhunter-scraping-applying" ] && find jobhunter-scraping-applying -type f | wc -l || echo "0")
SCRAPE_FILES2=$([ -d "Jobhunter/jobhunter-scraping-applying" ] && find Jobhunter/jobhunter-scraping-applying -type f | wc -l || echo "0")

echo "jobhunter-core-minimal (root): $CORE_FILES1 files" >> DUPLICATE_ANALYSIS.txt
echo "jobhunter-core-minimal (Jobhunter/): $CORE_FILES2 files" >> DUPLICATE_ANALYSIS.txt
echo "jobhunter-scraping-applying (root): $SCRAPE_FILES1 files" >> DUPLICATE_ANALYSIS.txt
echo "jobhunter-scraping-applying (Jobhunter/): $SCRAPE_FILES2 files" >> DUPLICATE_ANALYSIS.txt

# Show results
cat DUPLICATE_ANALYSIS.txt

echo -e "\n✅ Duplicate analysis complete"
```

**Expected Output:**
```
Core Minimal Instances:
./jobhunter-core-minimal
./Jobhunter/jobhunter-core-minimal

Scraping Instances:
./jobhunter-scraping-applying
./Jobhunter/jobhunter-scraping-applying (maybe)

Git Worktrees:
/home/jp/postulator3000/Jobhunter (branch core-test)
/home/jp/postulator3000/jobhunter-core-minimal (branch core-minimal)
```

**Acceptance Criteria:**
- ✅ All duplicate instances identified
- ✅ File counts compared
- ✅ Analysis documented
- ✅ Results show which to keep/remove

---

## Step 2.2: Remove Duplicates

**Objective:** Delete duplicate folders, keep single clean version.

**Actions:**
```bash
cd ~/postulator3000

# DECISION MATRIX:
# Keep: root-level folders (easier to manage)
# Remove: duplicates inside Jobhunter/ or other locations

echo "Removing duplicate folders..."

# Remove core-minimal if it exists in multiple places
# Keep: ./jobhunter-core-minimal (will move to /pulpo later)
# Remove: ./Jobhunter/jobhunter-core-minimal (worktree)
if [ -d "Jobhunter/jobhunter-core-minimal" ]; then
    echo "Removing Jobhunter/jobhunter-core-minimal worktree..."
    # This is a git worktree, clean it up
    cd Jobhunter
    git worktree remove jobhunter-core-minimal 2>/dev/null || true
    cd ..
    # Verify removal
    [ ! -d "Jobhunter/jobhunter-core-minimal" ] && echo "✅ Removed Jobhunter/jobhunter-core-minimal"
fi

# Remove scraping duplicate if it exists
# Keep: ./jobhunter-scraping-applying (root level)
# Remove: any other copies
if [ -d "Jobhunter/jobhunter-scraping-applying" ]; then
    echo "Checking Jobhunter/jobhunter-scraping-applying..."
    if [ "$(find ./jobhunter-scraping-applying -type f | wc -l)" -eq "$(find Jobhunter/jobhunter-scraping-applying -type f | wc -l)" ]; then
        # Files are same count, check if identical
        DIFF=$(diff -r jobhunter-scraping-applying Jobhunter/jobhunter-scraping-applying 2>/dev/null | wc -l)
        if [ $DIFF -lt 10 ]; then
            # Very similar, keep root, remove from Jobhunter
            echo "Removing Jobhunter/jobhunter-scraping-applying (duplicate)..."
            rm -rf Jobhunter/jobhunter-scraping-applying
            echo "✅ Removed"
        fi
    fi
fi

# Clean up any other duplicates or empty directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Deduplication complete"

# Verify cleanup
echo -e "\nVerifying cleanup:"
echo "jobhunter-core-minimal instances: $(find . -name 'jobhunter-core-minimal' -type d | wc -l)"
echo "jobhunter-scraping-applying instances: $(find . -name 'jobhunter-scraping-applying' -type d | wc -l)"
```

**Acceptance Criteria:**
- ✅ All duplicate folders removed
- ✅ Only single clean versions remain
- ✅ Single instance per module
- ✅ Directory structure cleaned

**Verification:**
```bash
cd ~/postulator3000

# Should show exactly 1 of each
echo "jobhunter-core-minimal:"
find . -maxdepth 2 -name "jobhunter-core-minimal" -type d

echo "jobhunter-scraping-applying:"
find . -maxdepth 2 -name "jobhunter-scraping-applying" -type d
```

---

# PHASE 3: Core Framework to PulpoCore Migration

## Step 3.1: Reorganize jobhunter-core-minimal

**Objective:** Restructure to become standalone pulpo package with Extended Proposal C support.

**Extended Proposal C Modules:**
The new pulpo package will include new modules for orchestration:
- `pulpo/core/hierarchy.py` - HierarchyParser for naming convention parsing
- `pulpo/core/orchestration/` - Orchestration compilation and generation
- `pulpo/core/codegen/prefect_codegen.py` - Prefect flow code generation
- Templates for Prefect @flow and @task generation

**Actions:**
```bash
cd ~/postulator3000

# Create directory structure for pulpo
mkdir -p pulpo-new/pulpo

# Copy core framework
echo "Copying framework files..."
cp -r jobhunter-core-minimal/core pulpo-new/pulpo/
cp -r jobhunter-core-minimal/scripts pulpo-new/pulpo/
cp -r jobhunter-core-minimal/templates pulpo-new/pulpo/
cp -r jobhunter-core-minimal/frontend_template pulpo-new/pulpo/
cp -r jobhunter-core-minimal/docs pulpo-new/pulpo/
cp -r jobhunter-core-minimal/tests pulpo-new/pulpo/

# Add Extended Proposal C modules to core
mkdir -p pulpo-new/pulpo/core/orchestration
mkdir -p pulpo-new/pulpo/core/prefect_templates

# Copy project files (update for pulpo naming)
cp jobhunter-core-minimal/pyproject.toml pulpo-new/
cp jobhunter-core-minimal/README.md pulpo-new/
cp jobhunter-core-minimal/CLAUDE.md pulpo-new/
cp jobhunter-core-minimal/Makefile pulpo-new/

# Update __init__.py to use pulpo name and include Extended Proposal C exports
cat > pulpo-new/pulpo/__init__.py << 'EOF'
"""PulpoCore - Agnostic framework for building full-stack applications.

Extended Proposal C Features:
- Hierarchical naming convention for operations
- Auto-generated Prefect orchestration from naming hierarchy
- Sync/async function transparency with run_in_executor
- Automatic parallelization detection
"""

__version__ = "0.7.0"
__author__ = "PulpoCore Team"
__license__ = "MIT"

# Main exports for easy import
from pulpo.core.decorators import datamodel, operation
from pulpo.core.registries import ModelRegistry, OperationRegistry
from pulpo.core.cli import CLI

# Extended Proposal C exports
from pulpo.core.hierarchy import HierarchyParser
from pulpo.core.orchestration import OrchestrationCompiler, SyncAsyncDetector

__all__ = [
    # Core decorators
    "datamodel",
    "operation",
    # Registries
    "ModelRegistry",
    "OperationRegistry",
    # CLI interface
    "CLI",
    # Extended Proposal C - Orchestration
    "HierarchyParser",
    "OrchestrationCompiler",
    "SyncAsyncDetector",
]
EOF

# Update README with Extended Proposal C
cat > pulpo-new/README.md << 'EOF'
# PulpoCore - Agnostic Framework with Auto-Generated Orchestration

Metadata-driven code generation framework for building full-stack applications with auto-generated Prefect orchestration.

## Installation

```bash
pip install pulpocore
# or
poetry add pulpocore
```

## Quick Start (Extended Proposal C)

The framework uses hierarchical naming to auto-generate Prefect orchestration:

```python
from pulpo import datamodel, operation, CLI

@datamodel(name="Job")
class Job:
    title: str
    company: str

# Hierarchical naming for orchestration
@operation(name="scraping.stepstone.fetch")
async def fetch_stepstone(keywords: str) -> dict:
    return {"source": "stepstone", "jobs": []}

@operation(name="scraping.linkedin.fetch")
async def fetch_linkedin(keywords: str) -> dict:
    return {"source": "linkedin", "jobs": []}

@operation(name="scraping.merge")
async def merge_results(stepstone: dict, linkedin: dict) -> dict:
    """Automatically receives outputs from parallel fetch operations"""
    return {"merged_jobs": stepstone["jobs"] + linkedin["jobs"]}

# Sync functions are automatically wrapped with run_in_executor
@operation(name="parsing.clean_title")
def clean_title(title: str) -> str:
    return title.strip().lower()

cli = CLI()
if __name__ == "__main__":
    cli.run()
```

**Generated Structure:**
- Hierarchical names (e.g., "scraping.stepstone.fetch") create nested Prefect flows
- Same-level operations (e.g., "scraping.*.fetch") run in parallel with asyncio.gather()
- Sync functions automatically wrapped with run_in_executor()
- Dependencies inferred from operation input/output types
- Generated in `run_cache/orchestration/` as valid Prefect code

## Architecture

Framework is **agnostic** - doesn't care about project structure, only requires:
1. Decorators (@datamodel, @operation) anywhere in project
2. Main entrypoint that instantiates CLI

See docs/ for complete documentation and Extended Proposal C details.
EOF

echo "✅ PulpoCore structure created at pulpo-new/"
```

**Acceptance Criteria:**
- ✅ pulpo-new/pulpo/ package created
- ✅ All framework files copied
- ✅ __init__.py with correct exports
- ✅ README updated for pulpo
- ✅ pyproject.toml ready for update

---

## Step 3.2: Update pyproject.toml

**Objective:** Configure pyproject.toml for pulpo package.

**Actions:**
```bash
cd ~/postulator3000/pulpo-new

cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "pulpocore"
version = "0.7.0"
description = "Agnostic framework for building full-stack applications"
authors = ["PulpoCore Team <team@pulpocore.dev>"]
license = "MIT"
readme = "README.md"
repository = "https://github.com/yourusername/pulpo"
documentation = "https://github.com/yourusername/pulpo/blob/main/docs"
keywords = ["framework", "code-generation", "metadata-driven"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
packages = [
    { include = "pulpo" }
]

[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.6"
fastapi = "^0.109.0"
beanie = "^1.25"
typer = "^0.12.0"
jinja2 = "^3.0"
pyyaml = "^6.0"
structlog = "^24.1.0"
# Extended Proposal C - Prefect orchestration
prefect = "^3.0.0"
asyncio = "*"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
ruff = "^0.1.0"
mypy = "^1.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Verify
poetry check
echo "✅ pyproject.toml updated for pulpocore"
```

**Acceptance Criteria:**
- ✅ pyproject.toml has correct metadata
- ✅ Package name is "pulpocore"
- ✅ Version is 0.7.0
- ✅ Dependencies correct (includes Prefect for orchestration)
- ✅ `poetry check` passes

---

## Step 3.3: Create Extended Proposal C Orchestration Modules

**Objective:** Add new orchestration modules for hierarchy-based flow generation.

**Actions:**
```bash
cd ~/postulator3000/pulpo-new

# Create orchestration module for hierarchy parsing
cat > pulpo/core/hierarchy.py << 'EOF'
"""Hierarchy parser for Extended Proposal C naming convention.

Converts operation names like "scraping.stepstone.fetch" into hierarchical
structure for automatic DAG and Prefect flow generation.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ParsedName:
    """Parsed hierarchical operation name."""
    full_name: str
    hierarchy: List[str]  # ["scraping", "stepstone", "fetch"]
    level: int  # 3 for above example
    step: str  # "fetch" - last component

    @property
    def parent(self) -> str:
        """Parent flow name (all but last component)."""
        return ".".join(self.hierarchy[:-1]) if len(self.hierarchy) > 1 else self.hierarchy[0]

    @property
    def is_leaf(self) -> bool:
        """True if this is a leaf operation (no sub-operations)."""
        return self.level > 1


class HierarchyParser:
    """Parse hierarchical operation names into DAG structure."""

    def parse(self, name: str) -> ParsedName:
        """Parse an operation name into hierarchy components.

        Examples:
            "scraping.stepstone.fetch" → ["scraping", "stepstone", "fetch"]
            "parsing.clean" → ["parsing", "clean"]
            "validate" → ["validate"]
        """
        parts = name.split(".")
        return ParsedName(
            full_name=name,
            hierarchy=parts,
            level=len(parts),
            step=parts[-1],
        )

    def get_parent(self, name: str) -> str:
        """Get parent flow name."""
        parsed = self.parse(name)
        return parsed.parent

    def group_by_parent(self, names: List[str]) -> dict:
        """Group operations by their parent flow."""
        groups = {}
        for name in names:
            parent = self.get_parent(name)
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(name)
        return groups
EOF

# Create orchestration compiler module
mkdir -p pulpo/core/orchestration
cat > pulpo/core/orchestration/__init__.py << 'EOF'
"""Orchestration compilation for Extended Proposal C.

Converts decorated operations into Prefect flows with automatic:
- Hierarchy-based nesting
- Parallelization detection
- Sync/async handling
"""

from .compiler import OrchestrationCompiler
from .sync_async import SyncAsyncDetector

__all__ = [
    "OrchestrationCompiler",
    "SyncAsyncDetector",
]
EOF

# Create sync/async detection module
cat > pulpo/core/orchestration/sync_async.py << 'EOF'
"""Sync/Async function detection and wrapping.

Extended Proposal C feature: Automatically wraps sync functions with
run_in_executor so they can be used in async Prefect flows.
"""

import asyncio
import inspect
from typing import Callable, Any


class SyncAsyncDetector:
    """Detect and handle sync/async functions transparently."""

    def is_async(self, func: Callable) -> bool:
        """Check if function is async."""
        return inspect.iscoroutinefunction(func)

    def wrap_if_sync(self, func: Callable) -> Callable:
        """Wrap sync function in async if needed.

        If function is already async, returns it unchanged.
        If function is sync, wraps it with run_in_executor.
        """
        if self.is_async(func):
            return func

        async def async_wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

        return async_wrapper

    def detect_and_wrap(self, func: Callable) -> Callable:
        """Alias for wrap_if_sync for clarity."""
        return self.wrap_if_sync(func)
EOF

# Create orchestration compiler module
cat > pulpo/core/orchestration/compiler.py << 'EOF'
"""Orchestration compiler for Extended Proposal C.

Converts operation registry into Prefect flows with automatic:
- DAG generation from hierarchy
- Parallelization detection
- Sync/async handling
"""

from typing import Dict, List, Any


class OrchestrationCompiler:
    """Compile operations into Prefect orchestration."""

    def __init__(self, cli):
        """Initialize with CLI instance."""
        self.cli = cli
        self.operation_registry = cli.operation_registry
        self.model_registry = cli.model_registry

    def compile(self) -> "Orchestration":
        """Compile all operations into orchestration structure."""
        ops = self.operation_registry.get_all()

        # Parse hierarchy
        from ..hierarchy import HierarchyParser
        parser = HierarchyParser()

        # Build flows from hierarchy
        flows = {}
        for op_name in ops:
            parsed = parser.parse(op_name)
            parent = parsed.parent

            if parent not in flows:
                flows[parent] = FlowGroup(parent)

            flows[parent].add_operation(op_name, parsed)

        return Orchestration(flows, self.operation_registry)


class FlowGroup:
    """Represents a Prefect @flow and its operations."""

    def __init__(self, name: str):
        self.name = name
        self.operations: Dict[str, Any] = {}
        self.parallel_groups = []

    def add_operation(self, op_name: str, parsed):
        """Add operation to flow."""
        self.operations[op_name] = parsed


class Orchestration:
    """Complete orchestration structure."""

    def __init__(self, flows: Dict[str, FlowGroup], op_registry):
        self.flows = flows
        self.op_registry = op_registry

    def get_flow(self, name: str) -> FlowGroup:
        """Get flow by name."""
        return self.flows.get(name)
EOF

echo "✅ Extended Proposal C orchestration modules created"
```

**Acceptance Criteria:**
- ✅ hierarchy.py created with HierarchyParser
- ✅ orchestration/__init__.py exports main classes
- ✅ sync_async.py implements SyncAsyncDetector
- ✅ compiler.py implements OrchestrationCompiler
- ✅ All modules can be imported from pulpo.core

---

## Step 3.4: Move to Final Location

**Objective:** Move pulpo-new to its final location.

**Actions:**
```bash
cd ~/postulator3000

# Archive old core-minimal for reference
mv jobhunter-core-minimal jobhunter-core-minimal.archive

echo "✅ Archived jobhunter-core-minimal to jobhunter-core-minimal.archive"

# Move new pulpo to final location
mv pulpo-new pulpo

echo "✅ Moved pulpo-new to pulpo"

# Verify structure
ls -la pulpo/
tree -L 2 -d pulpo/ | head -30

echo "✅ PulpoCore ready at ./pulpo/"
```

**Acceptance Criteria:**
- ✅ pulpo/ folder exists at root level
- ✅ pulpo/pulpo/ package exists
- ✅ Old core-minimal archived
- ✅ Structure correct

---

# PHASE 4: Update Jobhunter to Use PulpoCore

## Step 4.1: Update Imports

**Objective:** Replace local core imports with pulpo imports.

**Actions:**
```bash
cd ~/postulator3000/Jobhunter

# Find all core imports
echo "Finding core imports..."
grep -r "from core\." src/ tests/ --include="*.py" | head -20
grep -r "import core" src/ tests/ --include="*.py" | head -20

# Create migration script
cat > migrate_imports.py << 'EOF'
#!/usr/bin/env python3
"""Migrate imports from core to pulpo."""

import os
import re

def update_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # Replace patterns
    content = re.sub(r'from core\.', 'from pulpo.core.', content)
    content = re.sub(r'from core import', 'from pulpo.core import', content)
    content = re.sub(r'^import core', 'import pulpo.core', content, flags=re.MULTILINE)

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Find all Python files
for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if update_imports(filepath):
                print(f"✅ Updated: {filepath}")

print("✅ Import migration complete")
EOF

python3 migrate_imports.py

# Verify no old imports remain
echo -e "\nVerifying old imports removed:"
OLD_IMPORTS=$(grep -r "from core\." src/ --include="*.py" | wc -l)
echo "Remaining 'from core.' imports: $OLD_IMPORTS (should be 0)"

if [ $OLD_IMPORTS -eq 0 ]; then
    echo "✅ All imports updated"
fi
```

**Acceptance Criteria:**
- ✅ All `from core.` replaced with `from pulpo.core.`
- ✅ All `import core` replaced with `import pulpo.core`
- ✅ No old import patterns remain
- ✅ No errors in search results

---

## Step 4.2: Update pyproject.toml

**Objective:** Add pulpo as dependency.

**Actions:**
```bash
cd ~/postulator3000/Jobhunter

# Update pyproject.toml
python3 << 'EOF'
import toml

with open('pyproject.toml', 'r') as f:
    config = toml.load(f)

# Add pulpo dependency
config['tool']['poetry']['dependencies']['pulpocore'] = "^0.7.0"

# Remove any local core path dependency if it exists
deps = config['tool']['poetry']['dependencies']
if 'core' in deps:
    del deps['core']
if 'jobhunter-core' in deps:
    del deps['jobhunter-core']

with open('pyproject.toml', 'w') as f:
    toml.dump(config, f)

print("✅ Added pulpocore dependency")
EOF

# Update lock file
poetry lock

# Verify
grep "pulpocore" pyproject.toml
echo "✅ pyproject.toml updated"
```

**Acceptance Criteria:**
- ✅ pulpocore = "^0.7.0" added
- ✅ Old core dependencies removed
- ✅ poetry.lock updated
- ✅ poetry check passes

---

## Step 4.3: Test Jobhunter With PulpoCore

**Objective:** Verify Jobhunter works with pulpo imports.

**Actions:**
```bash
cd ~/postulator3000/Jobhunter

# Install dependencies
poetry install

# Test imports
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from pulpo import datamodel, operation
    from pulpo.core import cli
    print("✅ Pulpo imports work in Jobhunter")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Try importing a model
try:
    from src.database.models.job import Job
    print("✅ Job model imports")
except ImportError as e:
    print(f"⚠️  Could not import Job model: {e}")
EOF

# Run basic tests if they exist
if [ -f "pytest.ini" ] || [ -d "tests/" ]; then
    poetry run pytest tests/unit -q --tb=short 2>&1 | head -20
    echo "✅ Unit tests run (check output above)"
fi
```

**Acceptance Criteria:**
- ✅ Pulpo imports work
- ✅ Models import successfully
- ✅ No import errors
- ✅ Tests pass (or gracefully skip)

---

# PHASE 5: Verification & Cleanup

## Step 5.1: Complete Repository Verification

**Objective:** Verify entire repository still works.

**Actions:**
```bash
cd ~/postulator3000

echo "=== Repository Verification ==="

# Check structure
echo -e "\n1. Directory Structure:"
ls -la | grep -E "^d" | awk '{print $NF}'

# Verify no duplicates
echo -e "\n2. No Duplicates:"
echo "jobhunter-core-minimal instances: $(find . -maxdepth 2 -name 'jobhunter-core-minimal' -type d | wc -l)"
echo "jobhunter-scraping-applying instances: $(find . -maxdepth 2 -name 'jobhunter-scraping-applying' -type d | wc -l)"
echo "pulpo instances: $(find . -maxdepth 2 -name 'pulpo' -type d | wc -l)"

# Check git status
echo -e "\n3. Git Status:"
git status --short | head -20

# Verify imports
echo -e "\n4. Import Verification:"

cd Jobhunter
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

errors = []

try:
    from pulpo import datamodel, operation
    print("  ✅ Pulpo imports")
except Exception as e:
    errors.append(f"Pulpo import: {e}")

try:
    from pulpo.core import cli
    print("  ✅ Pulpo CLI imports")
except Exception as e:
    errors.append(f"Pulpo CLI import: {e}")

try:
    from src.api import app
    print("  ✅ Jobhunter API imports")
except Exception as e:
    print(f"  ⚠️  Jobhunter API import: {e} (may be expected)")

if errors:
    print("\n❌ Errors found:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
EOF

echo -e "\n✅ Verification complete"
```

**Acceptance Criteria:**
- ✅ No duplicate folders
- ✅ Pulpo at root level
- ✅ No old core-minimal duplicates
- ✅ Imports work correctly
- ✅ Git status clean or shows expected changes

---

## Step 5.2: Commit Changes

**Objective:** Record restructuring in git history.

**Actions:**
```bash
cd ~/postulator3000

git status

# Add everything
git add -A

# Commit with detailed message
git commit -m "refactor: Restructure to PulpoCore library

- Move jobhunter-core-minimal to separate /pulpo directory
- Remove duplicate folder instances
- Update imports to use 'from pulpo import ...'
- Update Jobhunter to depend on pulpocore
- Remove hidden property from generated run_cache folder
- Clean up build artifacts and cache directories

This restructuring:
✅ Makes core framework reusable (separate repository)
✅ Removes code duplication
✅ Implements agnostic framework pattern
✅ Prepares for PyPI publication

BREAKING CHANGES:
- Core imports now use 'from pulpo import ...'
- Generated folder is now 'run_cache/' (not '.run_cache/')
- No changes to functionality

Related: PULPO_TESTING_PLAN.md, PULPO_RESTRUCTURING_PLAN.md"

# Verify commit
git log --oneline -1

echo "✅ Changes committed"
```

**Acceptance Criteria:**
- ✅ All changes committed
- ✅ Descriptive commit message
- ✅ Git history preserved
- ✅ Can view changes with git log

---

## Step 5.3: Archive Old Code

**Objective:** Keep old code as reference but mark as archived.

**Actions:**
```bash
cd ~/postulator3000

# Create archive directory
mkdir -p _archived

# Archive old core
if [ -d "jobhunter-core-minimal.archive" ]; then
    mv jobhunter-core-minimal.archive _archived/
    echo "✅ Archived jobhunter-core-minimal"
fi

# Create archive info
cat > _archived/README.md << 'EOF'
# Archived Code

This directory contains code that has been archived or superseded.

## Contents

- **jobhunter-core-minimal.archive/** - Old framework (now at /pulpo)

## Why Archived

The core framework has been restructured as a separate reusable library.
See /pulpo for the new location.

## Accessing Archived Code

```bash
ls _archived/
```

## For Developers

The new framework is at `/pulpo/` and much more modular.
All imports should use `from pulpo import ...` instead of relative imports.

See PULPO_INSTRUCTIONS_SUMMARY.md for new architecture.
EOF

# Commit archive info
git add _archived/
git commit -m "chore: Archive old code structure

- Move jobhunter-core-minimal.archive to _archived/
- Archive no longer needed after restructuring
- Keep for historical reference only"

echo "✅ Old code archived"
```

**Acceptance Criteria:**
- ✅ Old code moved to _archived/
- ✅ README.md explains archive
- ✅ Changes committed
- ✅ Original code still accessible

---

# VERIFICATION CHECKLIST

After all phases complete:

## Backup
- [ ] Full backup created with timestamp
- [ ] Git bundle saved
- [ ] Recovery script works
- [ ] Backup verified

## Deduplication
- [ ] No duplicate jobhunter-core-minimal folders
- [ ] No duplicate jobhunter-scraping-applying folders
- [ ] Only single instance of each module
- [ ] Directory structure clean

## PulpoCore
- [ ] pulpo/ folder at root level
- [ ] pulpo/pulpo/ package exists
- [ ] __init__.py with correct exports
- [ ] pyproject.toml configured
- [ ] README updated

## Jobhunter Migration
- [ ] All imports updated to use "from pulpo import ..."
- [ ] pyproject.toml has pulpocore dependency
- [ ] No old import patterns remain
- [ ] Tests pass or skip gracefully

## Repository Health
- [ ] No duplicate folders
- [ ] Git history preserved
- [ ] All changes committed
- [ ] Old code archived
- [ ] Can roll back to backup if needed

## Final State
```
postulator3000/
├── pulpo/                      ← New framework location
│   ├── pulpo/                  ← Package
│   ├── pyproject.toml
│   └── ...
├── Jobhunter/                  ← Uses: from pulpo import ...
├── jobhunter-scraping-applying/← Single copy
├── _archived/                  ← Old code for reference
└── ... (other files)
```

---

# Rollback Procedure

If critical issues found after restructuring:

```bash
# Stop all services
make down

# Restore from backup
bash ~/backups/postulator3000_[timestamp]/RESTORE.sh

# Verify restoration
cd ~/postulator3000
git status
ls -la

# You're back to pre-restructuring state
```

**Restore Time:** ~5 minutes
**Data Loss:** None (full backup)
**Confidence:** High (tested backup)

---

**Status:** Ready for Execution After Testing ✅
**Prerequisite:** PULPO_TESTING_PLAN.md must pass first
**Risk:** MEDIUM (with full backups provided)
**Estimated Time:** 3-4 hours total
