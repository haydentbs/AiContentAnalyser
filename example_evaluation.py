#!/usr/bin/env python3
"""Example script demonstrating how to use the MetricEvaluator agent.

This script loads configuration, creates an LLM client and MetricEvaluator agent,
and runs an evaluation on a sample piece of content against a specific metric.
"""

import asyncio
import logging
import sys
import tomli
from pathlib import Path

from config.models import LLMConfig, Metric
from agents.llm_client import create_llm_client, LLMClientError
from agents.metric_evaluator import MetricEvaluator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Sample content for evaluation
SAMPLE_CONTENT = """# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on developing systems that can learn from and make decisions based on data. Unlike traditional programming, where explicit instructions are provided, machine learning algorithms build models based on sample data to make predictions or decisions without being explicitly programmed to do so.

## Types of Machine Learning

There are several types of machine learning approaches:

1. **Supervised Learning**: The algorithm is trained on labeled data, learning to map inputs to known outputs.
2. **Unsupervised Learning**: The algorithm finds patterns in unlabeled data.
3. **Reinforcement Learning**: The algorithm learns by interacting with an environment and receiving feedback.

## Applications

Machine learning has numerous applications across various industries:

- Healthcare: Disease diagnosis, personalized treatment plans
- Finance: Fraud detection, algorithmic trading
- Retail: Recommendation systems, inventory management
- Transportation: Self-driving vehicles, traffic prediction

## Challenges

Despite its potential, machine learning faces several challenges:

- Data quality and quantity requirements
- Interpretability of complex models
- Ethical concerns regarding bias and privacy
- Computational resources needed for training

As the field continues to evolve, researchers are working to address these challenges while expanding the capabilities and applications of machine learning technologies.
"""


async def main():
    """Run the example evaluation."""
    try:
        # Load configuration from config.toml
        logger.info("Loading configuration from config.toml")
        config_path = Path("config.toml")
        if not config_path.exists():
            logger.error("config.toml not found")
            return
        
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        # Create LLM configuration
        llm_config = LLMConfig(**config_data["llm"])
        
        # If API key is not in the config, try to get it from the openai section
        if not llm_config.api_key and llm_config.provider == "openai" and "openai" in config_data:
            llm_config.api_key = config_data["openai"].get("api_key")
        
        logger.info(f"Using LLM provider: {llm_config.provider}, model: {llm_config.model_name}")
        
        # Create LLM client
        llm_client = create_llm_client(llm_config)
        
        # Test LLM connection
        logger.info("Testing LLM connection...")
        connection_test = await llm_client.test_connection()
        if not connection_test.success:
            logger.error(f"LLM connection failed: {connection_test.error}")
            return
        
        logger.info(f"LLM connection successful: {connection_test.message}")
        
        # Create MetricEvaluator agent
        evaluator = MetricEvaluator(llm_client)
        
        # Define a metric for evaluation
        metric = Metric(
            name="clarity",
            description="How clear and understandable is the content for the target audience?",
            weight=0.8,
            category="readability"
        )
        
        # Run the evaluation
        logger.info(f"Evaluating content against metric: {metric.name}")
        result = await evaluator.evaluate_metric(SAMPLE_CONTENT, metric)
        
        # Display the results
        print("\n" + "="*50)
        print(f"Evaluation Results for '{metric.name}' metric")
        print("="*50)
        print(f"Score: {result.score}/5")
        print(f"Confidence: {result.confidence:.2f}")
        print("\nReasoning:")
        print(result.reasoning)
        print("\nImprovement Advice:")
        print(result.improvement_advice)
        print("\nPositive Examples:")
        for i, example in enumerate(result.positive_examples, 1):
            print(f"{i}. {example}")
        print("\nImprovement Examples:")
        for i, example in enumerate(result.improvement_examples, 1):
            print(f"{i}. {example}")
        print("="*50)
        
    except LLMClientError as e:
        logger.error(f"LLM client error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())