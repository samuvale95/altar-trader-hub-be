#!/usr/bin/env python3
"""
Script to run database migrations.

This script is called automatically by Heroku's release phase (see Procfile).
It can also be run manually for specific migration operations.
"""

import sys
import os
import logging
from alembic.config import Config
from alembic import command

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables_if_not_exist():
    """Create all database tables if they don't exist."""
    try:
        from app.core.database import init_db
        logger.info("Creating database tables if they don't exist...")
        init_db()
        logger.info("Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def run_migration(action="upgrade", revision="head"):
    """
    Run database migration.
    
    Args:
        action: Migration action (upgrade, downgrade, revision, history, current)
        revision: Target revision (default: head)
    """
    
    try:
        # Get the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to alembic.ini
        alembic_ini_path = os.path.join(script_dir, "alembic.ini")
        
        if not os.path.exists(alembic_ini_path):
            logger.warning("alembic.ini not found, creating tables directly...")
            return create_tables_if_not_exist()
        
        # Create Alembic config
        alembic_cfg = Config(alembic_ini_path)
        
        logger.info(f"Running migration action: {action} (revision: {revision})")
        
        if action == "upgrade":
            command.upgrade(alembic_cfg, revision)
            logger.info("Migration upgrade completed successfully")
        elif action == "downgrade":
            command.downgrade(alembic_cfg, revision)
            logger.info("Migration downgrade completed successfully")
        elif action == "revision":
            message = sys.argv[3] if len(sys.argv) > 3 else "Auto migration"
            command.revision(alembic_cfg, autogenerate=True, message=message)
            logger.info(f"Created new migration: {message}")
        elif action == "history":
            command.history(alembic_cfg)
        elif action == "current":
            command.current(alembic_cfg)
        else:
            logger.error(f"Unknown action: {action}")
            print("Available actions: upgrade, downgrade, revision, history, current")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.info("Attempting to create tables directly...")
        return create_tables_if_not_exist()


def main():
    """Main entry point."""
    # If no arguments provided, default to upgrade (for Heroku release phase)
    if len(sys.argv) < 2:
        logger.info("No action specified, defaulting to 'upgrade head'")
        success = run_migration("upgrade", "head")
    else:
        action = sys.argv[1]
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        success = run_migration(action, revision)
    
    if not success:
        logger.error("Migration failed!")
        sys.exit(1)
    
    logger.info("Migration completed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
