from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    id: str
    tenant_id: str
    text: str


@dataclass(frozen=True)
class Answer:
    text: str
    source_ids: tuple[str, ...]


def answer_with_fake_rag(
    documents: list[Document],
    *,
    tenant_id: str,
    query: str,
    max_sources: int = 3,
) -> Answer:
    """A deterministic fake for testing permissions, budgets and citations."""
    if not query.strip() or not 1 <= max_sources <= 10:
        raise ValueError("invalid RAG budget")
    terms = set(query.lower().split())
    allowed = [document for document in documents if document.tenant_id == tenant_id]
    ranked = sorted(
        allowed,
        key=lambda document: len(terms.intersection(document.text.lower().split())),
        reverse=True,
    )
    selected = tuple(document.id for document in ranked[:max_sources])
    return Answer(text="fake answer; inspect cited sources", source_ids=selected)
