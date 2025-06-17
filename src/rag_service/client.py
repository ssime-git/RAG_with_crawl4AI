"""
Client for interacting with the RAG service API.
This provides a clean interface for other components to interact with the RAG service.
"""

import os
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rag_service_client")

class RAGServiceClient:
    """Client for interacting with the RAG service API."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the RAG service client.
        
        Args:
            base_url: Base URL of the RAG service. If not provided, uses the RAG_SERVICE_URL
                     environment variable or defaults to http://localhost:8000.
        """
        self.base_url = base_url or os.environ.get("RAG_SERVICE_URL", "http://localhost:8000")
        self._session = None
        logger.info(f"Initialized RAG service client with base URL: {self.base_url}")
    
    def get_session(self) -> aiohttp.ClientSession:
        """Get a shared aiohttp ClientSession or create a new one if needed."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            logger.info("Created new aiohttp ClientSession for RAG service client")
        return self._session
    
    async def close_session(self) -> None:
        """Close the session if it exists."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("Closed aiohttp ClientSession for RAG service client")
    
    async def health_check(self) -> bool:
        """Check if the RAG service is healthy.
        
        Returns:
            True if the service is healthy, False otherwise.
        """
        try:
            session = self.get_session()
            async with session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"RAG Service is healthy: {data}")
                    return True
                else:
                    logger.warning(f"RAG Service health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Could not connect to RAG Service: {e}")
            return False
    
    async def retrieve(self, query: str, n_results: int = 5, collection_name: str = "docs") -> str:
        """Retrieve context from the RAG service.
        
        Args:
            query: The search query.
            n_results: Number of results to retrieve.
            collection_name: Name of the collection to search.
            
        Returns:
            The retrieved context as a string.
        """
        try:
            session = self.get_session()
            async with session.post(
                f"{self.base_url}/retrieve",
                json={
                    "query": query,
                    "n_results": n_results,
                    "collection_name": collection_name
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["context"]
                else:
                    error_text = await response.text()
                    logger.error(f"RAG Service error: {response.status} - {error_text}")
                    return f"Error retrieving context: {response.status}"
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return f"Error: {str(e)}"
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> str:
        """Generate text using the RAG service.
        
        Args:
            prompt: The prompt to generate text from.
            system_prompt: Optional system prompt to guide the generation.
            temperature: Temperature for text generation.
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            The generated text.
        """
        try:
            session = self.get_session()
            async with session.post(
                f"{self.base_url}/generate",
                json={
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["text"]
                else:
                    error_text = await response.text()
                    logger.error(f"RAG Service error: {response.status} - {error_text}")
                    return f"Error generating text: {response.status}"
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error: {str(e)}"
    
    async def rag_query(
        self, 
        query: str, 
        n_results: int = 5, 
        collection_name: str = "docs", 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> tuple[str, str]:
        """Perform a RAG query - retrieve documents and generate an answer.
        
        Args:
            query: The query to answer.
            n_results: Number of results to retrieve.
            collection_name: Name of the collection to search.
            temperature: Temperature for text generation.
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            A tuple of (answer, context).
        """
        try:
            session = self.get_session()
            async with session.post(
                f"{self.base_url}/rag-query",
                json={
                    "query": query,
                    "n_results": n_results,
                    "collection_name": collection_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["answer"], data["context"]
                else:
                    error_text = await response.text()
                    logger.error(f"RAG Service error: {response.status} - {error_text}")
                    return f"Error performing RAG query: {response.status}", ""
        except Exception as e:
            logger.error(f"Error performing RAG query: {e}")
            return f"Error: {str(e)}", ""
            
    async def insert_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        collection_name: str = "docs",
        db_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert documents into the RAG service.
        
        Args:
            documents: List of document texts to insert.
            metadatas: List of metadata dictionaries for each document.
            ids: List of unique IDs for each document.
            collection_name: Name of the collection to insert into.
            
        Returns:
            Dictionary with success status, message, and count of inserted documents.
        """
        try:
            # Validate input data
            if len(documents) != len(metadatas) or len(documents) != len(ids):
                error_msg = "The number of documents, metadatas, and ids must be the same"
                logger.error(error_msg)
                return {"success": False, "message": error_msg, "count": 0}
                
            session = self.get_session()
            # Create payload and add db_dir if provided
            payload = {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids,
                "collection_name": collection_name
            }
            
            if db_dir:
                payload["db_dir"] = db_dir
                
            async with session.post(
                f"{self.base_url}/insert-documents",
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully inserted {data['count']} documents")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"RAG Service error: {response.status} - {error_text}")
                    return {"success": False, "message": f"Error: {response.status}", "count": 0}
        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            return {"success": False, "message": f"Error: {str(e)}", "count": 0}
