"""
AgriGrantCoach Rubric Analyzer Module

Dynamically extracts evaluation criteria from USDA AFRI solicitations using LLMs.
This creates an accurate, source-based rubric rather than hard-coded criteria.
"""

import json
from typing import Dict, List
from pathlib import Path
from openai import OpenAI

from config import Config


class RubricAnalyzer:
    """Analyzes solicitation documents to extract evaluation rubrics."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.client = OpenAI(api_key=config.GROQ_API_KEY)

    def extract_rubric(self, solicitation_text: str) -> Dict:
        """
        Extract evaluation criteria from the solicitation using LLM analysis.

        Args:
            solicitation_text: Full text of the USDA AFRI solicitation

        Returns:
            Dictionary containing structured rubric with requirements and priorities
        """
        print("\n🔍 Analyzing solicitation to extract evaluation rubric...")

        prompt = self._build_rubric_extraction_prompt(solicitation_text)

        try:
            response = self.client.chat.completions.create(
                model=self.config.GROQ_ANALYSIS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert USDA grant administrator with deep knowledge of AFRI (Agriculture and Food Research Initiative) programs. Your task is to extract evaluation criteria from solicitations with precision."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.GROQ_ANALYSIS_TEMPERATURE,
                max_tokens=self.config.GROQ_ANALYSIS_MAX_TOKENS,
            )

            rubric_json_str = response.choices[0].message.content

            # Extract JSON from markdown code blocks if present
            if "```json" in rubric_json_str:
                rubric_json_str = rubric_json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in rubric_json_str:
                rubric_json_str = rubric_json_str.split("```")[1].split("```")[0].strip()

            rubric = json.loads(rubric_json_str)

            print(f"✅ Extracted {len(rubric.get('requirements', []))} requirements")
            print(f"✅ Identified {len(rubric.get('priorities', []))} program priorities")

            return rubric

        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Failed to parse rubric JSON: {e}")
            print(f"Raw response: {rubric_json_str[:500]}...")
            return self._get_fallback_rubric()

        except Exception as e:
            print(f"❌ Error extracting rubric: {e}")
            return self._get_fallback_rubric()

    def _build_rubric_extraction_prompt(self, solicitation_text: str) -> str:
        """Build the prompt for extracting rubric from solicitation."""

        # Truncate if too long (keep first 15000 chars which should cover key sections)
        if len(solicitation_text) > 15000:
            solicitation_text = solicitation_text[:15000] + "\n\n[...truncated for length...]"

        return f"""You are analyzing a USDA AFRI Data Science for Food and Agricultural Systems (DSFAS) solicitation.

Extract the evaluation criteria, requirements, and priorities that reviewers will use to assess proposals.

**SOLICITATION TEXT:**
{solicitation_text}

**YOUR TASK:**
Analyze the solicitation and create a structured JSON rubric. Be COMPREHENSIVE and extract ALL requirements. Focus on:

1. **Mandatory Requirements** - Things the proposal MUST have (e.g., AFRI priorities, stakeholder letters)
2. **Evaluation Criteria** - How proposals will be scored
3. **Program Priorities** - Specific focus areas or themes
4. **Constraints** - Budget limits, page limits, required sections, etc.
5. **Data Management Requirements** - FAIR data standards, data sharing plans, repositories, CARE principles
6. **Sustainability Requirements** - Long-term plans, maintenance, continued access
7. **Stakeholder Engagement** - Letters of support, community involvement, justification of need

PAY SPECIAL ATTENTION TO:
- FAIR data standards (Findable, Accessible, Interoperable, Reusable)
- CARE data principles (Collective benefit, Authority to control, Responsibility, Ethics)
- Data sharing and management plans
- Stakeholder justification and letters of support
- Budget and duration constraints

**OUTPUT FORMAT (JSON):**
{{
  "program_name": "AFRI DSFAS (A1541)",
  "requirements": [
    {{
      "id": "req_1",
      "category": "Mandatory|Evaluation|Priority|Constraint",
      "title": "Brief title",
      "description": "Detailed description of what's required",
      "weight": "High|Medium|Low",
      "evidence_keywords": ["keyword1", "keyword2"]
    }}
  ],
  "priorities": [
    {{
      "id": "pri_1",
      "title": "Priority title",
      "description": "What this priority emphasizes",
      "keywords": ["keyword1", "keyword2"]
    }}
  ],
  "constraints": {{
    "budget_limit": "value if specified",
    "duration": "project duration",
    "page_limits": {{}},
    "data_sharing": "requirements"
  }},
  "evaluation_weights": {{
    "scientific_merit": "percentage if specified",
    "broader_impacts": "percentage if specified"
  }}
}}

**IMPORTANT:**
- Extract ONLY what is explicitly stated in the solicitation
- Use exact quotes where possible in descriptions
- The evidence_keywords should be terms that would appear in a proposal addressing this requirement
- Be comprehensive but precise

Return ONLY the JSON object, no additional text."""

    def _get_fallback_rubric(self) -> Dict:
        """
        Provide a basic fallback rubric if extraction fails.
        Based on typical USDA AFRI requirements.
        """
        return {
            "program_name": "AFRI DSFAS (A1541) - Fallback Rubric",
            "requirements": [
                {
                    "id": "req_1",
                    "category": "Mandatory",
                    "title": "Data Science Focus",
                    "description": "Proposal must demonstrate use of data science, AI, or ML approaches",
                    "weight": "High",
                    "evidence_keywords": ["data science", "machine learning", "AI", "artificial intelligence", "analytics"]
                },
                {
                    "id": "req_2",
                    "category": "Mandatory",
                    "title": "Agricultural Application",
                    "description": "Must address food and agricultural systems",
                    "weight": "High",
                    "evidence_keywords": ["agriculture", "food systems", "farming", "crop", "livestock"]
                },
                {
                    "id": "req_3",
                    "category": "Mandatory",
                    "title": "FAIR Data Standards",
                    "description": "Any development of data resources must use FAIR (Findable, Accessible, Interoperable, and Reusable) standards",
                    "weight": "High",
                    "evidence_keywords": ["FAIR", "Findable", "Accessible", "Interoperable", "Reusable", "data standards", "CARE"]
                },
                {
                    "id": "req_4",
                    "category": "Evaluation",
                    "title": "Data Sharing and Management",
                    "description": "Must include data management and sharing plan",
                    "weight": "High",
                    "evidence_keywords": ["data sharing", "data management", "open data", "repository"]
                },
                {
                    "id": "req_5",
                    "category": "Evaluation",
                    "title": "Educational Impact",
                    "description": "Educational and training components",
                    "weight": "Medium",
                    "evidence_keywords": ["education", "training", "students", "workforce"]
                }
            ],
            "priorities": [],
            "constraints": {},
            "evaluation_weights": {}
        }

    def analyze_requirement_coverage(self, rubric: Dict, narrative_text: str) -> Dict:
        """
        Perform a quick keyword-based check to identify potential gaps.

        Args:
            rubric: The extracted rubric
            narrative_text: The proposal narrative text

        Returns:
            Dictionary with coverage analysis
        """
        print("\n📊 Performing initial requirement coverage check...")

        narrative_lower = narrative_text.lower()
        coverage = {
            "covered": [],
            "potentially_missing": [],
            "unclear": []
        }

        for req in rubric.get('requirements', []):
            keywords = req.get('evidence_keywords', [])

            # Check if ANY keyword is present
            matches = sum(1 for kw in keywords if kw.lower() in narrative_lower)

            if matches >= len(keywords) * 0.5:  # 50% of keywords found
                coverage["covered"].append({
                    "id": req['id'],
                    "title": req['title'],
                    "match_count": matches,
                    "total_keywords": len(keywords)
                })
            elif matches > 0:
                coverage["unclear"].append({
                    "id": req['id'],
                    "title": req['title'],
                    "match_count": matches,
                    "total_keywords": len(keywords)
                })
            else:
                coverage["potentially_missing"].append({
                    "id": req['id'],
                    "title": req['title'],
                    "weight": req.get('weight', 'Unknown')
                })

        print(f"  ✓ Covered: {len(coverage['covered'])} requirements")
        print(f"  ? Unclear: {len(coverage['unclear'])} requirements")
        print(f"  ⚠ Potentially missing: {len(coverage['potentially_missing'])} requirements")

        return coverage

    def save_rubric(self, rubric: Dict, output_path: Path = None):
        """Save the extracted rubric to JSON file."""
        if output_path is None:
            output_path = self.config.OUTPUT_DIR / 'solicitation_rubric.json'

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rubric, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Rubric saved to: {output_path}")


if __name__ == "__main__":
    # Test the rubric analyzer
    from data_loader import DataLoader

    Config.validate()

    loader = DataLoader()
    solicitation_text, _ = loader.load_solicitation()

    analyzer = RubricAnalyzer()
    rubric = analyzer.extract_rubric(solicitation_text)

    # Save rubric
    analyzer.save_rubric(rubric)

    # Print sample
    print("\n" + "="*60)
    print("Sample Requirements:")
    print("="*60)
    for req in rubric.get('requirements', [])[:3]:
        print(f"\n{req['id']}: {req['title']}")
        print(f"  Category: {req['category']}")
        print(f"  Weight: {req.get('weight', 'N/A')}")
        print(f"  Description: {req['description'][:100]}...")
