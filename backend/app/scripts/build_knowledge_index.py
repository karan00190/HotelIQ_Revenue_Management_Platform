"""Build-time script (runs during `docker build`, no secrets/network needed):
re-chunks app/knowledge/*.md, verifies every chunk's hash still matches the
committed app/knowledge/embeddings.json, and builds a local Chroma index from
those already-computed vectors. Fails loudly if the corpus and the committed
embeddings have drifted apart (someone edited a .md file without re-running
embed_knowledge.py) rather than silently indexing stale or mismatched text.
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed_knowledge import KNOWLEDGE_DIR, chunk_markdown, sha256_of  # noqa: E402

EMBEDDINGS_PATH = KNOWLEDGE_DIR / "embeddings.json"
CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma"
COLLECTION_NAME = "hoteliq_knowledge"


def load_committed_embeddings() -> dict:
    if not EMBEDDINGS_PATH.exists():
        raise SystemExit(
            f"{EMBEDDINGS_PATH} not found. Run `python -m app.scripts.embed_knowledge` "
            "first (requires GEMINI_API_KEY) and commit the resulting file."
        )
    data = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
    return {chunk["id"]: chunk for chunk in data["chunks"]}


def verify_hashes(committed: dict) -> list[dict]:
    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    fresh_chunks = []
    for path in md_files:
        fresh_chunks.extend(chunk_markdown(path))

    fresh_ids = {c["id"] for c in fresh_chunks}
    committed_ids = set(committed.keys())

    if fresh_ids != committed_ids:
        missing = fresh_ids - committed_ids
        extra = committed_ids - fresh_ids
        raise SystemExit(
            "Knowledge corpus and embeddings.json are out of sync (chunk set changed).\n"
            f"  In markdown but not embedded: {sorted(missing) or 'none'}\n"
            f"  In embeddings.json but no longer in markdown: {sorted(extra) or 'none'}\n"
            "Run `python -m app.scripts.embed_knowledge` and commit the updated file."
        )

    mismatched = []
    for chunk in fresh_chunks:
        fresh_hash = sha256_of(chunk["text"])
        committed_hash = committed[chunk["id"]]["sha256"]
        if fresh_hash != committed_hash:
            mismatched.append(chunk["id"])

    if mismatched:
        raise SystemExit(
            "Knowledge corpus has changed since embeddings.json was generated "
            f"(hash mismatch on: {mismatched}).\n"
            "Run `python -m app.scripts.embed_knowledge` and commit the updated file."
        )

    return fresh_chunks


def build_index(committed: dict, chunk_order: list[dict]):
    import chromadb
    from chromadb.config import Settings

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))
    collection = client.create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    ids = [c["id"] for c in chunk_order]
    embeddings = [committed[c["id"]]["embedding"] for c in chunk_order]
    documents = [committed[c["id"]]["text"] for c in chunk_order]
    metadatas = [
        {"source": committed[c["id"]]["source"], "title": committed[c["id"]]["title"], "heading": committed[c["id"]]["heading"]}
        for c in chunk_order
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return collection.count()


def main():
    committed = load_committed_embeddings()
    fresh_chunks = verify_hashes(committed)
    print(f"Hash check passed: {len(fresh_chunks)} chunks match embeddings.json exactly.")

    count = build_index(committed, fresh_chunks)
    print(f"Built Chroma collection '{COLLECTION_NAME}' at {CHROMA_DIR} with {count} chunks.")


if __name__ == "__main__":
    main()
