"""Quick test to verify the data models work correctly."""

from config.models import Metric, MetricResult, EvaluationResult, LLMConfig, AppConfig
from datetime import datetime

# Test Metric model
metric = Metric(
    name="clarity",
    description="How clear and understandable is the content?",
    weight=0.8,
    category="readability"
)
print(f"✓ Metric model created: {metric.name}")

# Test MetricResult model
metric_result = MetricResult(
    metric=metric,
    score=4,
    reasoning="The content is generally clear with good structure.",
    improvement_advice="Consider adding more examples to clarify complex concepts.",
    positive_examples=["Clear headings", "Good paragraph structure"],
    improvement_examples=["Technical jargon in paragraph 3", "Long sentence in conclusion"]
)
print(f"✓ MetricResult model created with score: {metric_result.score}")

# Test EvaluationResult model
evaluation = EvaluationResult(
    content_hash="abc123",
    overall_score=3.8,
    category_scores={"readability": 4.0, "accuracy": 3.6},
    metric_results=[metric_result],
    metadata={"word_count": 500}
)
print(f"✓ EvaluationResult model created with overall score: {evaluation.overall_score}")

# Test LLMConfig model
llm_config = LLMConfig(
    provider="openai",
    model_name="gpt-4",
    temperature=0.3
)
print(f"✓ LLMConfig model created for provider: {llm_config.provider}")

# Test AppConfig model
app_config = AppConfig(
    llm=llm_config,
    guidelines_path="guidelines.yaml",
    reports_dir="reports"
)
print(f"✓ AppConfig model created with reports dir: {app_config.reports_dir}")

print("\n✅ All data models are working correctly!")