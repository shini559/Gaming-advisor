#!/usr/bin/env python3
"""
Script to apply Alembic migrations
Usage: python migrate.py
"""

import subprocess
import os

def run_command(cmd):
    """Run command and handle errors"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def main():
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found.")
        print("Please copy .env.example to .env and configure your Azure PostgreSQL credentials.")
        return
    
    print("📦 Applying database migrations...")
    
    # Show current revision
    print("\n📍 Current database revision:")
    run_command("alembic current")
    
    # Show pending migrations
    print("\n📋 Pending migrations:")
    run_command("alembic show head")
    
    # Apply migrations
    print("\n⚡ Applying migrations...")
    if run_command("alembic upgrade head"):
        print("✅ Migrations applied successfully!")
        
        # Show new current revision
        print("\n📍 New database revision:")
        run_command("alembic current")
    else:
        print("❌ Failed to apply migrations")

if __name__ == "__main__":
    main()