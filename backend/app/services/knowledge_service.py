"""RAG search over the committed knowledge corpus (app/knowledge/*.md, indexed
into a local Chroma collection by app/scripts/build_knowledge_index.py at
Docker build time). Query-time embedding is a single Gemini embedContent
call - Chroma's default ONNX embedder is never instantiated because every
add/query here always supplies its own pre-computed vector.
"""

import math
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "hoteliq_knowledge"
EMBED_MODEL = "gemini-embedding-001"
OUTPUT_DIMENSIONALITY = 768

_collection = None


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _embed_query(query: str) -> list[float]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set - knowledge search is unavailable")

    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:embedContent?key={api_key}",
        json={
            "content": {"parts": [{"text": query}]},
            "taskType": "RETRIEVAL_QUERY",
            "outputDimensionality": OUTPUT_DIMENSIONALITY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    values = resp.json()["embedding"]["values"]
    return _l2_normalize(values)


def _get_collection():
    """Loading the collection is cheap (a local path check + opening a
    sqlite file), so failure is never cached - only success is. Caching
    failure would permanently disable knowledge search for the rest of the
    process's life after one transient error, with no way to recover short
    of a restart."""
    global _collection
    if _collection is not None:
        return _collection

    if not CHROMA_DIR.exists():
        raise RuntimeError(
            f"Knowledge index not found at {CHROMA_DIR}. "
            "Run `python -m app.scripts.build_knowledge_index` first."
        )

    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))
    _collection = client.get_collection(name=COLLECTION_NAME)
    return _collection


def is_available() -> bool:
    try:
        _get_collection()
        return True
    except Exception:
        return False


def chunk_count() -> int:
    try:
        return _get_collection().count()
    except Exception:
        return 0


def search(query: str, k: int = 4) -> list[dict]:
    """Return up to k knowledge chunks most relevant to query, most relevant first."""
    collection = _get_collection()
    query_vector = _embed_query(query)

    result = collection.query(query_embeddings=[query_vector], n_results=k)

    hits = []
    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        hits.append(
            {
                "id": chunk_id,
                "source": metadata.get("source"),
                "title": metadata.get("title"),
                "heading": metadata.get("heading"),
                "text": document,
                "distance": distance,
            }
        )
    return hits


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m app.services.knowledge_service "your query here"')

    query_text = " ".join(sys.argv[1:])
    results = search(query_text, k=4)

    print(f"Query: {query_text}\n")
    for i, hit in enumerate(results, start=1):
        print(f"[{i}] {hit['id']}  (distance={hit['distance']:.4f})")
        print(f"    source: {hit['source']} | heading: {hit['heading']}")
        snippet = hit["text"].replace("\n", " ")[:160]
        print(f"    {snippet}...\n")
