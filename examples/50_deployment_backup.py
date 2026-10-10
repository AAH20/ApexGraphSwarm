"""Example 50: Deployment - backup and disaster recovery.

Backup and restore procedures for the control plane database.
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

def backup_database(source_path, backup_dir):
    """Create a consistent backup of the control database."""
    source = Path(source_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"control_backup_{timestamp}.sqlite"

    # Use SQLite backup API for consistency
    source_conn = sqlite3.connect(str(source))
    backup_conn = sqlite3.connect(str(backup_path))

    with backup_conn:
        source_conn.backup(backup_conn)

    source_conn.close()
    backup_conn.close()

    print(f"Backup created: {backup_path}")
    return backup_path

def restore_database(backup_path, target_path):
    """Restore the control database from a backup."""
    backup = Path(backup_path)
    target = Path(target_path)

    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup}")

    # Create target directory if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Copy backup to target
    shutil.copy2(backup, target)
    print(f"Restored: {target}")

def verify_database(db_path):
    """Verify database integrity."""
    conn = sqlite3.connect(str(db_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result[0] == "ok"
    finally:
        conn.close()

# Example usage
print("Backup and Disaster Recovery Procedures:")
print("=" * 50)

# Backup
# backup_path = backup_database("/var/lib/apex/control.sqlite", "/backups/apex/")

# Restore
# restore_database("/backups/apex/control_backup_20260101_120000.sqlite", "/var/lib/apex/control.sqlite")

# Verify
# is_valid = verify_database("/var/lib/apex/control.sqlite")
# print(f"Database integrity: {'OK' if is_valid else 'CORRUPTED'}")

print("\nProcedures defined:")
print("  - backup_database(source, backup_dir)")
print("  - restore_database(backup_path, target_path)")
print("  - verify_database(db_path)")
