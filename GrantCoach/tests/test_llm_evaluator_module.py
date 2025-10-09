import unittest
import os
from llm_evaluator import LLMEvaluator, EvaluationResult, EvaluationCriteria

class TestLLMEvaluatorModule(unittest.TestCase):

    def setUp(self):
        # Paths for valid test files
        self.solicitation_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Solicitation.pdf"
        self.proposal_path = "/Users/quamos/Desktop/CADS/DataAILab/GrantCoach/data/ExpandAI_Full_Proposal_TSU_Expanded.pdf"
        self.evaluator = LLMEvaluator(use_mock_llm=True)

    def test_evaluator_initialization(self):
        """Test that LLMEvaluator initializes correctly."""
        self.assertIsInstance(self.evaluator.evaluation_criteria, list)
        self.assertGreater(len(self.evaluator.evaluation_criteria), 0)
        self.assertTrue(self.evaluator.use_mock_llm)

    def test_evaluation_criteria_structure(self):
        """Test that evaluation criteria are properly structured."""
        for criterion in self.evaluator.evaluation_criteria:
            self.assertIsInstance(criterion, EvaluationCriteria)
            self.assertGreater(criterion.weight, 0)
            self.assertGreater(criterion.max_score, 0)
            self.assertIsNotNone(criterion.name)
            self.assertIsNotNone(criterion.description)

    def test_faculty_information_extraction(self):
        """Only run if files exist"""
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        from document_processor import DocumentProcessor
        processor = DocumentProcessor()
        processed_data = processor.process_documents(self.solicitation_path, self.proposal_path)

        faculty_info = self.evaluator.extract_faculty_information(processed_data["sections"]["proposal"])

        # Verify structure
        self.assertIsInstance(faculty_info, dict)
        self.assertIn("pi", faculty_info)
        self.assertIn("co_pi", faculty_info)
        self.assertIn("expertise_areas", faculty_info)
        self.assertIn("prior_funding", faculty_info)
        self.assertIn("publications", faculty_info)

    def test_readability_metrics(self):
        """Test readability metrics calculation."""
        test_text = """
        This is a test sentence. This is another sentence. The quick brown fox jumps over the lazy dog.
        This proposal discusses artificial intelligence and machine learning applications in education.
        The research aims to improve learning outcomes through innovative teaching methods.
        """

        metrics = self.evaluator.calculate_readability_metrics(test_text)

        # Verify structure
        self.assertIsInstance(metrics, dict)
        if "error" not in metrics:
            self.assertIn("flesch_kincaid_grade", metrics)
            self.assertIn("flesch_reading_ease", metrics)
            self.assertIn("sentence_count", metrics)
            self.assertIn("word_count", metrics)

    def test_proposal_quality_evaluation(self):
        """Only run if files exist"""
        if not (os.path.exists(self.solicitation_path) and os.path.exists(self.proposal_path)):
            self.skipTest("Test PDFs not found.")

        from document_processor import DocumentProcessor
        processor = DocumentProcessor()
        processed_data = processor.process_documents(self.solicitation_path, self.proposal_path)

        # Mock alignment results
        alignment_results = {
            "Project Summary": {"score": 0.5},
            "Intellectual Merit": {"score": 0.3},
            "Broader Impacts": {"score": 0.4}
        }

        evaluation_results = self.evaluator.evaluate_proposal_quality(
            processed_data["sections"]["proposal"],
            alignment_results
        )

        # Verify structure
        self.assertIsInstance(evaluation_results, list)
        self.assertGreater(len(evaluation_results), 0)

        for result in evaluation_results:
            self.assertIsInstance(result, EvaluationResult)
            self.assertGreaterEqual(result.score, 0)
            self.assertLessEqual(result.score, 10)
            self.assertIsInstance(result.strengths, list)
            self.assertIsInstance(result.weaknesses, list)
            self.assertIsInstance(result.recommendations, list)

    def test_evaluation_summary_generation(self):
        """Test evaluation summary generation."""
        # Create mock evaluation results
        mock_results = [
            EvaluationResult(
                criterion="Alignment with Solicitation",
                score=7.5,
                justification="Good alignment",
                strengths=["Well-aligned with requirements"],
                weaknesses=[],
                recommendations=[]
            ),
            EvaluationResult(
                criterion="Intellectual Merit",
                score=6.0,
                justification="Moderate merit",
                strengths=["Some innovative aspects"],
                weaknesses=["Need more detail"],
                recommendations=["Expand methodology section"]
            )
        ]

        summary = self.evaluator.generate_evaluation_summary(mock_results)

        # Verify structure
        self.assertIsInstance(summary, dict)
        self.assertIn("overall_score", summary)
        self.assertIn("category", summary)
        self.assertIn("recommendation", summary)
        self.assertIn("top_strengths", summary)
        self.assertIn("critical_weaknesses", summary)
        self.assertIn("priority_recommendations", summary)
        self.assertIn("detailed_results", summary)

        # Verify score is in valid range
        self.assertGreaterEqual(summary["overall_score"], 0)
        self.assertLessEqual(summary["overall_score"], 10)

    def test_individual_criterion_evaluations(self):
        """Test individual criterion evaluation methods."""
        proposal_sections = {
            "Intellectual Merit": "This proposal has innovative aspects and significant contribution to the field.",
            "Broader Impacts": "The project will benefit underrepresented groups and improve education.",
            "Project Summary": "Clear summary of the proposed research activities and expected outcomes."
        }

        # Test intellectual merit evaluation
        merit_result = self.evaluator._evaluate_intellectual_merit(proposal_sections)
        self.assertIsInstance(merit_result, EvaluationResult)
        self.assertEqual(merit_result.criterion, "Intellectual Merit")

        # Test broader impacts evaluation
        impacts_result = self.evaluator._evaluate_broader_impacts(proposal_sections)
        self.assertIsInstance(impacts_result, EvaluationResult)
        self.assertEqual(impacts_result.criterion, "Broader Impacts")

        # Test clarity evaluation
        clarity_result = self.evaluator._evaluate_clarity(proposal_sections)
        self.assertIsInstance(clarity_result, EvaluationResult)
        self.assertEqual(clarity_result.criterion, "Clarity and Organization")

    def test_overall_score_calculation(self):
        """Test overall score calculation with weights."""
        mock_results = [
            EvaluationResult("Criterion 1", 8.0, "Justification", [], [], []),
            EvaluationResult("Criterion 2", 6.0, "Justification", [], [], [])
        ]

        # Set custom weights for testing
        self.evaluator.evaluation_criteria = [
            EvaluationCriteria("Criterion 1", "Description", 0.6),
            EvaluationCriteria("Criterion 2", "Description", 0.4)
        ]

        overall_score = self.evaluator.calculate_overall_score(mock_results)
        expected_score = (8.0 * 0.6) + (6.0 * 0.4)  # Weighted average
        self.assertAlmostEqual(overall_score, expected_score, places=1)

if __name__ == "__main__":
    unittest.main()