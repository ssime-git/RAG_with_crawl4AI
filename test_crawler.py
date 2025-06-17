#!/usr/bin/env python3
"""
Test script for the web crawler with the updated Playwright configuration.
This script tests the crawler with a simple URL to verify that the browser connection errors are resolved.
"""

import asyncio
import logging
import sys
from src.crawler.web_crawler import crawl_batch, crawl_recursive_internal_links

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("crawler_test")

async def test_crawl_batch(url):
    """Test the crawl_batch function with a single URL."""
    logger.info(f"Testing crawl_batch with URL: {url}")
    try:
        results = await crawl_batch([url], max_concurrent=1)
        logger.info(f"Successfully crawled {len(results)} pages")
        return results
    except Exception as e:
        logger.error(f"Error during crawl_batch: {e}", exc_info=True)
        return None

async def test_crawl_recursive(url):
    """Test the crawl_recursive_internal_links function with a single URL."""
    logger.info(f"Testing crawl_recursive_internal_links with URL: {url}")
    try:
        results = await crawl_recursive_internal_links([url], max_depth=1, max_concurrent=1)
        logger.info(f"Successfully crawled {len(results)} pages recursively")
        return results
    except Exception as e:
        logger.error(f"Error during crawl_recursive_internal_links: {e}", exc_info=True)
        return None

async def main():
    """Run the crawler tests."""
    if len(sys.argv) < 2:
        print("Usage: python test_crawler.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    logger.info(f"Starting crawler tests with URL: {url}")
    
    # Test crawl_batch
    batch_results = await test_crawl_batch(url)
    if batch_results:
        logger.info("crawl_batch test PASSED")
    else:
        logger.error("crawl_batch test FAILED")
    
    # Test crawl_recursive_internal_links
    recursive_results = await test_crawl_recursive(url)
    if recursive_results:
        logger.info("crawl_recursive_internal_links test PASSED")
    else:
        logger.error("crawl_recursive_internal_links test FAILED")

if __name__ == "__main__":
    asyncio.run(main())
