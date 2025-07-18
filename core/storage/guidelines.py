"""Guidelines management system for Content Scorecard."""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from ..config.models import Metric


class GuidelineMetric(BaseModel):
    """Represents a metric within a guideline category."""
    description: str = Field(..., description="Description of what this metric evaluates")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of this metric within its category")


class GuidelineCategory(BaseModel):
    """Represents a category of evaluation guidelines."""
    weight: float = Field(..., ge=0.0, description="Weight of this category in overall scoring")
    description: str = Field(..., description="Description of this category")
    metrics: Dict[str, GuidelineMetric] = Field(..., description="Metrics within this category")
    
    def validate_metric_weights(self) -> bool:
        """Validate that metric weights sum to approximately 1.0."""
        total_weight = sum(metric.weight for metric in self.metrics.values())
        return abs(total_weight - 1.0) < 0.01  # Allow small floating point errors


class Guidelines(BaseModel):
    """Complete guidelines configuration."""
    categories: Dict[str, GuidelineCategory] = Field(..., description="Categories of evaluation guidelines")
    
    def validate_structure(self) -> bool:
        """Validate the overall guidelines structure."""
        if not self.categories:
            return False
        
        # Validate each category's metric weights
        for category_name, category in self.categories.items():
            if not category.validate_metric_weights():
                raise ValueError(f"Metric weights in category '{category_name}' do not sum to 1.0")
        
        return True
    
    def to_metrics_list(self) -> List[Metric]:
        """Convert guidelines to a list of Metric objects."""
        metrics = []
        for category_name, category in self.categories.items():
            for metric_name, metric_config in category.metrics.items():
                metric = Metric(
                    name=metric_name,
                    description=metric_config.description,
                    weight=metric_config.weight,
                    category=category_name
                )
                metrics.append(metric)
        return metrics


def get_default_guidelines() -> Guidelines:
    """Get default guidelines with 5 categories and multiple metrics."""
    default_data = {
        "categories": {
            "clarity": {
                "weight": 1.0,
                "description": "How clear and understandable is the content?",
                "metrics": {
                    "conciseness": {
                        "description": "Is the writing free of unnecessary filler words and redundancy?",
                        "weight": 0.3
                    },
                    "jargon_usage": {
                        "description": "Is technical jargon properly defined or avoided when appropriate?",
                        "weight": 0.4
                    },
                    "logical_structure": {
                        "description": "Does the content follow a logical flow with clear headings and transitions?",
                        "weight": 0.3
                    }
                }
            },
            "accuracy": {
                "weight": 1.2,
                "description": "How factually correct and well-supported is the content?",
                "metrics": {
                    "data_support": {
                        "description": "Are claims backed by credible data, sources, or evidence?",
                        "weight": 0.6
                    },
                    "fact_verification": {
                        "description": "Are there any apparent factual errors or unsupported claims?",
                        "weight": 0.4
                    }
                }
            },
            "engagement": {
                "weight": 0.9,
                "description": "How engaging and compelling is the content for the target audience?",
                "metrics": {
                    "audience_relevance": {
                        "description": "Is the content relevant and valuable to the intended audience?",
                        "weight": 0.4
                    },
                    "tone_appropriateness": {
                        "description": "Is the tone appropriate for the content type and audience?",
                        "weight": 0.3
                    },
                    "call_to_action": {
                        "description": "Does the content include clear next steps or calls to action where appropriate?",
                        "weight": 0.3
                    }
                }
            },
            "completeness": {
                "weight": 1.1,
                "description": "How complete and comprehensive is the content coverage?",
                "metrics": {
                    "topic_coverage": {
                        "description": "Are all important aspects of the topic adequately covered?",
                        "weight": 0.5
                    },
                    "depth_analysis": {
                        "description": "Is the analysis sufficiently detailed for the intended purpose?",
                        "weight": 0.3
                    },
                    "context_provision": {
                        "description": "Is sufficient background context provided for understanding?",
                        "weight": 0.2
                    }
                }
            },
            "readability": {
                "weight": 0.8,
                "description": "How easy is the content to read and understand?",
                "metrics": {
                    "sentence_structure": {
                        "description": "Are sentences well-constructed with appropriate length and complexity?",
                        "weight": 0.4
                    },
                    "paragraph_organization": {
                        "description": "Are paragraphs well-organized with clear topic sentences?",
                        "weight": 0.3
                    },
                    "formatting_consistency": {
                        "description": "Is formatting consistent and does it enhance readability?",
                        "weight": 0.3
                    }
                }
            }
        }
    }
    
    return Guidelines(**default_data)


def load_guidelines(file_path: Optional[str] = None) -> Guidelines:
    """
    Load guidelines from YAML file with fallback to defaults.
    
    Args:
        file_path: Path to the guidelines YAML file. If None, uses 'guidelines.yaml'
    
    Returns:
        Guidelines object with loaded or default configuration
    
    Raises:
        ValidationError: If the loaded guidelines fail validation
    """
    if file_path is None:
        file_path = "guidelines.yaml"
    
    guidelines_path = Path(file_path)
    
    # If file doesn't exist, return default guidelines
    if not guidelines_path.exists():
        print(f"Guidelines file '{file_path}' not found. Using default guidelines.")
        return get_default_guidelines()
    
    try:
        # Load and parse YAML file
        with open(guidelines_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        if not yaml_data:
            print(f"Guidelines file '{file_path}' is empty. Using default guidelines.")
            return get_default_guidelines()
        
        # Validate and create Guidelines object
        guidelines = Guidelines(**yaml_data)
        guidelines.validate_structure()
        
        print(f"Successfully loaded guidelines from '{file_path}'")
        return guidelines
        
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file '{file_path}': {e}")
        print("Using default guidelines.")
        return get_default_guidelines()
        
    except ValidationError as e:
        print(f"Invalid guidelines structure in '{file_path}': {e}")
        print("Using default guidelines.")
        return get_default_guidelines()
        
    except Exception as e:
        print(f"Unexpected error loading guidelines from '{file_path}': {e}")
        print("Using default guidelines.")
        return get_default_guidelines()


def save_guidelines(guidelines: Guidelines, file_path: Optional[str] = None) -> bool:
    """
    Save guidelines to YAML file.
    
    Args:
        guidelines: Guidelines object to save
        file_path: Path to save the file. If None, uses 'guidelines.yaml'
    
    Returns:
        True if successful, False otherwise
    """
    if file_path is None:
        file_path = "guidelines.yaml"
    
    try:
        guidelines_path = Path(file_path)
        guidelines_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for YAML serialization
        data = guidelines.model_dump()
        
        with open(guidelines_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
        
        print(f"Guidelines saved to '{file_path}'")
        return True
        
    except Exception as e:
        print(f"Error saving guidelines to '{file_path}': {e}")
        return False