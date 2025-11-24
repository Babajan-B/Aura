"""
Text chunking service for splitting documents into manageable chunks.
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    text: str
    section_name: str
    chunk_index: int
    char_count: int


def extract_markdown_sections(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Extract sections from markdown text based on headers.

    Args:
        markdown_text: The full markdown document

    Returns:
        List of tuples (section_name, section_content)
    """
    sections = []
    current_section = "Introduction"
    current_content = []

    lines = markdown_text.split('\n')

    for line in lines:
        # Check if line is a header (starts with #)
        if line.strip().startswith('#'):
            # Save previous section if it has content
            if current_content:
                sections.append((
                    current_section,
                    '\n'.join(current_content).strip()
                ))

            # Extract new section name (remove # symbols and clean)
            current_section = re.sub(r'^#+\s*', '', line.strip())
            current_section = re.sub(r'[^a-zA-Z0-9\s]', '', current_section).strip()
            current_content = []
        else:
            current_content.append(line)

    # Add the last section
    if current_content:
        sections.append((
            current_section,
            '\n'.join(current_content).strip()
        ))

    return sections


def chunk_text(
    text: str,
    section_name: str,
    min_chunk_size: int = 300,
    max_chunk_size: int = 1500,
    overlap: int = 100
) -> List[TextChunk]:
    """
    Split text into chunks while respecting natural boundaries.

    Args:
        text: Text to chunk
        section_name: Name of the section this text belongs to
        min_chunk_size: Minimum characters per chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of TextChunk objects
    """
    chunks = []

    # Clean the text
    text = text.strip()

    # If text is smaller than max_chunk_size, return as single chunk
    if len(text) <= max_chunk_size:
        if len(text) >= min_chunk_size or len(text) > 0:
            chunks.append(TextChunk(
                text=text,
                section_name=section_name,
                chunk_index=0,
                char_count=len(text)
            ))
        return chunks

    # Split by paragraphs (double newlines)
    paragraphs = re.split(r'\n\n+', text)

    current_chunk = []
    current_size = 0
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para)

        # If adding this paragraph exceeds max size, save current chunk
        if current_size + para_size > max_chunk_size and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(TextChunk(
                text=chunk_text,
                section_name=section_name,
                chunk_index=chunk_index,
                char_count=len(chunk_text)
            ))

            # Keep last part for overlap
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-1]
                if len(overlap_text) > overlap:
                    overlap_text = overlap_text[-overlap:]
                current_chunk = [overlap_text]
                current_size = len(overlap_text)
            else:
                current_chunk = []
                current_size = 0

            chunk_index += 1

        # Add paragraph to current chunk
        current_chunk.append(para)
        current_size += para_size

    # Add remaining chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        if len(chunk_text) >= min_chunk_size or chunk_index == 0:
            chunks.append(TextChunk(
                text=chunk_text,
                section_name=section_name,
                chunk_index=chunk_index,
                char_count=len(chunk_text)
            ))

    return chunks


def chunk_markdown_document(
    markdown_text: str,
    min_chunk_size: int = 300,
    max_chunk_size: int = 1500,
    overlap: int = 100
) -> List[TextChunk]:
    """
    Chunk an entire markdown document by first splitting into sections,
    then chunking each section.

    Args:
        markdown_text: Full markdown document
        min_chunk_size: Minimum characters per chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap

    Returns:
        List of all chunks from all sections
    """
    all_chunks = []

    # Extract sections
    sections = extract_markdown_sections(markdown_text)

    print(f"Found {len(sections)} sections in document")

    # Chunk each section
    for section_name, section_content in sections:
        if not section_content.strip():
            continue

        section_chunks = chunk_text(
            text=section_content,
            section_name=section_name,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            overlap=overlap
        )

        print(f"  Section '{section_name}': {len(section_chunks)} chunks")

        all_chunks.extend(section_chunks)

    print(f"Total chunks created: {len(all_chunks)}")

    return all_chunks


def load_and_chunk_file(
    file_path: str,
    min_chunk_size: int = 300,
    max_chunk_size: int = 1500,
    overlap: int = 100
) -> List[TextChunk]:
    """
    Load a markdown file and chunk it.

    Args:
        file_path: Path to the markdown file
        min_chunk_size: Minimum characters per chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap

    Returns:
        List of TextChunk objects
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return chunk_markdown_document(
        content,
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
        overlap=overlap
    )
