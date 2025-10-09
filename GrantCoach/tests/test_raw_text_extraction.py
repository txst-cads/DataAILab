import unittest
import os
from grant_coach import extract_raw_text
from unittest.mock import patch, MagicMock

class TestRawTextExtraction(unittest.TestCase):

    def setUp(self):
        # Paths for valid test files
        self.solicitation_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
        self.proposal_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Full_Proposal_TSU_Expanded.pdf"

    def test_valid_input(self):
        # Only run if files exist
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")
        raw_texts = extract_raw_text(self.solicitation_path, self.proposal_path)
        self.assertIn("solicitation", raw_texts)
        self.assertIn("proposal", raw_texts)
        self.assertGreater(len(raw_texts["solicitation"]), 0)
        self.assertGreater(len(raw_texts["proposal"]), 0)
        self.assertRegex(raw_texts["solicitation"], r"NSF|nsf")
        self.assertRegex(raw_texts["solicitation"], r"ExpandAI|expandai")
        self.assertRegex(raw_texts["proposal"], r"Project Summary|PROJECT SUMMARY")
        
    def test_invalid_path(self):
        with self.assertRaises(ValueError) as cm:
            extract_raw_text("data/missing.pdf", self.proposal_path)
        self.assertIn("File not found", str(cm.exception))

    @patch("grant_coach.fitz.open")
    @patch("grant_coach.os.path.exists", return_value=True)
    def test_empty_text(self, mock_exists, mock_fitz_open):
        # Mock fitz.open to return a doc with pages that have empty text
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [MagicMock(get_text=MagicMock(return_value=""))]
        mock_fitz_open.return_value = mock_doc
        with self.assertRaises(ValueError) as cm:
            extract_raw_text(self.solicitation_path, self.proposal_path)
        self.assertIn("No text extracted", str(cm.exception))

if __name__ == "__main__":
    unittest.main()