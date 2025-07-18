"""Ollama client implementation."""

import asyncio
import time
import json
from typing import Optional, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

from .llm_client import (
    BaseLLMClient, 
    LLMResponse, 
    ConnectionTestResult,
    LLMClientError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError
)
from ..config.models import LLMConfig


class OllamaClient(BaseLLMClient):
    """Ollama API client implementation."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if aiohttp is None:
            raise LLMClientError(
                "aiohttp package not installed. Install with: pip install aiohttp"
            )
        
        if not config.base_url:
            raise LLMClientError(
                "Ollama base URL is required. Set it in config.toml or OLLAMA_BASE_URL environment variable"
            )
        
        self.base_url = config.base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        use_structured_output: bool = False,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using Ollama API."""
        if use_structured_output:
            self.logger.debug("Structured outputs not supported by Ollama, using regular JSON mode")
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            # Add any additional options
            if kwargs:
                payload["options"].update(kwargs)
            
            self.logger.debug(f"Making Ollama API request with model: {self.config.model_name}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 404:
                        raise LLMConnectionError(
                            f"Model '{self.config.model_name}' not found",
                            troubleshooting=f"Make sure it's installed with: ollama pull {self.config.model_name}. "
                            f"Check available models with: ollama list"
                        )
                    
                    if response.status == 429:
                        raise LLMRateLimitError(
                            "Ollama server is busy",
                            troubleshooting="The server may be processing other requests or under heavy load. "
                            "Consider adjusting the model parameters for faster responses or try again later."
                        )
                    
                    if response.status == 500:
                        error_text = await response.text()
                        raise LLMConnectionError(
                            f"Ollama server error (500): {error_text}",
                            troubleshooting="This may indicate an issue with the Ollama server or insufficient resources. "
                            "Try restarting the Ollama service or using a smaller model."
                        )
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise LLMConnectionError(
                            f"Ollama API error {response.status}: {error_text}",
                            troubleshooting="Check that the Ollama server is running correctly and the API hasn't changed. "
                            "Verify that you're using a compatible version of Ollama."
                        )
                    
                    response_data = await response.json()
                    
                    if "response" not in response_data:
                        raise LLMInvalidResponseError("Invalid response format from Ollama API")
                    
                    content = response_data["response"].strip()
                    
                    if not content:
                        raise LLMInvalidResponseError("Empty response from Ollama API")
                    
                    # Extract usage information if available
                    usage = None
                    if "eval_count" in response_data and "prompt_eval_count" in response_data:
                        usage = {
                            "prompt_tokens": response_data.get("prompt_eval_count", 0),
                            "completion_tokens": response_data.get("eval_count", 0),
                            "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)
                        }
                    
                    metadata = {
                        "model": response_data.get("model", self.config.model_name),
                        "created_at": response_data.get("created_at"),
                        "done": response_data.get("done", True),
                        "total_duration": response_data.get("total_duration"),
                        "load_duration": response_data.get("load_duration"),
                        "prompt_eval_duration": response_data.get("prompt_eval_duration"),
                        "eval_duration": response_data.get("eval_duration")
                    }
                    
                    return LLMResponse(
                        content=content,
                        model=response_data.get("model", self.config.model_name),
                        usage=usage,
                        metadata=metadata
                    )
                    
        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"Ollama connection error: {e}")
            raise LLMConnectionError(
                f"Cannot connect to Ollama server at {self.base_url}",
                troubleshooting=f"Make sure Ollama is running and accessible. "
                f"Try running 'ollama list' in your terminal to verify the service is active. "
                f"Error details: {e}"
            ) from e
            
        except aiohttp.ClientTimeout as e:
            self.logger.error(f"Ollama timeout error: {e}")
            raise LLMConnectionError(
                f"Request to Ollama timed out",
                troubleshooting=f"The model may be too large or your system resources insufficient. "
                f"Try a smaller model or increase the timeout. Error details: {e}"
            ) from e
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Ollama JSON decode error: {e}")
            raise LLMInvalidResponseError(
                f"Invalid JSON response from Ollama",
                troubleshooting=f"The Ollama API may have changed or returned malformed data. "
                f"Check for Ollama updates or try a different model. Error details: {e}"
            ) from e
            
        except Exception as e:
            self.logger.error(f"Unexpected Ollama error: {e}")
            raise LLMClientError(
                f"Unexpected error when calling Ollama API",
                troubleshooting=f"This is an unhandled error that may require investigation. "
                f"Check Ollama logs for more details. Error: {e}"
            ) from e
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Ollama API."""
        start_time = time.time()
        
        try:
            # First, check if Ollama server is running
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                try:
                    async with session.get(f"{self.base_url}/api/tags") as response:
                        if response.status != 200:
                            return ConnectionTestResult(
                                success=False,
                                message=f"Ollama server responded with status {response.status}",
                                error=f"HTTP {response.status}. Make sure Ollama is running with 'ollama serve' command."
                            )
                        
                        # Check if the model is available
                        models_data = await response.json()
                        available_models = [model["name"] for model in models_data.get("models", [])]
                        
                        if not available_models:
                            return ConnectionTestResult(
                                success=False,
                                message="No models found in Ollama",
                                error="Pull a model with 'ollama pull <model_name>' before using"
                            )
                        
                        if self.config.model_name not in available_models:
                            return ConnectionTestResult(
                                success=False,
                                message=f"Model '{self.config.model_name}' not found in Ollama",
                                error=f"Available models: {', '.join(available_models)}. Pull the model with 'ollama pull {self.config.model_name}'"
                            )
                except aiohttp.ClientConnectorError:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Could not connect to Ollama server at {self.base_url}",
                        error="Make sure Ollama is running with 'ollama serve' command"
                    )
            
            # Test actual generation
            test_prompt = "Hello, this is a connection test. Please respond with 'Connection successful'."
            
            response = await self.generate_response(
                prompt=test_prompt,
                max_tokens=50
            )
            
            response_time = time.time() - start_time
            
            # Get model information from response if available
            model_name = response.model or self.config.model_name
            
            return ConnectionTestResult(
                success=True,
                message=f"Successfully connected to Ollama using model {model_name}",
                response_time=response_time
            )
                
        except LLMConnectionError as e:
            return ConnectionTestResult(
                success=False,
                message="Failed to connect to Ollama server",
                error=str(e)
            )
        except LLMRateLimitError as e:
            return ConnectionTestResult(
                success=False,
                message="Ollama server is busy",
                error=str(e)
            )
        except LLMInvalidResponseError as e:
            return ConnectionTestResult(
                success=False,
                message="Ollama returned an invalid response",
                error=str(e)
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Unexpected error during Ollama connection test",
                error=f"{str(e)}. Check if Ollama is installed and running."
            )