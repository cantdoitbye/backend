# truststream/tests/test_explainability_engine.py

"""
Unit Tests for TrustStream Explainability Engine

This module contains comprehensive unit tests for the Explainability Engine,
testing multi-level explanations, feature importance analysis, similar case retrieval,
counterfactual examples, bias detection, and interactive visualizations.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from truststream.explainability_engine import (
    TrustStreamExplainabilityEngine, ExplanationLevel, FeatureImportance,
    SimilarCase, CounterfactualExample, BiasAnalysis, UncertaintyMetrics,
    InteractiveVisualization, AppealGuidance, AuditTrail
)


class TestExplanationLevel(unittest.TestCase):
    """Test cases for ExplanationLevel data class."""
    
    def test_explanation_level_creation(self):
        """Test ExplanationLevel creation for different audiences."""
        # Simple explanation for general users
        simple_explanation = ExplanationLevel(
            level="simple",
            audience="general_user",
            title="Content Review Result",
            summary="Your post was flagged because it contains language that might be harmful to others.",
            key_points=[
                "The content contains potentially offensive language",
                "Community guidelines require respectful communication",
                "You can edit your post to remove the flagged content"
            ],
            confidence_score=0.87,
            visual_elements={
                "trust_score_gauge": 0.65,
                "flagged_phrases": ["offensive term 1", "inappropriate phrase"],
                "suggestion_highlights": True
            },
            next_steps=[
                "Review the highlighted phrases in your content",
                "Edit your post to use more respectful language",
                "Resubmit for review"
            ]
        )
        
        self.assertEqual(simple_explanation.level, "simple")
        self.assertEqual(simple_explanation.audience, "general_user")
        self.assertIn("flagged", simple_explanation.summary)
        self.assertEqual(len(simple_explanation.key_points), 3)
        self.assertAlmostEqual(simple_explanation.confidence_score, 0.87, places=2)
        self.assertIn("trust_score_gauge", simple_explanation.visual_elements)
        
        # Technical explanation for moderators
        technical_explanation = ExplanationLevel(
            level="technical",
            audience="moderator",
            title="AI Moderation Analysis - Technical Report",
            summary="Multi-agent consensus analysis flagged content with 87% confidence based on toxicity detection (0.82), quality assessment (0.71), and bias analysis (0.65).",
            key_points=[
                "Toxicity Detector Agent: 0.82 confidence - detected hate speech patterns",
                "Quality Assessment Agent: 0.71 confidence - below community standards",
                "Bias Detection Agent: 0.65 confidence - potential discriminatory language",
                "Consensus mechanism weighted average: 0.73",
                "Trust pyramid adjustment: -0.15 (user history factor)"
            ],
            confidence_score=0.87,
            visual_elements={
                "agent_consensus_chart": True,
                "feature_importance_plot": True,
                "decision_tree_visualization": True,
                "similar_cases_comparison": True
            },
            next_steps=[
                "Review individual agent analyses",
                "Examine similar historical cases",
                "Consider user appeal if submitted",
                "Apply appropriate moderation action"
            ]
        )
        
        self.assertEqual(technical_explanation.level, "technical")
        self.assertEqual(technical_explanation.audience, "moderator")
        self.assertIn("Multi-agent consensus", technical_explanation.summary)
        self.assertEqual(len(technical_explanation.key_points), 5)
        self.assertIn("agent_consensus_chart", technical_explanation.visual_elements)


class TestFeatureImportance(unittest.TestCase):
    """Test cases for FeatureImportance analysis."""
    
    def test_feature_importance_creation(self):
        """Test FeatureImportance creation with SHAP and LIME values."""
        feature_importance = FeatureImportance(
            method="shap",
            features={
                "toxic_language_score": 0.45,
                "sentiment_negativity": 0.32,
                "user_trust_score": -0.18,
                "content_length": 0.08,
                "caps_lock_ratio": 0.15,
                "profanity_count": 0.38,
                "context_appropriateness": -0.12,
                "community_standards_alignment": -0.08
            },
            global_importance={
                "toxic_language_score": 0.52,
                "sentiment_negativity": 0.28,
                "user_trust_score": 0.15,
                "profanity_count": 0.35,
                "caps_lock_ratio": 0.12
            },
            explanation="SHAP values indicate that toxic language detection and profanity count are the strongest predictors for this moderation decision.",
            visualization_data={
                "shap_waterfall": "base64_encoded_plot_data",
                "feature_ranking": ["toxic_language_score", "profanity_count", "sentiment_negativity"],
                "interaction_effects": {
                    ("toxic_language_score", "user_trust_score"): -0.05,
                    ("sentiment_negativity", "context_appropriateness"): 0.03
                }
            }
        )
        
        self.assertEqual(feature_importance.method, "shap")
        self.assertAlmostEqual(feature_importance.features["toxic_language_score"], 0.45, places=2)
        self.assertAlmostEqual(feature_importance.features["user_trust_score"], -0.18, places=2)
        self.assertIn("SHAP values", feature_importance.explanation)
        self.assertIn("shap_waterfall", feature_importance.visualization_data)
        self.assertEqual(len(feature_importance.features), 8)


class TestSimilarCase(unittest.TestCase):
    """Test cases for SimilarCase retrieval and analysis."""
    
    def test_similar_case_creation(self):
        """Test SimilarCase creation with comprehensive case data."""
        similar_case = SimilarCase(
            case_id="case_78901",
            content_hash="abc123def456",
            similarity_score=0.89,
            decision="flagged",
            confidence=0.82,
            timestamp=datetime.now() - timedelta(days=15),
            features_matched=[
                "toxic_language_pattern",
                "sentiment_negativity",
                "community_context"
            ],
            outcome_details={
                "moderation_action": "temporary_mute",
                "duration_hours": 24,
                "appeal_submitted": True,
                "appeal_outcome": "upheld",
                "user_response": "accepted"
            },
            anonymized_content="[User] posted content containing [TOXIC_PATTERN] in [COMMUNITY_CONTEXT]",
            moderator_notes="Clear violation of community guidelines. User acknowledged and improved behavior.",
            learning_value=0.75
        )
        
        self.assertEqual(similar_case.case_id, "case_78901")
        self.assertAlmostEqual(similar_case.similarity_score, 0.89, places=2)
        self.assertEqual(similar_case.decision, "flagged")
        self.assertIn("toxic_language_pattern", similar_case.features_matched)
        self.assertEqual(similar_case.outcome_details["moderation_action"], "temporary_mute")
        self.assertIn("[TOXIC_PATTERN]", similar_case.anonymized_content)
        self.assertAlmostEqual(similar_case.learning_value, 0.75, places=2)


class TestCounterfactualExample(unittest.TestCase):
    """Test cases for CounterfactualExample generation."""
    
    def test_counterfactual_example_creation(self):
        """Test CounterfactualExample creation with alternative scenarios."""
        counterfactual = CounterfactualExample(
            original_content="This is absolutely terrible and stupid content that nobody should read!",
            modified_content="This content could be improved with more constructive feedback and specific suggestions.",
            changes_made=[
                "Removed inflammatory language ('terrible', 'stupid')",
                "Added constructive framing",
                "Replaced absolute statements with suggestions",
                "Maintained core message while improving tone"
            ],
            predicted_outcome="approved",
            confidence_change=0.68,  # From flagged (0.87) to approved (0.19)
            feature_changes={
                "toxic_language_score": -0.72,  # Significant reduction
                "sentiment_negativity": -0.45,
                "constructiveness": +0.58,
                "respectfulness": +0.63
            },
            explanation="By removing inflammatory language and reframing the message constructively, the content would likely be approved while maintaining the original intent.",
            educational_value="This example shows how tone and word choice significantly impact content moderation decisions."
        )
        
        self.assertIn("terrible", counterfactual.original_content)
        self.assertIn("constructive", counterfactual.modified_content)
        self.assertEqual(counterfactual.predicted_outcome, "approved")
        self.assertAlmostEqual(counterfactual.confidence_change, 0.68, places=2)
        self.assertAlmostEqual(counterfactual.feature_changes["toxic_language_score"], -0.72, places=2)
        self.assertIn("inflammatory language", counterfactual.changes_made[0])
        self.assertIn("tone and word choice", counterfactual.educational_value)


class TestTrustStreamExplainabilityEngine(unittest.TestCase):
    """Test cases for TrustStreamExplainabilityEngine main class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.explainability_engine = TrustStreamExplainabilityEngine()
        
        # Mock moderation decision
        self.mock_decision = {
            'decision_id': 'decision_12345',
            'content_id': 'content_67890',
            'user_id': 'user_54321',
            'decision': 'flagged',
            'confidence': 0.87,
            'agent_results': {
                'toxicity_detector': {'score': 0.82, 'confidence': 0.91},
                'quality_assessor': {'score': 0.71, 'confidence': 0.85},
                'bias_detector': {'score': 0.65, 'confidence': 0.78}
            },
            'trust_pyramid_scores': {
                'intelligence': 0.72,
                'appeal': 0.68,
                'social': 0.75,
                'humanity': 0.71
            },
            'content': "This is some example content that was flagged",
            'timestamp': datetime.now()
        }
        
        # Mock user context
        self.mock_user_context = {
            'user_id': 'user_54321',
            'trust_score': 0.69,
            'reputation_score': 0.73,
            'community_standing': 'good',
            'previous_violations': 2,
            'appeal_history': 1,
            'account_age_days': 180
        }
    
    def test_explainability_engine_initialization(self):
        """Test TrustStreamExplainabilityEngine initialization."""
        self.assertIsInstance(self.explainability_engine, TrustStreamExplainabilityEngine)
        self.assertIsInstance(self.explainability_engine.explanation_cache, dict)
        self.assertIsInstance(self.explainability_engine.similar_cases_db, list)
    
    def test_multi_level_explanation_generation(self):
        """Test generation of explanations for different audiences."""
        # Generate simple explanation for general user
        simple_explanation = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="simple",
            audience="general_user"
        )
        
        self.assertIsInstance(simple_explanation, ExplanationLevel)
        self.assertEqual(simple_explanation.level, "simple")
        self.assertEqual(simple_explanation.audience, "general_user")
        self.assertIn("flagged", simple_explanation.summary.lower())
        self.assertGreater(len(simple_explanation.key_points), 0)
        self.assertGreater(len(simple_explanation.next_steps), 0)
        
        # Generate technical explanation for moderator
        technical_explanation = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="technical",
            audience="moderator"
        )
        
        self.assertIsInstance(technical_explanation, ExplanationLevel)
        self.assertEqual(technical_explanation.level, "technical")
        self.assertEqual(technical_explanation.audience, "moderator")
        self.assertIn("agent", technical_explanation.summary.lower())
        
        # Generate detailed explanation for admin
        detailed_explanation = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="detailed",
            audience="admin"
        )
        
        self.assertIsInstance(detailed_explanation, ExplanationLevel)
        self.assertEqual(detailed_explanation.level, "detailed")
        self.assertEqual(detailed_explanation.audience, "admin")
    
    @patch('shap.Explainer')
    def test_shap_feature_importance_analysis(self, mock_shap_explainer):
        """Test SHAP-based feature importance analysis."""
        # Mock SHAP explainer and values
        mock_explainer_instance = Mock()
        mock_shap_explainer.return_value = mock_explainer_instance
        
        mock_shap_values = np.array([0.45, -0.18, 0.32, 0.08, 0.15, 0.38, -0.12, -0.08])
        mock_explainer_instance.shap_values.return_value = mock_shap_values
        
        # Generate SHAP analysis
        feature_importance = self.explainability_engine.analyze_feature_importance(
            decision_data=self.mock_decision,
            method="shap"
        )
        
        self.assertIsInstance(feature_importance, FeatureImportance)
        self.assertEqual(feature_importance.method, "shap")
        self.assertGreater(len(feature_importance.features), 0)
        self.assertIn("explanation", feature_importance.__dict__)
        
        # Verify SHAP explainer was called
        mock_shap_explainer.assert_called_once()
        mock_explainer_instance.shap_values.assert_called_once()
    
    @patch('lime.lime_text.LimeTextExplainer')
    def test_lime_feature_importance_analysis(self, mock_lime_explainer):
        """Test LIME-based feature importance analysis."""
        # Mock LIME explainer
        mock_explainer_instance = Mock()
        mock_lime_explainer.return_value = mock_explainer_instance
        
        mock_explanation = Mock()
        mock_explanation.as_list.return_value = [
            ('toxic_language', 0.45),
            ('sentiment_negative', 0.32),
            ('user_trust', -0.18),
            ('profanity', 0.38)
        ]
        mock_explainer_instance.explain_instance.return_value = mock_explanation
        
        # Generate LIME analysis
        feature_importance = self.explainability_engine.analyze_feature_importance(
            decision_data=self.mock_decision,
            method="lime"
        )
        
        self.assertIsInstance(feature_importance, FeatureImportance)
        self.assertEqual(feature_importance.method, "lime")
        self.assertGreater(len(feature_importance.features), 0)
        
        # Verify LIME explainer was called
        mock_lime_explainer.assert_called_once()
        mock_explainer_instance.explain_instance.assert_called_once()
    
    def test_similar_case_retrieval(self):
        """Test retrieval of similar historical cases."""
        # Mock similar cases in database
        mock_cases = [
            {
                'case_id': 'case_001',
                'content_hash': 'hash_001',
                'decision': 'flagged',
                'confidence': 0.85,
                'features': ['toxic_language', 'sentiment_negative'],
                'timestamp': datetime.now() - timedelta(days=10)
            },
            {
                'case_id': 'case_002',
                'content_hash': 'hash_002',
                'decision': 'approved',
                'confidence': 0.72,
                'features': ['quality_high', 'constructive'],
                'timestamp': datetime.now() - timedelta(days=20)
            }
        ]
        
        self.explainability_engine.similar_cases_db = mock_cases
        
        # Retrieve similar cases
        similar_cases = self.explainability_engine.find_similar_cases(
            decision_data=self.mock_decision,
            similarity_threshold=0.7,
            max_cases=5
        )
        
        self.assertIsInstance(similar_cases, list)
        self.assertGreater(len(similar_cases), 0)
        
        for case in similar_cases:
            self.assertIsInstance(case, SimilarCase)
            self.assertGreater(case.similarity_score, 0.7)
    
    def test_counterfactual_example_generation(self):
        """Test generation of counterfactual examples."""
        # Generate counterfactual examples
        counterfactuals = self.explainability_engine.generate_counterfactual_examples(
            decision_data=self.mock_decision,
            num_examples=3
        )
        
        self.assertIsInstance(counterfactuals, list)
        self.assertGreater(len(counterfactuals), 0)
        self.assertLessEqual(len(counterfactuals), 3)
        
        for counterfactual in counterfactuals:
            self.assertIsInstance(counterfactual, CounterfactualExample)
            self.assertNotEqual(counterfactual.original_content, counterfactual.modified_content)
            self.assertGreater(len(counterfactual.changes_made), 0)
            self.assertIn(counterfactual.predicted_outcome, ['approved', 'flagged', 'rejected'])
    
    def test_trust_factor_breakdown(self):
        """Test trust factor breakdown analysis."""
        trust_breakdown = self.explainability_engine.analyze_trust_factors(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context
        )
        
        self.assertIn('trust_pyramid_analysis', trust_breakdown)
        self.assertIn('user_history_impact', trust_breakdown)
        self.assertIn('community_context', trust_breakdown)
        self.assertIn('behavioral_patterns', trust_breakdown)
        
        # Verify trust pyramid scores
        pyramid_analysis = trust_breakdown['trust_pyramid_analysis']
        self.assertIn('intelligence', pyramid_analysis)
        self.assertIn('appeal', pyramid_analysis)
        self.assertIn('social', pyramid_analysis)
        self.assertIn('humanity', pyramid_analysis)
        
        # Verify user history impact
        history_impact = trust_breakdown['user_history_impact']
        self.assertIn('previous_violations_weight', history_impact)
        self.assertIn('account_age_factor', history_impact)
        self.assertIn('community_standing_bonus', history_impact)
    
    def test_agent_reasoning_analysis(self):
        """Test individual agent reasoning analysis."""
        agent_analysis = self.explainability_engine.analyze_agent_reasoning(
            decision_data=self.mock_decision
        )
        
        self.assertIn('individual_agents', agent_analysis)
        self.assertIn('consensus_mechanism', agent_analysis)
        self.assertIn('disagreement_analysis', agent_analysis)
        
        # Verify individual agent analysis
        individual_agents = agent_analysis['individual_agents']
        self.assertIn('toxicity_detector', individual_agents)
        self.assertIn('quality_assessor', individual_agents)
        self.assertIn('bias_detector', individual_agents)
        
        # Each agent should have reasoning explanation
        for agent_name, agent_data in individual_agents.items():
            self.assertIn('reasoning', agent_data)
            self.assertIn('confidence_factors', agent_data)
            self.assertIn('key_features', agent_data)
        
        # Verify consensus mechanism analysis
        consensus = agent_analysis['consensus_mechanism']
        self.assertIn('weighting_strategy', consensus)
        self.assertIn('final_score_calculation', consensus)
        self.assertIn('confidence_aggregation', consensus)
    
    def test_bias_detection_analysis(self):
        """Test bias detection and analysis."""
        bias_analysis = self.explainability_engine.detect_bias(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context
        )
        
        self.assertIsInstance(bias_analysis, BiasAnalysis)
        self.assertIn('demographic_bias', bias_analysis.bias_types)
        self.assertIn('confirmation_bias', bias_analysis.bias_types)
        self.assertIn('historical_bias', bias_analysis.bias_types)
        
        # Verify bias metrics
        self.assertGreater(len(bias_analysis.bias_metrics), 0)
        self.assertIn('fairness_score', bias_analysis.bias_metrics)
        self.assertIn('demographic_parity', bias_analysis.bias_metrics)
        
        # Verify mitigation suggestions
        self.assertGreater(len(bias_analysis.mitigation_suggestions), 0)
        
        # Check confidence in bias detection
        self.assertGreaterEqual(bias_analysis.detection_confidence, 0.0)
        self.assertLessEqual(bias_analysis.detection_confidence, 1.0)
    
    def test_uncertainty_quantification(self):
        """Test uncertainty quantification in decisions."""
        uncertainty_metrics = self.explainability_engine.quantify_uncertainty(
            decision_data=self.mock_decision
        )
        
        self.assertIsInstance(uncertainty_metrics, UncertaintyMetrics)
        
        # Verify uncertainty components
        self.assertIn('model_uncertainty', uncertainty_metrics.uncertainty_sources)
        self.assertIn('data_uncertainty', uncertainty_metrics.uncertainty_sources)
        self.assertIn('agent_disagreement', uncertainty_metrics.uncertainty_sources)
        
        # Verify confidence intervals
        self.assertIn('lower_bound', uncertainty_metrics.confidence_intervals)
        self.assertIn('upper_bound', uncertainty_metrics.confidence_intervals)
        self.assertIn('confidence_level', uncertainty_metrics.confidence_intervals)
        
        # Verify uncertainty score is valid
        self.assertGreaterEqual(uncertainty_metrics.overall_uncertainty, 0.0)
        self.assertLessEqual(uncertainty_metrics.overall_uncertainty, 1.0)
        
        # Verify reliability assessment
        self.assertIn('high_confidence_threshold', uncertainty_metrics.reliability_assessment)
        self.assertIn('decision_reliability', uncertainty_metrics.reliability_assessment)
    
    @patch('plotly.graph_objects.Figure')
    def test_interactive_visualization_generation(self, mock_plotly_figure):
        """Test generation of interactive visualizations."""
        # Mock Plotly figure
        mock_fig = Mock()
        mock_plotly_figure.return_value = mock_fig
        mock_fig.to_html.return_value = "<html>Mock visualization</html>"
        
        # Generate interactive visualization
        visualization = self.explainability_engine.create_interactive_visualization(
            decision_data=self.mock_decision,
            visualization_type="decision_tree"
        )
        
        self.assertIsInstance(visualization, InteractiveVisualization)
        self.assertEqual(visualization.visualization_type, "decision_tree")
        self.assertIn("html", visualization.html_content.lower())
        self.assertGreater(len(visualization.interactive_elements), 0)
        
        # Test different visualization types
        for viz_type in ["feature_importance", "agent_consensus", "trust_breakdown", "similar_cases"]:
            viz = self.explainability_engine.create_interactive_visualization(
                decision_data=self.mock_decision,
                visualization_type=viz_type
            )
            self.assertEqual(viz.visualization_type, viz_type)
    
    def test_appeal_guidance_generation(self):
        """Test generation of appeal guidance."""
        appeal_guidance = self.explainability_engine.generate_appeal_guidance(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context
        )
        
        self.assertIsInstance(appeal_guidance, AppealGuidance)
        
        # Verify appeal eligibility assessment
        self.assertIn(appeal_guidance.appeal_eligibility, ['eligible', 'not_eligible', 'conditional'])
        
        # Verify guidance components
        self.assertGreater(len(appeal_guidance.recommended_actions), 0)
        self.assertGreater(len(appeal_guidance.evidence_suggestions), 0)
        self.assertGreater(len(appeal_guidance.success_factors), 0)
        
        # Verify success probability
        self.assertGreaterEqual(appeal_guidance.success_probability, 0.0)
        self.assertLessEqual(appeal_guidance.success_probability, 1.0)
        
        # Verify timeline information
        self.assertIn('review_timeline', appeal_guidance.process_information)
        self.assertIn('required_information', appeal_guidance.process_information)
        
        # Verify alternative options
        self.assertGreater(len(appeal_guidance.alternative_options), 0)
    
    def test_audit_trail_creation(self):
        """Test creation of comprehensive audit trails."""
        audit_trail = self.explainability_engine.create_audit_trail(
            decision_data=self.mock_decision,
            explanation_requests=[
                {'level': 'simple', 'audience': 'general_user', 'timestamp': datetime.now()},
                {'level': 'technical', 'audience': 'moderator', 'timestamp': datetime.now()}
            ]
        )
        
        self.assertIsInstance(audit_trail, AuditTrail)
        
        # Verify audit trail components
        self.assertEqual(audit_trail.decision_id, self.mock_decision['decision_id'])
        self.assertGreater(len(audit_trail.explanation_history), 0)
        self.assertGreater(len(audit_trail.access_log), 0)
        
        # Verify decision metadata
        self.assertIn('model_version', audit_trail.decision_metadata)
        self.assertIn('agent_versions', audit_trail.decision_metadata)
        self.assertIn('configuration_hash', audit_trail.decision_metadata)
        
        # Verify data lineage
        self.assertIn('input_data_sources', audit_trail.data_lineage)
        self.assertIn('feature_extraction_methods', audit_trail.data_lineage)
        self.assertIn('preprocessing_steps', audit_trail.data_lineage)
        
        # Verify compliance information
        self.assertIn('gdpr_compliance', audit_trail.compliance_info)
        self.assertIn('data_retention_policy', audit_trail.compliance_info)
        self.assertIn('anonymization_applied', audit_trail.compliance_info)
    
    def test_explanation_caching(self):
        """Test explanation caching mechanism."""
        # Generate explanation (should be cached)
        explanation1 = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="simple",
            audience="general_user"
        )
        
        # Generate same explanation again (should use cache)
        explanation2 = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="simple",
            audience="general_user"
        )
        
        # Verify caching worked
        cache_key = self.explainability_engine._generate_cache_key(
            self.mock_decision['decision_id'], "simple", "general_user"
        )
        self.assertIn(cache_key, self.explainability_engine.explanation_cache)
        
        # Explanations should be identical (from cache)
        self.assertEqual(explanation1.summary, explanation2.summary)
        self.assertEqual(explanation1.key_points, explanation2.key_points)
    
    def test_batch_explanation_generation(self):
        """Test batch generation of explanations."""
        # Create multiple mock decisions
        mock_decisions = [
            {**self.mock_decision, 'decision_id': f'decision_{i}', 'content_id': f'content_{i}'}
            for i in range(5)
        ]
        
        # Generate batch explanations
        batch_explanations = self.explainability_engine.generate_batch_explanations(
            decisions_data=mock_decisions,
            user_contexts=[self.mock_user_context] * 5,
            explanation_level="simple",
            audience="general_user"
        )
        
        self.assertEqual(len(batch_explanations), 5)
        
        for explanation in batch_explanations:
            self.assertIsInstance(explanation, ExplanationLevel)
            self.assertEqual(explanation.level, "simple")
            self.assertEqual(explanation.audience, "general_user")
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Generate explanation with performance tracking
        start_time = datetime.now()
        
        explanation = self.explainability_engine.generate_explanation(
            decision_data=self.mock_decision,
            user_context=self.mock_user_context,
            explanation_level="technical",
            audience="moderator",
            track_performance=True
        )
        
        end_time = datetime.now()
        
        # Verify performance metrics were collected
        self.assertIn('performance_metrics', explanation.__dict__)
        
        performance_metrics = explanation.performance_metrics
        self.assertIn('generation_time_ms', performance_metrics)
        self.assertIn('feature_analysis_time_ms', performance_metrics)
        self.assertIn('similar_cases_retrieval_time_ms', performance_metrics)
        self.assertIn('visualization_generation_time_ms', performance_metrics)
        
        # Verify timing is reasonable
        total_time = (end_time - start_time).total_seconds() * 1000
        self.assertLess(performance_metrics['generation_time_ms'], total_time * 2)  # Allow some overhead


class TestExplainabilityEngineIntegration(unittest.TestCase):
    """Integration tests for Explainability Engine."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.explainability_engine = TrustStreamExplainabilityEngine()
        
        # Mock comprehensive decision data
        self.comprehensive_decision = {
            'decision_id': 'integration_test_001',
            'content_id': 'content_integration_001',
            'user_id': 'user_integration_001',
            'decision': 'flagged',
            'confidence': 0.89,
            'agent_results': {
                'toxicity_detector': {
                    'score': 0.85,
                    'confidence': 0.92,
                    'reasoning': 'Detected hate speech patterns and offensive language',
                    'features': ['hate_speech_indicators', 'offensive_terms']
                },
                'quality_assessor': {
                    'score': 0.68,
                    'confidence': 0.81,
                    'reasoning': 'Content quality below community standards',
                    'features': ['grammar_issues', 'coherence_problems']
                },
                'bias_detector': {
                    'score': 0.72,
                    'confidence': 0.76,
                    'reasoning': 'Potential discriminatory language detected',
                    'features': ['discriminatory_terms', 'bias_indicators']
                }
            },
            'trust_pyramid_scores': {
                'intelligence': 0.71,
                'appeal': 0.64,
                'social': 0.78,
                'humanity': 0.69
            },
            'content': "This is comprehensive test content for integration testing of the explainability engine",
            'timestamp': datetime.now(),
            'metadata': {
                'content_type': 'text_post',
                'community_id': 'community_test_001',
                'language': 'en',
                'content_length': 95
            }
        }
        
        self.comprehensive_user_context = {
            'user_id': 'user_integration_001',
            'trust_score': 0.67,
            'reputation_score': 0.71,
            'community_standing': 'good',
            'previous_violations': 1,
            'appeal_history': 0,
            'account_age_days': 365,
            'activity_level': 'moderate',
            'community_contributions': 45
        }
    
    @patch('truststream.explainability_engine.TrustStreamExplainabilityEngine.analyze_feature_importance')
    @patch('truststream.explainability_engine.TrustStreamExplainabilityEngine.find_similar_cases')
    @patch('truststream.explainability_engine.TrustStreamExplainabilityEngine.generate_counterfactual_examples')
    def test_comprehensive_explanation_workflow(self, mock_counterfactuals, mock_similar_cases, mock_feature_importance):
        """Test complete explanation generation workflow."""
        # Mock all components
        mock_feature_importance.return_value = FeatureImportance(
            method="shap",
            features={"toxic_language": 0.45, "sentiment": 0.32},
            global_importance={"toxic_language": 0.52},
            explanation="Mock feature importance",
            visualization_data={}
        )
        
        mock_similar_cases.return_value = [
            SimilarCase(
                case_id="similar_001",
                content_hash="hash_001",
                similarity_score=0.87,
                decision="flagged",
                confidence=0.84,
                timestamp=datetime.now() - timedelta(days=5),
                features_matched=["toxic_language"],
                outcome_details={"action": "temporary_mute"},
                anonymized_content="Similar flagged content",
                moderator_notes="Clear violation",
                learning_value=0.8
            )
        ]
        
        mock_counterfactuals.return_value = [
            CounterfactualExample(
                original_content="Original problematic content",
                modified_content="Improved respectful content",
                changes_made=["Removed offensive language"],
                predicted_outcome="approved",
                confidence_change=0.65,
                feature_changes={"toxic_language": -0.7},
                explanation="Mock counterfactual",
                educational_value="Shows improvement path"
            )
        ]
        
        # Generate comprehensive explanation
        comprehensive_explanation = self.explainability_engine.generate_comprehensive_explanation(
            decision_data=self.comprehensive_decision,
            user_context=self.comprehensive_user_context,
            include_all_components=True
        )
        
        # Verify all components are included
        self.assertIn('multi_level_explanations', comprehensive_explanation)
        self.assertIn('feature_importance', comprehensive_explanation)
        self.assertIn('similar_cases', comprehensive_explanation)
        self.assertIn('counterfactual_examples', comprehensive_explanation)
        self.assertIn('trust_factor_breakdown', comprehensive_explanation)
        self.assertIn('agent_reasoning', comprehensive_explanation)
        self.assertIn('bias_analysis', comprehensive_explanation)
        self.assertIn('uncertainty_metrics', comprehensive_explanation)
        self.assertIn('interactive_visualizations', comprehensive_explanation)
        self.assertIn('appeal_guidance', comprehensive_explanation)
        self.assertIn('audit_trail', comprehensive_explanation)
        
        # Verify multi-level explanations
        multi_level = comprehensive_explanation['multi_level_explanations']
        self.assertIn('simple', multi_level)
        self.assertIn('technical', multi_level)
        self.assertIn('detailed', multi_level)
        
        # Verify all mocked components were called
        mock_feature_importance.assert_called()
        mock_similar_cases.assert_called()
        mock_counterfactuals.assert_called()
    
    def test_real_world_scenario_simulation(self):
        """Test explainability engine with realistic scenario."""
        # Simulate a real-world moderation scenario
        real_world_decision = {
            'decision_id': 'real_world_001',
            'content_id': 'post_789012',
            'user_id': 'user_345678',
            'decision': 'flagged',
            'confidence': 0.91,
            'agent_results': {
                'toxicity_detector': {
                    'score': 0.88,
                    'confidence': 0.94,
                    'reasoning': 'High confidence detection of toxic language patterns',
                    'features': ['hate_speech', 'personal_attacks', 'inflammatory_language']
                },
                'quality_assessor': {
                    'score': 0.45,
                    'confidence': 0.87,
                    'reasoning': 'Content lacks constructive value and violates community standards',
                    'features': ['low_quality_indicators', 'unconstructive_criticism']
                },
                'bias_detector': {
                    'score': 0.79,
                    'confidence': 0.83,
                    'reasoning': 'Detected potential discriminatory language and bias',
                    'features': ['discriminatory_terms', 'stereotyping_language']
                }
            },
            'trust_pyramid_scores': {
                'intelligence': 0.58,  # Lower due to poor content quality
                'appeal': 0.42,       # Low due to toxic behavior
                'social': 0.61,       # Moderate social connections
                'humanity': 0.39      # Low due to harmful content
            },
            'content': "Realistic example of problematic content that would be flagged by the system",
            'timestamp': datetime.now(),
            'metadata': {
                'content_type': 'comment',
                'community_id': 'community_politics_001',
                'language': 'en',
                'content_length': 87,
                'parent_post_id': 'post_123456',
                'engagement_metrics': {
                    'likes': 2,
                    'dislikes': 15,
                    'reports': 8
                }
            }
        }
        
        real_world_user_context = {
            'user_id': 'user_345678',
            'trust_score': 0.48,  # Low trust score
            'reputation_score': 0.52,
            'community_standing': 'poor',
            'previous_violations': 5,
            'appeal_history': 2,
            'account_age_days': 90,  # Relatively new account
            'activity_level': 'high',
            'community_contributions': 12,
            'recent_behavior_trend': 'declining'
        }
        
        # Generate explanation for different audiences
        user_explanation = self.explainability_engine.generate_explanation(
            decision_data=real_world_decision,
            user_context=real_world_user_context,
            explanation_level="simple",
            audience="general_user"
        )
        
        moderator_explanation = self.explainability_engine.generate_explanation(
            decision_data=real_world_decision,
            user_context=real_world_user_context,
            explanation_level="technical",
            audience="moderator"
        )
        
        # Verify user explanation is appropriate
        self.assertEqual(user_explanation.audience, "general_user")
        self.assertIn("flagged", user_explanation.summary.lower())
        self.assertGreater(len(user_explanation.next_steps), 0)
        
        # Verify moderator explanation includes technical details
        self.assertEqual(moderator_explanation.audience, "moderator")
        self.assertIn("agent", moderator_explanation.summary.lower())
        self.assertIn("confidence", moderator_explanation.summary.lower())
        
        # Generate appeal guidance
        appeal_guidance = self.explainability_engine.generate_appeal_guidance(
            decision_data=real_world_decision,
            user_context=real_world_user_context
        )
        
        # With multiple violations and low trust score, appeal success should be lower
        self.assertLess(appeal_guidance.success_probability, 0.5)
        self.assertGreater(len(appeal_guidance.recommended_actions), 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)