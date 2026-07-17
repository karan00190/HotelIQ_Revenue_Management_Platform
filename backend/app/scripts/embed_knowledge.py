"""Dev-run script: chunk app/knowledge/*.md by heading, embed each chunk via
Gemini's free embedContent API, and write the committed app/knowledge/embeddings.json
artifact. Run this manually whenever a knowledge markdown file changes -
build_knowledge_index.py (the Docker build step) only re-hashes and indexes
what this script already embedded; it never calls the embeddings API itself.
"""

import hashlib
import json
import math
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
OUTPUT_PATH = KNOWLEDGE_DIR / "embeddings.json"
EMBED_MODEL = "gemini-embedding-001"
OUTPUT_DIMENSIONALITY = 768


def slugify(heading: str) -> str:
    slug = heading.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def chunk_markdown(path: Path) -> list[dict]:
    """Split a method-card markdown file into one chunk per H2 (##) section,
    with the document's H1 title prepended to each chunk for standalone context."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title_line = next((l for l in lines if l.startswith("# ")), None)
    title = title_line[2:].strip() if title_line else path.stem

    sections: list[dict] = []
    current_heading = None
    current_lines: list[str] = []

    def flush():
        if current_heading is not None:
            body = "\n".join(current_lines).strip()
            sections.append({"heading": current_heading, "body": body})

    for line in lines:
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)
    flush()

    chunks = []
    for section in sections:
        chunk_text = f"# {title}\n\n## {section['heading']}\n\n{section['body']}"
        chunks.append(
            {
                "id": f"{path.stem}::{slugify(section['heading'])}",
                "source": path.name,
                "title": title,
                "heading": section["heading"],
                "text": chunk_text,
            }
        )
    return chunks


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def embed_text(text: str, api_key: str) -> list[float]:
    resp = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:embedContent?key={api_key}",
        json={
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": OUTPUT_DIMENSIONALITY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    values = resp.json()["embedding"]["values"]
    return l2_normalize(values)


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set in environment/.env")

    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        raise SystemExit(f"No .md files found in {KNOWLEDGE_DIR}")

    all_chunks = []
    for path in md_files:
        all_chunks.extend(chunk_markdown(path))

    print(f"Found {len(md_files)} knowledge files, {len(all_chunks)} heading-level chunks.")

    records = []
    for i, chunk in enumerate(all_chunks, start=1):
        vector = embed_text(chunk["text"], api_key)
        records.append(
            {
                "id": chunk["id"],
                "source": chunk["source"],
                "title": chunk["title"],
                "heading": chunk["heading"],
                "text": chunk["text"],
                "sha256": sha256_of(chunk["text"]),
                "embedding": vector,
            }
        )
        print(f"  [{i}/{len(all_chunks)}] embedded {chunk['id']} (dim={len(vector)})")
        time.sleep(0.2)

    OUTPUT_PATH.write_text(json.dumps({"model": EMBED_MODEL, "dimensionality": OUTPUT_DIMENSIONALITY, "chunks": records}, indent=2), encoding="utf-8")
    print(f"\nWrote {len(records)} embedded chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
