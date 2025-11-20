#!/usr/bin/env python3
"""
AgriGrantCoach-AFRI Main Orchestrator

Entry point for the complete analysis pipeline.
Coordinates all modules to generate comprehensive proposal assessment.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import Config
from src.data_loader import DataLoader
from src.rubric_analyzer import RubricAnalyzer
from src.semantic_analyzer import SemanticAnalyzer
from src.team_analyzer import TeamAnalyzer
from src.report_generator import ReportGenerator


class AgriGrantCoach:
    """Main orchestrator for the analysis pipeline."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.data_loader = DataLoader(config)
        self.rubric_analyzer = RubricAnalyzer(config)
        self.semantic_analyzer = SemanticAnalyzer(config)
        self.team_analyzer = TeamAnalyzer(config)
        self.report_generator = ReportGenerator(config)

    def run_full_analysis(self, save_intermediates: bool = True) -> Path:
        """
        Run the complete analysis pipeline.

        Args:
            save_intermediates: Whether to save intermediate JSON files

        Returns:
            Path to the final report
        """
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║         AgriGrantCoach-AFRI Analysis Pipeline               ║")
        print("║    Comprehensive USDA AFRI Proposal Assessment Tool          ║")
        print("╚══════════════════════════════════════════════════════════════╝\n")

        start_time = datetime.now()

        try:
            # ============================================================
            # PHASE 1: Data Loading
            # ============================================================
            print("\n" + "="*60)
            print("PHASE 1: DOCUMENT LOADING")
            print("="*60)

            all_data = self.data_loader.load_all()

            if save_intermediates:
                self.data_loader.save_chunks_to_json(all_data)

            # ============================================================
            # PHASE 2: Solicitation Analysis
            # ============================================================
            print("\n" + "="*60)
            print("PHASE 2: SOLICITATION RUBRIC EXTRACTION")
            print("="*60)

            rubric = self.rubric_analyzer.extract_rubric(all_data['solicitation']['text'])

            if save_intermediates:
                self.rubric_analyzer.save_rubric(rubric)

            # Quick coverage check
            initial_coverage = self.rubric_analyzer.analyze_requirement_coverage(
                rubric,
                all_data['narrative']['text']
            )

            # ============================================================
            # PHASE 3: Semantic Alignment Analysis
            # ============================================================
            print("\n" + "="*60)
            print("PHASE 3: PROPOSAL-SOLICITATION ALIGNMENT ANALYSIS")
            print("="*60)

            alignment_analysis = self.semantic_analyzer.analyze_proposal_alignment(
                rubric,
                all_data['narrative']['chunks']
            )

            if save_intermediates:
                self.semantic_analyzer.save_alignment_analysis(alignment_analysis)
                self.semantic_analyzer.save_index()

            # ============================================================
            # PHASE 4: Team Analysis
            # ============================================================
            print("\n" + "="*60)
            print("PHASE 4: TEAM EXPERTISE & CAPACITY ANALYSIS")
            print("="*60)

            # Extract individual profiles
            personnel_profiles = {}
            for name, personnel_data_dict in all_data['personnel'].items():
                # Reconstruct PersonnelData object
                from src.data_loader import PersonnelData
                personnel_data = PersonnelData(
                    name=name,
                    biosketch_text=personnel_data_dict['biosketch_text'],
                    cps_text=personnel_data_dict['cps_text'],
                    biosketch_chunks=personnel_data_dict['biosketch_chunks'],
                    cps_chunks=personnel_data_dict['cps_chunks']
                )
                personnel_profiles[name] = self.team_analyzer.extract_pi_profile(
                    name,
                    personnel_data
                )

            # Analyze team composition
            team_analysis = self.team_analyzer.analyze_team_composition(
                personnel_profiles,
                rubric,
                all_data['narrative']['text']
            )

            if save_intermediates:
                self.team_analyzer.save_team_analysis(personnel_profiles, team_analysis)

            # ============================================================
            # PHASE 5: Report Generation
            # ============================================================
            print("\n" + "="*60)
            print("PHASE 5: COMPREHENSIVE REPORT GENERATION")
            print("="*60)

            metadata = {
                'analysis_date': datetime.now().isoformat(),
                'total_chunks_analyzed': all_data['metadata']['total_chunks'],
                'team_size': all_data['metadata']['team_size'],
                'alignment_score': alignment_analysis['overall_score'],
                'team_score': team_analysis['overall_score']
            }

            report = self.report_generator.generate_report(
                rubric=rubric,
                alignment_analysis=alignment_analysis,
                team_analysis=team_analysis,
                personnel_profiles=personnel_profiles,
                metadata=metadata
            )

            report_path = self.report_generator.save_report(report)

            # ============================================================
            # COMPLETION
            # ============================================================
            elapsed = datetime.now() - start_time

            print("\n" + "╔" + "="*58 + "╗")
            print("║" + " "*18 + "ANALYSIS COMPLETE" + " "*23 + "║")
            print("╚" + "="*58 + "╝")
            print(f"\n✅ Total time: {elapsed.total_seconds():.1f} seconds")
            print(f"\n📊 Key Results:")
            print(f"   • Alignment Score: {alignment_analysis['overall_score']:.1f}%")
            print(f"   • Team Strength: {team_analysis['overall_score']}/10")
            print(f"   • Requirements Analyzed: {len(rubric.get('requirements', []))}")
            print(f"   • Strong Alignments: {len(alignment_analysis.get('strong_alignments', []))}")
            print(f"   • Identified Gaps: {len(alignment_analysis.get('gaps', []))}")
            print(f"\n📄 Final Report: {report_path}")
            print(f"\n💡 Next Steps:")
            print(f"   1. Review the comprehensive report at: {report_path}")
            print(f"   2. Check intermediate analyses in: {self.config.OUTPUT_DIR}")
            print(f"   3. Address high-priority recommendations")
            print(f"   4. Re-run analysis after revisions to track improvement\n")

            return report_path

        except KeyboardInterrupt:
            print("\n\n⚠️  Analysis interrupted by user")
            sys.exit(1)

        except Exception as e:
            print(f"\n\n❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def run_quick_analysis(self) -> Dict:
        """
        Run a quick analysis without full semantic search.
        Useful for rapid feedback.

        Returns:
            Dictionary with summary results
        """
        print("🚀 Running quick analysis (keyword-based)...\n")

        # Load data
        all_data = self.data_loader.load_all()

        # Extract rubric
        rubric = self.rubric_analyzer.extract_rubric(all_data['solicitation']['text'])

        # Quick coverage check
        coverage = self.rubric_analyzer.analyze_requirement_coverage(
            rubric,
            all_data['narrative']['text']
        )

        print("\n📊 Quick Analysis Results:")
        print(f"   • Requirements covered: {len(coverage['covered'])}")
        print(f"   • Potentially missing: {len(coverage['potentially_missing'])}")

        if coverage['potentially_missing']:
            print("\n⚠️  Potentially Missing Requirements:")
            for item in coverage['potentially_missing'][:5]:
                print(f"   - {item['title']} ({item['weight']} priority)")

        return coverage


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AgriGrantCoach-AFRI: Comprehensive USDA AFRI proposal analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full analysis
  python main.py

  # Run full analysis without saving intermediate files
  python main.py --no-intermediates

  # Quick analysis (keyword-based, faster)
  python main.py --quick

  # Display configuration
  python main.py --show-config
        """
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick keyword-based analysis (faster, less comprehensive)'
    )

    parser.add_argument(
        '--no-intermediates',
        action='store_true',
        help='Do not save intermediate JSON files'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Display current configuration and exit'
    )

    args = parser.parse_args()

    try:
        # Validate configuration
        Config.validate()

        if args.show_config:
            print(Config.display_config())
            return 0

        # Initialize coach
        coach = AgriGrantCoach()

        if args.quick:
            coach.run_quick_analysis()
        else:
            coach.run_full_analysis(save_intermediates=not args.no_intermediates)

        return 0

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and data directory.")
        return 1

    except FileNotFoundError as e:
        print(f"\n❌ File Not Found: {e}")
        print("\nPlease ensure all required documents are in the data/ directory.")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
