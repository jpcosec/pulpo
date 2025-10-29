#!/usr/bin/env python3
"""Backup and restore MongoDB and Prefect data.

Provides utilities to backup and restore Docker volumes for:
- MongoDB (jobhunter-mongo-data)
- Prefect (jobhunter-prefect-data)

Usage:
    python backup.py backup [--name backup-name]
    python backup.py restore <backup-name>
    python backup.py list
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKUPS_DIR = Path(".backups")
MONGO_VOLUME = "jobhunter-mongo-data"
PREFECT_VOLUME = "jobhunter-prefect-data"


def ensure_backups_dir():
    """Create backups directory if it doesn't exist."""
    BACKUPS_DIR.mkdir(exist_ok=True)


def get_backup_name(name: str | None = None) -> str:
    """Generate backup name with timestamp."""
    if name:
        return name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"backup-{timestamp}"


def backup_mongo(backup_name: str) -> bool:
    """Backup MongoDB volume."""
    print(f"\n📦 Backing up MongoDB (volume: {MONGO_VOLUME})...")

    backup_path = BACKUPS_DIR / backup_name / "mongo"
    backup_path.mkdir(parents=True, exist_ok=True)

    try:
        # Create tar archive from volume
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v", f"{MONGO_VOLUME}:/data",
            "-v", f"{backup_path}:/backup",
            "alpine",
            "tar", "czf", "/backup/mongo.tar.gz", "-C", "/data", "."
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ MongoDB backed up to {backup_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to backup MongoDB: {e}")
        return False


def backup_prefect(backup_name: str) -> bool:
    """Backup Prefect volume."""
    print(f"\n📦 Backing up Prefect (volume: {PREFECT_VOLUME})...")

    backup_path = BACKUPS_DIR / backup_name / "prefect"
    backup_path.mkdir(parents=True, exist_ok=True)

    try:
        # Create tar archive from volume
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v", f"{PREFECT_VOLUME}:/data",
            "-v", f"{backup_path}:/backup",
            "alpine",
            "tar", "czf", "/backup/prefect.tar.gz", "-C", "/data", "."
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Prefect backed up to {backup_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to backup Prefect: {e}")
        return False


def restore_mongo(backup_name: str) -> bool:
    """Restore MongoDB volume from backup."""
    print(f"\n📥 Restoring MongoDB from {backup_name}...")

    backup_file = BACKUPS_DIR / backup_name / "mongo" / "mongo.tar.gz"

    if not backup_file.exists():
        print(f"   ❌ Backup file not found: {backup_file}")
        return False

    try:
        # Extract tar archive to volume
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v", f"{MONGO_VOLUME}:/data",
            "-v", f"{backup_file.parent}:/backup",
            "alpine",
            "tar", "xzf", "/backup/mongo.tar.gz", "-C", "/data"
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ MongoDB restored from {backup_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to restore MongoDB: {e}")
        return False


def restore_prefect(backup_name: str) -> bool:
    """Restore Prefect volume from backup."""
    print(f"\n📥 Restoring Prefect from {backup_name}...")

    backup_file = BACKUPS_DIR / backup_name / "prefect" / "prefect.tar.gz"

    if not backup_file.exists():
        print(f"   ❌ Backup file not found: {backup_file}")
        return False

    try:
        # Extract tar archive to volume
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v", f"{PREFECT_VOLUME}:/data",
            "-v", f"{backup_file.parent}:/backup",
            "alpine",
            "tar", "xzf", "/backup/prefect.tar.gz", "-C", "/data"
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Prefect restored from {backup_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to restore Prefect: {e}")
        return False


def list_backups():
    """List available backups."""
    ensure_backups_dir()

    backups = sorted([d for d in BACKUPS_DIR.iterdir() if d.is_dir()])

    if not backups:
        print("\n❌ No backups found")
        return

    print("\n📋 Available backups:\n")
    for backup in backups:
        mongo_exists = (backup / "mongo" / "mongo.tar.gz").exists()
        prefect_exists = (backup / "prefect" / "prefect.tar.gz").exists()
        size = sum(f.stat().st_size for f in backup.rglob("*") if f.is_file())
        size_mb = size / (1024 * 1024)

        status = []
        if mongo_exists:
            status.append("📦 MongoDB")
        if prefect_exists:
            status.append("🔄 Prefect")

        status_str = " + ".join(status) if status else "❌ Empty"
        print(f"  {backup.name:<30} {status_str:<30} ({size_mb:.1f} MB)")


def main():
    """Main entry point."""
    ensure_backups_dir()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "backup":
        name = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--name" else None
        backup_name = get_backup_name(name)

        print(f"\n🔄 Creating backup: {backup_name}")

        success = True
        success = backup_mongo(backup_name) and success
        success = backup_prefect(backup_name) and success

        if success:
            print(f"\n✅ Backup complete: {backup_name}")
            print(f"   📁 Location: {BACKUPS_DIR / backup_name}")
        else:
            print("\n⚠️  Backup partially failed")
            sys.exit(1)

    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ Usage: python backup.py restore <backup-name>")
            sys.exit(1)

        backup_name = sys.argv[2]

        print(f"\n🔄 Restoring from: {backup_name}")

        success = True
        success = restore_mongo(backup_name) and success
        success = restore_prefect(backup_name) and success

        if success:
            print("\n✅ Restore complete")
            print("   Note: Restart services with 'make restart' or 'make up'")
        else:
            print("\n⚠️  Restore partially failed")
            sys.exit(1)

    elif command == "list":
        list_backups()

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
