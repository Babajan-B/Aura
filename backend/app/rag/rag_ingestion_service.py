"""
RAG Ingestion Service for processing and storing internal knowledge (masterRAG.md).
"""
import os
from typing import List, Dict, Any
from app.rag.chunking_service import load_and_chunk_file, TextChunk
from app.rag.embedding_service import generate_internal_rag_embedding, generate_embeddings_batch
from app.db.database import get_db_pool, log_system_event


async def store_rag_chunk(
    section_name: str,
    chunk_text: str,
    embedding_vector: List[float]
) -> str:
    """
    Store a single RAG chunk with its embedding in the database.

    Args:
        section_name: Name of the section
        chunk_text: Text content of the chunk
        embedding_vector: Embedding vector for the chunk

    Returns:
        chunk_id (UUID as string)
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Convert embedding vector to string format for pgvector
            vector_str = '[' + ','.join(map(str, embedding_vector)) + ']'

            result = await conn.fetchrow("""
                INSERT INTO internal_rag_embeddings (
                    section_name,
                    chunk_text,
                    embedding_vector,
                    created_at
                )
                VALUES ($1, $2, $3::vector, NOW())
                RETURNING chunk_id
            """, section_name, chunk_text, vector_str)

            return str(result['chunk_id'])

    except Exception as e:
        await log_system_event(
            "error",
            "rag",
            f"Failed to store RAG chunk: {str(e)}"
        )
        raise


async def clear_existing_rag_embeddings() -> int:
    """
    Clear all existing RAG embeddings from the database.
    Useful for re-ingesting the knowledge base.

    Returns:
        Number of deleted records
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM internal_rag_embeddings")
            # Extract count from result string like "DELETE 10"
            count = int(result.split()[-1]) if result.split()[-1].isdigit() else 0

            await log_system_event(
                "info",
                "rag",
                f"Cleared {count} existing RAG embeddings"
            )

            return count

    except Exception as e:
        await log_system_event(
            "error",
            "rag",
            f"Failed to clear RAG embeddings: {str(e)}"
        )
        raise


async def get_rag_embeddings_count() -> int:
    """
    Get the count of RAG embeddings in the database.

    Returns:
        Number of embeddings
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM internal_rag_embeddings"
            )
            return result or 0

    except Exception as e:
        print(f"Failed to get RAG embeddings count: {e}")
        return 0


async def ingest_master_rag(
    master_rag_path: str,
    clear_existing: bool = True,
    min_chunk_size: int = 300,
    max_chunk_size: int = 1500,
    overlap: int = 100
) -> Dict[str, Any]:
    """
    Complete RAG ingestion pipeline for masterRAG.md.

    Steps:
    1. Optionally clear existing embeddings
    2. Load and chunk the masterRAG.md file
    3. Generate embeddings for each chunk
    4. Store chunks and embeddings in database

    Args:
        master_rag_path: Path to masterRAG.md file
        clear_existing: Whether to clear existing embeddings first
        min_chunk_size: Minimum chunk size in characters
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters

    Returns:
        Dict with ingestion results
    """
    print("\n" + "="*60)
    print("RAG Ingestion Pipeline Starting...")
    print("="*60 + "\n")

    results = {
        "success": False,
        "file_path": master_rag_path,
        "chunks_processed": 0,
        "embeddings_generated": 0,
        "embeddings_stored": 0,
        "errors": []
    }

    try:
        # Step 1: Check if file exists
        if not os.path.exists(master_rag_path):
            error_msg = f"masterRAG.md not found at: {master_rag_path}"
            results["errors"].append(error_msg)
            await log_system_event("error", "rag", error_msg)
            return results

        print(f"✓ Found masterRAG.md at: {master_rag_path}\n")

        # Step 2: Clear existing embeddings if requested
        if clear_existing:
            print("Step 1: Clearing existing RAG embeddings...")
            cleared_count = await clear_existing_rag_embeddings()
            print(f"✓ Cleared {cleared_count} existing embeddings\n")

        # Step 3: Load and chunk the document
        print("Step 2: Loading and chunking masterRAG.md...")
        chunks = load_and_chunk_file(
            master_rag_path,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            overlap=overlap
        )
        results["chunks_processed"] = len(chunks)
        print(f"✓ Created {len(chunks)} chunks\n")

        if not chunks:
            error_msg = "No chunks created from masterRAG.md"
            results["errors"].append(error_msg)
            await log_system_event("error", "rag", error_msg)
            return results

        # Step 4: Generate embeddings for all chunks
        print("Step 3: Generating embeddings...")
        chunk_texts = [chunk.text for chunk in chunks]

        embeddings = await generate_embeddings_batch(
            chunk_texts,
            task_type="retrieval_document",
            batch_size=50,
            delay=0.5
        )
        results["embeddings_generated"] = len(embeddings)
        print(f"✓ Generated {len(embeddings)} embeddings\n")

        # Step 5: Store chunks and embeddings
        print("Step 4: Storing chunks and embeddings in database...")
        stored_count = 0

        for chunk, embedding in zip(chunks, embeddings):
            try:
                chunk_id = await store_rag_chunk(
                    section_name=chunk.section_name,
                    chunk_text=chunk.text,
                    embedding_vector=embedding
                )
                stored_count += 1

                if stored_count % 5 == 0:
                    print(f"  Stored {stored_count}/{len(chunks)} chunks...")

            except Exception as e:
                error_msg = f"Failed to store chunk from section '{chunk.section_name}': {str(e)}"
                results["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")

        results["embeddings_stored"] = stored_count
        print(f"✓ Stored {stored_count} chunks with embeddings\n")

        # Final success check
        if stored_count > 0:
            results["success"] = True
            await log_system_event(
                "info",
                "rag",
                f"RAG ingestion completed: {stored_count} chunks stored"
            )

        # Print summary
        print("="*60)
        if results["success"]:
            print("RAG Ingestion: SUCCESS ✓")
            print(f"  - Chunks processed: {results['chunks_processed']}")
            print(f"  - Embeddings generated: {results['embeddings_generated']}")
            print(f"  - Embeddings stored: {results['embeddings_stored']}")
        else:
            print("RAG Ingestion: FAILED ✗")
            if results["errors"]:
                print("\nErrors:")
                for error in results["errors"]:
                    print(f"  - {error}")
        print("="*60 + "\n")

        return results

    except Exception as e:
        error_msg = f"RAG ingestion pipeline failed: {str(e)}"
        results["errors"].append(error_msg)
        await log_system_event("error", "rag", error_msg)
        print(f"\n✗ {error_msg}\n")
        return results


async def get_rag_statistics() -> Dict[str, Any]:
    """
    Get statistics about the RAG knowledge base.

    Returns:
        Dict with statistics
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Total count
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM internal_rag_embeddings"
            )

            # Count by section
            sections = await conn.fetch("""
                SELECT section_name, COUNT(*) as chunk_count
                FROM internal_rag_embeddings
                GROUP BY section_name
                ORDER BY chunk_count DESC
            """)

            # Average chunk size
            avg_size = await conn.fetchval("""
                SELECT AVG(LENGTH(chunk_text))
                FROM internal_rag_embeddings
            """)

            return {
                "total_chunks": total or 0,
                "sections": [dict(row) for row in sections],
                "average_chunk_size": int(avg_size) if avg_size else 0,
                "embedding_dimension": 768
            }

    except Exception as e:
        print(f"Failed to get RAG statistics: {e}")
        return {
            "total_chunks": 0,
            "sections": [],
            "average_chunk_size": 0,
            "embedding_dimension": 768
        }
