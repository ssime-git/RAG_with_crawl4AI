"""
FastAPI service for RAG (Retrieval-Augmented Generation) operations.
This service handles all ChromaDB interactions and provides endpoints for document retrieval.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from dotenv import load_dotenv

# Import ChromaDB client functions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.chroma_client import (
    get_chroma_client,
    get_or_create_collection,
    query_collection,
    format_results_as_context,
    add_documents_to_collection
)
from llm.client import LLMClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rag_service")

# Load environment variables
load_dotenv()

# Check for Google API key
if not os.getenv("GOOGLE_API_KEY"):
    logger.error("Error: GOOGLE_API_KEY environment variable not set.")
    logger.error("Please create a .env file with your Google API key or set it in your environment.")
    sys.exit(1)

# Initialize LiteLLM client - will be done in startup event handler
# to avoid 'event loop already running' error

# Create FastAPI app
app = FastAPI(
    title="RAG Service API",
    description="API for Retrieval-Augmented Generation operations using ChromaDB",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize LLMClient properly in async context
        await LLMClient.initialize()
        logger.info("LLMClient initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing LLMClient: {str(e)}")
        # Don't exit - allow service to start even if LLM client fails
        # as health endpoint should still work

# Define request and response models
class RetrieveRequest(BaseModel):
    query: str
    n_results: int = 5
    collection_name: str = "docs"
    
class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
class RAGQueryRequest(BaseModel):
    query: str
    n_results: int = 5
    collection_name: str = "docs"
    temperature: float = 0.7
    max_tokens: int = 1000
    
class RetrieveResponse(BaseModel):
    context: str
    
class GenerateResponse(BaseModel):
    text: str
    
class RAGQueryResponse(BaseModel):
    answer: str
    context: str
    
class DocumentInsertRequest(BaseModel):
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    ids: List[str]
    collection_name: str = "docs"
    
class DocumentInsertResponse(BaseModel):
    success: bool
    message: str
    count: int

# Global variables
DB_DIR = os.environ.get("DB_DIR", "./chroma_db")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rag-service"}

# Retrieve endpoint
@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest):
    """Retrieve relevant documents from ChromaDB based on a search query"""
    try:
        # Get ChromaDB client and collection
        client = get_chroma_client(DB_DIR)
        collection = get_or_create_collection(
            client,
            request.collection_name,
            embedding_model_name=EMBEDDING_MODEL
        )
        
        # Query the collection
        query_results = query_collection(
            collection,
            request.query,
            n_results=request.n_results
        )
        
        # Format the results as context
        context = format_results_as_context(query_results)
        
        return RetrieveResponse(context=context)
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

# Generate endpoint
@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text using LiteLLM with Gemini 2 Flash"""
    try:
        text = await LLMClient.generate(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return GenerateResponse(text=text)
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")

# RAG query endpoint (combines retrieve and generate)
@app.post("/rag-query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """Perform a RAG query - retrieve documents and generate an answer"""
    try:
        # First retrieve relevant documents
        client = get_chroma_client(DB_DIR)
        collection = get_or_create_collection(
            client,
            request.collection_name,
            embedding_model_name=EMBEDDING_MODEL
        )
        
        # Query the collection
        query_results = query_collection(
            collection,
            request.query,
            n_results=request.n_results
        )
        
        # Format the results as context
        context = format_results_as_context(query_results)
        
        # Generate an answer using the context
        system_prompt = (
            "You are a helpful assistant that answers questions based on the provided documentation. "
            "Use only the context provided to answer the question. "
            "If the context doesn't contain the answer, clearly state that the information isn't available "
            "in the current documentation."
        )
        
        prompt = f"Context:\n{context}\n\nQuestion: {request.query}\n\nAnswer:"
        
        answer = await LLMClient.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return RAGQueryResponse(answer=answer, context=context)
    except Exception as e:
        logger.error(f"Error performing RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing RAG query: {str(e)}")

# Document insertion endpoint
@app.post("/insert-documents", response_model=DocumentInsertResponse)
async def insert_documents(request: DocumentInsertRequest):
    """Insert documents into ChromaDB"""
    try:
        # Validate input data
        if len(request.documents) != len(request.metadatas) or len(request.documents) != len(request.ids):
            raise HTTPException(
                status_code=400, 
                detail="The number of documents, metadatas, and ids must be the same"
            )
            
        # Get ChromaDB client and collection
        client = get_chroma_client(DB_DIR)
        collection = get_or_create_collection(
            client,
            request.collection_name,
            embedding_model_name=EMBEDDING_MODEL
        )
        
        # Add documents to the collection
        add_documents_to_collection(
            collection=collection,
            documents=request.documents,
            metadatas=request.metadatas,
            ids=request.ids
        )
        
        return DocumentInsertResponse(
            success=True,
            message=f"Successfully inserted {len(request.documents)} documents",
            count=len(request.documents)
        )
    except Exception as e:
        logger.error(f"Error inserting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error inserting documents: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
