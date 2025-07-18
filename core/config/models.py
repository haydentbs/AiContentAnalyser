"""Core data models for the Content Scorecard application."""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    model_config = {"protected_namespaces": ()}
    
    provider: Literal["openai", "ollama", "lmstudio"] = Field(..., description="LLM provider to use")
    model_name: str = Field(..., description="Name of the model to use")
    api_key: Optional[str] = Field(None, description="API key for the provider (if required)")
    base_url: Optional[str] = Field(None, description="Base URL for the provider API")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Temperature for text generation")


class Sample(BaseModel):
    """Represents a sample content entry."""
    id: str = Field(..., description="Unique identifier for the sample")
    title: str = Field(..., description="Title of the sample content")
    description: str = Field(..., description="Brief description of the sample content")
    content: str = Field(..., description="The actual sample content")


class UpdateSettingsRequest(BaseModel):
    """Request model for updating application settings."""
    llm: LLMConfig = Field(..., description="LLM configuration to update")


class TestConnectionRequest(BaseModel):
    """Request model for testing LLM connection."""
    llm: LLMConfig = Field(..., description="LLM configuration to test")


class Metric(BaseModel):
    """Represents a single evaluation metric."""
    name: str = Field(..., description="Name of the metric")
    description: str = Field(..., description="Description of what this metric evaluates")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of this metric (0.0 to 1.0)")
    category: str = Field(..., description="Category this metric belongs to")


class MetricResult(BaseModel):
    """Result of evaluating content against a single metric."""
    metric: Metric = Field(..., description="The metric that was evaluated")
    score: int = Field(..., ge=1, le=5, description="Score from 1-5")
    reasoning: str = Field(..., description="Detailed reasoning for the score")
    improvement_advice: str = Field(..., description="Specific advice for improvement")
    positive_examples: List[str] = Field(default_factory=list, description="Examples of what works well in the content")
    improvement_examples: List[str] = Field(default_factory=list, description="Specific examples that need improvement")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the evaluation (0.0 to 1.0)")


class EvaluationResult(BaseModel):
    """Complete evaluation result for a piece of content."""
    content_hash: str = Field(..., description="Hash of the evaluated content")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the evaluation was performed")
    overall_score: float = Field(..., ge=1.0, le=5.0, description="Overall weighted score")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Scores by category")
    metric_results: List[MetricResult] = Field(default_factory=list, description="Individual metric results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the evaluation")


class AppConfig(BaseModel):
    """Main application configuration."""
    llm: LLMConfig = Field(..., description="LLM configuration")
    guidelines_path: str = Field(default="guidelines.yaml", description="Path to guidelines file")
    reports_dir: str = Field(default="reports", description="Directory for saving reports")
    ui_theme: str = Field(default="light", description="UI theme")