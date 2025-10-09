import argparse
import os
import json
import re
import fitz  # PyMuPDF
from typing import List, Dict, Tuple

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks for better processing.
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)

        if i + chunk_size >= len(words):
            break

    return chunks

def extract_sections(text: str, doc_type: str) -> Dict[str, str]:
    """
    Extract sections from document text based on common patterns.
    """
    sections = {}

    if doc_type == "solicitation":
        # Common solicitation section patterns
        section_patterns = [
            (r'(?i)program\s*description', 'Program Description'),
            (r'(?i)eligibility\s*information', 'Eligibility'),
            (r'(?i)award\s*information', 'Award Information'),
            (r'(?i)review\s*criteria', 'Review Criteria'),
            (r'(?i)proposal\s*preparation', 'Proposal Preparation'),
            (r'(?i)deadlines', 'Deadlines'),
            (r'(?i)contact\s*information', 'Contact Information'),
        ]
    else:  # proposal
        # Common proposal section patterns
        section_patterns = [
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

    # Find section boundaries
    section_positions = []
    for pattern, section_name in section_patterns:
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

def extract_raw_text(solicitation_path, proposal_path):
    """
    Extract raw text from solicitation and proposal PDFs using PyMuPDF.
    Returns a dictionary with raw text and parsed sections for each document.
    """
    # Validate file paths
    for path, doc_type in [(solicitation_path, "solicitation"), (proposal_path, "proposal")]:
        if not path.endswith(".pdf"):
            raise ValueError(f"Invalid PDF path for {doc_type}: {path}")
        if not os.path.exists(path):
            raise ValueError(f"File not found for {doc_type}: {path}")

    # Initialize output dictionary
    result = {
        "raw_texts": {"solicitation": "", "proposal": ""},
        "sections": {"solicitation": {}, "proposal": {}},
        "chunks": {"solicitation": [], "proposal": []}
    }

    # Process each PDF
    for path, doc_type in [(solicitation_path, "solicitation"), (proposal_path, "proposal")]:
        try:
            # Open PDF
            doc = fitz.open(path)
            raw_text = ""
            # Extract text from each page
            for page in doc:
                raw_text += page.get_text("text") + " "
            doc.close()  # Free memory

            # Basic whitespace cleaning
            raw_text = re.sub(r'\s+', ' ', raw_text.strip())

            # Validate non-empty
            if not raw_text:
                raise ValueError(f"No text extracted from {doc_type}")

            result["raw_texts"][doc_type] = raw_text

            # Extract sections
            sections = extract_sections(raw_text, doc_type)
            result["sections"][doc_type] = sections

            # Create chunks from each section
            all_chunks = []
            for section_name, section_text in sections.items():
                section_chunks = chunk_text(section_text)
                for i, chunk in enumerate(section_chunks):
                    all_chunks.append({
                        "text": chunk,
                        "section": section_name,
                        "chunk_id": f"{section_name}_{i}"
                    })

            result["chunks"][doc_type] = all_chunks

        except Exception as e:
            raise ValueError(f"Failed to process {doc_type} PDF: {str(e)}")

    # Save to disk for debugging
    with open("data/processed_texts.json", "w") as f:
        json.dump(result, f, indent=2)

    return result

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Grant Coach MVP")
    parser.add_argument("solicitation", help="Path to solicitation PDF")
    parser.add_argument("proposal", help="Path to proposal PDF")
    args = parser.parse_args()

    # Extract processed text
    processed_data = extract_raw_text(args.solicitation, args.proposal)

    # Print summary for verification
    print(f"Solicitation text length: {len(processed_data['raw_texts']['solicitation'])} characters")
    print(f"Proposal text length: {len(processed_data['raw_texts']['proposal'])} characters")
    print(f"Solicitation sections found: {len(processed_data['sections']['solicitation'])}")
    print(f"Proposal sections found: {len(processed_data['sections']['proposal'])}")
    print(f"Solicitation chunks: {len(processed_data['chunks']['solicitation'])}")
    print(f"Proposal chunks: {len(processed_data['chunks']['proposal'])}")

    # Print section names for verification
    print("\nSolicitation sections:")
    for section in processed_data['sections']['solicitation'].keys():
        print(f"  - {section}")
    print("\nProposal sections:")
    for section in processed_data['sections']['proposal'].keys():
        print(f"  - {section}")

if __name__ == "__main__":
    main()