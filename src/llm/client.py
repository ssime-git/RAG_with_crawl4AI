"""
LiteLLM client module for handling LLM interactions via the LiteLLM REST API service.
"""

import os
import json
import logging
import aiohttp
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the LiteLLM API base URL from environment or use default
LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE", "http://litellm:4000")
DEFAULT_MODEL = os.environ.get("MODEL_NAME", "gemini-2.0-flash")

# Global session for reuse
_session = None

# Create a global session for reuse
_session = None

def get_session():
    """Get a shared aiohttp ClientSession or create a new one if needed."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
        logger.info("Created new aiohttp ClientSession")
    return _session

async def close_session():
    """Close the global session if it exists."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
        logger.info("Closed aiohttp ClientSession")

class LLMClient:
    """
    Client for interacting with LLMs through LiteLLM API.
    """
    
    @staticmethod
    async def initialize():
        """
        Initialize the LLM client asynchronously.
        It checks if the LiteLLM API is accessible and logs the status.
        """
        logger.info(f"LLMClient initialized with API endpoint: {LITELLM_API_BASE}")
        logger.info(f"Using model: {DEFAULT_MODEL}")
        
        # Test connection to LiteLLM API
        try:
            session = get_session()
            async with session.get(f"{LITELLM_API_BASE}/health", timeout=5) as response:
                if response.status == 200:
                    logger.info("LiteLLM API is healthy")
                    return True
                else:
                    logger.warning(f"LiteLLM API health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.warning(f"Could not connect to LiteLLM API: {e}")
            return False
    
    @staticmethod
    async def generate(
        prompt: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using LiteLLM API.
        
        Args:
            prompt: The user prompt
            model: The model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        # Format the model name for LiteLLM API
        if not model.startswith("gemini/") and model.startswith("gemini"):
            model_name = f"gemini/{model}"
        else:
            model_name = model
        
        logger.info(f"Generating completion with model: {model_name}")
        
        try:
            session = get_session()
            try:
                async with session.post(
                    f"{LITELLM_API_BASE}/v1/chat/completions",
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30  # Longer timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"LiteLLM API error: {response.status} - {error_text}")
                        return f"Error: LiteLLM API returned status {response.status}"
            except aiohttp.ClientError as e:
                logger.error(f"HTTP request error: {e}")
                return f"Error: Failed to connect to LiteLLM API: {e}"
        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return f"Error: {str(e)} (Type: {type(e).__name__})"
    
    @staticmethod
    async def chat_completion_stream(
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """Not implemented yet - placeholder for streaming API"""
        # This would be implemented similarly but with streaming support
        raise NotImplementedError("Streaming API not implemented yet")
        
    @staticmethod
    async def cleanup():
        """Clean up resources used by the LLMClient.
        This should be called when the application is shutting down.
        """
        await close_session()

    @staticmethod
    async def chat_completion(
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using LiteLLM API.
        
        Args:
            messages: List of message dictionaries with role and content
            model: The model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LiteLLM API response as a dictionary
        """
        # Format the model name for LiteLLM API
        if not model.startswith("gemini/") and model.startswith("gemini"):
            model_name = f"gemini/{model}"
        else:
            model_name = model
        
        logger.info(f"Generating chat completion with model: {model_name}")
        
        try:
            session = get_session()
            try:
                async with session.post(
                    f"{LITELLM_API_BASE}/v1/chat/completions",
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=30  # Longer timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Successfully received chat completion response")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"LiteLLM API error: {response.status} - {error_text}")
                        return {"error": f"LiteLLM API returned status {response.status}", "details": error_text}
            except aiohttp.ClientError as e:
                logger.error(f"HTTP request error in chat_completion: {e}")
                return {"error": f"Failed to connect to LiteLLM API: {e}"}
        except Exception as e:
            logger.error(f"Error generating chat completion: {e}")
            return {"error": str(e), "type": type(e).__name__}
