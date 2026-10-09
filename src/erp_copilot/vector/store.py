"""Pinecone knowledge store. Pinecone embeds the text itself (integrated embedding), so no
separate embedding model or API key is needed."""

from functools import lru_cache
from pathlib import Path

from pinecone import Pinecone

from erp_copilot.config import PineconeSettings

KNOWLEDGE_DIR = Path(__file__).resolve().parents[3] / "knowledge"


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a markdown doc into one chunk per '## ' section, each prefixed with the doc title."""
    title = ""
    sections: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif sections:
            sections[-1][1].append(line)
    return [
        {
            "_id": f"{source}-{i}",
            "chunk_text": f"{title} - {section}\n{' '.join(l.strip() for l in body if l.strip())}",
            "source": source,
            "section": section,
        }
        for i, (section, body) in enumerate(sections)
    ]


def load_knowledge_chunks(directory: Path = KNOWLEDGE_DIR) -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(directory.glob("*.md")):
        chunks.extend(chunk_markdown(path.read_text(), path.stem))
    return chunks


@lru_cache
def _client() -> Pinecone:
    return Pinecone(api_key=PineconeSettings().pinecone_api_key)


def ensure_index() -> None:
    settings = PineconeSettings()
    pc = _client()
    if not pc.has_index(settings.pinecone_index):
        pc.create_index_for_model(
            name=settings.pinecone_index,
            cloud=settings.pinecone_cloud,
            region=settings.pinecone_region,
            embed={"model": settings.pinecone_embed_model, "field_map": {"text": "chunk_text"}},
        )


@lru_cache
def get_index():
    settings = PineconeSettings()
    return _client().Index(host=_client().describe_index(settings.pinecone_index).host)


def upsert_chunks(chunks: list[dict], batch_size: int = 90) -> int:
    namespace = PineconeSettings().pinecone_namespace
    index = get_index()
    for start in range(0, len(chunks), batch_size):
        index.upsert_records(namespace=namespace, records=chunks[start : start + batch_size])
    return len(chunks)


def search(query: str, top_k: int = 3) -> list[dict]:
    response = get_index().search(
        namespace=PineconeSettings().pinecone_namespace,
        top_k=top_k,
        inputs={"text": query},
        fields=["chunk_text", "source", "section"],
    )
    return [
        {
            "source": hit.fields.get("source"),
            "section": hit.fields.get("section"),
            "text": hit.fields.get("chunk_text"),
            "score": round(hit.score, 3),
        }
        for hit in response.result.hits
    ]
