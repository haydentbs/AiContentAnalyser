"""Adapter for CoordinatorAgent to provide progress tracking and error handling."""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union

from ..agents.coordinator_agent import CoordinatorAgent
from ..config.models import EvaluationResult, MetricResult
from ..storage.guidelines import Guidelines


logger = logging.getLogger(__name__)


class CoordinatorAdapter:
    """Adapter for CoordinatorAgent with progress tracking and error handling."""
    
    def __init__(self, coordinator: CoordinatorAgent):
        """Initialize the adapter.
        
        Args:
            coordinator: CoordinatorAgent to adapt
        """
        self.coordinator = coordinator
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Progress tracking
        self.progress_callbacks: Dict[str, Callable[[str, int, int], None]] = {}
    
    def register_progress_callback(
        self, 
        request_id: str, 
        callback: Callable[[str, int, int], None]
    ) -> None:
        """Register a callback for progress updates.
        
        Args:
            request_id: ID of the request
            callback: Function to call with progress updates (request_id, completed, total)
        """
        self.progress_callbacks[request_id] = callback
    
    def unregister_progress_callback(self, request_id: str) -> None:
        """Unregister a progress callback.
        
        Args:
            request_id: ID of the request
        """
        if request_id in self.progress_callbacks:
            del self.progress_callbacks[request_id]
    
    async def evaluate_content(
        self, 
        content: str, 
        guidelines: Guidelines,
        metrics_to_evaluate: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> Union[EvaluationResult, Dict[str, Any]]:
        """Evaluate content with progress tracking.
        
        Args:
            content: Content to evaluate
            guidelines: Guidelines for evaluation
            metrics_to_evaluate: Optional list of specific metrics to evaluate
            request_id: Optional request ID for progress tracking
            
        Returns:
            Evaluation result or error response
        """
        self.logger.info(f"Evaluating content (request_id: {request_id}, metrics: {metrics_to_evaluate or 'all'})")
        
        try:
            # Create a patched version of the coordinator's evaluate_content method
            # that tracks progress
            original_method = self.coordinator.evaluate_content
            
            # Determine which metrics will be evaluated
            metrics = guidelines.to_metrics_list()
            if metrics_to_evaluate:
                metrics = [m for m in metrics if m.name in metrics_to_evaluate]
            
            total_metrics = len(metrics)
            completed_metrics = 0
            
            # Create a wrapper for the _evaluate_metric_with_semaphore method
            original_evaluate_metric = self.coordinator._evaluate_metric_with_semaphore
            
            async def wrapped_evaluate_metric(*args, **kwargs):
                result = await original_evaluate_metric(*args, **kwargs)
                
                nonlocal completed_metrics
                completed_metrics += 1
                
                # Call progress callback if registered
                if request_id and request_id in self.progress_callbacks:
                    self.progress_callbacks[request_id](request_id, completed_metrics, total_metrics)
                
                return result
            
            # Temporarily replace the method
            self.coordinator._evaluate_metric_with_semaphore = wrapped_evaluate_metric
            
            try:
                # Call the original method
                result = await original_method(
                    content=content,
                    guidelines=guidelines,
                    metrics_to_evaluate=metrics_to_evaluate
                )
                return result
                
            finally:
                # Restore the original method
                self.coordinator._evaluate_metric_with_semaphore = original_evaluate_metric
                
        except Exception as e:
            self.logger.error(f"Error evaluating content: {e}")
            return {"error": f"Error evaluating content: {str(e)}"}
    
    async def evaluate_metric(
        self, 
        content: str, 
        metric_name: str,
        guidelines: Guidelines,
        request_id: Optional[str] = None
    ) -> Union[MetricResult, Dict[str, Any]]:
        """Evaluate a single metric.
        
        Args:
            content: Content to evaluate
            metric_name: Name of the metric to evaluate
            guidelines: Guidelines for evaluation
            request_id: Optional request ID for progress tracking
            
        Returns:
            Metric result or error response
        """
        self.logger.info(f"Evaluating metric {metric_name} (request_id: {request_id})")
        
        try:
            # Find the requested metric
            metrics = guidelines.to_metrics_list()
            metric = next((m for m in metrics if m.name == metric_name), None)
            
            if not metric:
                self.logger.warning(f"Invalid metric requested: {metric_name}")
                available_metrics = [m.name for m in metrics]
                return {
                    "error": f"Invalid metric: {metric_name}",
                    "available_metrics": available_metrics
                }
            
            # Evaluate content with just this metric
            result = await self.evaluate_content(
                content=content,
                guidelines=guidelines,
                metrics_to_evaluate=[metric_name],
                request_id=request_id
            )
            
            # Check if there was an error
            if isinstance(result, dict) and "error" in result:
                return result
            
            # Extract just the single metric result
            if result.metric_results:
                return result.metric_results[0]
            else:
                return {"error": "Evaluation completed but no results were returned"}
                
        except Exception as e:
            self.logger.error(f"Error evaluating metric: {e}")
            return {"error": f"Error evaluating metric: {str(e)}"}