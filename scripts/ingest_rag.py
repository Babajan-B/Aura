#!/usr/bin/env python3
"""
RAG Ingestion CLI Script

Ingests masterRAG.md, generates embeddings, and stores them in the database.

Usage:
    python scripts/ingest_rag.py              # Run ingestion
    python scripts/ingest_rag.py --stats      # Show statistics only
    python scripts/ingest_rag.py --keep       # Keep existing embeddings
"""
import sys
import asyncio
import os
import argparse

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.rag.rag_ingestion_service import (
    ingest_master_rag,
    get_rag_statistics,
    get_rag_embeddings_count
)
from app.db.database import close_db_pool


async def show_statistics():
    """Show RAG knowledge base statistics."""
    print("\n📊 RAG Knowledge Base Statistics\n")

    stats = await get_rag_statistics()

    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Average Chunk Size: {stats['average_chunk_size']} characters")
    print(f"Embedding Dimension: {stats['embedding_dimension']}")

    if stats['sections']:
        print(f"\nChunks by Section:")
        for section in stats['sections']:
            print(f"  • {section['section_name']}: {section['chunk_count']} chunks")
    else:
        print("\n⚠️  No RAG embeddings found in database.")
        print("   Run: python scripts/ingest_rag.py")

    print()


async def run_ingestion(clear_existing: bool = True):
    """Run the RAG ingestion pipeline."""
    # Determine masterRAG.md path
    master_rag_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'docs',
        'masterRAG.md'
    )

    master_rag_path = os.path.abspath(master_rag_path)

    print(f"\n🚀 Starting RAG Ingestion")
    print(f"   File: {master_rag_path}")
    print(f"   Clear existing: {clear_existing}\n")

    # Check current count
    current_count = await get_rag_embeddings_count()
    if current_count > 0:
        print(f"ℹ️  Current embeddings in database: {current_count}")
        if clear_existing:
            print("   These will be cleared and regenerated.\n")
        else:
            print("   New embeddings will be added.\n")

    # Run ingestion
    results = await ingest_master_rag(
        master_rag_path=master_rag_path,
        clear_existing=clear_existing,
        min_chunk_size=300,
        max_chunk_size=1500,
        overlap=100
    )

    # Return appropriate exit code
    if results["success"]:
        print("✅ RAG ingestion completed successfully!\n")
        return 0
    else:
        print("❌ RAG ingestion failed.\n")
        if results["errors"]:
            print("Errors:")
            for error in results["errors"]:
                print(f"  - {error}")
        print()
        return 1


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest masterRAG.md into the vector database"
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only (no ingestion)'
    )
    parser.add_argument(
        '--keep',
        action='store_true',
        help='Keep existing embeddings (do not clear)'
    )

    args = parser.parse_args()

    exit_code = 0

    try:
        if args.stats:
            # Just show statistics
            await show_statistics()
        else:
            # Run ingestion
            exit_code = await run_ingestion(clear_existing=not args.keep)

            # Show statistics after ingestion
            print("\n" + "="*60)
            await show_statistics()

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
