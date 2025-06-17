"""
Web crawler implementation using Crawl4AI.
"""

import asyncio
from typing import List, Dict, Any
import re
from urllib.parse import urlparse, urldefrag
from xml.etree import ElementTree
import requests

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, MemoryAdaptiveDispatcher


def is_sitemap(url: str) -> bool:
    """
    Check if a URL points to a sitemap.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a sitemap, False otherwise
    """
    return url.endswith('sitemap.xml') or 'sitemap' in urlparse(url).path


def is_txt(url: str) -> bool:
    """
    Check if a URL points to a text file.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a text file, False otherwise
    """
    return url.endswith('.txt')


def smart_chunk_markdown(markdown: str, max_len: int = 1000) -> List[str]:
    """
    Hierarchically splits markdown by #, ##, ### headers, then by characters, to ensure all chunks < max_len.
    
    Args:
        markdown: Markdown text to chunk
        max_len: Maximum length of each chunk
        
    Returns:
        List of markdown chunks
    """
    def split_by_header(md, header_pattern):
        indices = [m.start() for m in re.finditer(header_pattern, md, re.MULTILINE)]
        indices.append(len(md))
        return [md[indices[i]:indices[i+1]].strip() for i in range(len(indices)-1) if md[indices[i]:indices[i+1]].strip()]

    chunks = []

    for h1 in split_by_header(markdown, r'^# .+$'):
        if len(h1) > max_len:
            for h2 in split_by_header(h1, r'^## .+$'):
                if len(h2) > max_len:
                    for h3 in split_by_header(h2, r'^### .+$'):
                        if len(h3) > max_len:
                            for i in range(0, len(h3), max_len):
                                chunks.append(h3[i:i+max_len].strip())
                        else:
                            chunks.append(h3)
                else:
                    chunks.append(h2)
        else:
            chunks.append(h1)

    final_chunks = []

    for c in chunks:
        if len(c) > max_len:
            final_chunks.extend([c[i:i+max_len].strip() for i in range(0, len(c), max_len)])
        else:
            final_chunks.append(c)

    return [c for c in final_chunks if c]


def extract_section_info(chunk: str) -> Dict[str, Any]:
    """
    Extracts headers and stats from a chunk.
    
    Args:
        chunk: Markdown chunk
        
    Returns:
        Dictionary with header information and statistics
    """
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }


def parse_sitemap(sitemap_url: str) -> List[str]:
    """
    Parse a sitemap XML file and extract URLs.
    
    Args:
        sitemap_url: URL of the sitemap
        
    Returns:
        List of URLs from the sitemap
    """
    resp = requests.get(sitemap_url)
    urls = []

    if resp.status_code == 200:
        try:
            tree = ElementTree.fromstring(resp.content)
            urls = [loc.text for loc in tree.findall('.//{*}loc')]
        except Exception as e:
            print(f"Error parsing sitemap XML: {e}")

    return urls


async def crawl_recursive_internal_links(start_urls, max_depth=3, max_concurrent=3) -> List[Dict[str,Any]]:
    """
    Recursive crawl using logic from 5-crawl_recursive_internal_links.py. Returns list of dicts with url and markdown.
    
    Args:
        start_urls: List of URLs to start crawling from
        max_depth: Maximum recursion depth
        max_concurrent: Maximum number of concurrent browser sessions
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    # Browser configuration for Docker environment with Playwright image
    browser_config = BrowserConfig(
        headless=True, 
        verbose=True  # Enable verbose logging
    )
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, 
        stream=False
    )
    
    # Reduce concurrency to avoid memory issues
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=60.0,  # Lower threshold to be safer
        check_interval=2.0,
        max_session_permit=max_concurrent
    )

    visited = set()

    def normalize_url(url):
        return urldefrag(url)[0]

    current_urls = set([normalize_url(u) for u in start_urls])
    results_all = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for depth in range(max_depth):
            urls_to_crawl = [normalize_url(url) for url in current_urls if normalize_url(url) not in visited]
            if not urls_to_crawl:
                break

            results = await crawler.arun_many(urls=urls_to_crawl, config=run_config, dispatcher=dispatcher)
            next_level_urls = set()

            for result in results:
                norm_url = normalize_url(result.url)
                visited.add(norm_url)

                if result.success and result.markdown:
                    results_all.append({'url': result.url, 'markdown': result.markdown})
                    for link in result.links.get("internal", []):
                        next_url = normalize_url(link["href"])
                        if next_url not in visited:
                            next_level_urls.add(next_url)

            current_urls = next_level_urls

    return results_all


async def crawl_markdown_file(url: str) -> List[Dict[str,Any]]:
    """Crawl a .txt or markdown file using logic from 4-crawl_and_chunk_markdown.py."""
    # Browser configuration for Docker environment with Playwright image
    browser_config = BrowserConfig(
        headless=True, 
        verbose=True  # Enable verbose logging
    )
    
    crawl_config = CrawlerRunConfig()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        if result.success and result.markdown:
            return [{'url': url, 'markdown': result.markdown}]
        else:
            print(f"Failed to crawl {url}: {result.error_message}")
            return []


async def crawl_batch(urls: List[str], max_concurrent: int = 5) -> List[Dict[str,Any]]:
    """
    Batch crawl using logic from 3-crawl_sitemap_in_parallel.py.
    
    Args:
        urls: List of URLs to crawl
        max_concurrent: Maximum number of concurrent browser sessions (reduced for stability)
        
    Returns:
        List of dictionaries with URL and markdown content
    """
    # Browser configuration for Docker environment with Playwright image
    browser_config = BrowserConfig(
        headless=True, 
        verbose=True  # Enable verbose logging
    )
    
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, 
        stream=False
    )
    
    # Reduce concurrency to avoid memory issues
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=60.0,  # Lower threshold to be safer
        check_interval=2.0,
        max_session_permit=max_concurrent
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=crawl_config, dispatcher=dispatcher)
        return [{'url': r.url, 'markdown': r.markdown} for r in results if r.success and r.markdown]
