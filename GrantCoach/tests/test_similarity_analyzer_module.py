import unittest
import os
import numpy as np
from similarity_analyzer import SimilarityAnalyzer

class TestSimilarityAnalyzerModule(unittest.TestCase):

    def setUp(self):
        # Paths for valid test files
        self.solicitation_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
        self.proposal_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Full_Proposal_TSU_Expanded.pdf"
        self.analyzer = SimilarityAnalyzer()

    def test_analyzer_initialization(self):
        """Test that SimilarityAnalyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer.model)
        self.assertEqual(self.analyzer.dimension, 384)  # all-MiniLM-L6-v2 dimension
        self.assertIsNone(self.analyzer.index)
        self.assertEqual(len(self.analyzer.chunk_metadata), 0)
        self.assertFalse(self.analyzer.is_built)

    def test_embedding_creation(self):
        """Test embedding creation from text chunks."""
        test_chunks = [
            {"text": "This is a test sentence about AI research.", "section": "test", "chunk_id": "test_0"},
            {"text": "Another sentence about machine learning.", "section": "test", "chunk_id": "test_1"}
        ]

        embeddings = self.analyzer.create_embeddings(test_chunks)
        self.assertEqual(embeddings.shape, (2, 384))
        self.assertTrue(isinstance(embeddings, np.ndarray))

    def test_index_building(self):
        """Test FAISS index building."""
        test_chunks = [
            {"text": "AI research proposal", "section": "test", "chunk_id": "test_0"},
            {"text": "Machine learning application", "section": "test", "chunk_id": "test_1"}
        ]

        self.analyzer.build_index(test_chunks, [])
        self.assertIsNotNone(self.analyzer.index)
        self.assertEqual(len(self.analyzer.chunk_metadata), 2)
        self.assertEqual(self.analyzer.index.ntotal, 2)
        self.assertTrue(self.analyzer.is_built)

    def test_similarity_search(self):
        """Test similarity search functionality."""
        test_chunks = [
            {"text": "AI research and machine learning", "section": "test", "chunk_id": "test_0"},
            {"text": "Budget analysis for grants", "section": "budget", "chunk_id": "budget_0"},
            {"text": "Educational impact assessment", "section": "impact", "chunk_id": "impact_0"}
        ]

        self.analyzer.build_index(test_chunks, [])

        # Search for AI-related content
        results = self.analyzer.similarity_search("artificial intelligence research", k=2)
        self.assertLessEqual(len(results), 2)
        self.assertTrue(all('chunk' in r and 'distance' in r and 'rank' in r for r in results))

        # AI-related chunk should rank higher
        ai_chunk_found = any('AI research' in r['chunk']['text'] for r in results)
        self.assertTrue(ai_chunk_found)

    def test_filtered_similarity_search(self):
        """Test similarity search with document type filtering."""
        solicitation_chunks = [
            {"text": "NSF funding opportunities", "section": "program", "chunk_id": "sol_0", "document_type": "solicitation"}
        ]
        proposal_chunks = [
            {"text": "Our research proposal", "section": "summary", "chunk_id": "prop_0", "document_type": "proposal"}
        ]

        self.analyzer.build_index(solicitation_chunks, proposal_chunks)

        # Search with solicitation filter
        results = self.analyzer.similarity_search("funding", k=5, filter_doc_type="solicitation")
        self.assertTrue(all(r['chunk']['document_type'] == 'solicitation' for r in results))

    def test_index_save_load(self):
        """Test saving and loading FAISS index."""
        test_chunks = [
            {"text": "Test content for saving", "section": "test", "chunk_id": "test_0"}
        ]

        self.analyzer.build_index(test_chunks, [])

        # Save index
        test_path = "data/test_index.faiss"
        self.analyzer.save_index(test_path)
        self.assertTrue(os.path.exists(test_path))

        # Load index in new instance
        new_analyzer = SimilarityAnalyzer()
        new_analyzer.load_index(test_path, test_chunks)

        self.assertIsNotNone(new_analyzer.index)
        self.assertEqual(len(new_analyzer.chunk_metadata), 1)
        self.assertTrue(new_analyzer.is_built)

        # Clean up
        if os.path.exists(test_path):
            os.remove(test_path)

    def test_get_index_statistics(self):
        """Test index statistics generation."""
        test_chunks = [
            {"text": "Test content", "section": "test", "chunk_id": "test_0", "document_type": "proposal"},
            {"text": "More test content", "section": "test", "chunk_id": "test_1", "document_type": "solicitation"}
        ]

        self.analyzer.build_index(test_chunks, [])
        stats = self.analyzer.get_index_statistics()

        self.assertEqual(stats["status"], "Built")
        self.assertEqual(stats["total_chunks"], 2)
        self.assertEqual(stats["embedding_dimension"], 384)
        self.assertIn("proposal", stats["document_types"])
        self.assertIn("solicitation", stats["document_types"])

    def test_full_integration_with_documents(self):
        """Only run if files exist"""
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        from document_processor import DocumentProcessor
        processor = DocumentProcessor()
        processed_data = processor.process_documents(self.solicitation_path, self.proposal_path)

        # Test full alignment analysis
        alignment_results = self.analyzer.analyze_proposal_solicitation_alignment(processed_data)

        # Verify structure
        self.assertIsInstance(alignment_results, dict)
        self.assertGreater(len(alignment_results), 0)

        # Verify each result has required fields
        for section, result in alignment_results.items():
            self.assertIn('score', result)
            self.assertIn('similar_solicitation_sections', result)
            self.assertIn('evidence_count', result)

        # Test gap analysis
        gaps = self.analyzer.find_gaps_in_proposal(processed_data)
        self.assertIsInstance(gaps, dict)

if __name__ == "__main__":
    unittest.main()