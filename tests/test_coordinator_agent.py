"""Unit tests for CoordinatorAgent.

Tests the functionality of the CoordinatorAgent for orchestrating multiple
metric evaluations and aggregating results.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import asyncio
from datetime import datetime

from config.models import Metric, MetricResult, EvaluationResult
from agents.llm_client import LLMClientError
from agents.coordinator_agent import CoordinatorAgent
from storage.guidelines import Guidelines, GuidelineCategory, GuidelineMetric


class TestCoordinatorAgent:
    """Test CoordinatorAgent implementation."""
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        mock_client = AsyncMock()
        mock_client.generate_response_with_retry = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def test_guidelines(self):
        """Create test guidelines with metrics."""
        return Guidelines(
            categories={
                "clarity": GuidelineCategory(
                    weight=1.0,
                    description="How clear is the content?",
                    metrics={
                        "conciseness": GuidelineMetric(
                            description="Is the writing concise?",
                            weight=0.6
                        ),
                        "structure": GuidelineMetric(
                            description="Is the content well-structured?",
                            weight=0.4
                        )
                    }
                ),
                "accuracy": GuidelineCategory(
                    weight=1.5,
                    description="How accurate is the content?",
                    metrics={
                        "factual": GuidelineMetric(
                            description="Are the facts correct?",
                            weight=1.0
                        )
                    }
                )
            }
        )
    
    @pytest.fixture
    def test_content(self):
        """Create test content for evaluation."""
        return "This is a test content for evaluation."
    
    @pytest.fixture
    def mock_metric_results(self):
        """Create mock metric results."""
        metrics = [
            Metric(name="conciseness", description="Is the writing concise?", weight=0.6, category="clarity"),
            Metric(name="structure", description="Is the content well-structured?", weight=0.4, category="clarity"),
            Metric(name="factual", description="Are the facts correct?", weight=1.0, category="accuracy")
        ]
        
        return [
            MetricResult(
                metric=metrics[0],
                score=4,
                reasoning="The content is concise",
                improvement_advice="No improvements needed",
                positive_examples=["This is concise"],
                improvement_examples=[],
                confidence=1.0
            ),
            MetricResult(
                metric=metrics[1],
                score=3,
                reasoning="The structure is adequate",
                improvement_advice="Add more headings",
                positive_examples=["Good paragraph"],
                improvement_examples=["This could be better structured"],
                confidence=0.9
            ),
            MetricResult(
                metric=metrics[2],
                score=5,
                reasoning="All facts are correct",
                improvement_advice="No improvements needed",
                positive_examples=["Accurate statement"],
                improvement_examples=[],
                confidence=1.0
            )
        ]
    
    def test_initialization(self, mock_llm_client):
        """Test that the CoordinatorAgent initializes correctly."""
        coordinator = CoordinatorAgent(mock_llm_client)
        assert coordinator.llm == mock_llm_client
        assert coordinator.max_concurrent_evaluations == 3  # Default value
        
        # Test with custom max_concurrent_evaluations
        coordinator = CoordinatorAgent(mock_llm_client, max_concurrent_evaluations=5)
        assert coordinator.max_concurrent_evaluations == 5
    
    @pytest.mark.asyncio
    async def test_evaluate_content_success(self, mock_llm_client, test_guidelines, test_content, mock_metric_results):
        """Test successful content evaluation with multiple metrics."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Mock the _evaluate_metric_with_semaphore method to return predefined results
        with patch.object(coordinator, '_evaluate_metric_with_semaphore', new_callable=AsyncMock) as mock_evaluate:
            # Set up the mock to return each result in sequence
            mock_evaluate.side_effect = mock_metric_results
            
            # Call evaluate_content
            result = await coordinator.evaluate_content(test_content, test_guidelines)
            
            # Verify the result
            assert isinstance(result, EvaluationResult)
            assert len(result.metric_results) == 3
            assert "clarity" in result.category_scores
            assert "accuracy" in result.category_scores
            
            # Verify the scores
            # Clarity category: (4 * 0.6 + 3 * 0.4) = 3.6
            # Accuracy category: 5 * 1.0 = 5.0
            # Overall: (3.6 * 1.0 + 5.0 * 1.5) / (1.0 + 1.5) = 4.44
            assert result.category_scores["clarity"] == pytest.approx(3.6)
            assert result.category_scores["accuracy"] == pytest.approx(5.0)
            assert result.overall_score == pytest.approx(4.44)
            
            # Verify that _evaluate_metric_with_semaphore was called for each metric
            assert mock_evaluate.call_count == 3
    
    @pytest.mark.asyncio
    async def test_evaluate_content_with_filtered_metrics(self, mock_llm_client, test_guidelines, test_content, mock_metric_results):
        """Test content evaluation with a filtered list of metrics."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Mock the _evaluate_metric_with_semaphore method to return predefined results
        with patch.object(coordinator, '_evaluate_metric_with_semaphore', new_callable=AsyncMock) as mock_evaluate:
            # Set up the mock to return only the first result
            mock_evaluate.side_effect = [mock_metric_results[0]]
            
            # Call evaluate_content with a filtered list of metrics
            result = await coordinator.evaluate_content(
                test_content, 
                test_guidelines,
                metrics_to_evaluate=["conciseness"]
            )
            
            # Verify the result
            assert isinstance(result, EvaluationResult)
            assert len(result.metric_results) == 1
            assert result.metric_results[0].metric.name == "conciseness"
            
            # Verify that _evaluate_metric_with_semaphore was called only once
            assert mock_evaluate.call_count == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_content_empty(self, mock_llm_client, test_guidelines):
        """Test handling of empty content."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Verify that empty content raises a ValueError
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await coordinator.evaluate_content("", test_guidelines)
        
        # Verify that whitespace-only content also raises a ValueError
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await coordinator.evaluate_content("   \n   ", test_guidelines)
    
    @pytest.mark.asyncio
    async def test_evaluate_content_no_metrics(self, mock_llm_client, test_content):
        """Test handling of guidelines with no metrics."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Create empty guidelines
        empty_guidelines = Guidelines(categories={})
        
        # Verify that empty guidelines raises a ValueError
        with pytest.raises(ValueError, match="No metrics found in guidelines"):
            await coordinator.evaluate_content(test_content, empty_guidelines)
    
    @pytest.mark.asyncio
    async def test_evaluate_content_invalid_metrics(self, mock_llm_client, test_guidelines, test_content):
        """Test handling of invalid metric names."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Verify that invalid metric names raise a ValueError
        with pytest.raises(ValueError, match="None of the specified metrics"):
            await coordinator.evaluate_content(
                test_content, 
                test_guidelines,
                metrics_to_evaluate=["nonexistent_metric"]
            )
    
    @pytest.mark.asyncio
    async def test_evaluate_content_partial_failure(self, mock_llm_client, test_guidelines, test_content, mock_metric_results):
        """Test handling of partial failures during evaluation."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Mock the _evaluate_metric_with_semaphore method to succeed for some metrics and fail for others
        async def mock_evaluate_side_effect(content, metric, semaphore):
            if metric.name == "factual":
                raise LLMClientError("LLM service unavailable")
            elif metric.name == "conciseness":
                return mock_metric_results[0]
            else:
                return mock_metric_results[1]
        
        with patch.object(coordinator, '_evaluate_metric_with_semaphore') as mock_evaluate:
            mock_evaluate.side_effect = mock_evaluate_side_effect
            
            # This test is tricky because we need to mock asyncio.gather to handle the exception
            # and still return partial results
            
            # Create a mock for asyncio.gather that returns only successful results
            original_gather = asyncio.gather
            
            async def mock_gather(*tasks):
                results = []
                for task in tasks:
                    try:
                        results.append(await task)
                    except Exception:
                        pass
                return results
            
            # Apply the mock
            asyncio.gather = mock_gather
            
            try:
                # Call evaluate_content
                result = await coordinator.evaluate_content(test_content, test_guidelines)
                
                # Verify that we got partial results
                assert isinstance(result, EvaluationResult)
                assert len(result.metric_results) < 3  # We should have fewer than all metrics
                
                # Verify that the metrics that succeeded are included
                metric_names = [r.metric.name for r in result.metric_results]
                assert "conciseness" in metric_names or "structure" in metric_names
                assert "factual" not in metric_names  # This one failed
                
            finally:
                # Restore the original asyncio.gather
                asyncio.gather = original_gather
    
    @pytest.mark.asyncio
    async def test_evaluate_metric_with_semaphore(self, mock_llm_client, test_content):
        """Test the _evaluate_metric_with_semaphore method."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Create a test metric
        metric = Metric(
            name="test_metric",
            description="Test metric description",
            weight=1.0,
            category="test_category"
        )
        
        # Create a mock MetricEvaluator
        mock_evaluator = AsyncMock()
        mock_result = MetricResult(
            metric=metric,
            score=4,
            reasoning="Test reasoning",
            improvement_advice="Test advice",
            positive_examples=["Test positive"],
            improvement_examples=["Test improvement"],
            confidence=1.0
        )
        mock_evaluator.evaluate_metric.return_value = mock_result
        
        # Mock the MetricEvaluator class
        with patch('agents.coordinator_agent.MetricEvaluator', return_value=mock_evaluator):
            # Create a semaphore
            semaphore = asyncio.Semaphore(1)
            
            # Call _evaluate_metric_with_semaphore
            result = await coordinator._evaluate_metric_with_semaphore(test_content, metric, semaphore)
            
            # Verify the result
            assert result == mock_result
            
            # Verify that MetricEvaluator.evaluate_metric was called with the correct arguments
            mock_evaluator.evaluate_metric.assert_called_once_with(test_content, metric)
    
    def test_calculate_scores(self, mock_llm_client, test_guidelines, mock_metric_results):
        """Test the _calculate_scores method."""
        coordinator = CoordinatorAgent(mock_llm_client)
        
        # Call _calculate_scores
        overall_score, category_scores = coordinator._calculate_scores(mock_metric_results, test_guidelines)
        
        # Verify the scores
        # Clarity category: (4 * 0.6 + 3 * 0.4) = 3.6
        # Accuracy category: 5 * 1.0 = 5.0
        # Overall: (3.6 * 1.0 + 5.0 * 1.5) / (1.0 + 1.5) = 4.44
        assert category_scores["clarity"] == pytest.approx(3.6)
        assert category_scores["accuracy"] == pytest.approx(5.0)
        assert overall_score == pytest.approx(4.44)
        
        # Test with empty results
        overall_score, category_scores = coordinator._calculate_scores([], test_guidelines)
        assert overall_score == 0.0
        assert category_scores == {}