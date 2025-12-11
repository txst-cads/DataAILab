"""
Competency Engine (The Brain)
==============================
RAG-powered evaluation system that:
1. Extracts dynamic rubrics from solicitations
2. Validates narrative strength through evidence retrieval
3. Maps team competencies to requirements
4. Generates gap analysis with specific recommendations

All outputs include citations to source documents.
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RubricCriterion:
    """Represents a single evaluation criterion from the solicitation."""
    id: str
    title: str
    description: str
    weight_points: int
    keywords: List[str]
    compliance_requirements: List[str]


@dataclass
class EvaluationResult:
    """Result of evaluating one criterion against the narrative."""
    criterion: RubricCriterion
    score: Optional[float]  # 0-10, or None if criterion not applicable
    evidence_found: List[Tuple[str, str]]  # [(text, citation), ...]
    gaps: List[str]
    recommendations: List[str]
    team_alignment: Dict[str, List[str]]  # {member_name: [relevant_expertise]}


class CompetencyEngine:
    """
    Main evaluation engine that orchestrates the analysis.
    """

    def __init__(self, ingester=None, team_data: Dict = None):
        """
        Args:
            ingester: DocumentIngester instance with loaded vector stores
            team_data: Team competency data from FacultyBot
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.validation_model = "gpt-4o"  # Use better model for validation
        self.ingester = ingester
        self.team_data = team_data or {"team_members": []}
        self.proposal_priority = None  # Will be detected from narrative
        self.total_cost = 0.0  # Track API costs

    def detect_proposal_priority(self) -> Dict[str, any]:
        """
        Detect which priority/focus area the proposal is targeting.
        This prevents evaluating against irrelevant criteria.

        Returns:
            Dict with priority info: {
                'primary_priority': str (e.g., 'Priority 1: Postsecondary'),
                'target_audience': str (e.g., 'undergraduate students', 'K-12 teachers'),
                'confidence': float (0-1)
            }
        """
        if not self.ingester or "narrative" not in self.ingester.vector_stores:
            return {'primary_priority': 'Unknown', 'target_audience': 'Unknown', 'confidence': 0.0}

        print("🎯 Detecting proposal priority and target audience...")

        # Search for priority indicators in narrative
        priority_searches = [
            "absolute priority competitive preference priority 1 priority 2 priority 6",
            "target audience learners students teachers K-12 postsecondary",
            "undergraduate graduate workforce teacher preparation",
            "higher education community college university",
            "short-term programs micro-credentials certificates stackable",
            "workforce pell talent marketplace work-based learning",
            "high-skill high-wage in-demand industry sectors"
        ]

        priority_evidence = []
        for query in priority_searches:
            results = self.ingester.search(query, doc_type="narrative", k=2)
            priority_evidence.extend([doc.page_content for doc, _ in results])

        # Use LLM to analyze priority
        prompt = f"""Analyze this grant proposal excerpt to determine its PRIMARY PRIORITY and TARGET AUDIENCE.

**Proposal Excerpts:**
{chr(10).join(priority_evidence[:5])}

**Task:** Identify:
1. Which grant priority this proposal is addressing:
   - Priority 1: Postsecondary Outcomes/Workforce
   - Priority 2: K-12 Teacher Preparation
   - Priority 6: Creation of New High-Quality Short-Term Programs (micro-credentials, certificates, Workforce Pell)
   - Other

2. The primary target audience (e.g., undergraduate students, K-12 teachers, working adults, etc.)
3. Your confidence level (0-1)

**Priority 6 Indicators:**
Look for: short-term programs, micro-credentials, certificates, Workforce Pell, talent marketplaces, work-based learning, stackable pathways, employer engagement, in-demand sectors

**Output Format (JSON):**
{{
  "primary_priority": "Priority X: [name]",
  "target_audience": "[specific audience]",
  "key_indicators": ["indicator 1", "indicator 2", "indicator 3"],
  "confidence": 0.XX
}}

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a grant analysis expert. Extract priority information accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            self.proposal_priority = result

            print(f"   ✅ Detected: {result.get('primary_priority', 'Unknown')}")
            print(f"   Audience: {result.get('target_audience', 'Unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")

            return result

        except Exception as e:
            print(f"   ⚠️ Could not detect priority: {e}")
            return {'primary_priority': 'Unknown', 'target_audience': 'Unknown', 'confidence': 0.0}

    def extract_rubric(self, solicitation_text: str = None) -> List[RubricCriterion]:
        """
        Extract NARRATIVE QUALITY dimensions from solicitation.
        Focus on what makes a proposal compelling, not compliance.

        Args:
            solicitation_text: Raw solicitation text (optional, will search if not provided)

        Returns:
            List of RubricCriterion objects representing narrative dimensions
        """
        print("🔍 Identifying narrative evaluation dimensions...")

        # If text not provided, retrieve from vector store
        if not solicitation_text and self.ingester:
            # Get representative chunks from solicitation
            search_queries = [
                "evaluation criteria merit review",
                "project significance impact",
                "innovation approach quality",
                "team qualifications capacity",
                "broader impacts outcomes"
            ]

            chunks = []
            for query in search_queries:
                results = self.ingester.search(query, doc_type="solicitation", k=3)
                chunks.extend([doc.page_content for doc, _ in results])

            solicitation_text = "\n\n".join(chunks[:10])  # Use top chunks

        prompt = f"""You are a senior grant writing consultant analyzing a funding opportunity.

Your task: Identify the KEY NARRATIVE DIMENSIONS that make proposals competitive.

Focus on SUBSTANCE, not compliance:
- What makes the science/project compelling?
- What demonstrates team strength?
- What shows innovation and impact?
- What builds reviewer confidence?

**Solicitation Text:**
{solicitation_text}

**Required Output Format (JSON):**
{{
  "criteria": [
    {{
      "id": "criterion_1",
      "title": "Brief title (e.g., 'Project Significance', 'Innovation Strength', 'Team Expertise')",
      "description": "What makes proposals strong on this dimension",
      "weight_points": <importance 1-100>,
      "keywords": ["domain terms", "key concepts"],
      "compliance_requirements": []
    }}
  ]
}}

**Instructions:**
- Extract 4-6 NARRATIVE dimensions (NOT compliance items)
- Focus on: Significance, Innovation, Approach Quality, Team Strength, Impact, Feasibility
- Weight by importance (not points - use 1-100 scale for relative importance)
- NO compliance items (page limits, formats, budgets)
- Keywords should be domain/content focused

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a grant evaluation expert. Extract rubrics precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)
            criteria = []

            for item in data.get("criteria", []):
                criteria.append(RubricCriterion(
                    id=item.get("id", "unknown"),
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    weight_points=item.get("weight_points", 0),
                    keywords=item.get("keywords", []),
                    compliance_requirements=item.get("compliance_requirements", [])
                ))

            print(f"   ✅ Extracted {len(criteria)} evaluation criteria")
            return criteria

        except Exception as e:
            print(f"   ❌ Error extracting rubric: {e}")
            return []

    def evaluate_criterion(
        self,
        criterion: RubricCriterion,
        narrative_search_k: int = 10  # INCREASED from 5 to 10 for better coverage
    ) -> EvaluationResult:
        """
        Evaluate a single criterion against the narrative and team data.
        Uses TWO-PASS system for accuracy:
        1. Extract what IS present in evidence
        2. Identify gaps with required evidence quotes
        3. Validate with GPT-4o for high-confidence results

        Args:
            criterion: RubricCriterion to evaluate
            narrative_search_k: Number of narrative chunks to retrieve

        Returns:
            EvaluationResult with scoring and recommendations
        """
        print(f"\n📊 Evaluating: {criterion.title}")

        # Step 1: Retrieve relevant evidence from narrative
        evidence_chunks = self._retrieve_evidence(criterion, narrative_search_k)

        print(f"   📝 Retrieved {len(evidence_chunks)} pieces of evidence")

        # CONFIDENCE CHECK: If we have very little evidence, flag for manual review
        if len(evidence_chunks) < 3:
            print(f"   ⚠️  WARNING: Limited evidence found for this criterion")
            print(f"   → This may indicate retrieval failure, not missing content")
            print(f"   → Recommendations may be generic - manual review suggested")

        # Step 2: Analyze team alignment
        team_alignment = self._analyze_team_alignment(criterion)

        # Step 3: Two-pass evaluation with validation
        evaluation = self._two_pass_evaluate(criterion, evidence_chunks, team_alignment)

        return evaluation

    def _retrieve_evidence(
        self,
        criterion: RubricCriterion,
        k: int
    ) -> List[Tuple[str, str]]:
        """
        Retrieve evidence from narrative using OPTIMIZED MULTI-STRATEGY search.
        Includes "Table Hunter" and "Proper Noun Hunter" to fix retrieval failures.

        Returns: List of (content, citation) tuples
        """
        if not self.ingester or "narrative" not in self.ingester.vector_stores:
            return []

        all_results = {}  # Use dict to deduplicate by citation

        # KEY CHANGE: Increase base retrieval depth
        base_k = k + 2

        # Strategy 0: BROAD CONTEXT SEARCH - Get major sections
        broad_searches = [
            "significance impact need problem",
            "innovation approach methodology",
            "qualifications expertise team capacity",
            "prior work preliminary results case studies",
            "broader impacts outcomes dissemination"
        ]
        for broad_query in broad_searches:
            broad_results = self.ingester.search(broad_query, doc_type="narrative", k=3)
            for doc, score in broad_results:
                citation = self.ingester.format_citation(doc)
                if citation not in all_results or score > all_results[citation][1]:
                    all_results[citation] = (doc.page_content, score * 0.8)

        # Strategy 1: General criterion-based search
        general_query = f"{criterion.title} {criterion.description} {' '.join(criterion.keywords[:5])}"
        general_results = self.ingester.search(general_query, doc_type="narrative", k=base_k)
        for doc, score in general_results:
            citation = self.ingester.format_citation(doc)
            if citation not in all_results or score > all_results[citation][1]:
                all_results[citation] = (doc.page_content, score)

        # Strategy 2: The "Table Hunter" (Fixes Metric Blindness)
        # If criterion mentions metrics/data/statistics, aggressively hunt for tables
        if any(w in criterion.description.lower() for w in ['metric', 'data', 'stat', 'evidence', 'outcome', 'quantitative']):
            table_queries = [
                f"Table relating to {criterion.title}",
                "Figure chart graph statistics",
                "evaluation metrics outcomes measures",
                "[Embedded Image",  # Catch OCR'd tables
                "| " # Pipe character often indicates tables
            ]
            for q in table_queries:
                results = self.ingester.search(q, doc_type="narrative", k=3)
                for doc, score in results:
                    citation = self.ingester.format_citation(doc)
                    # Artificial boost for table content
                    if citation not in all_results or score * 1.5 > all_results[citation][1]:
                        all_results[citation] = (doc.page_content, score * 1.5)

        # Strategy 3: The "Proper Noun Hunter"
        # Extract capitalized entities from criterion description and search for them
        proper_nouns = [word for word in criterion.description.split()
                       if word and word[0].isupper() and len(word) > 3 and not word.isupper()]
        for noun in proper_nouns[:5]:  # Limit to avoid over-querying
            noun_results = self.ingester.search(noun, doc_type="narrative", k=2)
            for doc, score in noun_results:
                citation = self.ingester.format_citation(doc)
                if citation not in all_results or score * 1.2 > all_results[citation][1]:
                    all_results[citation] = (doc.page_content, score * 1.2)

        # Strategy 4: DATA & STATISTICS search (fix "TWC data blindness")
        if any(kw in criterion.title.lower() or kw in criterion.description.lower()
               for kw in ['significance', 'impact', 'need', 'data', 'statistics', 'evidence']):
            data_queries = [
                "Texas Workforce Commission TWC labor market",
                "growth percent % projected demand statistics data",
                "SOC code occupation employment trends",
                "number of students learners participants served enrolled",
                "quantitative goals targets metrics outcomes",
                "expected impact measurable results evidence"
            ]
            for query in data_queries:
                data_results = self.ingester.search(query, doc_type="narrative", k=3)
                for doc, score in data_results:
                    citation = self.ingester.format_citation(doc)
                    if citation not in all_results or score * 1.2 > all_results[citation][1]:
                        all_results[citation] = (doc.page_content, score * 1.2)

        # Strategy 5: Team/personnel search
        if any(kw in criterion.title.lower() or kw in criterion.description.lower()
               for kw in ['team', 'personnel', 'qualifications', 'expertise', 'faculty', 'staff']):
            team_queries = [
                "principal investigator project director team members",
                "qualifications experience expertise credentials",
                "faculty staff personnel investigators"
            ]
            for query in team_queries:
                team_results = self.ingester.search(query, doc_type="narrative", k=3)
                for doc, score in team_results:
                    citation = self.ingester.format_citation(doc)
                    if citation not in all_results or score > all_results[citation][1]:
                        all_results[citation] = (doc.page_content, score)

        # Strategy 6: PRIOR WORK / CASE STUDIES search (fix "Prior Initiatives" synonym gap)
        if any(kw in criterion.title.lower() or kw in criterion.description.lower()
               for kw in ['track record', 'experience', 'prior', 'previous', 'success', 'feasibility', 'capacity']):
            prior_work_queries = [
                "prior initiatives previous projects",
                "ExpandAI TSUS STEM-CLEAR NSF funded",
                "case studies success stories track record",
                "preliminary results pilot data",
                "institutional history background experience",
                "proven capacity demonstrated success"
            ]
            for query in prior_work_queries:
                prior_results = self.ingester.search(query, doc_type="narrative", k=3)
                for doc, score in prior_results:
                    citation = self.ingester.format_citation(doc)
                    if citation not in all_results or score * 1.3 > all_results[citation][1]:
                        all_results[citation] = (doc.page_content, score * 1.3)

        # Strategy 7: Partnership/collaboration search
        if any(kw in criterion.title.lower() or kw in criterion.description.lower()
               for kw in ['partner', 'collaborat', 'stakeholder', 'community', 'industry', 'employer']):
            partner_queries = [
                "partnerships collaborations stakeholders partners",
                "industry employers workforce community organizations",
                "advisory board council validation",
                "memorandum of understanding MOU letters of support"
            ]
            for query in partner_queries:
                partner_results = self.ingester.search(query, doc_type="narrative", k=3)
                for doc, score in partner_results:
                    citation = self.ingester.format_citation(doc)
                    if citation not in all_results or score > all_results[citation][1]:
                        all_results[citation] = (doc.page_content, score)

        # Strategy 8: Search for each individual keyword
        for keyword in criterion.keywords[:5]:
            keyword_results = self.ingester.search(keyword, doc_type="narrative", k=2)
            for doc, score in keyword_results:
                citation = self.ingester.format_citation(doc)
                if citation not in all_results or score > all_results[citation][1]:
                    all_results[citation] = (doc.page_content, score)

        # Convert back to list and sort by score
        evidence = [(content, citation) for citation, (content, score) in
                   sorted(all_results.items(), key=lambda x: x[1][1], reverse=True)]

        # Return top k*5 pieces of evidence (AGGRESSIVE retrieval)
        return evidence[:k*5]

    def _analyze_team_alignment(self, criterion: RubricCriterion) -> Dict[str, List[str]]:
        """
        Map team members to criterion requirements.

        Returns: Dict of {member_name: [relevant_expertise]}
        """
        alignment = {}

        # Convert criterion keywords to lowercase for matching
        criterion_keywords = [kw.lower() for kw in criterion.keywords]

        for member in self.team_data.get("team_members", []):
            relevant_skills = []

            # Check research interests
            for interest in member.get("research_interests", []):
                # Handle both string and dict formats
                interest_text = interest
                if isinstance(interest, dict):
                    interest_text = interest.get("domain", interest.get("name", str(interest)))
                elif not isinstance(interest, str):
                    interest_text = str(interest)

                if any(kw in interest_text.lower() for kw in criterion_keywords):
                    relevant_skills.append(f"Research: {interest_text}")

            # Check expertise keywords
            for keyword in member.get("expertise_keywords", []):
                if keyword.lower() in criterion_keywords or any(kw in keyword.lower() for kw in criterion_keywords):
                    relevant_skills.append(f"Expertise: {keyword}")

            # Check publications (title matching)
            for pub in member.get("publications", [])[:3]:  # Top 3 pubs
                # Handle both string and dict formats
                pub_title = pub
                if isinstance(pub, dict):
                    pub_title = pub.get("title", str(pub))
                elif not isinstance(pub, str):
                    pub_title = str(pub)

                if any(kw in pub_title.lower() for kw in criterion_keywords):
                    relevant_skills.append(f"Publication: {pub_title[:80]}...")

            if relevant_skills:
                alignment[member.get("name", "Unknown")] = relevant_skills

        return alignment

    def _format_team_context(self, team_alignment: Dict[str, List[str]]) -> str:
        """
        Format comprehensive team context showing detailed qualifications.
        This tells the LLM that full CVs are available and provides rich team data.

        Args:
            team_alignment: Dict mapping member names to relevant skills

        Returns:
            Formatted string with detailed team information
        """
        if not team_alignment:
            return ""

        team_sections = []

        for member_name, matched_skills in team_alignment.items():
            # Find full member profile from team_data
            member_profile = None
            for member in self.team_data.get("team_members", []):
                if member.get("name") == member_name:
                    member_profile = member
                    break

            if not member_profile:
                # Fallback: just show matched skills
                team_sections.append(f"- **{member_name}**: {', '.join(matched_skills[:3])}")
                continue

            # Build comprehensive member summary
            parts = [f"**{member_name}** ({member_profile.get('title', 'N/A')})"]

            # Matched skills for this criterion (show up to 5)
            if matched_skills:
                parts.append(f"  → Relevant to criterion: {', '.join(matched_skills[:5])}")

            # Additional context from CV
            research_interests = member_profile.get('research_interests', [])
            if research_interests:
                interests_str = ', '.join(research_interests[:4])
                parts.append(f"  → Research focus: {interests_str}")

            expertise = member_profile.get('expertise_keywords', [])
            if expertise:
                expertise_str = ', '.join(expertise[:5])
                parts.append(f"  → Technical expertise: {expertise_str}")

            # Publications count
            pubs = member_profile.get('publications', [])
            if pubs:
                parts.append(f"  → Publications: {len(pubs)} documented in CV")

            # Notable achievements
            achievements = member_profile.get('notable_achievements', [])
            if achievements:
                parts.append(f"  → Notable achievements: {len(achievements)} listed")

            team_sections.append("\n".join(parts))

        return "\n\n".join(team_sections)

    def _two_pass_evaluate(
        self,
        criterion: RubricCriterion,
        evidence: List[Tuple[str, str]],
        team_alignment: Dict[str, List[str]]
    ) -> EvaluationResult:
        """
        Two-pass evaluation system for maximum accuracy.

        Pass 1: Extract what IS present in evidence (GPT-4o-mini)
        Pass 2: Identify true gaps with required quotes (GPT-4o-mini)
        Pass 3: Validate findings (GPT-4o - selective)

        Returns: EvaluationResult with verified gaps only
        """

        # PASS 1: Evidence Extraction (what IS there)
        print(f"   🔍 Pass 1: Extracting present content...")
        extracted_content = self._extract_present_content(criterion, evidence, team_alignment)

        # PASS 2: Gap Identification (what's MISSING)
        print(f"   🔍 Pass 2: Identifying genuine gaps...")
        gaps_and_score = self._identify_gaps_with_quotes(
            criterion, evidence, team_alignment, extracted_content
        )

        # PASS 3: Validation (GPT-4o for high-confidence results)
        # Only validate if we found significant gaps OR score is low
        if len(gaps_and_score['gaps']) > 2 or gaps_and_score['score'] < 7:
            print(f"   ✓ Pass 3: Validating with GPT-4o...")
            validated_result = self._validate_with_gpt4o(
                criterion, evidence, extracted_content, gaps_and_score
            )
            return validated_result
        else:
            print(f"   ✓ Pass 3: Skipped (high score, few gaps)")
            # Convert to EvaluationResult
            return EvaluationResult(
                criterion=criterion,
                score=gaps_and_score['score'],
                evidence_found=evidence,
                gaps=gaps_and_score['gaps'],
                recommendations=gaps_and_score['recommendations'],
                team_alignment=team_alignment
            )

    def _extract_present_content(
        self,
        criterion: RubricCriterion,
        evidence: List[Tuple[str, str]],
        team_alignment: Dict[str, List[str]]
    ) -> Dict:
        """
        PASS 1: FORENSIC EVIDENCE EXTRACTION
        Goal: Find evidence that ALREADY EXISTS, even if poorly formatted or in tables.
        Uses zero temperature for extraction accuracy.
        """
        evidence_text = "\n\n".join([
            f"**Evidence {i+1}** {citation}\n{content}"
            for i, (content, citation) in enumerate(evidence[:20])  # Limit to top 20 for cost
        ])

        # Format team expertise
        team_text = ""
        if team_alignment:
            team_text = "\n\n**TEAM MEMBERS TO LOOK FOR:**\n"
            for member, skills in team_alignment.items():
                team_text += f"- {member}\n"

        prompt = f"""You are a Forensic Grant Analyst. Your job is to find evidence that ALREADY EXISTS, even if it is poorly formatted, inside a table, or fragmented.

**CRITERION:** {criterion.title}
**DESCRIPTION:** {criterion.description}

**EVIDENCE CHUNKS:**
{evidence_text if evidence else "No evidence found."}

{team_text}

**YOUR TASK: FORENSIC EVIDENCE EXTRACTION**

You MUST extract everything that currently EXISTS in the text above:

1. **Exact Metrics/Numbers:**
   - Find ANY quantitative data (percentages, growth rates, target numbers, etc.)
   - Example: "20-30% growth", "80% fidelity", "60% satisfaction"
   - Look in OCR'd tables: [Embedded Image X]:

2. **Named Entities:**
   - Organizations: Texas Workforce Commission, CADS, NSF, etc.
   - Programs: ExpandAI, TSUS, STEM-CLEAR, etc.
   - People: Dr. Lopez, Dr. Berger, etc.

3. **Team Member References:**
   - Which team members are EXPLICITLY NAMED in the text?
   - Don't assume - only list if you see their name

4. **Table Detection:**
   - Does the text contain table-like structures?
   - Look for: pipe characters |, [Embedded Image], rows/columns

**OUTPUT JSON:**
{{
  "found_metrics": ["List exact numbers/targets found (e.g. '20-30% growth', 'GLAT gains ≥20 pts')"],
  "found_entities": ["List specific agencies/partners/programs mentioned"],
  "found_team_refs": ["Which team members are explicitly named"],
  "is_table_present": <true/false - set to true if text looks like OCR'd table rows>,
  "table_count": <number of tables detected>,
  "forensic_summary": "What evidence ACTUALLY EXISTS in the chunks above (not what's missing)"
}}

**CRITICAL RULES:**
- ONLY report what you can SEE in the evidence chunks
- DO NOT infer or assume content that isn't explicitly there
- If evidence is empty, return empty lists
- Be forensic - extract exact quotes for metrics

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # Use mini for extraction
                messages=[
                    {"role": "system", "content": "You are a forensic evidence extractor. Report ONLY what exists."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Zero temperature for extraction accuracy
                response_format={"type": "json_object"}
            )

            # Track cost
            self.total_cost += 0.003  # Approximate cost for mini

            result = json.loads(response.choices[0].message.content)

            # Print what was found
            metrics = result.get('found_metrics', [])
            entities = result.get('found_entities', [])
            team_refs = result.get('found_team_refs', [])
            tables = result.get('is_table_present', False)

            print(f"      Found: {len(metrics)} metrics, {len(entities)} entities, {len(team_refs)} team refs, tables={tables}")

            return result

        except Exception as e:
            print(f"      ⚠️ Error in extraction: {e}")
            return {
                "found_metrics": [],
                "found_entities": [],
                "found_team_refs": [],
                "is_table_present": False,
                "table_count": 0,
                "forensic_summary": "Error during extraction"
            }

    def _identify_gaps_with_quotes(
        self,
        criterion: RubricCriterion,
        evidence: List[Tuple[str, str]],
        team_alignment: Dict[str, List[str]],
        extracted_content: Dict
    ) -> Dict:
        """
        PASS 2: COACHING WITH NEGATIVE CONSTRAINTS
        Uses forensic findings to guide coaching and prevent hallucinated gaps.
        """
        evidence_text = "\n\n".join([
            f"**Evidence {i+1}** {citation}\n{content[:800]}..."
            for i, (content, citation) in enumerate(evidence[:15])  # Limit for cost
        ])

        # Extract forensic findings from Pass 1
        found_metrics = extracted_content.get('found_metrics', [])
        found_entities = extracted_content.get('found_entities', [])
        found_team_refs = extracted_content.get('found_team_refs', [])
        is_table_present = extracted_content.get('is_table_present', False)
        forensic_summary = extracted_content.get('forensic_summary', '')

        # Get team data for coaching
        team_members = self.team_data.get("team_members", [])
        team_context = ""
        if team_members:
            team_context = "\n\n**TEAM EXPERTISE AVAILABLE:**\n"
            for member in team_members[:5]:
                name = member.get("name", "Unknown")
                pubs = member.get("publications", [])[:2]
                interests = member.get("research_interests", [])[:3]
                team_context += f"\n- **{name}:**\n"
                if interests:
                    team_context += f"  Research: {', '.join(str(i) for i in interests)}\n"
                if pubs:
                    team_context += f"  Publications: {len(member.get('publications', []))} in CV\n"

        prompt = f"""You are a senior grant writing coach providing evidence-based feedback.

**CRITERION:** {criterion.title}
**DESCRIPTION:** {criterion.description}
**IMPORTANCE:** {criterion.weight_points}/100

**FORENSIC FINDINGS (Pass 1 - What IS Present):**
- Metrics Found: {json.dumps(found_metrics)}
- Entities Found: {json.dumps(found_entities)}
- Team Members Named: {json.dumps(found_team_refs)}
- Table Detected: {is_table_present}
- Summary: {forensic_summary}

{team_context}

**EVIDENCE SAMPLE:**
{evidence_text if evidence else "Limited evidence retrieved."}

**YOUR TASK: EVIDENCE-BASED COACHING**

Provide coaching to strengthen this narrative dimension.

**⛔ NEGATIVE CONSTRAINTS (DO NOT DO THIS):**
1. **NO BUDGETS:** Do not ask for budget breakdowns, financial projections, or dollar amounts.
2. **NO DUPLICATE REQUESTS:** If the 'Forensic Findings' show data/entities, DO NOT recommend adding them.
3. **NO GENERIC ADVICE:** Do not suggest "adding a personal anecdote" unless section is completely dry.
4. **RESPECT TABLES:** If 'Table Detected' is True, assume metrics are handled. Don't ask for "more quantitative data."
5. **NO SCOPE CREEP:** Stay focused on THIS criterion. Don't ask for attachments or separate documents.

**✅ POSITIVE COACHING FOCUS:**
1. **Narrative Enhancement:** How can existing content be made more compelling?
2. **Team Integration:** Which team members' expertise should be woven into the narrative?
3. **Storytelling:** How to strengthen the persuasive arc?
4. **Evidence Quality:** What would make the case more convincing (NOT what's missing, but how to strengthen)?

**SCORING GUIDANCE:**
- Score <6 ONLY if the section is genuinely empty or critically weak
- If metrics/entities/tables exist, score ≥6 baseline
- Focus scoring on narrative QUALITY, not just presence of content

**OUTPUT JSON:**
{{
  "narrative_score": <0-10>,
  "score_rationale": "Why this score, acknowledging what exists and what could be stronger",
  "improvement_opportunities": [
    {{
      "area": "What to strengthen (NOT what to add from scratch)",
      "current_state": "What's already there",
      "enhancement": "How to make it better/more compelling"
    }}
  ],
  "team_leverage_suggestions": [
    {{
      "member_name": "Team member name",
      "credential_to_highlight": "Specific expertise/pub from their CV",
      "integration_suggestion": "How/where to weave this into narrative"
    }}
  ]
}}

**CRITICAL:** Use the forensic findings to guide your coaching. Don't hallucinate gaps that don't exist.

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,  # Use mini (cheap)
                messages=[
                    {"role": "system", "content": "You are a forensic-aware coach. Use Pass 1 findings to avoid false gaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            # Track cost
            self.total_cost += 0.003

            result = json.loads(response.choices[0].message.content)

            # Extract and format coaching recommendations
            improvements = result.get('improvement_opportunities', [])
            team_suggestions = result.get('team_leverage_suggestions', [])

            # Format as actionable recommendations
            all_recs = []

            # Add improvement opportunities
            for imp in improvements:
                area = imp.get('area', '')
                enhancement = imp.get('enhancement', imp.get('how', ''))
                all_recs.append(f"[ENHANCE] {area}: {enhancement}")

            # Add team leverage suggestions
            for team_sug in team_suggestions:
                member = team_sug.get('member_name', 'Team member')
                suggestion = team_sug.get('integration_suggestion', team_sug.get('suggested_integration', ''))
                all_recs.append(f"[LEVERAGE] {member}: {suggestion}")

            score = float(result.get('narrative_score', 5))

            print(f"      Narrative Score: {score}/10")
            print(f"      Coaching recommendations: {len(all_recs)}")

            return {
                'score': score,
                'gaps': [],  # No longer using "gaps" terminology
                'recommendations': all_recs,
                'raw_data': result
            }

        except Exception as e:
            print(f"      ⚠️ Error in gap identification: {e}")
            return {'score': 5.0, 'gaps': ["Error during evaluation"], 'recommendations': []}

    def _validate_with_gpt4o(
        self,
        criterion: RubricCriterion,
        evidence: List[Tuple[str, str]],
        extracted_content: Dict,
        initial_findings: Dict
    ) -> EvaluationResult:
        """
        PASS 3: Use GPT-4o for EXPERT-LEVEL COACHING.
        Provides refined, high-quality recommendations for narrative improvement.
        Only called for low narrative scores or many recommendations.
        """
        evidence_text = "\n\n".join([
            f"**Evidence {i+1}** {citation}\n{content[:500]}..."
            for i, (content, citation) in enumerate(evidence[:5])  # Limit for cost
        ])

        # Extract key info from extracted content
        strengths = extracted_content.get('narrative_strengths', [])
        storytelling = extracted_content.get('storytelling_quality', '')

        prompt = f"""You are a nationally-recognized grant writing expert providing premium coaching.

**NARRATIVE DIMENSION:** {criterion.title}
**Initial Narrative Score:** {initial_findings['score']}/10

**CURRENT STRENGTHS:**
{json.dumps(strengths[:5], indent=2)}

**STORYTELLING ASSESSMENT:**
{storytelling}

**EVIDENCE SAMPLE:**
{evidence_text}

**INITIAL COACHING RECOMMENDATIONS:**
{json.dumps(initial_findings.get('recommendations', []), indent=2)}

**YOUR TASK: EXPERT-LEVEL COACHING**

As a senior expert, refine and enhance the coaching recommendations:

1. **Validate Recommendations:**
   - Are these suggestions truly valuable?
   - Remove any that ask for content that's already strong
   - Focus on high-impact improvements

2. **Add Expert Insights:**
   - What do highly competitive proposals do differently?
   - What narrative strategies work best for this type of project?
   - How to make this proposal memorable to reviewers?

3. **Prioritize Ruthlessly:**
   - What 2-3 changes would have the BIGGEST impact?
   - Which team strengths are most underutilized?
   - What would make reviewers enthusiastic advocates?

**Output Format (JSON):**
{{
  "validated_narrative_score": <0-10>,
  "score_explanation": "Expert assessment of narrative quality",
  "high_impact_recommendations": [
    {{
      "priority": "CRITICAL/HIGH",
      "recommendation": "Specific, actionable coaching",
      "expected_impact": "How this strengthens competitiveness",
      "implementation_tip": "Concrete guidance on how to implement"
    }}
  ],
  "narrative_strengths_to_preserve": ["What's working well - don't change"],
  "competitive_positioning_advice": "How to stand out from other proposals"
}}

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.validation_model,  # Use GPT-4o for validation
                messages=[
                    {"role": "system", "content": "You are a senior reviewer. Be strict - only confirm true gaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            # Track cost (GPT-4o is more expensive)
            self.total_cost += 0.03  # Approximate

            result = json.loads(response.choices[0].message.content)

            final_score = result.get('validated_narrative_score', initial_findings['score'])

            # Format high-impact recommendations
            high_impact_recs = []
            for rec_item in result.get('high_impact_recommendations', []):
                priority = rec_item.get('priority', 'HIGH')
                rec_text = rec_item.get('recommendation', '')
                impact = rec_item.get('expected_impact', '')
                tip = rec_item.get('implementation_tip', '')
                high_impact_recs.append(f"[{priority}] {rec_text}\n   Impact: {impact}\n   How: {tip}")

            # Add competitive positioning advice as recommendation
            positioning = result.get('competitive_positioning_advice', '')
            if positioning:
                high_impact_recs.append(f"[POSITIONING] {positioning}")

            print(f"      ✓ Expert-validated score: {final_score}/10 (was {initial_findings['score']})")
            print(f"      ✓ High-impact recommendations: {len(high_impact_recs)}")
            if result.get('narrative_strengths_to_preserve'):
                print(f"      ✓ Strengths to preserve: {len(result['narrative_strengths_to_preserve'])}")

            return EvaluationResult(
                criterion=criterion,
                score=float(final_score),
                evidence_found=evidence,
                gaps=[],  # No gaps - this is coaching mode
                recommendations=high_impact_recs,
                team_alignment={}
            )

        except Exception as e:
            print(f"      ⚠️ Error in validation: {e}")
            # Fallback to initial findings
            return EvaluationResult(
                criterion=criterion,
                score=initial_findings['score'],
                evidence_found=evidence,
                gaps=initial_findings['gaps'],
                recommendations=initial_findings['recommendations'],
                team_alignment={}
            )

    def _llm_evaluate(
        self,
        criterion: RubricCriterion,
        evidence: List[Tuple[str, str]],
        team_alignment: Dict[str, List[str]]
    ) -> EvaluationResult:
        """
        Use LLM to score the criterion and generate recommendations.
        """
        # Format evidence for prompt
        evidence_text = "\n\n".join([
            f"**Evidence {i+1}** {citation}\n{content}"
            for i, (content, citation) in enumerate(evidence)
        ])

        # Format team alignment - IMPROVED to show more detail
        team_text = self._format_team_context(team_alignment)

        # Generate team metadata summary
        team_members = self.team_data.get("team_members", [])
        team_metadata = f"""
**TEAM DOCUMENTATION STATUS:**
✅ Full CVs/Biosketches have been uploaded and analyzed for {len(team_members)} team member(s).
✅ Detailed expertise, publications, and qualifications extracted from uploaded vitae.
"""

        # Add proposal priority context to prevent wrong criteria evaluation
        priority_context = ""
        if self.proposal_priority:
            priority = self.proposal_priority.get('primary_priority', 'Unknown')
            audience = self.proposal_priority.get('target_audience', 'Unknown')
            priority_context = f"""
**🚨 CRITICAL - PROPOSAL PRIORITY CONTEXT 🚨**

This proposal explicitly targets: **{priority}**
Primary audience: **{audience}**

**PRIORITY 6 FOCUS: Creation of New High-Quality Short-Term Programs**
This proposal should be evaluated based on:
1. Development of SHORT-TERM PROGRAMS (micro-credentials, certificates)
2. WORKFORCE PELL ELIGIBILITY alignment
3. Three CORE ACTIVITIES:
   • Engaging employers and industry partners
   • Developing talent marketplaces/platforms
   • Integrating work-based learning (WBL) components
4. Alignment with HIGH-SKILL, HIGH-WAGE, IN-DEMAND sectors
5. Institutional capacity to deliver short-term programs

**MANDATORY RELEVANCE CHECK:**
Before evaluating this criterion, you MUST determine if it is relevant to Priority 6.

❌ **DO NOT EVALUATE** criteria that apply to different priorities:
   - If this is Priority 6 (Short-Term Programs), DO NOT evaluate:
     • K-12 teacher preparation/training
     • SEA/LEA partnerships (school districts)
     • Four-year degree programs
     • Traditional semester-long courses
     • Pre-service teacher education

   - If this is Priority 1 or 2, DO NOT evaluate Priority 6 specific elements

✅ **DO EVALUATE** for Priority 6:
   • Short-term program design (weeks/months, not years)
   • Workforce Pell compliance and eligibility
   • Employer engagement strategies
   • Talent marketplace development
   • Work-based learning integration
   • Micro-credentials and stackable pathways
   • In-demand industry sector alignment (AI, tech, healthcare, etc.)
   • Data collection for Workforce Pell reporting

If this criterion is NOT RELEVANT to Priority 6, you MUST mark it as "not_applicable" in your response and skip detailed evaluation.
"""

        prompt = f"""You are an expert grant proposal coach with deep experience in competitive proposal review. Your task is to evaluate how well this proposal addresses the following evaluation criterion.

{priority_context}

**CRITERION TO EVALUATE:**
Title: {criterion.title}
Description: {criterion.description}
Weight: {criterion.weight_points} points
Key Keywords: {', '.join(criterion.keywords)}
Compliance Requirements: {', '.join(criterion.compliance_requirements) if criterion.compliance_requirements else 'None specified'}

**EVIDENCE FROM PROPOSAL NARRATIVE:**
{evidence_text if evidence else "⚠️ No strong evidence found in narrative for this criterion."}

**📋 HOW TO READ THE EVIDENCE:**
- Look for text like "[Embedded Image X - imageY.jpg]:" followed by OCR'd content
- This OCR content often contains TABLES, METRICS, WORKFLOWS, and DATA
- Don't dismiss evidence just because it's from OCR - it's just as valid as regular text
- Prior work, case studies, and examples may be scattered across multiple evidence pieces
- Table references (e.g., "Table 11a") indicate data IS present - look for OCR sections
- Section numbers follow the proposal's structure (e.g., A.1, B.2.1, C.3) - not generic "Section 1.2"

{team_metadata if team_members else "⚠️ No team CVs/biosketches have been uploaded for analysis."}

**TEAM COMPETENCIES RELEVANT TO THIS CRITERION:**
{team_text if team_alignment else "⚠️ No team members found with expertise matching this criterion's keywords."}

**YOUR EVALUATION TASK:**

🚨 **CRITICAL INSTRUCTION - EVIDENCE-BASED EVALUATION ONLY** 🚨

You are performing an EVIDENCE-BASED evaluation. Your job is to assess ONLY what is documented in the evidence provided above.

**DO:**
✅ Give credit for content that IS present in the evidence (even if not perfectly formatted)
✅ Score based on ACTUAL evidence found, not theoretical ideals
✅ Recognize that tables, metrics, and workflows may be in OCR'd images
✅ Acknowledge prior work, case studies, and data when they appear in evidence

**DO NOT:**
❌ Suggest adding content that already exists in the evidence
❌ Recommend "best practices" if the content is already there
❌ Claim metrics are "missing" if they appear in tables (check OCR sections)
❌ Request additional sections if existing sections already cover the topic
❌ Penalize for formatting choices (narrative vs. table presentation)

**Evaluation Focus:**
1. **Evidence Review**: Is this criterion addressed in the provided evidence? (If YES, score 7+)
2. **Depth Check**: Does the evidence provide specific examples, data, or methodology?
3. **True Gaps ONLY**: Only report gaps if the evidence genuinely lacks the required content
4. **Constructive Feedback**: If content exists but could be stronger, acknowledge what's there first

Provide your evaluation as a JSON object with the following structure:

{{
  "criterion_relevance": "applicable/not_applicable",
  "relevance_explanation": "Brief explanation of why this criterion is or is not relevant to the proposal's stated priority",
  "score": <0-10, where 10 is excellent and competitive, OR null if not_applicable>,
  "score_rationale": "2-3 sentences explaining the score, citing specific strengths or weaknesses",
  "evidence_quality": "strong/moderate/weak",
  "specific_strengths": [
    "Specific strength 1 with evidence location (be concrete - cite sections/pages)",
    "Specific strength 2 with concrete examples"
  ],
  "hidden_weaknesses": [
    "Non-obvious weakness 1 that humans might miss",
    "Competitive gap 2 that becomes apparent when compared to strong proposals"
  ],
  "missing_synergies": [
    "Opportunity 1: Connection between team expertise and proposal that isn't exploited",
    "Opportunity 2: Potential collaboration or methodology that would strengthen the proposal"
  ],
  "recommendations": [
    {{
      "priority": "critical/high/medium",
      "action": "Specific actionable recommendation",
      "rationale": "Why this will strengthen the proposal",
      "implementation": "Concrete steps: e.g., 'Add paragraph in Section 2.3 citing Dr. X's 2023 work on Y'"
    }}
  ],
  "reviewer_perspective": "What a reviewer would think when evaluating this criterion"
}}

**CRITICAL GUIDELINES FOR RECOMMENDATIONS:**

🚨 **RULE #1: NEVER recommend adding content that already exists in the evidence!** 🚨

Before making ANY recommendation, verify:
1. Is the content truly ABSENT from all evidence pieces?
2. Is it missing from narrative text AND OCR'd tables/images?
3. Have you checked all [Embedded Image X] sections for this data?

**Recommendation Types (ONLY use if content is truly missing):**
1. **True Gaps**: Content genuinely not found in any evidence → Recommend adding
2. **Strengthening Existing**: Content exists but could be more explicit → Acknowledge what's there, suggest enhancement
3. **Better Presentation**: Content exists but buried → Suggest making it more prominent
4. **Cross-References**: Content in one section could be cited elsewhere → Suggest linking

**What NOT to Recommend:**
❌ "Add Table X with metrics" if Table X already exists (check OCR sections!)
❌ "Include prior work examples" if Section B.2.1 lists them
❌ "Add employer engagement strategies" if they're documented in the evidence
❌ "Include letters of support" if they're referenced (they're separate attachments)
❌ "Add Section X.Y" using made-up section numbers not in the proposal

**Format for Valid Recommendations:**
"[PRIORITY] Action: [Specific recommendation]. Rationale: [Why this strengthens the proposal]. Implementation: [Exactly where and how to add this, using ACTUAL section numbers from the proposal]"

**If Evidence is Strong (score 7+):**
Focus on MINOR enhancements, not major additions. Acknowledge strengths first.

**SCORING GUIDELINES:**
- 9-10: Excellent, highly competitive - strong evidence, clear methodology, well-aligned team
- 7-8: Good, competitive - solid foundation with minor gaps
- 5-6: Adequate but needs strengthening - key elements present but weak
- 3-4: Weak - major gaps in evidence or team alignment
- 0-2: Very weak - criterion barely addressed

Respond ONLY with valid JSON.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise grant evaluation coach. Provide actionable feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            # Check if criterion is not applicable
            if data.get("criterion_relevance") == "not_applicable":
                print(f"   ⚠️ Criterion marked as NOT APPLICABLE: {data.get('relevance_explanation', 'No explanation')}")
                # Return a special result that will be filtered out later
                return EvaluationResult(
                    criterion=criterion,
                    score=None,  # None indicates not applicable
                    evidence_found=[],
                    gaps=[f"NOT APPLICABLE: {data.get('relevance_explanation', 'This criterion does not apply to the proposal priority')}"],
                    recommendations=[],
                    team_alignment={}
                )

            # Format recommendations from new structure to simple list for backwards compatibility
            recommendations = data.get("recommendations", [])
            if recommendations and isinstance(recommendations[0], dict):
                formatted_recs = []
                for rec in recommendations:
                    priority = rec.get("priority", "medium").upper()
                    action = rec.get("action", "")
                    implementation = rec.get("implementation", "")
                    formatted_recs.append(f"[{priority}] {action}. {implementation}")
                recommendations = formatted_recs

            # Combine gaps with hidden weaknesses and missing synergies for comprehensive gap analysis
            all_gaps = []
            if data.get("hidden_weaknesses"):
                all_gaps.extend([f"Hidden Weakness: {w}" for w in data.get("hidden_weaknesses", [])])
            if data.get("missing_synergies"):
                all_gaps.extend([f"Missing Synergy: {s}" for s in data.get("missing_synergies", [])])
            # Include any traditional gaps too
            if data.get("gaps"):
                all_gaps.extend(data.get("gaps", []))

            result = EvaluationResult(
                criterion=criterion,
                score=float(data.get("score", 5.0)),
                evidence_found=evidence,
                gaps=all_gaps if all_gaps else data.get("gaps", []),
                recommendations=recommendations,
                team_alignment=team_alignment
            )

            print(f"   Score: {result.score}/10 ({data.get('evidence_quality', 'unknown')} evidence)")
            if data.get("specific_strengths"):
                print(f"   Strengths: {len(data.get('specific_strengths', []))}")
            if data.get("gaps"):
                print(f"   Gaps: {len(data.get('gaps', []))}")
            return result

        except Exception as e:
            print(f"   ❌ Error in LLM evaluation: {e}")
            return EvaluationResult(
                criterion=criterion,
                score=5.0,
                evidence_found=evidence,
                gaps=["Error during evaluation"],
                recommendations=["Review this section manually"],
                team_alignment=team_alignment
            )

    def generate_compliance_report(self) -> Dict:
        """
        Simplified compliance - just return a status.
        Deep compliance analysis is better done by humans.

        Returns: Compliance status dict
        """
        # Skip detailed compliance checks - focus on deep evaluation instead
        return {
            "status": "MANUAL_REVIEW",
            "checks": [],
            "message": "Please manually review solicitation compliance requirements"
        }

    def calculate_win_probability(self, evaluation_results: List[EvaluationResult]) -> float:
        """
        Calculate overall win probability based on criterion scores.

        Returns: Probability percentage (0-100)
        """
        if not evaluation_results:
            return 0.0

        # Weighted average if weights are available
        total_weight = sum(r.criterion.weight_points for r in evaluation_results)

        if total_weight > 0:
            weighted_score = sum(
                r.score * r.criterion.weight_points
                for r in evaluation_results
            ) / total_weight
        else:
            # Unweighted average
            weighted_score = sum(r.score for r in evaluation_results) / len(evaluation_results)

        # Convert 0-10 score to 0-100 probability
        probability = (weighted_score / 10) * 100

        return round(probability, 1)

    def run_full_evaluation(self) -> Dict:
        """
        Execute the complete evaluation pipeline.

        Returns: Comprehensive evaluation report data
        """
        print("\n" + "="*60)
        print("🚀 Starting Full Proposal Evaluation")
        print("="*60)

        # Important notice about PDF limitations
        print("\n⚠️  IMPORTANT: PDF Table Extraction Limitation")
        print("   Tables and data visualizations in PDFs may not be fully extracted.")
        print("   If the report claims data is missing, please manually verify tables.")
        print("   Consider providing DOCX versions for better data extraction.")

        # Step 0: Detect proposal priority/target audience
        print("\n📍 Step 0: Detecting proposal focus...")
        self.detect_proposal_priority()

        # Step 1: Extract rubric
        rubric = self.extract_rubric()

        # Step 2: Evaluate each criterion
        all_results = []
        for criterion in rubric:
            result = self.evaluate_criterion(criterion)
            all_results.append(result)

        # Filter out non-applicable criteria
        evaluation_results = [r for r in all_results if r.score is not None]
        skipped_criteria = [r for r in all_results if r.score is None]

        if skipped_criteria:
            print(f"\n⚠️  Skipped {len(skipped_criteria)} criterion/criteria not relevant to this proposal's priority:")
            for r in skipped_criteria:
                print(f"   - {r.criterion.title}")

        # Step 3: Compliance check
        compliance = self.generate_compliance_report()

        # Step 4: Calculate win probability (only from applicable criteria)
        win_probability = self.calculate_win_probability(evaluation_results)

        # Step 5: Compile report data
        report_data = {
            "win_probability": win_probability,
            "total_criteria": len(rubric),
            "evaluated_criteria": len(evaluation_results),
            "skipped_criteria": len(skipped_criteria),
            "proposal_priority": self.proposal_priority if self.proposal_priority else {"primary_priority": "Unknown", "target_audience": "Unknown"},
            "skipped_criteria_details": [
                {
                    "title": r.criterion.title,
                    "reason": r.gaps[0] if r.gaps else "Not applicable to proposal priority"
                }
                for r in skipped_criteria
            ],
            "compliance_status": compliance["status"],
            "compliance_findings": compliance["checks"],
            "criterion_evaluations": [
                {
                    "title": r.criterion.title,
                    "score": r.score,
                    "weight": r.criterion.weight_points,
                    "gaps": r.gaps,
                    "recommendations": r.recommendations,
                    "team_alignment": r.team_alignment,
                    "evidence_count": len(r.evidence_found)
                }
                for r in evaluation_results
            ],
            "team_summary": {
                "total_members": len(self.team_data.get("team_members", [])),
                "members": [
                    {
                        "name": m.get("name"),
                        "title": m.get("title"),
                        "expertise_areas": m.get("research_interests", [])[:3]
                    }
                    for m in self.team_data.get("team_members", [])
                ]
            }
        }

        print("\n" + "="*60)
        print(f"✅ Evaluation Complete!")
        print(f"   Win Probability: {win_probability}%")
        print(f"   Criteria Evaluated: {len(rubric)}")
        print(f"   💰 Total API Cost: ${self.total_cost:.3f}")
        print("="*60)

        # Add cost to report
        report_data['api_cost'] = round(self.total_cost, 3)

        return report_data


# CLI Interface for testing
if __name__ == "__main__":
    import sys
    from ingester import DocumentIngester
    from faculty_bot import FacultyBot

    print("=" * 60)
    print("🧠 GrantScout: Competency Engine")
    print("=" * 60)

    # This would normally receive data from the main orchestrator
    # For testing, we'll use placeholder logic

    if len(sys.argv) < 3:
        print("\nUsage: python evaluator.py <solicitation_path> <narrative_path> [team_json_path]")
        print("\nExample:")
        print("  python evaluator.py data/rfp.pdf data/draft.docx data/Team_Competency.json")
        sys.exit(1)

    solicitation_path = sys.argv[1]
    narrative_path = sys.argv[2]
    team_json_path = sys.argv[3] if len(sys.argv) > 3 else None

    # Load team data if provided
    team_data = {"team_members": []}
    if team_json_path:
        with open(team_json_path, 'r') as f:
            team_data = json.load(f)

    # Ingest documents
    print("\n📚 Loading documents...")
    ingester = DocumentIngester()
    ingester.ingest_multiple({
        "solicitation": solicitation_path,
        "narrative": narrative_path
    })

    # Run evaluation
    engine = CompetencyEngine(ingester=ingester, team_data=team_data)
    report = engine.run_full_evaluation()

    # Save report
    output_path = "data/evaluation_report.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Report saved to: {output_path}")
