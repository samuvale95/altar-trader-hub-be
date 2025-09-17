#!/usr/bin/env python3
"""
Script to run database migrations.
"""

import sys
import os
from alembic.config import Config
from alembic import command

def run_migration(action="upgrade", revision="head"):
    """Run database migration."""
    
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to alembic.ini
    alembic_cfg = os.path.join(script_dir, "alembic.ini")
    
    # Create Alembic config
    alembic_cfg = Config(alembic_cfg)
    
    if action == "upgrade":
        command.upgrade(alembic_cfg, revision)
    elif action == "downgrade":
        command.downgrade(alembic_cfg, revision)
    elif action == "revision":
        command.revision(alembic_cfg, autogenerate=True, message="Auto migration")
    elif action == "history":
        command.history(alembic_cfg)
    elif action == "current":
        command.current(alembic_cfg)
    else:
        print(f"Unknown action: {action}")
        print("Available actions: upgrade, downgrade, revision, history, current")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <action> [revision]")
        print("Actions: upgrade, downgrade, revision, history, current")
        sys.exit(1)
    
    action = sys.argv[1]
    revision = sys.argv[2] if len(sys.argv) > 2 else "head"
    
    run_migration(action, revision)
