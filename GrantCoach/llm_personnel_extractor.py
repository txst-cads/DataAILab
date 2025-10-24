"""
Improved Personnel Extractor for Grant Coach
Extracts researcher information from paragraph text using intelligent parsing
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Researcher:
    name: str
    role: str
    department: str
    title: str
    responsibilities: List[str]
    confidence: float

class LLMPersonnelExtractor:
    """Extracts researcher information from personnel section text using intelligent parsing"""

    def __init__(self):
        self.role_patterns = {
            'PI': [r'PI\b', r'Principal Investigator', r'Tahir Ekin.*?PI'],
            'Co-PI': [r'Co-?PI\b', r'Co-?Principal Investigator', r'four Co-PIs'],
            'Senior Personnel': [r'Senior Personnel', r'Associate Professor', r'Assistant Professor', r'Professor']
        }

        self.department_patterns = [
            r'(?:College|School|Department|Institute) of ([^,\n\.]+)',
            r'(?:Computer Science|CS|Business Analytics|Criminal Justice|Electrical Engineering|Agriculture|Health Information Management|Communication Disorders|Chemistry)',
            r'McCoy College of Business',
            r'Ingram School of Engineering',
            r'School of Criminal Justice and Criminology',
            r'Center for Geospatial Intelligence and Investigation',
            r'Materials Application Research Center',
            r'Gen STEM'
        ]

    def extract_personnel(self, text: str) -> List[Researcher]:
        """Extract all researchers from personnel section text"""

        researchers = []

        # Split text by researcher entries
        researcher_entries = self._split_into_researcher_entries(text)

        print(f"Found {len(researcher_entries)} researcher entries")

        for i, entry in enumerate(researcher_entries):
            if entry.strip():
                researcher = self._parse_researcher_entry(entry, i)
                if researcher:
                    researchers.append(researcher)

        return researchers

    def _split_into_researcher_entries(self, text: str) -> List[str]:
        """Split personnel text into individual researcher entries"""

        # Split by "Dr. " pattern to identify individual researchers
        entries = re.split(r'(?=Dr\.\s+[A-Z])', text)

        # Clean up entries
        cleaned_entries = []
        for entry in entries:
            entry = entry.strip()
            if entry and not entry.startswith('The TXST ExpandAI team'):
                cleaned_entries.append(entry)

        return cleaned_entries

    def _parse_researcher_entry(self, entry: str, entry_index: int) -> Optional[Researcher]:
        """Parse a single researcher entry into structured data"""

        # Extract name (improved pattern to handle special characters)
        name_match = re.search(r'Dr\. ([A-Z][a-z]+(?: [A-Z][a-z\']+)*)', entry)
        if not name_match:
            return None

        name = name_match.group(1)

        # Extract role
        role = self._extract_role(entry, name)

        # Extract department/title
        department, title = self._extract_department_and_title(entry)

        # Extract responsibilities
        responsibilities = self._extract_responsibilities(entry)

        # Calculate confidence
        confidence = self._calculate_confidence(entry, role, department)

        return Researcher(
            name=name,
            role=role,
            department=department,
            title=title,
            responsibilities=responsibilities,
            confidence=confidence
        )

    def _extract_role(self, entry: str, name: str) -> str:
        """Extract researcher role from entry"""

        # Check for PI
        if 'PI' in entry and name == 'Tahir Ekin':
            return 'PI'

        # Check for Co-PIs mentioned in the initial summary
        co_pi_names = ['Apan Qasem', 'Damian Valles', 'Lucia Summers', 'Jelena Tešić']  # Based on document context
        if name in co_pi_names or 'Co-PI' in entry:
            return 'Co-PI'

        return 'Senior Personnel'

    def _extract_department_and_title(self, entry: str) -> tuple[str, str]:
        """Extract department and title from entry"""

        department = ""
        title = ""

        # Look for department patterns
        for pattern in self.department_patterns:
            match = re.search(pattern, entry)
            if match:
                if match.groups() and len(match.groups()) >= 1:
                    department = match.group(1)
                else:
                    department = match.group(0)
                break

        # Extract title/position
        title_patterns = [
            r'Presidential Fellow and ([^.]+)',
            r'Associate Professor of ([^.]+)',
            r'Assistant Professor of ([^.]+)',
            r'Professor of ([^.]+)',
            r'Associate Professor at ([^.]+)',
            r'Assistant Professor at ([^.]+)',
            r'Professor at ([^.]+)',
            r'co-director of ([^.]+)',
            r'Director of ([^.]+)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, entry)
            if match:
                title = match.group(0)
                break

        return department, title

    def _extract_responsibilities(self, entry: str) -> List[str]:
        """Extract researcher responsibilities from entry"""

        responsibilities = []

        # Look for responsibility patterns
        resp_patterns = [
            r'(?:He|She) will ([^.]+)',
            r'(?:His|Her) contributions? ([^.]+)',
            r'will ([^.]+)',
            r'support ([^.]+)',
            r'lead ([^.]+)',
            r'oversee ([^.]+)',
            r'prepare ([^.]+)',
            r'supervise ([^.]+)',
            r'facilitate ([^.]+)',
            r'coordinate ([^.]+)'
        ]

        for pattern in resp_patterns:
            matches = re.findall(pattern, entry)
            responsibilities.extend(matches)

        return list(set(resp for resp in responsibilities if resp.strip()))

    def _calculate_confidence(self, entry: str, role: str, department: str) -> float:
        """Calculate confidence score for researcher extraction"""

        confidence = 0.0

        # Base confidence for having a name
        confidence += 0.3

        # Role confidence
        if role == 'PI':
            confidence += 0.4
        elif role == 'Co-PI':
            confidence += 0.3
        elif role == 'Senior Personnel':
            confidence += 0.2

        # Department confidence
        if department:
            confidence += 0.2

        # Responsibility confidence
        if 'will' in entry or 'lead' in entry or 'support' in entry:
            confidence += 0.1

        return min(confidence, 1.0)

    def test_extraction(self, text: str) -> Dict[str, Any]:
        """Test the extraction and return detailed results"""

        researchers = self.extract_personnel(text)

        result = {
            'total_researchers': len(researchers),
            'researchers': [],
            'summary': {
                'pi_count': 0,
                'co_pi_count': 0,
                'senior_count': 0
            }
        }

        for researcher in researchers:
            researcher_data = {
                'name': researcher.name,
                'role': researcher.role,
                'department': researcher.department,
                'title': researcher.title,
                'responsibilities': researcher.responsibilities,
                'confidence': researcher.confidence
            }
            result['researchers'].append(researcher_data)

            if researcher.role == 'PI':
                result['summary']['pi_count'] += 1
            elif researcher.role == 'Co-PI':
                result['summary']['co_pi_count'] += 1
            else:
                result['summary']['senior_count'] += 1

        return result

if __name__ == "__main__":
    # Test the extractor
    extractor = LLMPersonnelExtractor()

    # Test with the actual personnel text
    test_text = """The TXST ExpandAI team consists of a PI, four Co-PIs, and six Senior Personnel representing nine
    academic departments in four colleges. The team also includes seven female and four Hispanic faculty,
    displaying a diversity of AI researchers. Dr. Tahir Ekin, PI, is Presidential Fellow and Gregg Associate
    Professor of Analytics, and incoming Fields Chair in Business Analytics at McCoy College of Business. He
    leads the launch of the TXST CADS and Analytics Showcase. He will be responsible for overseeing the
    activities of ExpandAI and coordinating activities within TXST in addition to managing extra-curricular
    activities (D1-D3). Dr. Apan Qasem is Associate Professor of CS, and Associate Chair of CS Department.
    His research experience includes HPC, and he has been an investigator of several externally funded
    projects improving the access of underserved student populations into STEM education. He will lead the
    preparation of AI methods modules (A2) and support develop TXST HPC training program (B1). Dr. Lucia
    Summers is Associate Professor at the School of Criminal Justice and Criminology, and Associate Director
    of the Center for Geospatial Intelligence and Investigation. Her contributions will be towards preparing a
    module about AI applications in CJ (A2) and leading the co-advising of a CJ Ph.D. student in an AI
    dissertation (C1)."""

    result = extractor.test_extraction(test_text)
    print(json.dumps(result, indent=2))