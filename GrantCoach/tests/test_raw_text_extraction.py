import unittest
import os
from document_processor import DocumentProcessor
from unittest.mock import patch, MagicMock

class TestRawTextExtraction(unittest.TestCase):

    def setUp(self):
        # Paths for valid test files
        self.solicitation_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
        self.proposal_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Full_Proposal_TSU_Expanded.pdf"
        self.processor = DocumentProcessor()

    def test_valid_input(self):
        # Only run if files exist
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        processed_data = self.processor.process_documents(self.solicitation_path, self.proposal_path)
        raw_texts = processed_data["raw_texts"]

        self.assertIn("solicitation", raw_texts)
        self.assertIn("proposal", raw_texts)
        self.assertGreater(len(raw_texts["solicitation"]), 0)
        self.assertGreater(len(raw_texts["proposal"]), 0)
        self.assertRegex(raw_texts["solicitation"], r"NSF|nsf")
        self.assertRegex(raw_texts["solicitation"], r"ExpandAI|expandai")
        self.assertRegex(raw_texts["proposal"], r"Project Summary|PROJECT SUMMARY")

    def test_invalid_path(self):
        with self.assertRaises(ValueError) as cm:
            self.processor.process_documents("data/missing.pdf", self.proposal_path)
        self.assertIn("File not found", str(cm.exception))

    def test_chunking_functionality(self):
        """Test text chunking functionality."""
        test_text = "This is a test sentence with multiple words. It should be split into chunks. Each chunk should have overlapping content for better context preservation."
        chunks = self.processor.chunk_text(test_text, chunk_size=10, overlap=3)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.split()) <= 10 for chunk in chunks))
        self.assertTrue(any("test sentence" in chunk for chunk in chunks))

    def test_section_extraction(self):
        """Test section extraction from documents."""
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

    @patch("document_processor.fitz.open")
    @patch("document_processor.os.path.exists", return_value=True)
    def test_empty_text(self, mock_exists, mock_fitz_open):
        # Mock fitz.open to return a doc with pages that have empty text
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [MagicMock(get_text=MagicMock(return_value=""))]
        mock_fitz_open.return_value = mock_doc

        with self.assertRaises(ValueError) as cm:
            self.processor.extract_pdf_text(self.solicitation_path)
        self.assertIn("No text extracted", str(cm.exception))

    def test_nsf_validation(self):
        """Test NSF requirement validation."""
        # Only run if files exist
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        processed_data = self.processor.process_documents(self.solicitation_path, self.proposal_path)
        validation = self.processor.validate_nsf_requirements(processed_data["sections"]["proposal"])

        # Check that validation returns a dictionary
        self.assertIsInstance(validation, dict)
        self.assertIn("Project Summary", validation)
        self.assertIn("Intellectual Merit", validation)
        self.assertIn("Broader Impacts", validation)

if __name__ == "__main__":
    unittest.main()