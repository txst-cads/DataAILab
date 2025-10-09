"""
Grant Coach - Main Application Entry Point

Orchestrates all modules for comprehensive grant proposal evaluation.
Follows Single Responsibility Principle by focusing only on workflow orchestration.
"""

import argparse
import os
import json
import sys
from datetime import datetime
from typing import Dict, Optional

# Import modules
from document_processor import DocumentProcessor
from similarity_analyzer import SimilarityAnalyzer
from llm_evaluator import LLMEvaluator
from report_generator import ReportGenerator


class GrantCoach:
    """
    Main Grant Coach application that orchestrates all analysis modules.
    """

    def __init__(self, use_mock_llm: bool = False):
        """
        Initialize Grant Coach with all modules.

        Args:
            use_mock_llm: Whether to use mock LLM responses for testing
        """
        self.document_processor = DocumentProcessor()
        self.similarity_analyzer = SimilarityAnalyzer()
        self.llm_evaluator = LLMEvaluator(use_mock_llm=use_mock_llm)
        self.report_generator = ReportGenerator()
        self.analysis_results = {}

    def analyze_proposals(self, solicitation_path: str, proposal_path: str,
                         save_intermediate: bool = True,
                         output_format: str = "both") -> Dict:
        """
        Perform complete analysis of grant proposal against solicitation.

        Args:
            solicitation_path: Path to solicitation PDF
            proposal_path: Path to proposal PDF
            save_intermediate: Whether to save intermediate results
            output_format: Output format ('json', 'txt', 'both')

        Returns:
            Complete analysis results dictionary
        """
        print("🚀 Starting Grant Coach Analysis...")
        print(f"📄 Solicitation: {solicitation_path}")
        print(f"📝 Proposal: {proposal_path}")
        print("="*60)

        # Step 1: Document Processing
        print("📋 Step 1: Processing documents...")
        try:
            processed_data = self.document_processor.process_documents(
                solicitation_path, proposal_path
            )

            # Add processing timestamp
            processed_data["metadata"]["processing_date"] = datetime.now().isoformat()

            # Generate document statistics
            stats = self.document_processor.get_document_statistics(processed_data)
            processed_data["statistics"] = stats

            # Validate NSF requirements
            nsf_validation = self.document_processor.validate_nsf_requirements(
                processed_data["sections"]["proposal"]
            )

            print(f"  ✓ Solicitation: {stats['solicitation']['char_count']} chars, "
                  f"{stats['solicitation']['section_count']} sections, "
                  f"{stats['solicitation']['chunk_count']} chunks")
            print(f"  ✓ Proposal: {stats['proposal']['char_count']} chars, "
                  f"{stats['proposal']['section_count']} sections, "
                  f"{stats['proposal']['chunk_count']} chunks")
            print(f"  ✓ Total chunks for analysis: {stats['total_chunks']}")
            print(f"  ✓ NSF requirements: {'✓' if all(nsf_validation.values()) else '⚠'}")

            if save_intermediate:
                self._save_intermediate_results("processed_data", processed_data)

        except Exception as e:
            print(f"  ❌ Document processing failed: {e}")
            raise

        # Step 2: Similarity Analysis
        print("\n🔍 Step 2: Performing similarity analysis...")
        try:
            # Build similarity index
            self.similarity_analyzer.build_index(
                processed_data["chunks"]["solicitation"],
                processed_data["chunks"]["proposal"]
            )

            # Analyze proposal-solicitation alignment
            alignment_results = self.similarity_analyzer.analyze_proposal_solicitation_alignment(
                processed_data
            )

            # Find gaps in proposal coverage
            gaps_analysis = self.similarity_analyzer.find_gaps_in_proposal(processed_data)

            # Calculate overall alignment score
            overall_alignment = sum(
                result['score'] for result in alignment_results.values()
            ) / len(alignment_results) if alignment_results else 0.0

            print(f"  ✓ Index built with {stats['total_chunks']} chunks")
            print(f"  ✓ Overall alignment score: {overall_alignment:.3f}")
            print(f"  ✓ Sections analyzed: {len(alignment_results)}")
            print(f"  ✓ Coverage gaps identified: {len(gaps_analysis)}")

            if save_intermediate:
                self._save_intermediate_results("alignment_analysis", {
                    "alignment_results": alignment_results,
                    "gaps_analysis": gaps_analysis,
                    "overall_alignment": overall_alignment
                })

        except Exception as e:
            print(f"  ❌ Similarity analysis failed: {e}")
            raise

        # Step 3: LLM Evaluation
        print("\n🤖 Step 3: Evaluating proposal quality...")
        try:
            # Extract faculty information
            faculty_info = self.llm_evaluator.extract_faculty_information(
                processed_data["sections"]["proposal"]
            )

            # Evaluate proposal quality
            evaluation_results = self.llm_evaluator.evaluate_proposal_quality(
                processed_data["sections"]["proposal"],
                alignment_results
            )

            # Generate evaluation summary
            evaluation_summary = self.llm_evaluator.generate_evaluation_summary(
                evaluation_results
            )

            overall_score = evaluation_summary["overall_score"]

            print(f"  ✓ Faculty information extracted")
            print(f"  ✓ Proposal quality evaluated")
            print(f"  ✓ Overall quality score: {overall_score:.2f}/10.0")
            print(f"  ✓ Assessment category: {evaluation_summary['category']}")

            if save_intermediate:
                self._save_intermediate_results("llm_evaluation", {
                    "faculty_info": faculty_info,
                    "evaluation_results": [
                        {
                            "criterion": result.criterion,
                            "score": result.score,
                            "justification": result.justification,
                            "strengths": result.strengths,
                            "weaknesses": result.weaknesses,
                            "recommendations": result.recommendations
                        }
                        for result in evaluation_results
                    ],
                    "evaluation_summary": evaluation_summary
                })

        except Exception as e:
            print(f"  ❌ LLM evaluation failed: {e}")
            raise

        # Step 4: Report Generation
        print("\n📊 Step 4: Generating comprehensive report...")
        try:
            # Generate comprehensive report
            report = self.report_generator.generate_comprehensive_report(
                processed_data,
                alignment_results,
                evaluation_results,
                faculty_info,
                gaps_analysis
            )

            # Generate quick summary for console
            quick_summary = self.report_generator.generate_quick_summary(report)

            print(f"  ✓ Comprehensive report generated")
            print(f"  ✓ Quick summary prepared")

            # Save reports
            self._save_final_reports(report, output_format)

            # Print summary to console
            print(f"\n{quick_summary}")

        except Exception as e:
            print(f"  ❌ Report generation failed: {e}")
            raise

        # Step 5: Save final results
        print("\n💾 Step 5: Saving final results...")
        try:
            # Save index for future use
            index_path = "data/final_document_index.faiss"
            self.similarity_analyzer.save_index(index_path)
            print(f"  ✓ FAISS index saved to {index_path}")

            # Compile final results
            final_results = {
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "solicitation_file": solicitation_path,
                    "proposal_file": proposal_path,
                    "overall_score": float(overall_score),
                    "alignment_score": float(overall_alignment),
                    "assessment_category": evaluation_summary["category"]
                },
                "document_statistics": stats,
                "nsf_compliance": nsf_validation,
                "alignment_analysis": alignment_results,
                "evaluation_summary": evaluation_summary,
                "recommendations": [
                    {"text": rec.text, "priority": rec.priority, "category": rec.category}
                    for rec in report["detailed_recommendations"][:5]
                ]
            }

            # Save final summary
            with open("data/final_analysis_summary.json", "w") as f:
                json.dump(final_results, f, indent=2, default=str)

            print("  ✓ Final analysis summary saved")

        except Exception as e:
            print(f"  ❌ Final results saving failed: {e}")
            raise

        print("\n✅ Analysis completed successfully!")
        print("="*60)

        return {
            "processed_data": processed_data,
            "alignment_results": alignment_results,
            "evaluation_results": evaluation_results,
            "faculty_info": faculty_info,
            "gaps_analysis": gaps_analysis,
            "report": report,
            "final_summary": final_results
        }

    def _save_intermediate_results(self, name: str, data: Dict):
        """Save intermediate analysis results."""
        filepath = f"data/intermediate_{name}.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"    💾 Saved to {filepath}")

    def _save_final_reports(self, report: Dict, output_format: str):
        """Save final reports in specified format(s)."""
        if output_format in ["json", "both"]:
            self.report_generator.save_report_to_file(
                report, "data/final_report.json", "json"
            )
            print(f"    💾 JSON report saved to data/final_report.json")

        if output_format in ["txt", "both"]:
            self.report_generator.save_report_to_file(
                report, "data/final_report.txt", "txt"
            )
            print(f"    💾 Text report saved to data/final_report.txt")

    def validate_inputs(self, solicitation_path: str, proposal_path: str) -> bool:
        """
        Validate input file paths.

        Args:
            solicitation_path: Path to solicitation PDF
            proposal_path: Path to proposal PDF

        Returns:
            True if inputs are valid, False otherwise
        """
        if not os.path.exists(solicitation_path):
            print(f"❌ Solicitation file not found: {solicitation_path}")
            return False

        if not solicitation_path.lower().endswith('.pdf'):
            print(f"❌ Solicitation must be a PDF file: {solicitation_path}")
            return False

        if not os.path.exists(proposal_path):
            print(f"❌ Proposal file not found: {proposal_path}")
            return False

        if not proposal_path.lower().endswith('.pdf'):
            print(f"❌ Proposal must be a PDF file: {proposal_path}")
            return False

        return True


def main():
    """Main entry point for Grant Coach application."""
    parser = argparse.ArgumentParser(
        description="Grant Coach - AI-powered grant proposal evaluation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python grant_coach.py solicitation.pdf proposal.pdf
  python grant_coach.py solicitation.pdf proposal.pdf --save-intermediate
  python grant_coach.py solicitation.pdf proposal.pdf --format json
  python grant_coach.py solicitation.pdf proposal.pdf --mock-llm
        """
    )

    parser.add_argument(
        "solicitation",
        help="Path to solicitation PDF file"
    )

    parser.add_argument(
        "proposal",
        help="Path to proposal PDF file"
    )

    parser.add_argument(
        "--save-intermediate",
        action="store_true",
        help="Save intermediate analysis results"
    )

    parser.add_argument(
        "--format",
        choices=["json", "txt", "both"],
        default="both",
        help="Output format for final report (default: both)"
    )

    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use mock LLM responses for testing"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Initialize Grant Coach
    try:
        grant_coach = GrantCoach(use_mock_llm=args.mock_llm)

        if args.verbose:
            print("🔧 Grant Coach initialized successfully")
            print(f"  - Mock LLM: {'Enabled' if args.mock_llm else 'Disabled'}")
            print(f"  - Output format: {args.format}")
            print(f"  - Save intermediate: {args.save_intermediate}")

    except Exception as e:
        print(f"❌ Failed to initialize Grant Coach: {e}")
        sys.exit(1)

    # Validate inputs
    if not grant_coach.validate_inputs(args.solicitation, args.proposal):
        sys.exit(1)

    # Perform analysis
    try:
        results = grant_coach.analyze_proposals(
            solicitation_path=args.solicitation,
            proposal_path=args.proposal,
            save_intermediate=args.save_intermediate,
            output_format=args.format
        )

        if args.verbose:
            print("\n📈 Analysis Summary:")
            print(f"  - Overall Score: {results['final_summary']['metadata']['overall_score']:.2f}/10.0")
            print(f"  - Alignment Score: {results['final_summary']['metadata']['alignment_score']:.3f}")
            print(f"  - Category: {results['final_summary']['metadata']['assessment_category']}")
            print(f"  - Recommendations: {len(results['final_summary']['recommendations'])}")

        print(f"\n📁 Results saved to:")
        print(f"  - data/final_report.json")
        print(f"  - data/final_report.txt")
        print(f"  - data/final_analysis_summary.json")

    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()