"""Unit tests for UI visualization components.

Tests the functionality of the visualization components used in the Streamlit UI,
including gauge charts, radar charts, and metric result displays.
"""

import pytest
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st
from unittest.mock import patch, MagicMock

from config.models import Metric, MetricResult, EvaluationResult
from main import create_gauge_chart, create_radar_chart, display_metric_result, display_evaluation_results


class TestUIComponents:
    """Test UI visualization components."""
    
    @pytest.fixture
    def sample_metric_result(self):
        """Create a sample metric result for testing."""
        metric = Metric(
            name="clarity",
            description="How clear is the content?",
            weight=0.5,
            category="readability"
        )
        
        return MetricResult(
            metric=metric,
            score=4,
            reasoning="The content is generally clear and easy to understand.",
            improvement_advice="Consider simplifying some technical terms.",
            positive_examples=["This explanation is very clear.", "Good use of examples."],
            improvement_examples=["This sentence is too complex."],
            confidence=0.9
        )
    
    @pytest.fixture
    def sample_evaluation_result(self):
        """Create a sample evaluation result for testing."""
        # Create test metrics
        metrics = [
            Metric(name="clarity", description="How clear is the content?", weight=0.5, category="readability"),
            Metric(name="structure", description="How well-structured is the content?", weight=0.5, category="readability"),
            Metric(name="accuracy", description="How accurate is the content?", weight=1.0, category="quality")
        ]
        
        # Create test metric results
        metric_results = [
            MetricResult(
                metric=metrics[0],
                score=4,
                reasoning="The content is generally clear and easy to understand.",
                improvement_advice="Consider simplifying some technical terms.",
                positive_examples=["This explanation is very clear.", "Good use of examples."],
                improvement_examples=["This sentence is too complex."],
                confidence=0.9
            ),
            MetricResult(
                metric=metrics[1],
                score=3,
                reasoning="The structure is adequate but could be improved.",
                improvement_advice="Add more headings and subheadings.",
                positive_examples=["Good introduction section."],
                improvement_examples=["This section lacks a clear heading.", "Too many ideas in one paragraph."],
                confidence=0.8
            ),
            MetricResult(
                metric=metrics[2],
                score=5,
                reasoning="All information appears to be accurate.",
                improvement_advice="No improvements needed for accuracy.",
                positive_examples=["Correct citation of statistics.", "Accurate technical details."],
                improvement_examples=[],
                confidence=1.0
            )
        ]
        
        # Create test evaluation result
        return EvaluationResult(
            content_hash="abc123def456",
            timestamp=datetime(2024, 7, 18, 10, 30, 0),
            overall_score=4.0,
            category_scores={
                "readability": 3.5,
                "quality": 5.0
            },
            metric_results=metric_results,
            metadata={
                "word_count": 500,
                "evaluation_duration": 2.5
            }
        )
    
    def test_create_gauge_chart(self):
        """Test creation of gauge chart."""
        # Create gauge chart with different scores
        fig1 = create_gauge_chart(1.5, "Poor Score")
        fig2 = create_gauge_chart(3.0, "Average Score")
        fig3 = create_gauge_chart(4.8, "Excellent Score")
        
        # Verify the figures are created correctly
        assert isinstance(fig1, go.Figure)
        assert isinstance(fig2, go.Figure)
        assert isinstance(fig3, go.Figure)
        
        # Check that the charts have the correct values
        assert fig1.data[0].value == 1.5
        assert fig2.data[0].value == 3.0
        assert fig3.data[0].value == 4.8
        
        # Check that the titles are set correctly
        assert fig1.data[0].title.text == "Poor Score"
        assert fig2.data[0].title.text == "Average Score"
        assert fig3.data[0].title.text == "Excellent Score"
        
        # Check that the gauge ranges are set correctly (1-5)
        assert fig1.data[0].gauge.axis.range == [1, 5]
        assert fig2.data[0].gauge.axis.range == [1, 5]
        assert fig3.data[0].gauge.axis.range == [1, 5]
    
    def test_create_radar_chart(self):
        """Test creation of radar chart."""
        # Create radar chart with different category scores
        category_scores = {
            "readability": 3.5,
            "quality": 4.2,
            "engagement": 2.8,
            "accuracy": 4.5
        }
        
        fig = create_radar_chart(category_scores)
        
        # Verify the figure is created correctly
        assert isinstance(fig, go.Figure)
        
        # Check that the chart has the correct data
        # The first trace should be the category scores
        # Note: The radar chart adds the first category again at the end to close the polygon
        assert len(fig.data[0].r) == len(category_scores) + 1
        assert len(fig.data[0].theta) == len(category_scores) + 1
        
        # Check that the categories are included
        for category in category_scores.keys():
            assert category in fig.data[0].theta
        
        # Check that the second trace is the reference line (max score of 5)
        assert all(value == 5 for value in fig.data[1].r)
    
    @patch('streamlit.markdown')
    @patch('streamlit.write')
    @patch('streamlit.success')
    @patch('streamlit.warning')
    @patch('streamlit.columns')
    def test_display_metric_result(self, mock_columns, mock_warning, mock_success, mock_write, mock_markdown, sample_metric_result):
        """Test display of a single metric result."""
        # Mock the columns function to return MagicMock objects
        col1_mock = MagicMock()
        col2_mock = MagicMock()
        mock_columns.return_value = [col1_mock, col2_mock]
        
        # Call the function
        display_metric_result(sample_metric_result)
        
        # Verify markdown calls for metric name and description
        col1_mock.__enter__.return_value.markdown.assert_any_call("### Clarity")
        col1_mock.__enter__.return_value.markdown.assert_any_call("*How clear is the content?*")
        
        # Verify markdown call for score display
        col2_mock.__enter__.return_value.markdown.assert_called_with(
            '<h2 style=\'text-align: center; color: lightgreen;\'>4/5</h2>',
            unsafe_allow_html=True
        )
        
        # Verify markdown calls for section headers
        mock_markdown.assert_any_call("#### Reasoning")
        mock_markdown.assert_any_call("#### Improvement Advice")
        mock_markdown.assert_any_call("#### Positive Examples")
        mock_markdown.assert_any_call("#### Areas for Improvement")
        
        # Verify write calls for content
        mock_write.assert_any_call("The content is generally clear and easy to understand.")
        mock_write.assert_any_call("Consider simplifying some technical terms.")
        
        # Verify success calls for positive examples
        mock_success.assert_any_call('"This explanation is very clear."')
        mock_success.assert_any_call('"Good use of examples."')
        
        # Verify warning calls for improvement examples
        mock_warning.assert_called_with('"This sentence is too complex."')
    
    @patch('main.create_gauge_chart')
    @patch('main.create_radar_chart')
    @patch('streamlit.plotly_chart')
    @patch('streamlit.header')
    @patch('streamlit.subheader')
    @patch('streamlit.expander')
    def test_display_evaluation_results(self, mock_expander, mock_subheader, mock_header, 
                                       mock_plotly_chart, mock_radar_chart, mock_gauge_chart, 
                                       sample_evaluation_result):
        """Test display of complete evaluation results."""
        # Mock the chart creation functions
        mock_gauge_fig = MagicMock()
        mock_radar_fig = MagicMock()
        mock_gauge_chart.return_value = mock_gauge_fig
        mock_radar_chart.return_value = mock_radar_fig
        
        # Mock the expander context manager
        expander_mock = MagicMock()
        mock_expander.return_value.__enter__.return_value = expander_mock
        
        # Call the function
        with patch('main.display_metric_result') as mock_display_metric:
            display_evaluation_results(sample_evaluation_result)
            
            # Verify header and subheader calls
            mock_header.assert_called_with("Evaluation Results")
            mock_subheader.assert_any_call("Overall Score")
            mock_subheader.assert_any_call("Category Scores")
            mock_subheader.assert_any_call("Detailed Metric Results")
            
            # Verify chart creation calls
            mock_gauge_chart.assert_called_with(sample_evaluation_result.overall_score)
            mock_radar_chart.assert_called_with(sample_evaluation_result.category_scores)
            
            # Verify plotly chart display calls
            assert mock_plotly_chart.call_count == 2
            
            # Verify expander calls for categories
            mock_expander.assert_any_call("Readability - 2 metrics")
            mock_expander.assert_any_call("Quality - 1 metrics")
            
            # Verify metric result display calls
            assert mock_display_metric.call_count == 3