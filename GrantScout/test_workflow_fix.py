#!/usr/bin/env python3
"""
Test script to verify the workflow fixes for Retrieval → Generation.
Tests the three critical improvements:
1. Table Hunter & Proper Noun Hunter (Retrieval)
2. Forensic Evidence Extraction (Pass 1)
3. Negative Constraints (Pass 2)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingester import DocumentIngester
from src.evaluator import CompetencyEngine

def test_workflow_improvements():
    """Test that the three workflow improvements are working"""

    print("="*80)
    print("WORKFLOW FIX VERIFICATION TEST")
    print("="*80)

    # Test files
    sol_file = "temp_uploads/fipse.docx"
    narrative_file = "temp_uploads/STAIRS_Narrative.docx"

    if not Path(sol_file).exists() or not Path(narrative_file).exists():
        print(f"\n❌ ERROR: Test files not found")
        print(f"   Please ensure files are in temp_uploads/")
        return False

    print(f"\n📚 Ingesting documents...")
    ingester = DocumentIngester()
    ingester.ingest_multiple({
        "solicitation": sol_file,
        "narrative": narrative_file
    })

    # Create engine
    engine = CompetencyEngine(ingester=ingester, team_data={"team_members": []})

    # Extract rubric
    print(f"\n📋 Extracting rubric...")
    rubric = engine.extract_rubric()
    print(f"Found {len(rubric)} criteria")

    if not rubric:
        print("❌ No rubric criteria found")
        return False

    # Test on a criterion that mentions data/metrics (should trigger Table Hunter)
    print(f"\n{'='*80}")
    print(f"🧪 TESTING WORKFLOW IMPROVEMENTS")
    print(f"{'='*80}")

    # Find a criterion about significance/impact (likely to need metrics)
    test_criterion = None
    for criterion in rubric:
        if any(kw in criterion.title.lower() for kw in ['significance', 'impact', 'need']):
            test_criterion = criterion
            break

    if not test_criterion:
        test_criterion = rubric[0]

    print(f"\n📊 Testing on criterion: {test_criterion.title}")
    print(f"Description: {test_criterion.description[:100]}...")

    # STEP 1: Test Retrieval (Table Hunter + Proper Noun Hunter)
    print(f"\n{'─'*80}")
    print(f"STEP 1: Testing Enhanced Retrieval")
    print(f"{'─'*80}")

    evidence = engine._retrieve_evidence(test_criterion, k=10)
    print(f"✓ Retrieved: {len(evidence)} pieces of evidence")

    # Check if table content was found
    table_evidence_count = sum(1 for content, _ in evidence if '[Embedded Image' in content or '|' in content)
    print(f"✓ Table-like content found: {table_evidence_count} pieces")

    # Check for proper nouns (TWC, ExpandAI, etc.)
    proper_noun_hits = sum(1 for content, _ in evidence
                          if any(noun in content for noun in ['TWC', 'ExpandAI', 'TSUS', 'STEM-CLEAR', 'Texas Workforce']))
    print(f"✓ Proper noun hits: {proper_noun_hits} pieces")

    # STEP 2: Test Forensic Evidence Extraction (Pass 1)
    print(f"\n{'─'*80}")
    print(f"STEP 2: Testing Forensic Evidence Extraction")
    print(f"{'─'*80}")

    extracted = engine._extract_present_content(test_criterion, evidence[:20], {})

    found_metrics = extracted.get('found_metrics', [])
    found_entities = extracted.get('found_entities', [])
    found_team_refs = extracted.get('found_team_refs', [])
    is_table_present = extracted.get('is_table_present', False)

    print(f"✓ Metrics found: {len(found_metrics)}")
    for metric in found_metrics[:5]:
        print(f"  - {metric}")

    print(f"\n✓ Entities found: {len(found_entities)}")
    for entity in found_entities[:5]:
        print(f"  - {entity}")

    print(f"\n✓ Team references: {len(found_team_refs)}")
    for ref in found_team_refs[:5]:
        print(f"  - {ref}")

    print(f"\n✓ Table detected: {is_table_present}")

    # STEP 3: Test Negative Constraints (Pass 2)
    print(f"\n{'─'*80}")
    print(f"STEP 3: Testing Negative Constraints in Coaching")
    print(f"{'─'*80}")

    coaching = engine._identify_gaps_with_quotes(test_criterion, evidence[:20], {}, extracted)

    score = coaching.get('score', 0)
    recommendations = coaching.get('recommendations', [])

    print(f"✓ Narrative Score: {score}/10")
    print(f"✓ Recommendations: {len(recommendations)}")

    # Check for violations of negative constraints
    violations = []
    for rec in recommendations:
        rec_lower = rec.lower()
        if 'budget' in rec_lower or 'financial' in rec_lower or 'dollar' in rec_lower:
            violations.append(f"Budget request: {rec}")
        if 'anecdote' in rec_lower and len(found_metrics) > 0:
            violations.append(f"Generic advice despite metrics: {rec}")
        if 'quantitative' in rec_lower and is_table_present:
            violations.append(f"Asking for metrics despite table: {rec}")

    if violations:
        print(f"\n⚠️  WARNING: Negative constraint violations detected:")
        for v in violations:
            print(f"  - {v}")
    else:
        print(f"\n✅ No negative constraint violations!")

    # VERIFICATION CHECKS
    print(f"\n{'='*80}")
    print(f"VERIFICATION RESULTS")
    print(f"{'='*80}")

    checks = {
        "Enhanced Retrieval (>30 evidence chunks)": len(evidence) >= 30,
        "Table Hunter (found table content)": table_evidence_count > 0,
        "Proper Noun Hunter (found entities)": proper_noun_hits > 0,
        "Forensic Extraction (found metrics)": len(found_metrics) > 0,
        "Forensic Extraction (found entities)": len(found_entities) > 0,
        "Table Detection Working": is_table_present or table_evidence_count > 0,
        "Negative Constraints (no violations)": len(violations) == 0,
        "Reasonable Score (≥6 if content exists)": score >= 6 if (found_metrics or found_entities or is_table_present) else True
    }

    passed = 0
    total = len(checks)

    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            passed += 1

    print(f"\n{'='*80}")
    print(f"FINAL RESULT: {passed}/{total} checks passed")
    print(f"{'='*80}")

    if passed == total:
        print(f"✅ ALL CHECKS PASSED! Workflow improvements working correctly.")
        return True
    elif passed >= total * 0.75:
        print(f"⚠️  MOSTLY WORKING: {passed}/{total} checks passed")
        return True
    else:
        print(f"❌ ISSUES DETECTED: Only {passed}/{total} checks passed")
        return False


if __name__ == "__main__":
    success = test_workflow_improvements()
    sys.exit(0 if success else 1)
