# RAG_with_crawl4AI

## Inspiration

This project is inspired by the [crawl4AI](https://github.com/crawl4AI/crawl4AI) project, which is a web crawler that can be used to crawl websites and store the content in a ChromaDB database. [This tutorial](https://github.com/coleam00/ottomator-agents/blob/main/crawl4AI-agent-v2/README.md) was used as a reference.


## Example Usage

```sh
python insert_docs.py <URL> [--collection mydocs] [--db-dir ./chroma_db] [--embedding-model all-MiniLM-L6-v2] [--chunk-size 1000] [--max-depth 3] [--max-concurrent 10] [--batch-size 100]
```

### Arguments

* `URL` : The root URL, .txt file, or sitemap to crawl.
* `--collection` : ChromaDB collection name (default: docs)
* `--db-dir` : Directory for ChromaDB data (default: ./chroma_db)
* `--embedding-model` : Embedding model for vector storage (default: all-MiniLM-L6-v2)
* `--chunk-size` : Maximum characters per chunk (default: 1000)
* `--max-depth` : Recursion depth for regular URLs (default: 3)
* `--max-concurrent` : Max parallel browser sessions (default: 10)
* `--batch-size` : Batch size for ChromaDB insertion (default: 100)

### Examples for each type (regular URL, .txt, sitemap):

```sh
python insert_docs.py https://ai.pydantic.dev/
python insert_docs.py https://ai.pydantic.dev/llms-full.txt
python insert_docs.py https://ai.pydantic.dev/sitemap.xml
```

### Chunking Strategy
Splits content first by #, then by ##, then by ### headers.
If a chunk is still too large, splits by character count.
All chunks are less than the specified --chunk-size (default: 1000 characters).

### Metadata
Each chunk is stored with:

* Source URL
* Chunk index
* Extracted headers
* Character and word counts
