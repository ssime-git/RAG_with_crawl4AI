"""
insert_docs.py
--------------
Command-line utility to crawl any URL using Crawl4AI, detect content type (sitemap, .txt, or regular page),
use the appropriate crawl method, chunk the resulting Markdown into <1000 character blocks by header hierarchy,
and insert all chunks into ChromaDB with metadata.

Usage:
    python insert_docs.py <URL> [--collection COLLECTION] [--db-dir DB_DIR] [--chunk-size CHUNK_SIZE]
                          [--max-depth MAX_DEPTH] [--max-concurrent MAX_CONCURRENT]
                          [--batch-size BATCH_SIZE] [--rag-service-url RAG_SERVICE_URL]

Arguments:
    URL                     URL to crawl (regular, .txt, or sitemap)
    --collection            ChromaDB collection name (default: docs)
    --db-dir                ChromaDB directory path (passed to RAG service)
    --chunk-size            Max chunk size in characters (default: 1000)
    --max-depth             Recursion depth for regular URLs (default: 3)
    --max-concurrent        Max parallel browser sessions (default: 10)
    --batch-size            RAG service insert batch size (default: 100)
    --rag-service-url       RAG service URL (default: http://localhost:8000)
"""
import argparse
import sys
import asyncio
import os
import logging
from typing import List, Dict, Any

# Import from our modular structure
from crawler.web_crawler import (
    is_sitemap, is_txt, smart_chunk_markdown, extract_section_info,
    parse_sitemap, crawl_batch, crawl_markdown_file, crawl_recursive_internal_links
)
from rag_service.client import RAGServiceClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("insert_docs")

async def main():
    parser = argparse.ArgumentParser(description="Insert crawled docs into ChromaDB via RAG service")
    parser.add_argument("url", help="URL to crawl (regular, .txt, or sitemap)")
    parser.add_argument("--collection", default="docs", help="ChromaDB collection name")
    parser.add_argument("--db-dir", default=None, help="ChromaDB directory path (passed to RAG service)")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Max chunk size (chars)")
    parser.add_argument("--max-depth", type=int, default=3, help="Recursion depth for regular URLs")
    parser.add_argument("--max-concurrent", type=int, default=10, help="Max parallel browser sessions")
    parser.add_argument("--batch-size", type=int, default=100, help="RAG service insert batch size")
    parser.add_argument("--rag-service-url", default=os.environ.get("RAG_SERVICE_URL", "http://localhost:8000"), 
                        help="RAG service URL")
    args = parser.parse_args()
    
    # Initialize RAG service client
    rag_client = RAGServiceClient(args.rag_service_url)
    
    # Check if RAG service is healthy
    is_healthy = await rag_client.health_check()
    if not is_healthy:
        logger.error(f"RAG service is not healthy at {args.rag_service_url}")
        sys.exit(1)
    
    logger.info(f"RAG service is healthy at {args.rag_service_url}")

    # Detect URL type
    url = args.url
    if is_txt(url):
        logger.info(f"Detected .txt/markdown file: {url}")
        crawl_results = await crawl_markdown_file(url)
    elif is_sitemap(url):
        logger.info(f"Detected sitemap: {url}")
        sitemap_urls = parse_sitemap(url)
        if not sitemap_urls:
            logger.error("No URLs found in sitemap.")
            sys.exit(1)
        crawl_results = await crawl_batch(sitemap_urls, max_concurrent=args.max_concurrent)
    else:
        logger.info(f"Detected regular URL: {url}")
        crawl_results = await crawl_recursive_internal_links([url], max_depth=args.max_depth, max_concurrent=args.max_concurrent)

    # Chunk and collect metadata
    ids, documents, metadatas = [], [], []
    chunk_idx = 0
    for doc in crawl_results:
        url = doc['url']
        md = doc['markdown']
        chunks = smart_chunk_markdown(md, max_len=args.chunk_size)
        for chunk in chunks:
            ids.append(f"chunk-{chunk_idx}")
            documents.append(chunk)
            meta = extract_section_info(chunk)
            meta["chunk_index"] = chunk_idx
            meta["source"] = url
            metadatas.append(meta)
            chunk_idx += 1

    if not documents:
        logger.error("No documents found to insert.")
        sys.exit(1)

    logger.info(f"Inserting {len(documents)} chunks into collection '{args.collection}'...")
    
    # Process in batches to avoid overwhelming the service
    batch_size = args.batch_size
    total_inserted = 0
    
    for i in range(0, len(documents), batch_size):
        batch_end = min(i + batch_size, len(documents))
        batch_ids = ids[i:batch_end]
        batch_docs = documents[i:batch_end]
        batch_meta = metadatas[i:batch_end]
        
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_docs)} documents")
        
        # Insert documents using the RAG service client
        result = await rag_client.insert_documents(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids,
            collection_name=args.collection,
            db_dir=args.db_dir
        )
        
        if result["success"]:
            total_inserted += result["count"]
            logger.info(f"Batch {i//batch_size + 1} successful: {result['count']} documents inserted")
        else:
            logger.error(f"Batch {i//batch_size + 1} failed: {result['message']}")
    
    # Close the RAG service client session
    await rag_client.close_session()
    
    logger.info(f"Successfully added {total_inserted} chunks to collection '{args.collection}'.")
    
    return total_inserted

if __name__ == "__main__":
    asyncio.run(main())