"""Response formatter for MCP server."""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from pydantic import BaseModel

from ..config.models import EvaluationResult, MetricResult


logger = logging.getLogger(__name__)


class FormattingError(Exception):
    """Exception for formatting errors."""
    pass


class ResponseFormat(BaseModel):
    """Format specification for responses."""
    include_metadata: bool = True
    include_examples: bool = True
    include_confidence: bool = False
    format_type: str = "default"  # Options: default, compact, detailed


class ResponseFormatter:
    """Formatter for MCP responses."""
    
    @staticmethod
    def format_evaluation_result(
        result: EvaluationResult, 
        format_options: Optional[ResponseFormat] = None
    ) -> Dict[str, Any]:
        """Format an evaluation result for MCP response.
        
        Args:
            result: Evaluation result to format
            format_options: Optional formatting options
            
        Returns:
            Formatted result dictionary
        """
        if format_options is None:
            format_options = ResponseFormat()
        
        try:
            # Format metric results
            metric_results = []
            for metric_result in result.metric_results:
                metric_results.append(ResponseFormatter.format_metric_result(
                    metric_result, format_options
                ))
            
            # Format category scores
            category_scores = []
            for category, score in result.category_scores.items():
                category_scores.append({
                    "category": category,
                    "score": score
                })
            
            # Create the formatted result
            formatted_result = {
                "overall_score": result.overall_score,
                "category_scores": category_scores,
                "metric_results": metric_results,
            }
            
            # Add metadata if requested
            if format_options.include_metadata:
                formatted_result.update({
                    "timestamp": result.timestamp.isoformat(),
                    "content_hash": result.content_hash
                })
                
                # Include any additional metadata from the result
                if result.metadata:
                    formatted_result["metadata"] = result.metadata
            
            # Format based on format_type
            if format_options.format_type == "compact":
                # Remove detailed information for compact format
                for metric in formatted_result["metric_results"]:
                    if "reasoning" in metric:
                        metric["reasoning"] = ResponseFormatter._truncate_text(metric["reasoning"], 100)
                    if "improvement_advice" in metric:
                        metric["improvement_advice"] = ResponseFormatter._truncate_text(metric["improvement_advice"], 100)
                    if "positive_examples" in metric:
                        metric["positive_examples"] = [ResponseFormatter._truncate_text(ex, 50) for ex in metric["positive_examples"][:1]]
                    if "improvement_examples" in metric:
                        metric["improvement_examples"] = [ResponseFormatter._truncate_text(ex, 50) for ex in metric["improvement_examples"][:1]]
            
            elif format_options.format_type == "detailed":
                # Add additional details for detailed format
                formatted_result["summary"] = ResponseFormatter._generate_summary(result)
                formatted_result["recommendations"] = ResponseFormatter._generate_recommendations(result)
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting evaluation result: {e}")
            raise FormattingError(f"Failed to format evaluation result: {str(e)}")
    
    @staticmethod
    def format_metric_result(
        result: MetricResult, 
        format_options: Optional[ResponseFormat] = None
    ) -> Dict[str, Any]:
        """Format a metric result for MCP response.
        
        Args:
            result: Metric result to format
            format_options: Optional formatting options
            
        Returns:
            Formatted result dictionary
        """
        if format_options is None:
            format_options = ResponseFormat()
            
        formatted_result = {
            "metric": result.metric.name,
            "category": result.metric.category,
            "score": result.score,
            "reasoning": result.reasoning,
            "improvement_advice": result.improvement_advice,
        }
        
        # Include examples if requested
        if format_options.include_examples:
            formatted_result["positive_examples"] = result.positive_examples
            formatted_result["improvement_examples"] = result.improvement_examples
        
        # Include confidence if requested
        if format_options.include_confidence:
            formatted_result["confidence"] = result.confidence
            
        return formatted_result
    
    @staticmethod
    def format_error(error_message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format an error response.
        
        Args:
            error_message: Error message
            details: Optional additional error details
            
        Returns:
            Formatted error dictionary
        """
        error_response = {
            "error": error_message
        }
        
        if details:
            error_response.update(details)
        
        return error_response
    
    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """Truncate text to a maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def _generate_summary(result: EvaluationResult) -> str:
        """Generate a summary of the evaluation result.
        
        Args:
            result: Evaluation result
            
        Returns:
            Summary text
        """
        # Get the highest and lowest scoring categories
        categories = list(result.category_scores.items())
        categories.sort(key=lambda x: x[1], reverse=True)
        
        highest_category = categories[0] if categories else ("None", 0)
        lowest_category = categories[-1] if len(categories) > 1 else highest_category
        
        # Get the highest and lowest scoring metrics
        metrics = [(m.metric.name, m.score) for m in result.metric_results]
        metrics.sort(key=lambda x: x[1], reverse=True)
        
        highest_metric = metrics[0] if metrics else ("None", 0)
        lowest_metric = metrics[-1] if len(metrics) > 1 else highest_metric
        
        # Generate the summary
        summary = (
            f"Overall score: {result.overall_score:.1f}/5.0. "
            f"Strongest in {highest_category[0]} ({highest_category[1]:.1f}/5.0), "
            f"with highest score in {highest_metric[0]} ({highest_metric[1]}/5). "
            f"Areas for improvement include {lowest_category[0]} ({lowest_category[1]:.1f}/5.0), "
            f"particularly in {lowest_metric[0]} ({lowest_metric[1]}/5)."
        )
        
        return summary
    
    @staticmethod
    def _generate_recommendations(result: EvaluationResult) -> List[str]:
        """Generate recommendations based on the evaluation result.
        
        Args:
            result: Evaluation result
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Sort metrics by score (ascending)
        sorted_metrics = sorted(result.metric_results, key=lambda m: m.score)
        
        # Get the lowest scoring metrics (up to 3)
        lowest_metrics = sorted_metrics[:3]
        
        for metric in lowest_metrics:
            # Add a recommendation based on the improvement advice
            recommendations.append(
                f"Improve {metric.metric.name} ({metric.score}/5): {metric.improvement_advice}"
            )
        
        return recommendations