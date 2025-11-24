"""
Internal RAG retrieval service.
Retrieves relevant chunks from masterRAG.md embeddings based on queries.
"""
from typing import List, Dict
from app.db.database import get_db_pool


async def retrieve_internal_rag_rules(query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """
    Retrieve most relevant internal RAG chunks based on semantic similarity.
    
    Args:
        query_embedding: Query embedding vector
        top_k: Number of chunks to retrieve
        
    Returns:
        List of dicts with chunk_text, section_name, and similarity score
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Use cosine similarity for retrieval
        # pgvector uses <=> for cosine distance (1 - cosine similarity)
        rows = await conn.fetch(
            """
            SELECT 
                chunk_text,
                section_name,
                1 - (embedding_vector <=> $1::vector) as similarity
            FROM internal_rag_embeddings
            ORDER BY embedding_vector <=> $1::vector
            LIMIT $2
            """,
            query_embedding,
            top_k
        )
        
        return [
            {
                'chunk_text': row['chunk_text'],
                'section_name': row['section_name'],
                'similarity': float(row['similarity'])
            }
            for row in rows
        ]


async def get_rag_context_for_digest() -> str:
    """
    Get the complete RAG context needed for digest generation.
    Retrieves key rules from masterRAG.md without using embeddings.
    
    Returns:
        Formatted context string with all RAG rules
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Get all chunks from internal_rag_embeddings
        rows = await conn.fetch(
            """
            SELECT section_name, chunk_text
            FROM internal_rag_embeddings
            ORDER BY chunk_id
            """
        )
        
        # Format as context
        context_parts = []
        current_section = None
        
        for row in rows:
            section = row['section_name']
            text = row['chunk_text']
            
            if section != current_section:
                context_parts.append(f"\n## {section}")
                current_section = section
            
            context_parts.append(text)
        
        return "\n".join(context_parts)


async def get_rag_rules_for_summarization() -> str:
    """
    Get specific RAG rules for content summarization.
    
    Returns:
        Context string with summarization guidelines
    """
    context = await get_rag_context_for_digest()
    
    # The context includes all rules, but we'll format instructions
    summary_instructions = """
Based on the following internal guidelines, summarize and evaluate content:

{context}

Key requirements:
- Summaries: 2-4 sentences, factual only
- "Why this matters": Exactly 1 sentence linking to the user's goal
- No speculation, hype, or personal opinions
- Maintain professional, clear, neutral tone
    """.format(context=context)
    
    return summary_instructions
