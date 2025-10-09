import unittest
import os
from document_processor import DocumentProcessor

class TestSectionParsing(unittest.TestCase):

    def setUp(self):
        # Paths for valid test files
        self.solicitation_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
        self.proposal_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Full_Proposal_TSU_Expanded.pdf"
        self.processor = DocumentProcessor()

    def test_chunk_text(self):
        # Test basic chunking functionality
        test_text = "This is a test sentence with multiple words. It should be split into chunks. Each chunk should have overlapping content for better context preservation."
        chunks = self.processor.chunk_text(test_text, chunk_size=10, overlap=3)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.split()) <= 10 for chunk in chunks))
        self.assertTrue(any("test sentence" in chunk for chunk in chunks))

    def test_extract_sections_solicitation(self):
        # Test section extraction from solicitation
        test_text = """
        Program Description
        This is the program description section with details about the funding opportunity.

        Eligibility Information
        Only eligible institutions may apply.

        Review Criteria
        Proposals will be evaluated based on merit.
        """
        sections = self.processor.extract_sections(test_text, "solicitation")

        self.assertIn("Program Description", sections)
        self.assertIn("Eligibility", sections)
        self.assertIn("Review Criteria", sections)

    def test_extract_sections_proposal(self):
        # Test section extraction from proposal
        test_text = """
        Project Summary
        This is the project summary section.

        Intellectual Merit
        The intellectual merit of this proposal is significant.

        Broader Impacts
        The broader impacts include educational benefits.
        """
        sections = self.processor.extract_sections(test_text, "proposal")

        self.assertIn("Project Summary", sections)
        self.assertIn("Intellectual Merit", sections)
        self.assertIn("Broader Impacts", sections)

    def test_full_processing(self):
        # Only run if files exist
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        processed_data = self.processor.process_documents(self.solicitation_path, self.proposal_path)

        # Verify structure
        self.assertIn("raw_texts", processed_data)
        self.assertIn("sections", processed_data)
        self.assertIn("chunks", processed_data)

        # Verify sections were found
        self.assertGreater(len(processed_data["sections"]["solicitation"]), 0)
        self.assertGreater(len(processed_data["sections"]["proposal"]), 0)

        # Verify chunks were created
        self.assertGreater(len(processed_data["chunks"]["solicitation"]), 0)
        self.assertGreater(len(processed_data["chunks"]["proposal"]), 0)

        # Verify chunk structure
        for chunk in processed_data["chunks"]["proposal"]:
            self.assertIn("text", chunk)
            self.assertIn("section", chunk)
            self.assertIn("chunk_id", chunk)

    def test_required_nsf_sections(self):
        # Only run if files exist
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        processed_data = self.processor.process_documents(self.solicitation_path, self.proposal_path)
        proposal_sections = processed_data["sections"]["proposal"]

        # Check for key NSF sections
        required_sections = ["Project Summary", "Intellectual Merit", "Broader Impacts"]
        for section in required_sections:
            self.assertIn(section, proposal_sections, f"Missing required NSF section: {section}")

if __name__ == "__main__":
    unittest.main()