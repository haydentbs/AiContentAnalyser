"""LM Studio client implementation."""

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
from config.models import LLMConfig


class LMStudioClient(BaseLLMClient):
    """LM Studio API client implementation (OpenAI-compatible)."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if aiohttp is None:
            raise LLMClientError(
                "aiohttp package not installed. Install with: pip install aiohttp"
            )
        
        if not config.base_url:
            raise LLMClientError(
                "LM Studio base URL is required. Set it in config.toml or LMSTUDIO_BASE_URL environment variable"
            )
        
        self.base_url = config.base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using LM Studio API (OpenAI-compatible)."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Prepare the request payload (OpenAI-compatible format)
            payload = {
                "model": self.config.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "stream": False
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            # Add any additional parameters
            payload.update(kwargs)
            
            self.logger.debug(f"Making LM Studio API request with model: {self.config.model_name}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 404:
                        raise LLMConnectionError(
                            f"LM Studio endpoint not found",
                            troubleshooting=f"Make sure LM Studio is running and serving on {self.base_url}. "
                            f"Verify that you've started the local server in LM Studio by clicking 'Start Server' "
                            f"in the Inference Server tab."
                        )
                    
                    if response.status == 429:
                        raise LLMRateLimitError(
                            "LM Studio server is busy",
                            troubleshooting="The server may be processing other requests or under heavy load. "
                            "Consider reducing the complexity of your prompts or using a smaller model."
                        )
                    
                    if response.status == 500:
                        error_text = await response.text()
                        raise LLMConnectionError(
                            f"LM Studio server error (500): {error_text}",
                            troubleshooting="This may indicate an issue with the model or insufficient resources. "
                            "Try restarting LM Studio or selecting a different model."
                        )
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise LLMConnectionError(
                            f"LM Studio API error {response.status}: {error_text}",
                            troubleshooting="Check that LM Studio is configured correctly and the OpenAI-compatible API is enabled. "
                            "Verify that you're using a compatible version of LM Studio."
                        )
                    
                    response_data = await response.json()
                    
                    if "choices" not in response_data or not response_data["choices"]:
                        raise LLMInvalidResponseError("Invalid response format from LM Studio API")
                    
                    choice = response_data["choices"][0]
                    if "message" not in choice or "content" not in choice["message"]:
                        raise LLMInvalidResponseError("Invalid message format from LM Studio API")
                    
                    content = choice["message"]["content"].strip()
                    
                    if not content:
                        raise LLMInvalidResponseError("Empty response from LM Studio API")
                    
                    # Extract usage information if available
                    usage = None
                    if "usage" in response_data:
                        usage_data = response_data["usage"]
                        usage = {
                            "prompt_tokens": usage_data.get("prompt_tokens", 0),
                            "completion_tokens": usage_data.get("completion_tokens", 0),
                            "total_tokens": usage_data.get("total_tokens", 0)
                        }
                    
                    metadata = {
                        "model": response_data.get("model", self.config.model_name),
                        "created": response_data.get("created"),
                        "finish_reason": choice.get("finish_reason"),
                        "object": response_data.get("object")
                    }
                    
                    return LLMResponse(
                        content=content,
                        model=response_data.get("model", self.config.model_name),
                        usage=usage,
                        metadata=metadata
                    )
                    
        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"LM Studio connection error: {e}")
            raise LLMConnectionError(
                f"Cannot connect to LM Studio server at {self.base_url}",
                troubleshooting=f"Make sure LM Studio is running and the server is started. "
                f"In LM Studio, go to the 'Inference Server' tab and click 'Start Server'. "
                f"Error details: {e}"
            ) from e
            
        except aiohttp.ClientTimeout as e:
            self.logger.error(f"LM Studio timeout error: {e}")
            raise LLMConnectionError(
                f"Request to LM Studio timed out",
                troubleshooting=f"The model may be too large or your system resources insufficient. "
                f"Try a smaller model or adjust the parameters in LM Studio. Error details: {e}"
            ) from e
            
        except json.JSONDecodeError as e:
            self.logger.error(f"LM Studio JSON decode error: {e}")
            raise LLMInvalidResponseError(
                f"Invalid JSON response from LM Studio",
                troubleshooting=f"The LM Studio API may have returned malformed data. "
                f"Check that you're using a compatible version of LM Studio. Error details: {e}"
            ) from e
            
        except Exception as e:
            self.logger.error(f"Unexpected LM Studio error: {e}")
            raise LLMClientError(
                f"Unexpected error when calling LM Studio API",
                troubleshooting=f"This is an unhandled error that may require investigation. "
                f"Check LM Studio logs for more details. Error: {e}"
            ) from e
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to LM Studio API."""
        start_time = time.time()
        
        try:
            # First, check if LM Studio server is running by checking models endpoint
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                try:
                    async with session.get(f"{self.base_url}/v1/models") as response:
                        if response.status != 200:
                            return ConnectionTestResult(
                                success=False,
                                message=f"LM Studio server responded with status {response.status}",
                                error=f"HTTP {response.status}. Make sure LM Studio is running and the server is started in the Inference Server tab."
                            )
                        
                        # Check if any models are available
                        models_data = await response.json()
                        available_models = [model["id"] for model in models_data.get("data", [])]
                        
                        if not available_models:
                            return ConnectionTestResult(
                                success=False,
                                message="No models loaded in LM Studio",
                                error="Load a model in LM Studio before testing connection. Go to the Models tab and load a model."
                            )
                        
                        # Log available models for debugging
                        self.logger.debug(f"Available models in LM Studio: {', '.join(available_models)}")
                        
                        # Note: LM Studio doesn't require the model name to match exactly what's in the config
                        # It will use whatever model is currently loaded
                except aiohttp.ClientConnectorError:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Could not connect to LM Studio server at {self.base_url}",
                        error="Make sure LM Studio is running and the server is started in the Inference Server tab."
                    )
            
            # Test actual generation
            test_prompt = "Hello, this is a connection test. Please respond with 'Connection successful'."
            
            response = await self.generate_response(
                prompt=test_prompt,
                max_tokens=50
            )
            
            response_time = time.time() - start_time
            
            # Get model information from response
            model_name = response.model or self.config.model_name
            
            return ConnectionTestResult(
                success=True,
                message=f"Successfully connected to LM Studio using model {model_name}",
                response_time=response_time
            )
                
        except LLMConnectionError as e:
            return ConnectionTestResult(
                success=False,
                message="Failed to connect to LM Studio server",
                error=str(e)
            )
        except LLMRateLimitError as e:
            return ConnectionTestResult(
                success=False,
                message="LM Studio server is busy",
                error=str(e)
            )
        except LLMInvalidResponseError as e:
            return ConnectionTestResult(
                success=False,
                message="LM Studio returned an invalid response",
                error=str(e)
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Unexpected error during LM Studio connection test",
                error=f"{str(e)}. Check if LM Studio is running properly."
            )