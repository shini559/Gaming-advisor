#!/usr/bin/env python3
"""
Script to generate Alembic migration
Usage: python generate_migration.py "migration message"
"""

import sys
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
    # Get migration message
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "create users table"
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found. Make sure your database configuration is set.")
        print("You can copy .env.example to .env and fill in your Azure PostgreSQL credentials.")
        return
    
    # Generate migration
    cmd = f'alembic revision --autogenerate -m "{message}"'
    
    if run_command(cmd):
        print("✅ Migration generated successfully!")
        print("Next steps:")
        print("1. Review the generated migration file in migrations/versions/")
        print("2. Run: alembic upgrade head")
    else:
        print("❌ Failed to generate migration")

if __name__ == "__main__":
    main()