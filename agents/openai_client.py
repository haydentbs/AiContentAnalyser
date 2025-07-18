"""OpenAI client implementation using the official OpenAI API.

References:
- https://platform.openai.com/docs/api-reference/chat
- https://platform.openai.com/docs/models/gpt-4o-mini
"""

import asyncio
import time
from typing import Optional, Dict, Any, List

try:
    import openai
    from openai import AsyncOpenAI
    from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam
    from openai.types.chat.chat_completion import ChatCompletion, Choice
except ImportError:
    openai = None
    AsyncOpenAI = None

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


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if openai is None:
            raise LLMClientError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        
        if not config.api_key:
            raise LLMClientError(
                "OpenAI API key is required. Set it in config.toml or OPENAI_API_KEY environment variable"
            )
        
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using OpenAI API.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system instructions to guide the model's behavior
            max_tokens: Optional maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            LLMResponse object containing the model's response and metadata
            
        Raises:
            LLMRateLimitError: When API rate limits are exceeded
            LLMConnectionError: When connection to OpenAI API fails
            LLMInvalidResponseError: When the API returns an invalid response
        """
        try:
            # Prepare messages in the format expected by the OpenAI Chat API
            messages: List[ChatCompletionMessageParam] = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request parameters
            request_params = {
                "model": self.config.model_name,  # Using gpt-4o-mini as configured in config.toml
                "messages": messages,
                "temperature": self.config.temperature,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            # Add any additional parameters
            request_params.update(kwargs)
            
            self.logger.debug(f"Making OpenAI API request with model: {self.config.model_name}")
            
            # Call the OpenAI Chat Completions API
            response = await self.client.chat.completions.create(**request_params)
            
            if not response.choices or not response.choices[0].message.content:
                raise LLMInvalidResponseError("Empty response from OpenAI API")
            
            content = response.choices[0].message.content.strip()
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            metadata = {
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
                "created": response.created
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                metadata=metadata
            )
            
        except openai.RateLimitError as e:
            self.logger.warning(f"OpenAI rate limit exceeded: {e}")
            raise LLMRateLimitError(
                f"Rate limit exceeded: {e}",
                troubleshooting="Try again later or reduce the frequency of requests. "
                "Consider using a different model or increasing your OpenAI usage tier."
            ) from e
            
        except openai.APIConnectionError as e:
            self.logger.error(f"OpenAI connection error: {e}")
            raise LLMConnectionError(
                f"Connection error: {e}",
                troubleshooting="Please check your internet connection and ensure "
                "OpenAI services are not experiencing downtime. Visit https://status.openai.com/ "
                "to check the current API status."
            ) from e
            
        except openai.AuthenticationError as e:
            self.logger.error(f"OpenAI authentication error: {e}")
            raise LLMConnectionError(
                f"Authentication error: {e}",
                troubleshooting="Please check that your API key is valid and correctly "
                "configured in config.toml or as an environment variable (OPENAI_API_KEY)."
            ) from e
            
        except openai.BadRequestError as e:
            self.logger.error(f"OpenAI bad request: {e}")
            raise LLMInvalidResponseError(
                f"Bad request: {e}",
                troubleshooting="The request parameters may be invalid. Check the model name "
                "and ensure it's available in your OpenAI account."
            ) from e
            
        except Exception as e:
            self.logger.error(f"Unexpected OpenAI error: {e}")
            raise LLMClientError(f"Unexpected error: {e}") from e
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to OpenAI API."""
        start_time = time.time()
        
        try:
            # First check if we can access the models list
            try:
                models = await self.client.models.list()
                available_models = [model.id for model in models.data]
                
                # Check if configured model is available
                model_available = self.config.model_name in available_models
                if not model_available:
                    # For fine-tuned models or models that might not appear in the list
                    self.logger.warning(f"Model '{self.config.model_name}' not found in available models list")
            except Exception as e:
                self.logger.warning(f"Could not retrieve models list: {e}")
                # Continue with the test even if we can't list models
            
            # Use a simple test prompt
            test_prompt = "Hello, this is a connection test. Please respond with 'Connection successful'."
            
            response = await self.generate_response(
                prompt=test_prompt,
                max_tokens=50
            )
            
            response_time = time.time() - start_time
            
            if "connection successful" in response.content.lower():
                return ConnectionTestResult(
                    success=True,
                    message=f"Successfully connected to OpenAI API using model {response.model}",
                    response_time=response_time
                )
            else:
                return ConnectionTestResult(
                    success=True,
                    message=f"Connected to OpenAI API using model {response.model}",
                    response_time=response_time
                )
                
        except LLMConnectionError as e:
            return ConnectionTestResult(
                success=False,
                message="Failed to connect to OpenAI API",
                error=str(e)
            )
        except LLMRateLimitError as e:
            return ConnectionTestResult(
                success=False,
                message="OpenAI API rate limit exceeded during connection test",
                error=str(e)
            )
        except LLMInvalidResponseError as e:
            return ConnectionTestResult(
                success=False,
                message="OpenAI API returned an invalid response",
                error=str(e)
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Unexpected error during OpenAI connection test",
                error=str(e)
            )