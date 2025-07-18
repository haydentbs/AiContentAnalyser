"""Coordinator agent for orchestrating multiple metric evaluations.

This module implements the CoordinatorAgent that manages the evaluation workflow,
creates individual agents for each metric, runs evaluations in parallel,
and aggregates results into a complete evaluation report.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from config.models import Metric, MetricResult, EvaluationResult
from agents.llm_client import BaseLLMClient, LLMClientError
from agents.metric_evaluator import MetricEvaluator, EvaluationPromptTemplate
from storage.guidelines import Guidelines


# Set up logging
logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Agent for coordinating multiple metric evaluations."""
    
    def __init__(
        self, 
        llm_client: BaseLLMClient,
        max_concurrent_evaluations: int = 3,
        prompt_template: Optional[EvaluationPromptTemplate] = None
    ):
        """Initialize the CoordinatorAgent.
        
        Args:
            llm_client: LLM client for making API calls
            max_concurrent_evaluations: Maximum number of concurrent evaluations to run
            prompt_template: Optional custom prompt template for metric evaluators
        """
        self.llm = llm_client
        self.max_concurrent_evaluations = max_concurrent_evaluations
        self.prompt_template = prompt_template
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def evaluate_content(
        self, 
        content: str, 
        guidelines: Guidelines,
        metrics_to_evaluate: Optional[List[str]] = None
    ) -> EvaluationResult:
        """Evaluate content against all metrics in the guidelines.
        
        Args:
            content: The content to evaluate
            guidelines: Guidelines containing metrics and categories
            metrics_to_evaluate: Optional list of metric names to evaluate (if None, evaluates all)
            
        Returns:
            EvaluationResult containing all metric results and aggregated scores
            
        Raises:
            ValueError: If the content is invalid or no metrics are found
            LLMClientError: If there's an error with the LLM service
        """
        if not content.strip():
            raise ValueError("Content cannot be empty")
        
        # Get metrics from guidelines
        metrics = guidelines.to_metrics_list()
        if not metrics:
            raise ValueError("No metrics found in guidelines")
        
        # Filter metrics if a specific list is provided
        if metrics_to_evaluate:
            metrics = [m for m in metrics if m.name in metrics_to_evaluate]
            if not metrics:
                raise ValueError(f"None of the specified metrics {metrics_to_evaluate} found in guidelines")
        
        # Generate content hash for tracking
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Create a semaphore to limit concurrent evaluations
        semaphore = asyncio.Semaphore(self.max_concurrent_evaluations)
        
        # Create tasks for each metric evaluation
        self.logger.info(f"Starting evaluation of {len(metrics)} metrics")
        tasks = []
        for metric in metrics:
            task = self._evaluate_metric_with_semaphore(content, metric, semaphore)
            tasks.append(task)
        
        # Run all evaluations and gather results
        try:
            metric_results = await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error during metric evaluations: {e}")
            # If some evaluations failed, try to get partial results
            metric_results = [task.result() for task in asyncio.all_tasks() 
                             if task in tasks and task.done() and not task.exception()]
            if not metric_results:
                raise ValueError(f"All metric evaluations failed: {e}")
        
        # Calculate aggregated scores
        overall_score, category_scores = self._calculate_scores(metric_results, guidelines)
        
        # Create the evaluation result
        result = EvaluationResult(
            content_hash=content_hash,
            timestamp=datetime.now(),
            overall_score=overall_score,
            category_scores=category_scores,
            metric_results=metric_results,
            metadata={
                "metrics_evaluated": len(metric_results),
                "metrics_requested": len(metrics),
                "evaluation_time": datetime.now().isoformat()
            }
        )
        
        self.logger.info(f"Evaluation complete. Overall score: {overall_score:.2f}")
        return result
    
    async def _evaluate_metric_with_semaphore(
        self, 
        content: str, 
        metric: Metric, 
        semaphore: asyncio.Semaphore
    ) -> MetricResult:
        """Evaluate a single metric with semaphore for concurrency control.
        
        Args:
            content: The content to evaluate
            metric: The metric to evaluate against
            semaphore: Semaphore for limiting concurrent evaluations
            
        Returns:
            MetricResult containing the evaluation results
        """
        async with semaphore:
            try:
                evaluator = MetricEvaluator(self.llm, self.prompt_template)
                return await evaluator.evaluate_metric(content, metric)
            except Exception as e:
                self.logger.error(f"Error evaluating metric {metric.name}: {e}")
                raise
    
    def _calculate_scores(
        self, 
        metric_results: List[MetricResult], 
        guidelines: Guidelines
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate overall and category scores based on metric results.
        
        Args:
            metric_results: List of metric evaluation results
            guidelines: Guidelines containing category weights
            
        Returns:
            Tuple of (overall_score, category_scores)
        """
        # Group results by category
        results_by_category: Dict[str, List[MetricResult]] = {}
        for result in metric_results:
            category = result.metric.category
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append(result)
        
        # Calculate category scores
        category_scores: Dict[str, float] = {}
        category_weights: Dict[str, float] = {}
        
        # Get category weights from guidelines
        for category_name, category in guidelines.categories.items():
            category_weights[category_name] = category.weight
        
        # Calculate weighted score for each category
        for category, results in results_by_category.items():
            if not results:
                continue
                
            # Calculate weighted average of metric scores within the category
            category_score = 0.0
            total_weight = 0.0
            
            for result in results:
                # Use the metric's weight within its category
                metric_weight = result.metric.weight
                category_score += result.score * metric_weight
                total_weight += metric_weight
            
            if total_weight > 0:
                category_scores[category] = category_score / total_weight
        
        # Calculate overall score as weighted average of category scores
        overall_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = category_weights.get(category, 1.0)  # Default weight of 1.0 if not specified
            overall_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 0.0
        
        return overall_score, category_scores