"""Unit tests for report generation and storage system.

Tests the functionality of the ReportGenerator and ReportStorage classes for
generating and storing evaluation reports in different formats.
"""

import json
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from unittest.mock import patch, mock_open

from config.models import Metric, MetricResult, EvaluationResult
from storage.reports import ReportGenerator, ReportStorage


class TestReportGenerator:
    """Test ReportGenerator implementation."""
    
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
    
    def test_to_json(self, sample_evaluation_result):
        """Test conversion of EvaluationResult to JSON."""
        # Convert to JSON with pretty printing
        json_str = ReportGenerator.to_json(sample_evaluation_result, pretty=True)
        
        # Verify it's valid JSON
        result_dict = json.loads(json_str)
        
        # Check key fields
        assert result_dict["content_hash"] == "abc123def456"
        assert result_dict["timestamp"] == "2024-07-18T10:30:00"
        assert result_dict["overall_score"] == 4.0
        assert "readability" in result_dict["category_scores"]
        assert len(result_dict["metric_results"]) == 3
        
        # Test without pretty printing
        compact_json = ReportGenerator.to_json(sample_evaluation_result, pretty=False)
        assert len(compact_json) < len(json_str)  # Should be more compact
        
        # Verify it's still valid JSON
        json.loads(compact_json)
    
    def test_to_markdown(self, sample_evaluation_result):
        """Test conversion of EvaluationResult to Markdown."""
        # Convert to Markdown
        md_str = ReportGenerator.to_markdown(sample_evaluation_result)
        
        # Check for key sections and formatting
        assert "# Content Evaluation Report" in md_str
        assert "Generated: 2024-07-18 10:30:00" in md_str
        assert "## Overall Score: 4.00/5.00" in md_str
        assert "## Category Scores" in md_str
        assert "**Readability**: 3.50/5.00" in md_str
        assert "**Quality**: 5.00/5.00" in md_str
        assert "## Metric Results" in md_str
        
        # Check for metric details
        assert "### Readability" in md_str
        assert "#### Clarity" in md_str
        assert "**Score**: 4/5" in md_str
        assert "**Reasoning**: The content is generally clear" in md_str
        assert "**Improvement Advice**: Consider simplifying" in md_str
        
        # Check for examples
        assert "**Positive Examples**:" in md_str
        assert "- \"This explanation is very clear.\"" in md_str
        assert "**Improvement Examples**:" in md_str
        assert "- \"This sentence is too complex.\"" in md_str
        
        # Check for metadata
        assert "## Metadata" in md_str
        assert "**word_count**: 500" in md_str
        assert "**evaluation_duration**: 2.5" in md_str


class TestReportStorage:
    """Test ReportStorage implementation."""
    
    @pytest.fixture
    def temp_reports_dir(self):
        """Create a temporary directory for reports."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def report_storage(self, temp_reports_dir):
        """Create a ReportStorage instance with a temporary directory."""
        return ReportStorage(reports_dir=temp_reports_dir)
    
    @pytest.fixture
    def sample_evaluation_result(self):
        """Create a sample evaluation result for testing."""
        # Create a simple evaluation result
        return EvaluationResult(
            content_hash="abc123def456",
            timestamp=datetime(2024, 7, 18, 10, 30, 0),
            overall_score=4.0,
            category_scores={"readability": 3.5, "quality": 5.0},
            metric_results=[
                MetricResult(
                    metric=Metric(name="clarity", description="Test", weight=1.0, category="readability"),
                    score=4,
                    reasoning="Good clarity",
                    improvement_advice="None needed",
                    positive_examples=["Example"],
                    improvement_examples=[],
                    confidence=1.0
                )
            ],
            metadata={"test": "metadata"}
        )
    
    def test_ensure_reports_directory(self, report_storage, temp_reports_dir):
        """Test creation of reports directory."""
        # Remove the directory to test creation
        shutil.rmtree(temp_reports_dir)
        assert not os.path.exists(temp_reports_dir)
        
        # Ensure directory
        report_storage.ensure_reports_directory()
        assert os.path.exists(temp_reports_dir)
        assert os.path.isdir(temp_reports_dir)
    
    def test_ensure_reports_directory_error(self):
        """Test handling of directory creation errors."""
        # Create a ReportStorage with an invalid directory path
        invalid_path = "/nonexistent/directory/that/cannot/be/created"
        storage = ReportStorage(reports_dir=invalid_path)
        
        # Mock os.makedirs to raise an OSError
        with patch('os.makedirs') as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            
            with pytest.raises(OSError):
                storage.ensure_reports_directory()
    
    def test_generate_filename(self, report_storage, sample_evaluation_result):
        """Test generation of filenames."""
        # Generate JSON filename
        json_filename = report_storage.generate_filename(sample_evaluation_result, "json")
        assert json_filename.startswith("report_20240718_103000_")
        assert json_filename.endswith(".json")
        assert sample_evaluation_result.content_hash[:8] in json_filename
        
        # Generate Markdown filename
        md_filename = report_storage.generate_filename(sample_evaluation_result, "md")
        assert md_filename.startswith("report_20240718_103000_")
        assert md_filename.endswith(".md")
        assert sample_evaluation_result.content_hash[:8] in md_filename
    
    def test_save_report_json(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test saving a report in JSON format."""
        # Save the report
        file_path = report_storage.save_report(sample_evaluation_result, "json")
        
        # Verify the file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".json")
        
        # Verify the content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            assert data["content_hash"] == sample_evaluation_result.content_hash
            assert data["overall_score"] == sample_evaluation_result.overall_score
    
    def test_save_report_markdown(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test saving a report in Markdown format."""
        # Save the report
        file_path = report_storage.save_report(sample_evaluation_result, "md")
        
        # Verify the file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".md")
        
        # Verify the content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "# Content Evaluation Report" in content
            assert f"Content Hash: {sample_evaluation_result.content_hash}" in content
            assert f"## Overall Score: {sample_evaluation_result.overall_score:.2f}/5.00" in content
    
    def test_save_report_custom_filename(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test saving a report with a custom filename."""
        # Save with custom filename
        custom_filename = "custom_report.json"
        file_path = report_storage.save_report(sample_evaluation_result, "json", custom_filename)
        
        # Verify the file exists with the custom name
        assert os.path.basename(file_path) == custom_filename
        assert os.path.exists(file_path)
    
    def test_save_report_invalid_format(self, report_storage, sample_evaluation_result):
        """Test handling of invalid format types."""
        with pytest.raises(ValueError, match="Invalid format type"):
            report_storage.save_report(sample_evaluation_result, "invalid")
    
    def test_save_all_formats(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test saving a report in all formats."""
        # Save in all formats
        paths = report_storage.save_all_formats(sample_evaluation_result)
        
        # Verify both files exist
        assert "json" in paths
        assert "markdown" in paths
        assert os.path.exists(paths["json"])
        assert os.path.exists(paths["markdown"])
        assert paths["json"].endswith(".json")
        assert paths["markdown"].endswith(".md")
        
        # Verify they have the same prefix
        json_basename = os.path.basename(paths["json"])
        md_basename = os.path.basename(paths["markdown"])
        json_prefix = json_basename.rsplit(".", 1)[0]
        md_prefix = md_basename.rsplit(".", 1)[0]
        assert json_prefix == md_prefix
    
    def test_save_all_formats_custom_prefix(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test saving a report in all formats with a custom prefix."""
        # Save with custom prefix
        custom_prefix = "my_special_report"
        paths = report_storage.save_all_formats(sample_evaluation_result, custom_prefix)
        
        # Verify filenames
        assert os.path.basename(paths["json"]) == f"{custom_prefix}.json"
        assert os.path.basename(paths["markdown"]) == f"{custom_prefix}.md"
    
    def test_load_report(self, report_storage, sample_evaluation_result, temp_reports_dir):
        """Test loading a report from a file."""
        # Save a report
        file_path = report_storage.save_report(sample_evaluation_result, "json")
        
        # Load the report
        loaded_result = report_storage.load_report(file_path)
        
        # Verify it matches the original
        assert loaded_result.content_hash == sample_evaluation_result.content_hash
        assert loaded_result.overall_score == sample_evaluation_result.overall_score
        assert loaded_result.category_scores == sample_evaluation_result.category_scores
        assert len(loaded_result.metric_results) == len(sample_evaluation_result.metric_results)
    
    def test_load_report_file_not_found(self, report_storage):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            report_storage.load_report("nonexistent_file.json")
    
    def test_load_report_invalid_format(self, report_storage, temp_reports_dir):
        """Test handling of invalid file formats."""
        # Create a non-JSON file
        invalid_path = os.path.join(temp_reports_dir, "invalid.txt")
        with open(invalid_path, "w") as f:
            f.write("Not a JSON file")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            report_storage.load_report(invalid_path)
    
    def test_load_report_invalid_json(self, report_storage, temp_reports_dir):
        """Test handling of invalid JSON content."""
        # Create an invalid JSON file
        invalid_path = os.path.join(temp_reports_dir, "invalid.json")
        with open(invalid_path, "w") as f:
            f.write("Not a valid JSON content")
        
        with pytest.raises(json.JSONDecodeError):
            report_storage.load_report(invalid_path)