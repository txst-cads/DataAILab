"""
Similarity Analyzer Module

Handles FAISS indexing, embeddings, and similarity analysis operations.
Follows Single Responsibility Principle by focusing only on similarity analysis.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
import os


class SimilarityAnalyzer:
    """
    Handles all similarity analysis operations including embeddings,
    FAISS indexing, and proposal-solicitation alignment analysis.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the similarity analyzer with Sentence-BERT model.

        Args:
            model_name: Name of the Sentence-BERT model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.chunk_metadata = []
        self.is_built = False

    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Create embeddings for text chunks.

        Args:
            chunks: List of chunk dictionaries with 'text' field

        Returns:
            Numpy array of embeddings
        """
        if not chunks:
            raise ValueError("No chunks provided for embedding creation")

        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings

    def build_index(self, solicitation_chunks: List[Dict], proposal_chunks: List[Dict]):
        """
        Build FAISS index from document chunks.

        Args:
            solicitation_chunks: List of solicitation chunk dictionaries
            proposal_chunks: List of proposal chunk dictionaries
        """
        # Combine all chunks
        all_chunks = solicitation_chunks + proposal_chunks

        if not all_chunks:
            raise ValueError("No chunks provided for index building")

        # Create embeddings
        embeddings = self.create_embeddings(all_chunks)

        # Store metadata
        self.chunk_metadata = all_chunks

        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype(np.float32))
        self.is_built = True

    def similarity_search(self, query_text: str, k: int = 5,
                        filter_doc_type: Optional[str] = None) -> List[Dict]:
        """
        Find most similar chunks to query text.

        Args:
            query_text: Text to search for
            k: Number of results to return
            filter_doc_type: Optional filter for document type ('solicitation' or 'proposal')

        Returns:
            List of similarity results with chunk metadata and scores
        """
        if not self.is_built:
            raise ValueError("Index not built. Call build_index() first.")

        # Create query embedding
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)

        # Search index
        distances, indices = self.index.search(query_embedding.astype(np.float32), k)

        # Return results with metadata
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.chunk_metadata):
                chunk = self.chunk_metadata[idx]

                # Apply document type filter if specified
                if filter_doc_type and chunk.get('document_type') != filter_doc_type:
                    continue

                # Convert L2 distance to similarity score (0-1)
                similarity_score = max(0, 1 - distance)

                result = {
                    'chunk': chunk,
                    'distance': float(distance),
                    'similarity_score': similarity_score,
                    'rank': i + 1
                }
                results.append(result)

        return results

    def analyze_section_alignment(self, section_text: str,
                                target_sections: List[str] = None) -> Dict:
        """
        Analyze alignment between a section and target document sections.

        Args:
            section_text: Text of the section to analyze
            target_sections: List of target section names to focus on

        Returns:
            Dictionary with alignment analysis results
        """
        if not self.is_built:
            raise ValueError("Index not built. Call build_index() first.")

        # Find similar content
        similar_chunks = self.similarity_search(section_text, k=10)

        # Filter by target sections if specified
        if target_sections:
            similar_chunks = [
                c for c in similar_chunks
                if c['chunk']['section'] in target_sections
            ]

        # Group by section
        section_scores = {}
        for chunk_result in similar_chunks:
            section_name = chunk_result['chunk']['section']
            if section_name not in section_scores:
                section_scores[section_name] = []
            section_scores[section_name].append(chunk_result['similarity_score'])

        # Calculate average scores per section
        alignment_by_section = {}
        for section, scores in section_scores.items():
            alignment_by_section[section] = {
                'average_similarity': np.mean(scores),
                'max_similarity': np.max(scores),
                'evidence_count': len(scores),
                'top_evidence': [
                    c['chunk']['text'][:100] + '...'
                    for c in similar_chunks[:2]
                    if c['chunk']['section'] == section
                ]
            }

        # Calculate overall alignment score
        if alignment_by_section:
            overall_score = np.mean([
                result['similarity_score'] for result in similar_chunks
            ])
        else:
            overall_score = 0.0

        return {
            'overall_alignment': overall_score,
            'section_alignment': alignment_by_section,
            'total_similar_chunks': len(similar_chunks)
        }

    def analyze_proposal_solicitation_alignment(self, processed_data: Dict) -> Dict:
        """
        Analyze alignment between proposal and solicitation sections.

        Args:
            processed_data: Processed document data from DocumentProcessor

        Returns:
            Dictionary with alignment analysis for each proposal section
        """
        # Build index if not already built
        if not self.is_built:
            self.build_index(
                processed_data['chunks']['solicitation'],
                processed_data['chunks']['proposal']
            )

        alignment_results = {}

        # Get solicitation section names for targeting
        solicitation_sections = list(processed_data['sections']['solicitation'].keys())

        # Analyze each proposal section against solicitation
        for section_name, section_text in processed_data['sections']['proposal'].items():
            if section_name in ['References', 'Biographical Sketches']:
                continue  # Skip these sections for alignment analysis

            # Analyze alignment with solicitation
            alignment = self.analyze_section_alignment(
                section_text,
                target_sections=solicitation_sections
            )

            alignment_results[section_name] = {
                'score': alignment['overall_alignment'],
                'similar_solicitation_sections': list(alignment['section_alignment'].keys()),
                'alignment_details': alignment['section_alignment'],
                'evidence_count': alignment['total_similar_chunks']
            }

        return alignment_results

    def find_gaps_in_proposal(self, processed_data: Dict) -> Dict:
        """
        Identify gaps in proposal coverage compared to solicitation requirements.

        Args:
            processed_data: Processed document data from DocumentProcessor

        Returns:
            Dictionary with identified gaps and recommendations
        """
        if not self.is_built:
            self.build_index(
                processed_data['chunks']['solicitation'],
                processed_data['chunks']['proposal']
            )

        gaps = {}

        # Analyze each solicitation section for coverage in proposal
        for sol_section, sol_text in processed_data['sections']['solicitation'].items():
            # Search for similar content in proposal
            similar_chunks = self.similarity_search(
                sol_text,
                k=5,
                filter_doc_type='proposal'
            )

            # Calculate coverage score
            if similar_chunks:
                coverage_score = np.mean([c['similarity_score'] for c in similar_chunks])
            else:
                coverage_score = 0.0

            # Identify gap if coverage is low
            if coverage_score < 0.3:  # Threshold for gap detection
                gaps[sol_section] = {
                    'coverage_score': coverage_score,
                    'gap_severity': 'high' if coverage_score < 0.1 else 'medium',
                    'similar_proposal_content': [
                        c['chunk']['section'] for c in similar_chunks[:3]
                    ],
                    'recommendation': self._generate_gap_recommendation(
                        sol_section, coverage_score, similar_chunks
                    )
                }

        return gaps

    def _generate_gap_recommendation(self, section_name: str, coverage_score: float,
                                   similar_chunks: List[Dict]) -> str:
        """
        Generate recommendation for addressing a coverage gap.

        Args:
            section_name: Name of the solicitation section with gap
            coverage_score: Current coverage score
            similar_chunks: Similar content found in proposal

        Returns:
            Recommendation text
        """
        if coverage_score < 0.1:
            return f"Significant gap in addressing {section_name} requirements. Consider adding specific content that directly addresses this solicitation section."
        elif coverage_score < 0.3:
            return f"Partial coverage of {section_name}. Enhance existing content in related proposal sections to better address solicitation requirements."
        else:
            return f"Good coverage of {section_name}. Minor enhancements may improve alignment."

    def save_index(self, filepath: str):
        """
        Save FAISS index to disk.

        Args:
            filepath: Path to save the index
        """
        if not self.is_built:
            raise ValueError("No index to save. Build index first.")

        faiss.write_index(self.index, filepath)

    def load_index(self, filepath: str, metadata: List[Dict]):
        """
        Load FAISS index from disk.

        Args:
            filepath: Path to the saved index
            metadata: Chunk metadata corresponding to the index
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found: {filepath}")

        self.index = faiss.read_index(filepath)
        self.chunk_metadata = metadata
        self.is_built = True

    def get_index_statistics(self) -> Dict:
        """
        Get statistics about the current index.

        Returns:
            Dictionary with index statistics
        """
        if not self.is_built:
            return {"status": "No index built"}

        return {
            "status": "Built",
            "model_name": self.model_name,
            "embedding_dimension": self.dimension,
            "total_chunks": len(self.chunk_metadata),
            "index_type": "FlatL2",
            "document_types": list(set(c.get('document_type', 'unknown') for c in self.chunk_metadata)),
            "sections_represented": list(set(c.get('section', 'unknown') for c in self.chunk_metadata))
        }