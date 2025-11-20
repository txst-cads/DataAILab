"""
AgriGrantCoach Data Loader Module

Robust document parsers for PDF and DOCX files with metadata tracking
for accurate citation and evidence-based analysis.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import fitz  # PyMuPDF
from docx import Document
import re

from config import Config
from smart_chunker import SmartChunker


@dataclass
class DocumentChunk:
    """Represents a chunk of text with source metadata for citation."""
    text: str
    source_file: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    chunk_id: str = ""

    def get_citation(self) -> str:
        """Generate a citation string for this chunk."""
        if self.page_number is not None:
            return f"{self.source_file}:p{self.page_number}"
        elif self.paragraph_number is not None:
            return f"{self.source_file}:¶{self.paragraph_number}"
        return self.source_file


@dataclass
class PersonnelData:
    """Structured data for a single team member."""
    name: str
    biosketch_text: str
    cps_text: str
    biosketch_chunks: List[DocumentChunk]
    cps_chunks: List[DocumentChunk]


class PDFLoader:
    """Load and parse PDF documents with page-level tracking."""

    @staticmethod
    def load(pdf_path: Path) -> Tuple[str, List[DocumentChunk]]:
        """
        Load a PDF file and extract text with page metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (full_text, list of DocumentChunk objects)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        full_text = []
        chunks = []

        try:
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text()

                # Clean the text
                page_text = PDFLoader._clean_text(page_text)

                if page_text.strip():
                    full_text.append(page_text)

                    # Create chunk with metadata
                    chunk = DocumentChunk(
                        text=page_text,
                        source_file=pdf_path.name,
                        page_number=page_num,
                        chunk_id=f"{pdf_path.stem}_page_{page_num}"
                    )
                    chunks.append(chunk)

            doc.close()

        except Exception as e:
            raise RuntimeError(f"Error loading PDF {pdf_path}: {e}")

        return "\n\n".join(full_text), chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text by removing excessive whitespace."""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()


class DOCXLoader:
    """Load and parse DOCX documents with paragraph-level tracking."""

    @staticmethod
    def load(docx_path: Path, use_smart_chunking: bool = True) -> Tuple[str, List[DocumentChunk]]:
        """
        Load a DOCX file and extract text with intelligent chunking.

        Args:
            docx_path: Path to the DOCX file
            use_smart_chunking: If True, uses intelligent semantic chunking for long paragraphs

        Returns:
            Tuple of (full_text, list of DocumentChunk objects)
        """
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX not found: {docx_path}")

        full_text = []
        chunks = []

        try:
            doc = Document(docx_path)

            # Extract paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                para_text = paragraph.text.strip()
                if para_text:
                    paragraphs.append(para_text)
                    full_text.append(para_text)

            if use_smart_chunking:
                # Use smart chunker for better semantic matching
                chunker = SmartChunker(
                    target_chunk_size=int(Config.CHUNK_SIZE),
                    overlap=int(Config.CHUNK_OVERLAP)
                )

                for para_num, para_text in enumerate(paragraphs, start=1):
                    # Get semantic chunks for this paragraph
                    para_chunks = chunker.chunk_paragraph(para_text, para_num)

                    for semantic_chunk in para_chunks:
                        # Format chunk ID to show if paragraph was split
                        if semantic_chunk.total_chunks_in_paragraph > 1:
                            chunk_id = f"{docx_path.stem}_para_{para_num}_chunk_{semantic_chunk.chunk_index + 1}of{semantic_chunk.total_chunks_in_paragraph}"
                        else:
                            chunk_id = f"{docx_path.stem}_para_{para_num}"

                        # Create DocumentChunk
                        chunk = DocumentChunk(
                            text=semantic_chunk.text,
                            source_file=docx_path.name,
                            paragraph_number=para_num,
                            chunk_id=chunk_id
                        )
                        chunks.append(chunk)
            else:
                # Simple paragraph-based chunking (legacy)
                for para_num, para_text in enumerate(paragraphs, start=1):
                    chunk = DocumentChunk(
                        text=para_text,
                        source_file=docx_path.name,
                        paragraph_number=para_num,
                        chunk_id=f"{docx_path.stem}_para_{para_num}"
                    )
                    chunks.append(chunk)

        except Exception as e:
            raise RuntimeError(f"Error loading DOCX {docx_path}: {e}")

        return "\n\n".join(full_text), chunks

    @staticmethod
    def load_with_structure(docx_path: Path) -> Dict:
        """
        Load DOCX with additional structure (headings, tables, etc.).
        Useful for biosketches which have specific sections.

        Returns:
            Dict with structured content
        """
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX not found: {docx_path}")

        doc = Document(docx_path)

        structure = {
            'paragraphs': [],
            'tables': [],
            'headings': []
        }

        # Extract paragraphs with style information
        for para in doc.paragraphs:
            if para.text.strip():
                structure['paragraphs'].append({
                    'text': para.text.strip(),
                    'style': para.style.name if para.style else 'Normal'
                })

                # Identify headings
                if 'heading' in para.style.name.lower():
                    structure['headings'].append(para.text.strip())

        # Extract tables (common in biosketches for publications)
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            structure['tables'].append(table_data)

        return structure


class DataLoader:
    """Main data loader orchestrator for all document types."""

    def __init__(self, config: Config = Config):
        self.config = config

    def load_solicitation(self) -> Tuple[str, List[DocumentChunk]]:
        """
        Load the USDA AFRI solicitation PDF.

        Returns:
            Tuple of (full_text, chunks with page metadata)
        """
        solicitation_path = self.config.get_solicitation_path()
        print(f"📄 Loading solicitation: {solicitation_path.name}")
        return PDFLoader.load(solicitation_path)

    def load_narrative(self) -> Tuple[str, List[DocumentChunk]]:
        """
        Load the project narrative DOCX.

        Returns:
            Tuple of (full_text, chunks with paragraph metadata)
        """
        narrative_path = self.config.get_narrative_path()
        print(f"📝 Loading narrative: {narrative_path.name}")
        return DOCXLoader.load(narrative_path)

    def load_personnel_docs(self) -> Dict[str, PersonnelData]:
        """
        Load all biosketches and CPS documents for team members.

        Returns:
            Dictionary mapping personnel name to PersonnelData object
        """
        personnel_data = {}

        print("\n👥 Loading personnel documents...")

        for name in self.config.PERSONNEL_NAMES:
            # Find biosketch
            bio_pattern = f"*{name}*"
            bio_files = list(self.config.BIOSKETCHES_DIR.glob(bio_pattern))

            # Find CPS
            cps_files = list(self.config.CPS_DIR.glob(bio_pattern))

            if not bio_files:
                print(f"  ⚠️  Warning: No biosketch found for {name}")
                continue

            if not cps_files:
                print(f"  ⚠️  Warning: No CPS found for {name}")
                continue

            # Load documents
            bio_text, bio_chunks = DOCXLoader.load(bio_files[0])
            cps_text, cps_chunks = DOCXLoader.load(cps_files[0])

            personnel_data[name] = PersonnelData(
                name=name,
                biosketch_text=bio_text,
                cps_text=cps_text,
                biosketch_chunks=bio_chunks,
                cps_chunks=cps_chunks
            )

            print(f"  ✓ {name}: Bio ({len(bio_chunks)} chunks), CPS ({len(cps_chunks)} chunks)")

        return personnel_data

    def load_all(self) -> Dict:
        """
        Load all documents for the analysis pipeline.

        Returns:
            Dictionary containing all loaded documents and metadata
        """
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║          Loading AgriGrantCoach Documents                   ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        # Load solicitation
        solicitation_text, solicitation_chunks = self.load_solicitation()

        # Load narrative
        narrative_text, narrative_chunks = self.load_narrative()

        # Load personnel
        personnel_data = self.load_personnel_docs()

        # Compile all data
        all_data = {
            'solicitation': {
                'text': solicitation_text,
                'chunks': solicitation_chunks,
                'num_pages': len(solicitation_chunks)
            },
            'narrative': {
                'text': narrative_text,
                'chunks': narrative_chunks,
                'num_paragraphs': len(narrative_chunks)
            },
            'personnel': {
                name: {
                    'name': data.name,
                    'biosketch_text': data.biosketch_text,
                    'cps_text': data.cps_text,
                    'biosketch_chunks': data.biosketch_chunks,
                    'cps_chunks': data.cps_chunks
                }
                for name, data in personnel_data.items()
            },
            'metadata': {
                'total_chunks': len(solicitation_chunks) + len(narrative_chunks) +
                               sum(len(p.biosketch_chunks) + len(p.cps_chunks)
                                   for p in personnel_data.values()),
                'team_size': len(personnel_data)
            }
        }

        print(f"\n✅ Document loading complete!")
        print(f"   - Solicitation: {all_data['solicitation']['num_pages']} pages")
        print(f"   - Narrative: {all_data['narrative']['num_paragraphs']} paragraphs")
        print(f"   - Team members: {all_data['metadata']['team_size']}")
        print(f"   - Total chunks: {all_data['metadata']['total_chunks']}\n")

        return all_data

    def save_chunks_to_json(self, all_data: Dict, output_path: Optional[Path] = None):
        """
        Save all chunks to JSON for debugging/inspection.

        Args:
            all_data: The data dictionary from load_all()
            output_path: Optional custom output path
        """
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / 'document_chunks.json'

        # Convert DocumentChunk objects to dicts
        serializable_data = {
            'solicitation': {
                'chunks': [asdict(chunk) for chunk in all_data['solicitation']['chunks']]
            },
            'narrative': {
                'chunks': [asdict(chunk) for chunk in all_data['narrative']['chunks']]
            },
            'personnel': {
                name: {
                    'biosketch_chunks': [asdict(chunk) for chunk in data['biosketch_chunks']],
                    'cps_chunks': [asdict(chunk) for chunk in data['cps_chunks']]
                }
                for name, data in all_data['personnel'].items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Chunks saved to: {output_path}")


if __name__ == "__main__":
    # Test the data loader
    Config.validate()
    loader = DataLoader()
    data = loader.load_all()
    loader.save_chunks_to_json(data)
