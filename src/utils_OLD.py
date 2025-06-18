"""Utility functions for text processing and ChromaDB operations."""

# Import from our modular structure
from db.chroma_client import (
    get_chroma_client,
    get_or_create_collection,
    add_documents_to_collection,
    query_collection,
    format_results_as_context
)