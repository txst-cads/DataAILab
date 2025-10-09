"""
Document Processing Module

Handles PDF text extraction, section parsing, and chunking operations.
Follows Single Responsibility Principle by focusing only on document processing.
"""

import os
import re
import fitz  # PyMuPDF
from typing import List, Dict, Tuple


class DocumentProcessor:
    """
    Handles all document processing operations including PDF extraction,
    section parsing, and text chunking.
    """

    def __init__(self):
        self.section_patterns = {
            "solicitation": [
                (r'(?i)program\s*description', 'Program Description'),
                (r'(?i)eligibility\s*information', 'Eligibility'),
                (r'(?i)award\s*information', 'Award Information'),
                (r'(?i)review\s*criteria', 'Review Criteria'),
                (r'(?i)proposal\s*preparation', 'Proposal Preparation'),
                (r'(?i)deadlines', 'Deadlines'),
                (r'(?i)contact\s*information', 'Contact Information'),
            ],
            "proposal": [
                (r'(?i)project\s*summary', 'Project Summary'),
                (r'(?i)project\s*description', 'Project Description'),
                (r'(?i)intellectual\s*merit', 'Intellectual Merit'),
                (r'(?i)broader\s*impacts', 'Broader Impacts'),
                (r'(?i)biographical\s*sketches?', 'Biographical Sketches'),
                (r'(?i)budget\s*justification', 'Budget Justification'),
                (r'(?i)facilities\s*and\s*equipment', 'Facilities and Equipment'),
                (r'(?i)data\s*management', 'Data Management'),
                (r'(?i)mentoring\s*plan', 'Mentoring Plan'),
                (r'(?i)references\s*cited', 'References'),
            ]
        }

    def chunk_text(self, text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better processing.

        Args:
            text: Input text to chunk
            chunk_size: Maximum words per chunk
            overlap: Number of overlapping words between chunks

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

            if i + chunk_size >= len(words):
                break

        return chunks

    def extract_sections(self, text: str, doc_type: str) -> Dict[str, str]:
        """
        Extract sections from document text based on predefined patterns.

        Args:
            text: Full document text
            doc_type: Type of document ('solicitation' or 'proposal')

        Returns:
            Dictionary mapping section names to section text
        """
        sections = {}
        patterns = self.section_patterns.get(doc_type, [])

        # Find section boundaries
        section_positions = []
        for pattern, section_name in patterns:
            match = re.search(pattern, text)
            if match:
                section_positions.append((match.start(), section_name))

        # Sort by position
        section_positions.sort()

        # Extract sections
        for i, (start_pos, section_name) in enumerate(section_positions):
            end_pos = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(text)
            section_text = text[start_pos:end_pos].strip()

            if section_text:
                sections[section_name] = section_text

        # If no sections found, treat as single section
        if not sections:
            sections['Full Document'] = text

        return sections

    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract raw text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text as string

        Raises:
            ValueError: If PDF cannot be processed or no text extracted
        """
        if not pdf_path.endswith(".pdf"):
            raise ValueError(f"Invalid PDF path: {pdf_path}")

        if not os.path.exists(pdf_path):
            raise ValueError(f"File not found: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            raw_text = ""

            # Extract text from each page
            for page in doc:
                raw_text += page.get_text("text") + " "

            doc.close()

            # Basic whitespace cleaning
            raw_text = re.sub(r'\s+', ' ', raw_text.strip())

            if not raw_text:
                raise ValueError(f"No text extracted from {pdf_path}")

            return raw_text

        except Exception as e:
            raise ValueError(f"Failed to process PDF {pdf_path}: {str(e)}")

    def process_documents(self, solicitation_path: str, proposal_path: str) -> Dict:
        """
        Process both solicitation and proposal documents.

        Args:
            solicitation_path: Path to solicitation PDF
            proposal_path: Path to proposal PDF

        Returns:
            Dictionary containing processed data with raw texts, sections, and chunks
        """
        result = {
            "raw_texts": {"solicitation": "", "proposal": ""},
            "sections": {"solicitation": {}, "proposal": {}},
            "chunks": {"solicitation": [], "proposal": []},
            "metadata": {
                "solicitation_file": solicitation_path,
                "proposal_file": proposal_path,
                "processing_date": None  # Will be set by caller
            }
        }

        # Process each document
        for path, doc_type in [(solicitation_path, "solicitation"), (proposal_path, "proposal")]:
            # Extract raw text
            raw_text = self.extract_pdf_text(path)
            result["raw_texts"][doc_type] = raw_text

            # Extract sections
            sections = self.extract_sections(raw_text, doc_type)
            result["sections"][doc_type] = sections

            # Create chunks from each section
            all_chunks = []
            for section_name, section_text in sections.items():
                section_chunks = self.chunk_text(section_text)
                for i, chunk in enumerate(section_chunks):
                    all_chunks.append({
                        "text": chunk,
                        "section": section_name,
                        "chunk_id": f"{section_name}_{i}",
                        "document_type": doc_type
                    })

            result["chunks"][doc_type] = all_chunks

        return result

    def validate_nsf_requirements(self, proposal_sections: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate that required NSF sections are present in the proposal.

        Args:
            proposal_sections: Dictionary of proposal sections

        Returns:
            Dictionary indicating which required sections are present
        """
        required_sections = [
            "Project Summary",
            "Intellectual Merit",
            "Broader Impacts"
        ]

        validation_result = {}
        for section in required_sections:
            validation_result[section] = section in proposal_sections

        return validation_result

    def get_document_statistics(self, processed_data: Dict) -> Dict:
        """
        Generate statistics about the processed documents.

        Args:
            processed_data: Output from process_documents()

        Returns:
            Dictionary with document statistics
        """
        stats = {
            "solicitation": {
                "char_count": len(processed_data["raw_texts"]["solicitation"]),
                "section_count": len(processed_data["sections"]["solicitation"]),
                "chunk_count": len(processed_data["chunks"]["solicitation"])
            },
            "proposal": {
                "char_count": len(processed_data["raw_texts"]["proposal"]),
                "section_count": len(processed_data["sections"]["proposal"]),
                "chunk_count": len(processed_data["chunks"]["proposal"])
            },
            "total_chunks": (
                len(processed_data["chunks"]["solicitation"]) +
                len(processed_data["chunks"]["proposal"])
            )
        }

        return stats