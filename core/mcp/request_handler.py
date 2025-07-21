"""Request handler for MCP server."""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Tuple

from pydantic import BaseModel, Field, validator

from ..agents.coordinator_agent import CoordinatorAgent
from ..config.models import Metric, EvaluationResult
from ..storage.guidelines import Guidelines


logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP request model."""
    tool: str
    parameters: Dict[str, Any]


class MCPResponse(BaseModel):
    """MCP response model."""
    result: Dict[str, Any]
    error: Optional[str] = None


class EvaluateContentRequest(BaseModel):
    """Request model for content evaluation."""
    content: str = Field(..., description="Content to evaluate")
    metrics: Optional[List[str]] = Field(None, description="Specific metrics to evaluate (optional)")
    
    @validator('content')
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class EvaluateMetricRequest(BaseModel):
    """Request model for single metric evaluation."""
    content: str = Field(..., description="Content to evaluate")
    metric: str = Field(..., description="Name of the metric to evaluate")
    
    @validator('content')
    def content_not_empty(cls, v):
        """Validate that content is not empty."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class RequestValidationError(Exception):
    """Exception for request validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class RequestHandler:
    """Handler for MCP requests."""
    
    def __init__(
        self, 
        coordinator: Union['CoordinatorAgent', 'CoordinatorAdapter'], 
        guidelines: Guidelines,
        cache_size: int = 100,
        request_timeout: float = 300.0  # 5 minutes
    ):
        """Initialize the request handler.
        
        Args:
            coordinator: Coordinator agent or adapter for content evaluation
            guidelines: Guidelines for evaluation
            cache_size: Maximum number of results to cache
            request_timeout: Timeout for requests in seconds
        """
        self.coordinator = coordinator
        self.guidelines = guidelines
        self.cache_size = cache_size
        self.request_timeout = request_timeout
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Cache for evaluation results
        self.result_cache: Dict[str, Dict[str, Any]] = {}
        
        # Active requests with progress tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
    
    def _generate_request_id(self, content: str, metrics: Optional[List[str]] = None) -> str:
        """Generate a unique ID for a request based on content and metrics.
        
        Args:
            content: Content to evaluate
            metrics: Optional list of specific metrics to evaluate
            
        Returns:
            Unique request ID
        """
        import hashlib
        
        # Create a string representation of the request
        metrics_str = ",".join(sorted(metrics)) if metrics else "all"
        request_str = f"{content}:{metrics_str}"
        
        # Generate a hash
        return hashlib.md5(request_str.encode()).hexdigest()
    
    def _check_cache(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Check if a result is in the cache.
        
        Args:
            request_id: Request ID to check
            
        Returns:
            Cached result or None if not found
        """
        if request_id in self.result_cache:
            self.logger.info(f"Cache hit for request {request_id}")
            return self.result_cache[request_id]
        return None
    
    def _add_to_cache(self, request_id: str, result: Dict[str, Any]) -> None:
        """Add a result to the cache.
        
        Args:
            request_id: Request ID
            result: Result to cache
        """
        # If cache is full, remove the oldest entry
        if len(self.result_cache) >= self.cache_size:
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]
        
        self.result_cache[request_id] = result
        self.logger.info(f"Added result to cache for request {request_id}")
    
    def _track_request_progress(self, request_id: str, total_metrics: int) -> None:
        """Start tracking progress for a request.
        
        Args:
            request_id: Request ID
            total_metrics: Total number of metrics to evaluate
        """
        self.active_requests[request_id] = {
            "start_time": time.time(),
            "total_metrics": total_metrics,
            "completed_metrics": 0,
            "status": "in_progress"
        }
    
    def _update_request_progress(self, request_id: str, completed_metrics: int) -> None:
        """Update progress for a request.
        
        Args:
            request_id: Request ID
            completed_metrics: Number of completed metrics
        """
        if request_id in self.active_requests:
            self.active_requests[request_id]["completed_metrics"] = completed_metrics
    
    def _complete_request(self, request_id: str, status: str = "completed") -> None:
        """Mark a request as completed.
        
        Args:
            request_id: Request ID
            status: Final status (completed or error)
        """
        if request_id in self.active_requests:
            self.active_requests[request_id]["status"] = status
            self.active_requests[request_id]["end_time"] = time.time()
    
    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a request.
        
        Args:
            request_id: Request ID
            
        Returns:
            Request status information
        """
        if request_id not in self.active_requests:
            return {"error": f"Request {request_id} not found"}
        
        request = self.active_requests[request_id]
        
        # Calculate progress percentage
        progress = 0
        if request["total_metrics"] > 0:
            progress = (request["completed_metrics"] / request["total_metrics"]) * 100
        
        # Calculate elapsed time
        elapsed = time.time() - request["start_time"]
        
        return {
            "request_id": request_id,
            "status": request["status"],
            "progress": progress,
            "elapsed_time": elapsed,
            "total_metrics": request["total_metrics"],
            "completed_metrics": request["completed_metrics"]
        }
    
    async def handle_evaluate_content(
        self, 
        content: str, 
        metrics: Optional[List[str]] = None
    ) -> Union[EvaluationResult, Dict[str, Any]]:
        """Handle a request to evaluate content.
        
        Args:
            content: Content to evaluate
            metrics: Optional list of specific metrics to evaluate
            
        Returns:
            Evaluation result or error response
        """
        self.logger.info(f"Handling content evaluation request (metrics: {metrics or 'all'})")
        
        if not content.strip():
            self.logger.warning("Empty content received")
            return {"error": "Content cannot be empty"}
        
        # Generate a request ID
        request_id = self._generate_request_id(content, metrics)
        
        # Check cache first
        cached_result = self._check_cache(request_id)
        if cached_result:
            return cached_result
        
        try:
            # Validate metrics if provided
            if metrics:
                available_metrics = {m.name for m in self.guidelines.to_metrics_list()}
                invalid_metrics = [m for m in metrics if m not in available_metrics]
                if invalid_metrics:
                    self.logger.warning(f"Invalid metrics requested: {invalid_metrics}")
                    return {
                        "error": f"Invalid metrics: {', '.join(invalid_metrics)}",
                        "available_metrics": list(available_metrics)
                    }
            
            # Start tracking progress
            total_metrics = len(metrics) if metrics else len(self.guidelines.to_metrics_list())
            self._track_request_progress(request_id, total_metrics)
            
            # Create a task with timeout
            try:
                # Evaluate content
                result = await asyncio.wait_for(
                    self.coordinator.evaluate_content(
                        content=content,
                        guidelines=self.guidelines,
                        metrics_to_evaluate=metrics
                    ),
                    timeout=self.request_timeout
                )
                
                # Mark request as completed
                self._complete_request(request_id)
                
                # Cache the result
                if hasattr(result, "model_dump"):
                    self._add_to_cache(request_id, result.model_dump())
                
                return result
                
            except asyncio.TimeoutError:
                self.logger.error(f"Request {request_id} timed out after {self.request_timeout} seconds")
                self._complete_request(request_id, "timeout")
                return {"error": f"Request timed out after {self.request_timeout} seconds"}
            
        except Exception as e:
            self.logger.error(f"Error evaluating content: {e}")
            if request_id in self.active_requests:
                self._complete_request(request_id, "error")
            return {"error": f"Error evaluating content: {str(e)}"}
    
    async def handle_get_guidelines(self) -> Dict[str, Any]:
        """Handle a request to get the current guidelines.
        
        Returns:
            Guidelines information
        """
        self.logger.info("Handling get guidelines request")
        
        try:
            metrics = self.guidelines.to_metrics_list()
            
            # Format metrics by category
            metrics_by_category = {}
            for metric in metrics:
                if metric.category not in metrics_by_category:
                    metrics_by_category[metric.category] = []
                
                metrics_by_category[metric.category].append({
                    "name": metric.name,
                    "description": metric.description,
                    "weight": metric.weight
                })
            
            # Get category information
            categories = {}
            for category_name, category in self.guidelines.categories.items():
                categories[category_name] = {
                    "description": category.description,
                    "weight": category.weight
                }
            
            return {
                "categories": categories,
                "metrics_by_category": metrics_by_category
            }
            
        except Exception as e:
            self.logger.error(f"Error getting guidelines: {e}")
            return {"error": f"Error getting guidelines: {str(e)}"}
    
    async def handle_request_status(self, request_id: str) -> Dict[str, Any]:
        """Handle a request to get the status of an evaluation.
        
        Args:
            request_id: ID of the request to check
            
        Returns:
            Request status information
        """
        self.logger.info(f"Handling request status check for {request_id}")
        
        return await self.get_request_status(request_id)
    
    async def handle_evaluate_metric(
        self, 
        content: str, 
        metric_name: str
    ) -> Dict[str, Any]:
        """Handle a request to evaluate a single metric.
        
        Args:
            content: Content to evaluate
            metric_name: Name of the metric to evaluate
            
        Returns:
            Metric evaluation result or error response
        """
        self.logger.info(f"Handling single metric evaluation request: {metric_name}")
        
        if not content.strip():
            self.logger.warning("Empty content received")
            return {"error": "Content cannot be empty"}
        
        # Generate a request ID for this specific metric evaluation
        request_id = self._generate_request_id(content, [metric_name])
        
        # Check cache first
        cached_result = self._check_cache(request_id)
        if cached_result:
            return cached_result
        
        try:
            # Find the requested metric
            metrics = self.guidelines.to_metrics_list()
            metric = next((m for m in metrics if m.name == metric_name), None)
            
            if not metric:
                self.logger.warning(f"Invalid metric requested: {metric_name}")
                available_metrics = [m.name for m in metrics]
                return {
                    "error": f"Invalid metric: {metric_name}",
                    "available_metrics": available_metrics
                }
            
            # Start tracking progress
            self._track_request_progress(request_id, 1)
            
            try:
                # Evaluate content with just this metric
                result = await asyncio.wait_for(
                    self.coordinator.evaluate_content(
                        content=content,
                        guidelines=self.guidelines,
                        metrics_to_evaluate=[metric_name]
                    ),
                    timeout=self.request_timeout
                )
                
                # Mark request as completed
                self._complete_request(request_id)
                
                # Extract just the single metric result
                if result.metric_results:
                    metric_result = result.metric_results[0]
                    response = {
                        "metric": metric_result.metric.name,
                        "category": metric_result.metric.category,
                        "score": metric_result.score,
                        "reasoning": metric_result.reasoning,
                        "improvement_advice": metric_result.improvement_advice,
                        "positive_examples": metric_result.positive_examples,
                        "improvement_examples": metric_result.improvement_examples
                    }
                    
                    # Cache the result
                    self._add_to_cache(request_id, response)
                    
                    return response
                else:
                    self._complete_request(request_id, "error")
                    return {"error": "Evaluation completed but no results were returned"}
                    
            except asyncio.TimeoutError:
                self.logger.error(f"Request {request_id} timed out after {self.request_timeout} seconds")
                self._complete_request(request_id, "timeout")
                return {"error": f"Request timed out after {self.request_timeout} seconds"}
            
        except Exception as e:
            self.logger.error(f"Error evaluating metric: {e}")
            if request_id in self.active_requests:
                self._complete_request(request_id, "error")
            return {"error": f"Error evaluating metric: {str(e)}"}