#!/usr/bin/env python3
"""
Database setup and validation script for AI Learning Coach.

Usage:
    python scripts/setup_database.py validate    # Validate existing schema
    python scripts/setup_database.py migrate     # Apply migrations
    python scripts/setup_database.py full        # Migrate and validate
"""
import sys
import asyncio
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.schema_validator import (
    run_full_validation,
    apply_migration,
    check_pgvector_extension,
    enable_pgvector_extension
)
from app.db.database import close_db_pool


async def validate_only():
    """Run validation only."""
    print("\n🔍 Running database validation...\n")
    results = await run_full_validation()

    # Print detailed results
    if results["overall_status"] == "success":
        print("\n✅ Database is properly configured!")
        return 0
    else:
        print("\n❌ Database validation failed!")
        if results["tables"]["missing_tables"]:
            print(f"\nMissing tables: {', '.join(results['tables']['missing_tables'])}")
            print("\nRun: python scripts/setup_database.py migrate")
        return 1


async def migrate_only():
    """Apply database migrations."""
    print("\n📦 Applying database migrations...\n")

    migration_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'backend',
        'migrations',
        '001_initial_schema.sql'
    )

    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return 1

    result = await apply_migration(migration_file)

    if result["success"]:
        print(f"✅ {result['message']}")
        return 0
    else:
        print(f"❌ {result['message']}")
        if "error" in result:
            print(f"   Error: {result['error']}")
        return 1


async def full_setup():
    """Run full setup: migrate and validate."""
    print("\n🚀 Running full database setup...\n")

    # Step 1: Apply migrations
    print("Step 1: Applying migrations...")
    migrate_result = await migrate_only()

    if migrate_result != 0:
        print("\n❌ Migration failed. Please check the error above.")
        return 1

    # Step 2: Validate
    print("\nStep 2: Validating database...")
    validate_result = await validate_only()

    if validate_result == 0:
        print("\n✅ Full database setup completed successfully!")
        return 0
    else:
        print("\n⚠️  Setup completed with warnings. Please review the validation results above.")
        return 1


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/setup_database.py validate    # Validate existing schema")
        print("  python scripts/setup_database.py migrate     # Apply migrations")
        print("  python scripts/setup_database.py full        # Migrate and validate")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "validate":
            exit_code = await validate_only()
        elif command == "migrate":
            exit_code = await migrate_only()
        elif command == "full":
            exit_code = await full_setup()
        else:
            print(f"Unknown command: {command}")
            print("Valid commands: validate, migrate, full")
            exit_code = 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        # Clean up database connections
        await close_db_pool()

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
