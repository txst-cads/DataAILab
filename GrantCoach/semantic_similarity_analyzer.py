"""
Semantic Similarity Analyzer for Grant Coach
Uses FAISS and sentence embeddings for proposal-solicitation alignment
"""

import os
import json
import numpy as np
import faiss
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import re

logger = logging.getLogger(__name__)

@dataclass
class SemanticMatch:
    """Result of semantic similarity analysis"""
    text: str
    similarity_score: float
    source_type: str  # 'solicitation' or 'proposal'
    section: str
    position: int

@dataclass
class AlignmentAnalysis:
    """Comprehensive alignment analysis result"""
    overall_similarity: float
    solicitation_coverage: float
    proposal_relevance: float
    key_matches: List[SemanticMatch]
    gaps: List[str]
    recommendations: List[str]
    proposal_chunks: List[Dict[str, Any]] = None

class SemanticSimilarityAnalyzer:
    """FAISS-based semantic similarity analysis"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize semantic analyzer with sentence transformer model"""

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

        # FAISS index
        self.index = None
        self.indexed_chunks = []

        logger.info(f"Semantic Similarity Analyzer initialized with model: {model_name}")
        logger.info(f"Embedding dimension: {self.dimension}")

    def chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 100, save_chunks: bool = True) -> List[Dict[str, Any]]:
        """Enhanced document chunking with section-aware processing and efficient memory usage"""

        # Clean and preprocess text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\'\/\@\#\$\%\&\*\+\=\<\>\~\`\|\\]', '', text)

        # Split by sentences first, then group into chunks
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        chunks = []
        current_chunk = ""
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size <= chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_size = sentence_size

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Convert to chunk objects with metadata
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_objects.append({
                'id': f'chunk_{i}',
                'text': chunk,
                'length': len(chunk),
                'position': i,
                'section': self._detect_section_type(chunk)
            })

        logger.info(f"Created {len(chunk_objects)} chunks from document")

        # Save chunks to JSON for debugging
        if save_chunks:
            self._save_chunks_to_json(chunk_objects)

        return chunk_objects

    def _save_chunks_to_json(self, chunks: List[Dict[str, Any]]) -> None:
        """Save chunks to JSON file for debugging and verification"""
        import os
        from datetime import datetime

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/document_chunks_{timestamp}.json"

        # Prepare chunks data with section statistics
        chunks_data = {
            'timestamp': timestamp,
            'total_chunks': len(chunks),
            'section_stats': {},
            'chunks': chunks
        }

        # Calculate section statistics
        for chunk in chunks:
            section = chunk.get('section', 'unknown')
            if section not in chunks_data['section_stats']:
                chunks_data['section_stats'][section] = 0
            chunks_data['section_stats'][section] += 1

        # Save to JSON file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Chunks saved to {filename}")
            logger.info(f"Section distribution: {chunks_data['section_stats']}")
        except Exception as e:
            logger.error(f"Failed to save chunks to JSON: {e}")

    def _detect_section_type(self, text: str) -> str:
        """Enhanced section detection for grant proposals"""

        # Enhanced section keywords based on actual proposal structure
        section_keywords = {
            # Core proposal sections
            'objectives': ['objective', 'goal', 'aim', 'purpose', 'target', 'need and potential'],
            'capacity_building': ['capacity building', 'expanding', 'building plan', 'expanding curriculum', 'ai training'],
            'research_infrastructure': ['research infrastructure', 'ai research infrastructure', 'hpc training', 'ai infrastructure', 'computing infrastructure'],
            'broader_impacts': ['broader impacts', 'societal impact', 'community engagement', 'diversity impact'],
            'workforce_capacity': ['workforce capacity', 'workforce development', 'student development', 'career development'],
            'personnel': ['personnel', 'team', 'investigator', 'researcher', 'senior personnel'],
            'timeline': ['timeline', 'schedule', 'milestone', 'duration', 'period', 'activities'],

            # Technical sections
            'methodology': ['method', 'approach', 'technique', 'procedure', 'algorithm', 'pedagogy'],
            'outcomes': ['outcome', 'result', 'impact', 'deliverable', 'product', 'benefit'],
            'evaluation': ['evaluation', 'assessment', 'measure', 'metric', 'criteria'],
            'background': ['background', 'introduction', 'overview', 'summary'],
            'budget': ['budget', 'cost', 'funding', 'resource', 'financial'],
            'team': ['team', 'collaboration', 'partnership']
        }

        # Specific patterns for grant proposals
        grant_patterns = {
            'research_infrastructure': [
                r'B\. Expanding AI Research Infrastructure',
                r'Expanding AI Research Infrastructure',
                r'B1\. Launching a HPC training program',
                r'B2\. Providing continuous HPC support',
                r'B3\. Clear and measurable outcomes',
                r'HPC training program',
                r'AI infrastructure capacity',
                r'research infrastructure',
                r'AI research infrastructure',
                r'High-Performance Computing',
                r'HPC training',
                r'High-Performance Computing training program',
                r'on-site HPC and research lab infrastructure',
                r'computational infrastructure',
                r'HPC systems',
                r'research lab infrastructure',
                r'AI infrastructure',
                r'infrastructure resources',
                r'High-Performance Computing \(HPC\) training program',
                r'utilization of our on-site HPC and research lab infrastructure',
                r'HPC training programs targeted',
                r'hands-on experience with the systems'
            ],
            'capacity_building': [
                r'A\. Expanding Instructional and Curricular Capacity',
                r'Expanding.*Curricular Capacity',
                r'A1\. Launching inclusive AI training',
                r'A2\. Expanding the curriculum',
                r'A3\. Expanding the curriculum',
                r'A4\. Pedagogical approach',
                r'A5\. Clear and measurable outcomes',
                r'AI Summer School',
                r'AI methods modules',
                r'instructional capacity',
                'curricular capacity'
            ],
            'broader_impacts': [
                r'C\. Expanding.*Workforce Capacity',
                r'Expanding.*Workforce',
                r'Hispanic and low-income',
                r'first generation Latinas',
                r'workforce development',
                r'broader participation',
                r'3\. BROADER IMPACTS'
            ],
            'workforce_capacity': [
                r'C\. Expanding AI Workforce Capacity',
                r'D\. Expanding AI Workforce Capacity',
                r'Expanding AI Workforce Capacity',
                r'D1\. AI programming initiatives',
                r'D2\. AI programming initiatives',
                r'D3\. AI programming initiatives',
                r'Hispanic and low-income',
                r'first generation Latinas',
                r'student professional development',
                r'workforce capacity'
            ],
            'timeline': [
                r'Capacity Building Plan Timeline',
                r'E\. Capacity Building Plan Timeline',
                r'Table.*Activities.*Outcomes',
                r'timeline.*activities',
                r'major.*outcomes.*time'
            ]
        }

        text_lower = text.lower()

        # First check for specific grant patterns
        for section_type, patterns in grant_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return section_type

        # Then check general keywords
        for section_type, keywords in section_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return section_type

        return 'general'

    def create_embeddings(self, chunks: List[Dict[str, Any]]) -> np.ndarray:
        """Create embeddings for text chunks"""

        if not chunks:
            raise ValueError("No chunks provided for embedding creation")

        texts = [chunk['text'] for chunk in chunks]
        logger.info(f"Creating embeddings for {len(texts)} text chunks")

        # Optimize by batching for large documents
        batch_size = min(32, len(texts))
        logger.info(f"Using batch size: {batch_size}")

        try:
            # Process in batches for memory efficiency
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    batch_size=batch_size
                )
                all_embeddings.append(batch_embeddings)

            # Combine all batches
            embeddings = np.vstack(all_embeddings)
            logger.info(f"Created embeddings with shape: {embeddings.shape}")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise

    def build_faiss_index(self, solicitation_chunks: List[Dict[str, Any]]) -> None:
        """Build FAISS index from solicitation document chunks with caching optimization"""

        logger.info("Building FAISS index for solicitation document")

        # Check cache first
        cache_key = self._get_cache_key(solicitation_chunks)
        cached_index = self._load_cached_index(cache_key)

        if cached_index is not None:
            logger.info(f"Using cached FAISS index with {len(cached_index['chunks'])} chunks")
            self.index = cached_index['index']
            self.indexed_chunks = cached_index['chunks']
            return

        # Create embeddings with optimized batching
        embeddings = self.create_embeddings(solicitation_chunks)

        # Create FAISS index with optimal configuration
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype(np.float32))

        # Store chunk metadata
        self.indexed_chunks = solicitation_chunks

        # Cache the index for future use
        self._cache_index(cache_key, self.index, solicitation_chunks)

        logger.info(f"FAISS index built and cached with {len(self.indexed_chunks)} chunks")

    def _get_cache_key(self, chunks: List[Dict[str, Any]]) -> str:
        """Generate cache key based on chunk content"""
        import hashlib
        content_hash = hashlib.md5(''.join([chunk['text'] for chunk in chunks]).encode()).hexdigest()
        return f"faiss_index_{content_hash[:8]}"

    def _load_cached_index(self, cache_key: str) -> Optional[Dict]:
        """Load cached FAISS index if available"""
        import os
        try:
            index_file = f"data/{cache_key}.faiss"
            chunks_file = f"data/{cache_key}_chunks.json"

            if os.path.exists(index_file) and os.path.exists(chunks_file):
                # Load FAISS index
                index = faiss.read_index(index_file)
                # Load chunks
                with open(chunks_file, 'r') as f:
                    chunks = json.load(f)
                return {'index': index, 'chunks': chunks}
        except Exception as e:
            logger.warning(f"Failed to load cached index: {e}")
        return None

    def _cache_index(self, cache_key: str, index, chunks: List[Dict[str, Any]]) -> None:
        """Cache FAISS index and chunks for future use"""
        import os
        try:
            os.makedirs('data', exist_ok=True)
            index_file = f"data/{cache_key}.faiss"
            chunks_file = f"data/{cache_key}_chunks.json"

            # Save FAISS index
            faiss.write_index(index, index_file)
            # Save chunks
            with open(chunks_file, 'w') as f:
                json.dump(chunks, f)

            logger.info(f"Index cached to {index_file}")
        except Exception as e:
            logger.warning(f"Failed to cache index: {e}")

    def search_similar_content(self, query_text: str, k: int = 5) -> List[SemanticMatch]:
        """Search for semantically similar content in indexed solicitation"""

        if not self.index:
            raise ValueError("FAISS index not built. Call build_faiss_index() first.")

        # Create query embedding
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)

        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype(np.float32), k)

        # Convert to semantic matches
        matches = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.indexed_chunks) and idx >= 0:
                chunk = self.indexed_chunks[idx]

                # Convert L2 distance to similarity score (0-1)
                similarity_score = max(0, 1 - (distance / 2.0))  # Normalize to 0-1

                matches.append(SemanticMatch(
                    text=chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                    similarity_score=similarity_score,
                    source_type='solicitation',
                    section=chunk['section'],
                    position=chunk['position']
                ))

        return matches

    def analyze_proposal_alignment(self, proposal_text: str) -> AlignmentAnalysis:
        """Analyze proposal alignment with indexed solicitation"""

        if not self.index:
            raise ValueError("FAISS index not built. Call build_faiss_index() first.")

        # Chunk proposal document
        proposal_chunks = self.chunk_document(proposal_text, chunk_size=400, overlap=50)

        logger.info(f"Analyzing alignment for {len(proposal_chunks)} proposal chunks")

        all_matches = []
        chunk_scores = []

        for chunk in proposal_chunks:
            # Search for similar solicitation content
            matches = self.search_similar_content(chunk['text'], k=3)

            if matches:
                # Use the best match score for this chunk
                best_score = max(match.similarity_score for match in matches)
                chunk_scores.append(best_score)

                # Add to all matches if score is significant
                significant_matches = [m for m in matches if m.similarity_score > 0.3]
                all_matches.extend(significant_matches)

        # Calculate overall alignment metrics
        if chunk_scores:
            overall_similarity = np.mean(chunk_scores)
            solicitation_coverage = len([m for m in all_matches if m.similarity_score > 0.5]) / len(self.indexed_chunks)
            proposal_relevance = len([s for s in chunk_scores if s > 0.3]) / len(chunk_scores)
        else:
            overall_similarity = 0.0
            solicitation_coverage = 0.0
            proposal_relevance = 0.0

        # Sort matches by similarity score
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)

        # Identify gaps and recommendations
        gaps = self._identify_gaps(proposal_chunks, all_matches)
        recommendations = self._generate_recommendations(overall_similarity, all_matches, gaps)

        return AlignmentAnalysis(
            overall_similarity=overall_similarity,
            solicitation_coverage=solicitation_coverage,
            proposal_relevance=proposal_relevance,
            key_matches=all_matches[:10],  # Top 10 matches
            gaps=gaps,
            recommendations=recommendations,
            proposal_chunks=proposal_chunks
        )

    def _identify_gaps(self, proposal_chunks: List[Dict], matches: List[SemanticMatch]) -> List[str]:
        """Identify gaps in proposal coverage"""

        gaps = []

        # Check which solicitation sections are poorly covered
        section_coverage = {}
        for match in matches:
            section = match.section
            if section not in section_coverage:
                section_coverage[section] = []
            section_coverage[section].append(match.similarity_score)

        for section, scores in section_coverage.items():
            avg_score = np.mean(scores) if scores else 0
            if avg_score < 0.4:
                gaps.append(f"Limited coverage of {section} requirements")

        # Check for completely uncovered solicitation content
        covered_sections = set(match.section for match in matches)
        all_sections = set(chunk['section'] for chunk in self.indexed_chunks)

        uncovered_sections = all_sections - covered_sections
        if uncovered_sections:
            gaps.append(f"Missing content related to: {', '.join(list(uncovered_sections)[:3])}")

        return gaps[:5]  # Top 5 gaps

    def _generate_recommendations(self, overall_score: float, matches: List[SemanticMatch], gaps: List[str]) -> List[str]:
        """Generate recommendations for proposal improvement"""

        recommendations = []

        # Overall score recommendations
        if overall_score < 0.5:
            recommendations.append("Significant revision needed - consider major restructuring")
        elif overall_score < 0.7:
            recommendations.append("Moderate improvements needed - strengthen key sections")
        else:
            recommendations.append("Minor refinements suggested - address specific gaps")

        # Content-specific recommendations
        if gaps:
            recommendations.append(f"Address gaps: {gaps[0]}")

        # Match quality recommendations
        high_quality_matches = [m for m in matches if m.similarity_score > 0.7]
        if len(high_quality_matches) < 3:
            recommendations.append("Strengthen alignment with solicitation requirements")

        # Section-specific recommendations
        section_scores = {}
        for match in matches:
            section = match.section
            if section not in section_scores:
                section_scores[section] = []
            section_scores[section].append(match.similarity_score)

        for section, scores in section_scores.items():
            avg_score = np.mean(scores)
            if avg_score < 0.5 and section != 'general':
                recommendations.append(f"Improve {section} section to better address solicitation requirements")

        return recommendations[:5]  # Top 5 recommendations

    def save_index(self, filepath: str) -> None:
        """Save FAISS index to disk"""
        if not self.index:
            raise ValueError("No index to save")

        faiss.write_index(self.index, filepath)
        logger.info(f"FAISS index saved to {filepath}")

    def load_index(self, filepath: str, chunks: List[Dict[str, Any]]) -> None:
        """Load FAISS index from disk"""
        self.index = faiss.read_index(filepath)
        self.indexed_chunks = chunks
        logger.info(f"FAISS index loaded from {filepath} with {len(chunks)} chunks")

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "indexed_chunks": len(self.indexed_chunks),
            "embedding_dimension": self.dimension,
            "index_type": "IndexFlatL2",
            "model_name": self.model_name
        }

if __name__ == "__main__":
    # Test the semantic similarity analyzer
    analyzer = SemanticSimilarityAnalyzer()

    # Test documents
    solicitation_text = """
    The NSF ExpandAI program aims to build AI capacity at institutions.
    Key requirements include AI education programs, computational infrastructure,
    research capability enhancement, and broadening participation in AI.
    Institutions must demonstrate strong technical approaches and team expertise.
    """

    proposal_text = """
    Our project will expand AI capabilities through HPC training programs.
    We will develop AI curriculum modules and enhance research infrastructure.
    The team includes experts in machine learning and high-performance computing.
    We focus on educational impact and technical advancement.
    """

    print("🚀 Testing Semantic Similarity Analyzer...")

    # Test document chunking
    print("\n📋 Testing document chunking...")
    solicitation_chunks = analyzer.chunk_document(solicitation_text)
    proposal_chunks = analyzer.chunk_document(proposal_text)

    print(f"Solicitation: {len(solicitation_chunks)} chunks")
    print(f"Proposal: {len(proposal_chunks)} chunks")

    # Test embedding creation
    print("\n🔤 Testing embedding creation...")
    embeddings = analyzer.create_embeddings(solicitation_chunks)
    print(f"Embeddings shape: {embeddings.shape}")

    # Test FAISS index building
    print("\n🏗️ Testing FAISS index building...")
    analyzer.build_faiss_index(solicitation_chunks)
    print(f"Index built with {len(analyzer.indexed_chunks)} chunks")

    # Test similarity search
    print("\n🔍 Testing similarity search...")
    query = "AI education and training programs"
    matches = analyzer.search_similar_content(query, k=3)

    print(f"Query: {query}")
    for i, match in enumerate(matches):
        print(f"  {i+1}. Score: {match.similarity_score:.3f} - {match.text}")

    # Test alignment analysis
    print("\n🎯 Testing alignment analysis...")
    alignment = analyzer.analyze_proposal_alignment(proposal_text)

    print(f"Overall similarity: {alignment.overall_similarity:.3f}")
    print(f"Solicitation coverage: {alignment.solicitation_coverage:.3f}")
    print(f"Proposal relevance: {alignment.proposal_relevance:.3f}")
    print(f"Recommendations: {alignment.recommendations}")

    # Test index stats
    print("\n📊 Index stats:")
    stats = analyzer.get_index_stats()
    print(json.dumps(stats, indent=2))