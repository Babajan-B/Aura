"""
Embedding service for generating vector embeddings using Google Generative AI (Gemini).
"""
import google.generativeai as genai
from typing import List, Optional
import time
from app.core.config import get_settings
from app.db.database import log_system_event


# Global configuration flag
_gemini_configured = False


def configure_gemini():
    """
    Configure Gemini API with the API key.
    Only needs to be called once.
    """
    global _gemini_configured
    if not _gemini_configured:
        settings = get_settings()
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        genai.configure(api_key=settings.google_api_key)
        _gemini_configured = True


async def generate_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    """
    Generate embedding for a single text using Gemini.

    Args:
        text: Text to embed
        task_type: Type of embedding task
            - "retrieval_document": For documents to be retrieved
            - "retrieval_query": For search queries
            - "semantic_similarity": For similarity comparison
            - "classification": For classification tasks

    Returns:
        List of floats representing the embedding vector (768 dimensions)
    """
    try:
        configure_gemini()

        # Use the embedding model
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type=task_type
        )

        return result['embedding']

    except Exception as e:
        await log_system_event(
            "error",
            "rag",
            f"Failed to generate embedding: {str(e)}"
        )
        raise


async def generate_embeddings_batch(
    texts: List[str],
    task_type: str = "retrieval_document",
    batch_size: int = 100,
    delay: float = 1.0
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts with rate limiting.

    Args:
        texts: List of texts to embed
        task_type: Type of embedding task
        batch_size: Number of texts to process at once
        delay: Delay in seconds between batches

    Returns:
        List of embedding vectors
    """
    try:
        configure_gemini()

        all_embeddings = []
        total_texts = len(texts)

        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_texts + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")

            # Process batch
            for text in batch:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type=task_type
                )
                all_embeddings.append(result['embedding'])

            # Rate limiting delay
            if i + batch_size < total_texts:
                time.sleep(delay)

        await log_system_event(
            "info",
            "rag",
            f"Generated {len(all_embeddings)} embeddings successfully"
        )

        return all_embeddings

    except Exception as e:
        await log_system_event(
            "error",
            "rag",
            f"Failed to generate batch embeddings: {str(e)}"
        )
        raise


async def generate_goal_embedding(goal_text: str) -> List[float]:
    """
    Generate embedding specifically for a learning goal.

    Args:
        goal_text: The learning goal text

    Returns:
        Embedding vector for the goal
    """
    # Use retrieval_query task type for goals since they'll be used to query content
    return await generate_embedding(goal_text, task_type="retrieval_query")


async def generate_content_embedding(content_text: str) -> List[float]:
    """
    Generate embedding specifically for content items.

    Args:
        content_text: The content text (cleaned)

    Returns:
        Embedding vector for the content
    """
    # Use retrieval_document task type for content that will be retrieved
    return await generate_embedding(content_text, task_type="retrieval_document")


async def generate_internal_rag_embedding(chunk_text: str) -> List[float]:
    """
    Generate embedding for internal RAG knowledge chunks (masterRAG.md).

    Args:
        chunk_text: Text chunk from masterRAG.md

    Returns:
        Embedding vector for the chunk
    """
    # Use retrieval_document task type for internal knowledge
    return await generate_embedding(chunk_text, task_type="retrieval_document")


def get_embedding_dimension() -> int:
    """
    Get the dimension of Gemini embeddings.

    Returns:
        768 (dimension of models/embedding-001)
    """
    return 768
