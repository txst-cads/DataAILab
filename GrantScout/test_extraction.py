#!/usr/bin/env python3
"""
Test script to verify extraction is finding tables, metrics, and strategies.
Run this to see what Pass 1 extraction finds before full evaluation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingester import DocumentIngester
from src.evaluator import CompetencyEngine

print("="*80)
print("EXTRACTION TEST - Verifying Table, Metric, and Strategy Recognition")
print("="*80)

# Ingest documents
print("\n📚 Ingesting documents...")
ingester = DocumentIngester()
ingester.ingest_multiple({
    "solicitation": "temp_uploads/fipse.docx",
    "narrative": "temp_uploads/STAIRS_Narrative.docx"
})

# Create engine
engine = CompetencyEngine(ingester=ingester, team_data={"team_members": []})

# Extract rubric
print("\n📋 Extracting rubric...")
rubric = engine.extract_rubric()
print(f"Found {len(rubric)} criteria")

# Test extraction on first criterion
if rubric:
    test_criterion = rubric[0]
    print(f"\n🧪 Testing extraction for: {test_criterion.title}")
    print("="*80)

    # Get evidence
    evidence = engine._retrieve_evidence(test_criterion, k=5)
    print(f"\n1️⃣ Evidence retrieved: {len(evidence)} chunks")

    # Run Pass 1: Extraction
    print(f"\n2️⃣ Running Pass 1: Extraction...")
    extracted = engine._extract_present_content(test_criterion, evidence, {})

    print("\n📊 EXTRACTION RESULTS:")
    print("="*80)

    print(f"\n✓ Present elements: {len(extracted.get('present_elements', []))}")
    for i, elem in enumerate(extracted.get('present_elements', [])[:5], 1):
        print(f"  {i}. {elem.get('element', 'N/A')[:80]}...")

    print(f"\n✓ Tables found: {len(extracted.get('tables_found', []))}")
    for table in extracted.get('tables_found', []):
        print(f"  - {table}")

    print(f"\n✓ Metrics found: {len(extracted.get('metrics_found', []))}")
    for metric in extracted.get('metrics_found', []):
        print(f"  - {metric}")

    print(f"\n✓ Prior work found: {len(extracted.get('prior_work_found', []))}")
    for work in extracted.get('prior_work_found', []):
        print(f"  - {work}")

    print(f"\n✓ Strategies found: {len(extracted.get('strategies_found', []))}")
    for strategy in extracted.get('strategies_found', []):
        print(f"  - {strategy}")

    print(f"\n✓ Governance mechanisms: {len(extracted.get('governance_mechanisms', []))}")
    for gov in extracted.get('governance_mechanisms', []):
        print(f"  - {gov}")

    print(f"\n✓ Overall summary:")
    print(f"  {extracted.get('overall_summary', 'N/A')}")

    # Now test Pass 2: Gap identification
    print(f"\n\n3️⃣ Running Pass 2: Gap Identification...")
    gaps_result = engine._identify_gaps_with_quotes(test_criterion, evidence, {}, extracted)

    print("\n📊 GAP ANALYSIS RESULTS:")
    print("="*80)
    print(f"\n✓ Score: {gaps_result.get('score', 0)}/10")
    print(f"\n✓ Gaps identified: {len(gaps_result.get('gaps', []))}")
    for gap in gaps_result.get('gaps', []):
        print(f"  - {gap}")

    print(f"\n✓ Recommendations: {len(gaps_result.get('recommendations', []))}")
    for rec in gaps_result.get('recommendations', []):
        print(f"  - {rec}")

    print("\n" + "="*80)
    print("✅ EXTRACTION TEST COMPLETE")
    print("="*80)

    # Check for common failures
    print("\n🔍 VERIFICATION CHECKS:")
    print("-"*80)

    tables_found = extracted.get('tables_found', [])
    metrics_found = extracted.get('metrics_found', [])
    strategies_found = extracted.get('strategies_found', [])
    gaps = gaps_result.get('gaps', [])

    # Check 1: Table blindness
    if tables_found and any('metric' in gap.lower() or 'data' in gap.lower() for gap in gaps):
        print("⚠️  WARNING: Tables found but metrics gap claimed - possible table blindness")
    else:
        print("✅ Table blindness check: PASSED")

    # Check 2: Semantic understanding
    if strategies_found and any('strategy' in gap.lower() or 'adaptation' in gap.lower() for gap in gaps):
        print("⚠️  WARNING: Strategies found but strategy gap claimed - possible semantic failure")
    else:
        print("✅ Semantic understanding check: PASSED")

    # Check 3: Scope leak
    if any('budget' in gap.lower() or 'financial projection' in gap.lower() for gap in gaps):
        print("⚠️  WARNING: Budget/financial gaps claimed - scope leak detected")
    else:
        print("✅ Scope guardrails check: PASSED")

    print("\n" + "="*80)
    print(f"💰 API Cost for this test: ${engine.total_cost:.3f}")
    print("="*80)
