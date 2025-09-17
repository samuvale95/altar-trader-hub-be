#!/usr/bin/env python3
"""
Setup script for Altar Trader Hub Backend.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result

def setup_environment():
    """Set up the development environment."""
    
    print("🚀 Setting up Altar Trader Hub Backend...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", "venv"])
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/Linux/macOS
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Upgrade pip
    print("📦 Upgrading pip...")
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    
    # Install dependencies
    print("📦 Installing dependencies...")
    run_command([str(pip_path), "install", "-r", "requirements.txt"])
    
    # Install development dependencies
    print("📦 Installing development dependencies...")
    run_command([str(pip_path), "install", "-r", "requirements-dev.txt"])
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        shutil.copy("env.example", ".env")
        print("⚠️  Please edit .env file with your configuration")
    
    # Create necessary directories
    print("📁 Creating directories...")
    directories = ["logs", "data", "backups", "migrations/versions"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Start PostgreSQL and Redis")
    print("3. Run migrations: python migrate.py revision")
    print("4. Run migrations: python migrate.py upgrade")
    print("5. Start the application: python run.py")

if __name__ == "__main__":
    setup_environment()
