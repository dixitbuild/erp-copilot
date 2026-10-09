"""Load the markdown files in knowledge/ into Pinecone. Safe to re-run (records are upserted)."""

from erp_copilot.vector import store as vector_store
from erp_copilot.config import pinecone_configured


def main() -> None:
    if not pinecone_configured():
        raise SystemExit("PINECONE_API_KEY is missing. Add it to .env first.")
    vector_store.ensure_index()
    chunks = vector_store.load_knowledge_chunks()
    count = vector_store.upsert_chunks(chunks)
    print(f"Indexed {count} chunks from {vector_store.KNOWLEDGE_DIR}")
