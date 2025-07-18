"""MetricEvaluator agent for single metric evaluation.

This module implements the MetricEvaluator agent that evaluates content against a single metric
using structured LLM calls. It generates focused prompts for each metric and parses responses
to extract scores, reasoning, improvement advice, and specific examples.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Tuple, Any

import jinja2
from pydantic import BaseModel, Field

from ..config.models import Metric, MetricResult
from .llm_client import BaseLLMClient, LLMResponse, LLMClientError


# Set up logging
logger = logging.getLogger(__name__)


class EvaluationPromptTemplate(BaseModel):
    """Template for generating evaluation prompts."""
    system_prompt: str
    user_prompt_template: str


# Default prompt templates
DEFAULT_SYSTEM_PROMPT = """You are a Content Evaluation Expert specializing in analyzing written content against specific quality metrics.
Your task is to evaluate ONLY the specific metric described below, providing a fair and objective assessment.

Follow these guidelines:
1. Focus ONLY on the specific metric you are evaluating
2. Provide a score from 1-5 where:
   - 1: Poor (significant issues throughout)
   - 2: Below Average (multiple notable issues)
   - 3: Average (meets basic expectations)
   - 4: Good (exceeds expectations in some areas)
   - 5: Excellent (exceptional quality throughout)
3. Provide detailed reasoning for your score with specific references to the content
4. Identify 2-3 positive examples (quotes or sections that work well)
5. Identify 2-3 improvement examples (quotes or sections that could be improved)
6. Offer specific, actionable advice for improvement

CRITICAL: Your response MUST be ONLY valid JSON in the following exact format. Do not include any text before or after the JSON:

{
  "score": 3,
  "reasoning": "Your detailed explanation here",
  "improvement_advice": "Your specific actionable advice here",
  "positive_examples": ["Quote from content that works well", "Another positive example"],
  "improvement_examples": ["Quote that needs improvement", "Another improvement example"]
}

Return ONLY the JSON object above with your actual values. No additional text, explanation, or formatting.
"""

DEFAULT_USER_PROMPT_TEMPLATE = """# Content to Evaluate

{{ content }}

# Evaluation Metric

Metric: {{ metric.name }}
Description: {{ metric.description }}
Category: {{ metric.category }}

Please evaluate this content ONLY on the "{{ metric.name }}" metric as described above.
Provide your evaluation in the required JSON format with score, reasoning, improvement advice, 
positive examples (quotes that work well), and improvement examples (quotes that need work).
"""


class MetricEvaluator:
    """Agent for evaluating content against a single metric."""
    
    def __init__(
        self, 
        llm_client: BaseLLMClient,
        prompt_template: Optional[EvaluationPromptTemplate] = None
    ):
        """Initialize the MetricEvaluator agent.
        
        Args:
            llm_client: LLM client for making API calls
            prompt_template: Optional custom prompt template
        """
        self.llm = llm_client
        self.prompt_template = prompt_template or EvaluationPromptTemplate(
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            user_prompt_template=DEFAULT_USER_PROMPT_TEMPLATE
        )
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    async def evaluate_metric(self, content: str, metric: Metric) -> MetricResult:
        """Evaluate content against a single metric.
        
        Args:
            content: The content to evaluate
            metric: The metric to evaluate against
            
        Returns:
            MetricResult containing the evaluation results
            
        Raises:
            ValueError: If the content or metric is invalid
            LLMClientError: If there's an error with the LLM service
        """
        if not content.strip():
            raise ValueError("Content cannot be empty")
        
        # Generate focused prompt for this specific metric
        prompt = self._create_focused_prompt(content, metric)
        
        # Make LLM call
        self.logger.info(f"Evaluating metric: {metric.name} in category: {metric.category}")
        
        try:
            # Check if using OpenAI client and structured outputs are available
            use_structured_output = (
                hasattr(self.llm, '__class__') and 
                self.llm.__class__.__name__ == 'OpenAIClient'
            )
            
            if use_structured_output:
                self.logger.debug("Using OpenAI Structured Outputs for guaranteed JSON response")
                # Use simplified system prompt for structured outputs (no JSON formatting instructions needed)
                structured_system_prompt = """You are a Content Evaluation Expert specializing in analyzing written content against specific quality metrics.
Your task is to evaluate ONLY the specific metric described below, providing a fair and objective assessment.

Follow these guidelines:
1. Focus ONLY on the specific metric you are evaluating
2. Provide a score from 1-5 where:
   - 1: Poor (significant issues throughout)
   - 2: Below Average (multiple notable issues)
   - 3: Average (meets basic expectations)
   - 4: Good (exceeds expectations in some areas)
   - 5: Excellent (exceptional quality throughout)
3. Provide detailed reasoning for your score with specific references to the content
4. Identify 2-3 positive examples (quotes or sections that work well)
5. Identify 2-3 improvement examples (quotes or sections that could be improved)
6. Offer specific, actionable advice for improvement"""
                
                response = await self.llm.generate_response_with_retry(
                    prompt=prompt,
                    system_prompt=structured_system_prompt,
                    max_retries=2,
                    use_structured_output=True
                )
            else:
                response = await self.llm.generate_response_with_retry(
                    prompt=prompt,
                    system_prompt=self.prompt_template.system_prompt,
                    max_retries=2
                )
            
            # Parse the response to extract structured data
            result = self._parse_response(response, metric)
            
            self.logger.info(f"Evaluation complete for {metric.name}. Score: {result.score}")
            return result
            
        except LLMClientError as e:
            self.logger.error(f"LLM error during evaluation of {metric.name}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during evaluation of {metric.name}: {e}")
            raise ValueError(f"Failed to evaluate metric {metric.name}: {e}")
    
    def _create_focused_prompt(self, content: str, metric: Metric) -> str:
        """Create a focused prompt for evaluating a specific metric.
        
        Args:
            content: The content to evaluate
            metric: The metric to evaluate against
            
        Returns:
            Formatted prompt string
        """
        template = self.jinja_env.from_string(self.prompt_template.user_prompt_template)
        
        # Truncate content if it's too long (to avoid token limits)
        max_content_length = 8000  # Adjust based on model context window
        truncated_content = content
        if len(content) > max_content_length:
            truncated_content = content[:max_content_length] + "\n\n[Content truncated due to length...]"
        
        # Render the template with the metric and content
        prompt = template.render(
            content=truncated_content,
            metric=metric
        )
        
        return prompt
    
    def _parse_response(self, response: LLMResponse, metric: Metric) -> MetricResult:
        """Parse the LLM response to extract structured evaluation data.
        
        Args:
            response: LLM response containing the evaluation
            metric: The metric that was evaluated
            
        Returns:
            MetricResult containing the parsed evaluation
            
        Raises:
            ValueError: If the response cannot be parsed
        """
        content = response.content.strip()
        manual_parsing_used = False
        
        # Try to extract JSON from the response
        try:
            # First, try to parse the entire response as JSON
            result_data = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON using regex
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if not json_match:
                # Try to find a JSON object with more flexible pattern
                json_match = re.search(r'({[\s\S]*})', content, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group(1) if '```' in json_match.group(0) else json_match.group(0)
                    # Clean up the JSON string - remove any non-JSON text before or after
                    json_str = re.sub(r'^[^{]*', '', json_str)
                    json_str = re.sub(r'[^}]*$', '', json_str)
                    result_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.debug(f"Failed to parse JSON from response: {e}")
                    # Fall back to manual parsing
                    result_data = self._manual_parse_response(content)
                    manual_parsing_used = True
            else:
                # Fall back to manual parsing
                result_data = self._manual_parse_response(content)
                manual_parsing_used = True
        
        # Validate and extract required fields
        try:
            score = int(result_data.get("score", 0))
            if score < 1 or score > 5:
                self.logger.info(f"Invalid score {score}, clamping to range 1-5")
                score = max(1, min(5, score))
            
            reasoning = result_data.get("reasoning", "No reasoning provided")
            improvement_advice = result_data.get("improvement_advice", "No improvement advice provided")
            
            positive_examples = result_data.get("positive_examples", [])
            if not isinstance(positive_examples, list):
                positive_examples = [str(positive_examples)]
            
            improvement_examples = result_data.get("improvement_examples", [])
            if not isinstance(improvement_examples, list):
                improvement_examples = [str(improvement_examples)]
            
            # Use the confidence from manual parsing if available, otherwise calculate it
            if manual_parsing_used and "confidence" in result_data:
                confidence = result_data["confidence"]
            else:
                # Calculate confidence based on response completeness
                confidence = 1.0
                if not reasoning or reasoning == "No reasoning provided":
                    confidence -= 0.3
                if not improvement_advice or improvement_advice == "No improvement advice provided":
                    confidence -= 0.2
                if not positive_examples:
                    confidence -= 0.2
                if not improvement_examples:
                    confidence -= 0.2
                
                confidence = max(0.1, confidence)  # Ensure minimum confidence
            
            return MetricResult(
                metric=metric,
                score=score,
                reasoning=reasoning,
                improvement_advice=improvement_advice,
                positive_examples=positive_examples,
                improvement_examples=improvement_examples,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting fields from response data: {e}")
            raise ValueError(f"Failed to parse evaluation response: {e}")
    
    def _manual_parse_response(self, content: str) -> Dict[str, Any]:
        """Manually parse the response when JSON parsing fails.
        
        Args:
            content: The raw response content
            
        Returns:
            Dictionary with extracted fields
        """
        self.logger.info("Falling back to manual response parsing")
        
        result = {
            "score": 0,
            "reasoning": "",
            "improvement_advice": "",
            "positive_examples": [],
            "improvement_examples": [],
            # Set a lower confidence by default for manual parsing
            "confidence": 0.7
        }
        
        # Extract score (look for digits 1-5 near score indicators)
        score_match = re.search(r'score:?\s*(\d)', content, re.IGNORECASE)
        if score_match:
            try:
                result["score"] = int(score_match.group(1))
            except ValueError:
                pass
        else:
            # Further reduce confidence if we couldn't find a score
            result["confidence"] = 0.5
        
        # Extract reasoning
        reasoning_match = re.search(r'reasoning:?\s*(.*?)(?=improvement|positive|$)', content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()
        else:
            # Further reduce confidence if we couldn't find reasoning
            result["confidence"] -= 0.1
        
        # Extract improvement advice
        advice_match = re.search(r'improvement[_\s]advice:?\s*(.*?)(?=positive|examples|$)', content, re.IGNORECASE | re.DOTALL)
        if advice_match:
            result["improvement_advice"] = advice_match.group(1).strip()
        else:
            # Further reduce confidence if we couldn't find improvement advice
            result["confidence"] -= 0.1
        
        # Extract positive examples
        pos_examples = []
        pos_section_match = re.search(r'positive[_\s]examples:?\s*(.*?)(?=improvement|$)', content, re.IGNORECASE | re.DOTALL)
        if pos_section_match:
            pos_section = pos_section_match.group(1).strip()
            # Look for list items or quoted text
            pos_items = re.findall(r'(?:^|\n)[-*]\s*(.*?)(?=\n[-*]|\n\n|$)', pos_section, re.DOTALL)
            if pos_items:
                pos_examples = [item.strip() for item in pos_items]
            else:
                # Try to find quoted text
                pos_quotes = re.findall(r'"([^"]*)"', pos_section)
                if pos_quotes:
                    pos_examples = pos_quotes
                else:
                    # Just use the whole section
                    pos_examples = [pos_section]
        else:
            # Further reduce confidence if we couldn't find positive examples
            result["confidence"] -= 0.1
        
        result["positive_examples"] = pos_examples
        
        # Extract improvement examples
        imp_examples = []
        imp_section_match = re.search(r'improvement[_\s]examples:?\s*(.*?)(?=\n\n|$)', content, re.IGNORECASE | re.DOTALL)
        if imp_section_match:
            imp_section = imp_section_match.group(1).strip()
            # Look for list items or quoted text
            imp_items = re.findall(r'(?:^|\n)[-*]\s*(.*?)(?=\n[-*]|\n\n|$)', imp_section, re.DOTALL)
            if imp_items:
                imp_examples = [item.strip() for item in imp_items]
            else:
                # Try to find quoted text
                imp_quotes = re.findall(r'"([^"]*)"', imp_section)
                if imp_quotes:
                    imp_examples = imp_quotes
                else:
                    # Just use the whole section
                    imp_examples = [imp_section]
        else:
            # Further reduce confidence if we couldn't find improvement examples
            result["confidence"] -= 0.1
        
        result["improvement_examples"] = imp_examples
        
        # Ensure confidence doesn't go below 0.1
        result["confidence"] = max(0.1, result.get("confidence", 0.1))
        
        return result