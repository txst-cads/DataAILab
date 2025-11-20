"""
AgriGrantCoach Semantic Analyzer Module

Uses FAISS vector search to find evidence of solicitation requirements
in the proposal narrative. Provides citation-backed alignment analysis.
"""

import numpy as np
import faiss
from typing import Dict, List, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
import json
from openai import OpenAI

from config import Config
from data_loader import DocumentChunk


@dataclass
class AlignmentMatch:
    """Represents a match between a requirement and narrative chunk."""
    requirement_id: str
    requirement_title: str
    matched_chunk: DocumentChunk
    similarity_score: float
    rank: int  # 1 = best match, 2 = second best, etc.

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'requirement_id': self.requirement_id,
            'requirement_title': self.requirement_title,
            'matched_text': self.matched_chunk.text[:200] + '...' if len(self.matched_chunk.text) > 200 else self.matched_chunk.text,
            'citation': self.matched_chunk.get_citation(),
            'similarity_score': float(self.similarity_score),
            'rank': self.rank
        }


class SemanticAnalyzer:
    """Semantic similarity analyzer using FAISS."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.model = None
        self.index = None
        self.chunks = []
        self.llm_client = OpenAI(api_key=config.GROQ_API_KEY)

    def _load_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            print(f"🔄 Loading embedding model: {self.config.EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(self.config.EMBEDDING_MODEL)
            print("✅ Model loaded")

    def build_index(self, chunks: List[DocumentChunk]) -> faiss.Index:
        """
        Build FAISS index from document chunks.

        Args:
            chunks: List of DocumentChunk objects to index

        Returns:
            FAISS index
        """
        self._load_model()

        print(f"\n🔨 Building FAISS index from {len(chunks)} chunks...")

        # Extract text from chunks
        texts = [chunk.text for chunk in chunks]
        self.chunks = chunks

        # Generate embeddings
        print("  → Generating embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product = cosine similarity for normalized vectors
        self.index.add(embeddings.astype('float32'))

        print(f"✅ FAISS index built with {self.index.ntotal} vectors")

        return self.index

    def search_requirement(self, requirement_text: str, top_k: int = None) -> List[AlignmentMatch]:
        """
        Search for chunks that match a requirement.

        Args:
            requirement_text: The requirement to search for
            top_k: Number of top matches to return (default: from config)

        Returns:
            List of AlignmentMatch objects
        """
        if self.index is None or self.model is None:
            raise RuntimeError("Must call build_index() before searching")

        if top_k is None:
            top_k = self.config.TOP_K_MATCHES

        # Encode the query
        query_embedding = self.model.encode([requirement_text], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Search
        similarities, indices = self.index.search(query_embedding.astype('float32'), top_k)

        # Build matches
        matches = []
        for rank, (idx, score) in enumerate(zip(indices[0], similarities[0]), start=1):
            # Skip if below threshold
            if score < self.config.SEMANTIC_SIMILARITY_THRESHOLD:
                continue

            matches.append(AlignmentMatch(
                requirement_id="",  # Will be set by caller
                requirement_title="",  # Will be set by caller
                matched_chunk=self.chunks[idx],
                similarity_score=float(score),
                rank=rank
            ))

        return matches

    def verify_with_llm(
        self,
        requirement_title: str,
        requirement_description: str,
        candidate_chunks: List[Tuple[DocumentChunk, float]]
    ) -> List[Tuple[DocumentChunk, float, str]]:
        """
        Use LLM to verify if candidate chunks actually address the requirement.

        Args:
            requirement_title: The requirement title
            requirement_description: Detailed requirement description
            candidate_chunks: List of (chunk, similarity_score) tuples

        Returns:
            List of (chunk, adjusted_score, evidence_quote) tuples for verified matches
        """
        if not candidate_chunks:
            return []

        # Prepare chunks for LLM evaluation
        chunks_text = "\n\n".join([
            f"[Chunk {i+1}] (Paragraph {chunk.paragraph_number}):\n{chunk.text}"
            for i, (chunk, _) in enumerate(candidate_chunks)
        ])

        prompt = f"""You are evaluating whether a grant proposal addresses a specific solicitation requirement.

**REQUIREMENT:**
Title: {requirement_title}
Description: {requirement_description}

**PROPOSAL EXCERPTS TO EVALUATE:**
{chunks_text}

**YOUR TASK:**
For each chunk, determine if it addresses the requirement. Return a JSON array with your evaluation.

For each chunk, provide:
1. "chunk_number": The chunk number (1, 2, 3, etc.)
2. "addresses_requirement": true or false
3. "confidence": "high", "medium", or "low"
4. "evidence_quote": A direct quote from the chunk (if addresses_requirement is true)
5. "explanation": Brief explanation of your judgment

**IMPORTANT GUIDELINES:**
- Be generous but honest - if the content relates to the requirement, mark it true
- Look for synonyms and paraphrases, not just exact matches
- Consider implicit as well as explicit mentions
- For FAIR data standards: Look for "FAIR", "Findable", "Accessible", "Interoperable", "Reusable", "CARE", "data management", "data sharing"
- For stakeholder needs: Look for mentions of farmers, producers, communities, stakeholder engagement, needs assessment
- For AFRI priorities: Look for food security, climate change, sustainable agriculture, nutrition, bioenergy, etc.

Return ONLY the JSON array, no other text."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.config.GROQ_ANALYSIS_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert grant evaluator. You carefully assess whether proposal text addresses solicitation requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content

            # Extract JSON if wrapped in code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            evaluations = json.loads(result_text)

            # Process results
            verified_matches = []
            for eval_item in evaluations:
                if eval_item.get("addresses_requirement", False):
                    chunk_idx = eval_item["chunk_number"] - 1
                    if 0 <= chunk_idx < len(candidate_chunks):
                        chunk, orig_score = candidate_chunks[chunk_idx]

                        # Adjust score based on LLM confidence
                        confidence = eval_item.get("confidence", "medium")
                        if confidence == "high":
                            adjusted_score = max(orig_score, 0.85)  # Boost high-confidence matches
                        elif confidence == "medium":
                            adjusted_score = max(orig_score, 0.70)
                        else:  # low
                            adjusted_score = max(orig_score, 0.60)

                        evidence_quote = eval_item.get("evidence_quote", chunk.text[:200])

                        verified_matches.append((chunk, adjusted_score, evidence_quote))

            return verified_matches

        except Exception as e:
            print(f"⚠️  LLM verification failed: {e}")
            # Fallback: return chunks with original scores if similarity was decent
            return [(chunk, score, chunk.text[:200]) for chunk, score in candidate_chunks if score >= 0.55]

    def analyze_proposal_alignment(
        self,
        rubric: Dict,
        narrative_chunks: List[DocumentChunk]
    ) -> Dict:
        """
        Analyze how well the proposal narrative aligns with solicitation requirements.

        Args:
            rubric: The extracted rubric from rubric_analyzer
            narrative_chunks: Chunks from the proposal narrative

        Returns:
            Dictionary with detailed alignment analysis
        """
        print("\n🎯 Analyzing proposal-solicitation alignment...")

        # Build index from narrative
        self.build_index(narrative_chunks)

        alignment_results = {
            'overall_score': 0.0,
            'requirement_matches': [],
            'strong_alignments': [],
            'weak_alignments': [],
            'gaps': [],
            'citations': []
        }

        requirements = rubric.get('requirements', [])

        print(f"\n🔍 Searching for evidence of {len(requirements)} requirements...\n")

        total_score = 0.0
        max_possible_score = 0.0

        for req in requirements:
            req_id = req['id']
            req_title = req['title']
            req_description = req['description']
            req_weight = req.get('weight', 'Medium')

            # Weight mapping
            weight_values = {'High': 1.0, 'Medium': 0.7, 'Low': 0.5}
            weight_value = weight_values.get(req_weight, 0.7)

            # Search for this requirement in the narrative
            search_query = f"{req_title}. {req_description}"

            # Get semantic candidates (top 10, even if below threshold)
            query_embedding = self.model.encode([search_query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            similarities, indices = self.index.search(query_embedding.astype('float32'), 10)

            # Prepare candidates for LLM verification
            candidates = [
                (self.chunks[idx], float(score))
                for idx, score in zip(indices[0], similarities[0])
                if score > 0.3  # Very low threshold, just to filter noise
            ]

            # Use LLM to verify which candidates actually address the requirement
            print(f"  🤖 Verifying '{req_title}' with LLM...")
            verified_matches = self.verify_with_llm(req_title, req_description, candidates)

            # Convert to AlignmentMatch objects
            matches = []
            for rank, (chunk, score, evidence) in enumerate(verified_matches, start=1):
                match = AlignmentMatch(
                    requirement_id=req_id,
                    requirement_title=req_title,
                    matched_chunk=chunk,
                    similarity_score=score,
                    rank=rank
                )
                matches.append(match)

            # Calculate alignment score for this requirement
            if matches:
                # Use best match score, weighted
                best_score = matches[0].similarity_score
                weighted_score = best_score * weight_value
                total_score += weighted_score
                max_possible_score += weight_value

                # Categorize alignment
                if best_score >= 0.8:
                    category = "strong"
                    alignment_results['strong_alignments'].append({
                        'requirement': req_title,
                        'score': float(best_score),
                        'evidence': matches[0].matched_chunk.text[:150] + '...',
                        'citation': matches[0].matched_chunk.get_citation()
                    })
                elif best_score >= self.config.SEMANTIC_SIMILARITY_THRESHOLD:
                    category = "moderate"
                else:
                    category = "weak"
                    alignment_results['weak_alignments'].append({
                        'requirement': req_title,
                        'score': float(best_score),
                        'weight': req_weight
                    })

                print(f"  {'✓' if category == 'strong' else '~' if category == 'moderate' else '⚠'} {req_title}: {best_score:.2f}")

            else:
                # No matches found
                max_possible_score += weight_value
                category = "gap"
                alignment_results['gaps'].append({
                    'requirement': req_title,
                    'category': req.get('category'),
                    'weight': req_weight,
                    'description': req_description
                })
                print(f"  ✗ {req_title}: No strong evidence found")

            # Store requirement match data
            alignment_results['requirement_matches'].append({
                'requirement_id': req_id,
                'requirement_title': req_title,
                'category': req.get('category'),
                'weight': req_weight,
                'matches': [m.to_dict() for m in matches],
                'best_score': float(matches[0].similarity_score) if matches else 0.0,
                'alignment_category': category
            })

        # Calculate overall score
        if max_possible_score > 0:
            alignment_results['overall_score'] = (total_score / max_possible_score) * 100

        print(f"\n📊 Overall Alignment Score: {alignment_results['overall_score']:.1f}%")
        print(f"   - Strong alignments: {len(alignment_results['strong_alignments'])}")
        print(f"   - Weak alignments: {len(alignment_results['weak_alignments'])}")
        print(f"   - Gaps: {len(alignment_results['gaps'])}")

        return alignment_results

    def save_alignment_analysis(self, alignment_results: Dict, output_path: Path = None):
        """Save alignment analysis to JSON."""
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / 'alignment_analysis.json'

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(alignment_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Alignment analysis saved to: {output_path}")

    def save_index(self, output_path: Path = None):
        """Save FAISS index to disk for reuse."""
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / 'narrative.faiss'

        if self.index is not None:
            faiss.write_index(self.index, str(output_path))
            print(f"💾 FAISS index saved to: {output_path}")


if __name__ == "__main__":
    # Test the semantic analyzer
    from data_loader import DataLoader
    from rubric_analyzer import RubricAnalyzer

    Config.validate()

    # Load data
    loader = DataLoader()
    data = loader.load_all()

    # Load rubric
    rubric_path = Config.OUTPUT_DIR / 'solicitation_rubric.json'
    if rubric_path.exists():
        with open(rubric_path, 'r') as f:
            rubric = json.load(f)
    else:
        # Generate rubric
        analyzer = RubricAnalyzer()
        rubric = analyzer.extract_rubric(data['solicitation']['text'])
        analyzer.save_rubric(rubric)

    # Analyze alignment
    semantic_analyzer = SemanticAnalyzer()
    alignment = semantic_analyzer.analyze_proposal_alignment(
        rubric,
        data['narrative']['chunks']
    )

    # Save results
    semantic_analyzer.save_alignment_analysis(alignment)
    semantic_analyzer.save_index()
