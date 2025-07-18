"""Unit tests for guidelines management system."""

import pytest
import tempfile
import yaml
from pathlib import Path
from pydantic import ValidationError

from storage.guidelines import (
    Guidelines,
    GuidelineCategory,
    GuidelineMetric,
    load_guidelines,
    save_guidelines,
    get_default_guidelines
)
from config.models import Metric


class TestGuidelineMetric:
    """Test GuidelineMetric model."""
    
    def test_valid_metric_creation(self):
        """Test creating a valid GuidelineMetric."""
        metric = GuidelineMetric(
            description="Test metric description",
            weight=0.5
        )
        assert metric.description == "Test metric description"
        assert metric.weight == 0.5
    
    def test_invalid_weight_too_high(self):
        """Test that weight > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            GuidelineMetric(
                description="Test metric",
                weight=1.5
            )
    
    def test_invalid_weight_negative(self):
        """Test that negative weight raises ValidationError."""
        with pytest.raises(ValidationError):
            GuidelineMetric(
                description="Test metric",
                weight=-0.1
            )
    
    def test_missing_description(self):
        """Test that missing description raises ValidationError."""
        with pytest.raises(ValidationError):
            GuidelineMetric(weight=0.5)


class TestGuidelineCategory:
    """Test GuidelineCategory model."""
    
    def test_valid_category_creation(self):
        """Test creating a valid GuidelineCategory."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=0.6),
            "metric2": GuidelineMetric(description="Second metric", weight=0.4)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        assert category.weight == 1.0
        assert category.description == "Test category"
        assert len(category.metrics) == 2
    
    def test_validate_metric_weights_valid(self):
        """Test metric weight validation with valid weights."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=0.3),
            "metric2": GuidelineMetric(description="Second metric", weight=0.7)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        assert category.validate_metric_weights() is True
    
    def test_validate_metric_weights_invalid(self):
        """Test metric weight validation with invalid weights."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=0.3),
            "metric2": GuidelineMetric(description="Second metric", weight=0.8)  # Total = 1.1
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        assert category.validate_metric_weights() is False
    
    def test_validate_metric_weights_floating_point_tolerance(self):
        """Test that small floating point errors are tolerated."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=0.33333),
            "metric2": GuidelineMetric(description="Second metric", weight=0.33333),
            "metric3": GuidelineMetric(description="Third metric", weight=0.33334)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        # Total is 1.00000, should pass with tolerance
        assert category.validate_metric_weights() is True


class TestGuidelines:
    """Test Guidelines model."""
    
    def test_valid_guidelines_creation(self):
        """Test creating valid Guidelines."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=1.0)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        guidelines = Guidelines(categories={"test": category})
        assert len(guidelines.categories) == 1
        assert "test" in guidelines.categories
    
    def test_validate_structure_valid(self):
        """Test structure validation with valid guidelines."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=1.0)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        guidelines = Guidelines(categories={"test": category})
        assert guidelines.validate_structure() is True
    
    def test_validate_structure_empty_categories(self):
        """Test structure validation with empty categories."""
        guidelines = Guidelines(categories={})
        assert guidelines.validate_structure() is False
    
    def test_validate_structure_invalid_metric_weights(self):
        """Test structure validation with invalid metric weights."""
        metrics = {
            "metric1": GuidelineMetric(description="First metric", weight=0.3),
            "metric2": GuidelineMetric(description="Second metric", weight=0.8)  # Total = 1.1
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics
        )
        guidelines = Guidelines(categories={"test": category})
        
        with pytest.raises(ValueError, match="do not sum to 1.0"):
            guidelines.validate_structure()
    
    def test_to_metrics_list(self):
        """Test conversion to list of Metric objects."""
        metrics_config = {
            "metric1": GuidelineMetric(description="First metric", weight=0.6),
            "metric2": GuidelineMetric(description="Second metric", weight=0.4)
        }
        category = GuidelineCategory(
            weight=1.0,
            description="Test category",
            metrics=metrics_config
        )
        guidelines = Guidelines(categories={"test_category": category})
        
        metrics_list = guidelines.to_metrics_list()
        
        assert len(metrics_list) == 2
        assert all(isinstance(m, Metric) for m in metrics_list)
        assert metrics_list[0].name == "metric1"
        assert metrics_list[0].category == "test_category"
        assert metrics_list[0].weight == 0.6
        assert metrics_list[1].name == "metric2"
        assert metrics_list[1].category == "test_category"
        assert metrics_list[1].weight == 0.4


class TestDefaultGuidelines:
    """Test default guidelines functionality."""
    
    def test_get_default_guidelines(self):
        """Test that default guidelines are properly structured."""
        guidelines = get_default_guidelines()
        
        # Should have 5 categories
        assert len(guidelines.categories) == 5
        expected_categories = {"clarity", "accuracy", "engagement", "completeness", "readability"}
        assert set(guidelines.categories.keys()) == expected_categories
        
        # Validate structure
        assert guidelines.validate_structure() is True
        
        # Check that each category has metrics
        for category_name, category in guidelines.categories.items():
            assert len(category.metrics) > 0
            assert category.weight > 0
            assert category.description
            
            # Validate metric weights sum to 1.0
            assert category.validate_metric_weights() is True
    
    def test_default_guidelines_specific_content(self):
        """Test specific content of default guidelines."""
        guidelines = get_default_guidelines()
        
        # Test clarity category
        clarity = guidelines.categories["clarity"]
        assert clarity.weight == 1.0
        assert "conciseness" in clarity.metrics
        assert "jargon_usage" in clarity.metrics
        assert "logical_structure" in clarity.metrics
        
        # Test accuracy category
        accuracy = guidelines.categories["accuracy"]
        assert accuracy.weight == 1.2
        assert "data_support" in accuracy.metrics
        assert "fact_verification" in accuracy.metrics
        
        # Test that all metrics have proper descriptions
        for category in guidelines.categories.values():
            for metric in category.metrics.values():
                assert metric.description
                assert 0 <= metric.weight <= 1.0


class TestGuidelinesLoading:
    """Test guidelines loading functionality."""
    
    def test_load_guidelines_nonexistent_file(self, capsys):
        """Test loading guidelines when file doesn't exist."""
        guidelines = load_guidelines("nonexistent_file.yaml")
        
        # Should return default guidelines
        assert len(guidelines.categories) == 5
        
        # Should print warning message
        captured = capsys.readouterr()
        assert "not found" in captured.out
        assert "Using default guidelines" in captured.out
    
    def test_load_guidelines_valid_file(self):
        """Test loading guidelines from a valid YAML file."""
        # Create temporary YAML file
        test_data = {
            "categories": {
                "test_category": {
                    "weight": 1.0,
                    "description": "Test category description",
                    "metrics": {
                        "test_metric": {
                            "description": "Test metric description",
                            "weight": 1.0
                        }
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name
        
        try:
            guidelines = load_guidelines(temp_path)
            
            assert len(guidelines.categories) == 1
            assert "test_category" in guidelines.categories
            assert guidelines.categories["test_category"].weight == 1.0
            assert "test_metric" in guidelines.categories["test_category"].metrics
        finally:
            Path(temp_path).unlink()
    
    def test_load_guidelines_empty_file(self, capsys):
        """Test loading guidelines from an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            guidelines = load_guidelines(temp_path)
            
            # Should return default guidelines
            assert len(guidelines.categories) == 5
            
            # Should print warning message
            captured = capsys.readouterr()
            assert "is empty" in captured.out
            assert "Using default guidelines" in captured.out
        finally:
            Path(temp_path).unlink()
    
    def test_load_guidelines_invalid_yaml(self, capsys):
        """Test loading guidelines from invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            temp_path = f.name
        
        try:
            guidelines = load_guidelines(temp_path)
            
            # Should return default guidelines
            assert len(guidelines.categories) == 5
            
            # Should print error message
            captured = capsys.readouterr()
            assert "Error parsing YAML" in captured.out
            assert "Using default guidelines" in captured.out
        finally:
            Path(temp_path).unlink()
    
    def test_load_guidelines_invalid_structure(self, capsys):
        """Test loading guidelines with invalid structure."""
        # Create YAML with invalid structure (missing required fields)
        test_data = {
            "categories": {
                "invalid_category": {
                    "weight": 1.0
                    # Missing description and metrics
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name
        
        try:
            guidelines = load_guidelines(temp_path)
            
            # Should return default guidelines
            assert len(guidelines.categories) == 5
            
            # Should print validation error message
            captured = capsys.readouterr()
            assert "Invalid guidelines structure" in captured.out
            assert "Using default guidelines" in captured.out
        finally:
            Path(temp_path).unlink()
    
    def test_load_guidelines_default_path(self):
        """Test loading guidelines with default path."""
        # Should use default path when none provided
        guidelines = load_guidelines()
        
        # Should return default guidelines (since guidelines.yaml doesn't exist)
        assert len(guidelines.categories) == 5


class TestGuidelinesSaving:
    """Test guidelines saving functionality."""
    
    def test_save_guidelines_success(self):
        """Test successfully saving guidelines to file."""
        guidelines = get_default_guidelines()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # Remove the file so we can test creation
            Path(temp_path).unlink()
            
            result = save_guidelines(guidelines, temp_path)
            assert result is True
            
            # Verify file was created and contains valid YAML
            assert Path(temp_path).exists()
            
            # Load and verify content
            with open(temp_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert "categories" in loaded_data
            assert len(loaded_data["categories"]) == 5
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
    
    def test_save_guidelines_default_path(self):
        """Test saving guidelines with default path."""
        guidelines = get_default_guidelines()
        
        # Clean up any existing file
        default_path = Path("guidelines.yaml")
        if default_path.exists():
            default_path.unlink()
        
        try:
            result = save_guidelines(guidelines)
            assert result is True
            assert default_path.exists()
        finally:
            if default_path.exists():
                default_path.unlink()
    
    def test_save_guidelines_creates_directory(self):
        """Test that saving guidelines creates parent directories."""
        guidelines = get_default_guidelines()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "nested" / "directory" / "guidelines.yaml"
            
            result = save_guidelines(guidelines, str(nested_path))
            assert result is True
            assert nested_path.exists()
            
            # Verify content
            with open(nested_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            assert "categories" in loaded_data


if __name__ == "__main__":
    pytest.main([__file__])