"""
Smart Text Chunking Module

Intelligent text chunking that preserves semantic coherence while creating
focused embeddings for better semantic search.
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class SemanticChunk:
    """A semantically coherent chunk of text with metadata."""
    text: str
    source_paragraph: int
    chunk_index: int
    total_chunks_in_paragraph: int
    char_start: int
    char_end: int


class SmartChunker:
    """
    Intelligent text chunker that creates focused semantic units.
    Optimized for semantic search and accurate requirement matching.
    """

    def __init__(self, target_chunk_size: int = 400, overlap: int = 50):
        """
        Initialize the chunker.

        Args:
            target_chunk_size: Target size for chunks (in characters)
            overlap: Number of characters to overlap between chunks
        """
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using improved regex patterns.
        Handles common abbreviations and edge cases.
        """
        # Protect common abbreviations
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Ph\.D|e\.g|i\.e|vs|etc|Fig|al|et)\.\s+', r'\1<DOT> ', text)

        # Split on sentence boundaries (. ! ? followed by space and capital letter)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        # Restore abbreviations
        sentences = [s.replace('<DOT>', '.') for s in sentences]

        return [s.strip() for s in sentences if s.strip()]

    def chunk_paragraph(
        self,
        text: str,
        paragraph_number: int
    ) -> List[SemanticChunk]:
        """
        Chunk a single paragraph into semantically coherent pieces.

        For short paragraphs (<target_chunk_size), returns the whole paragraph.
        For long paragraphs, splits into sentences and groups them intelligently.

        Args:
            text: The paragraph text
            paragraph_number: The paragraph number for citation

        Returns:
            List of SemanticChunk objects
        """
        text = text.strip()

        if not text:
            return []

        # If paragraph is short enough, return as-is
        if len(text) <= self.target_chunk_size:
            return [SemanticChunk(
                text=text,
                source_paragraph=paragraph_number,
                chunk_index=0,
                total_chunks_in_paragraph=1,
                char_start=0,
                char_end=len(text)
            )]

        # Split into sentences
        sentences = self.split_into_sentences(text)

        if not sentences:
            return [SemanticChunk(
                text=text,
                source_paragraph=paragraph_number,
                chunk_index=0,
                total_chunks_in_paragraph=1,
                char_start=0,
                char_end=len(text)
            )]

        # Group sentences into chunks
        chunks = []
        current_sentences = []
        current_length = 0
        char_position = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence would exceed target and we have content
            if current_length + sentence_length > self.target_chunk_size and current_sentences:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_sentences)
                char_end = char_position + len(chunk_text)

                chunks.append(SemanticChunk(
                    text=chunk_text,
                    source_paragraph=paragraph_number,
                    chunk_index=len(chunks),
                    total_chunks_in_paragraph=0,  # Will update later
                    char_start=char_position,
                    char_end=char_end
                ))

                # Calculate overlap sentences
                overlap_sentences = []
                overlap_length = 0
                for sent in reversed(current_sentences):
                    if overlap_length + len(sent) <= self.overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_length += len(sent) + 1
                    else:
                        break

                # Start new chunk with overlap
                char_position = char_end - overlap_length if overlap_sentences else char_end
                current_sentences = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_sentences) + len(current_sentences) - 1
            else:
                # Add sentence to current chunk
                current_sentences.append(sentence)
                current_length += sentence_length + 1  # +1 for space

        # Add final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(SemanticChunk(
                text=chunk_text,
                source_paragraph=paragraph_number,
                chunk_index=len(chunks),
                total_chunks_in_paragraph=0,
                char_start=char_position,
                char_end=char_position + len(chunk_text)
            ))

        # Update total_chunks_in_paragraph for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks_in_paragraph = total_chunks

        return chunks

    def chunk_document(
        self,
        paragraphs: List[str]
    ) -> List[Dict]:
        """
        Chunk an entire document (list of paragraphs).

        Args:
            paragraphs: List of paragraph texts

        Returns:
            List of dictionaries with chunk info and metadata
        """
        all_chunks = []

        for para_num, para_text in enumerate(paragraphs, start=1):
            if not para_text.strip():
                continue

            para_chunks = self.chunk_paragraph(para_text, para_num)

            for chunk in para_chunks:
                all_chunks.append({
                    'text': chunk.text,
                    'paragraph_number': chunk.source_paragraph,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks_in_paragraph,
                    'is_split': chunk.total_chunks_in_paragraph > 1,
                    'citation': self._format_citation(chunk)
                })

        return all_chunks

    def _format_citation(self, chunk: SemanticChunk) -> str:
        """Format a citation string for a chunk."""
        if chunk.total_chunks_in_paragraph == 1:
            return f"¶{chunk.source_paragraph}"
        else:
            return f"¶{chunk.source_paragraph}.{chunk.index + 1}/{chunk.total_chunks_in_paragraph}"


def test_chunker():
    """Test the smart chunker with a sample paragraph."""

    # Sample long paragraph with FAIR
    sample_text = """
    The data streams collected via sensors will feed into a unified backend built on
    Python-based microservices (Flask/FastAPI) and a PostgreSQL database equipped with
    vector search capabilities (pgvector) for efficient semantic retrieval. A lightweight
    data lake using MinIO object storage will manage larger datasets such as images and
    sensor logs. The web dashboard developed in Streamlit or Dash with Plotly visualization
    will allow users to monitor conditions, track performance trends, and interact with
    AI-driven insights. For end users (e.g. farmers, extension agents, consultants), a
    responsive, multilingual web and mobile interface (built using React and Tailwind)
    will deliver a seamless experience through both dashboard and conversational chatbot modes.
    All components will be containerized using Docker and orchestrated via Kubernetes, enabling
    deployment on secure university servers or cloud environments such as AWS GovCloud. Data
    security and governance will follow FAIR (Findable, Accessible, Interoperable, Reusable)
    and CARE (Collective Benefit, Authority to Control, Responsibility, and Ethics) principles,
    with role-based access control and consent-based data sharing to protect farmers' information
    and ensure data privacy.
    """

    chunker = SmartChunker(target_chunk_size=400, overlap=50)
    chunks = chunker.chunk_paragraph(sample_text.strip(), paragraph_number=104)

    print(f"Original length: {len(sample_text.strip())} characters")
    print(f"Number of chunks: {len(chunks)}\n")

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}/{len(chunks)}:")
        print(f"  Length: {len(chunk.text)} chars")
        print(f"  Text: {chunk.text[:100]}...")
        print(f"  Has 'FAIR': {'FAIR' in chunk.text}")
        print()


if __name__ == "__main__":
    test_chunker()
