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


class NoRelevantSources(LookupError):
    """No tenant-visible document has a positive lexical match."""


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
    scored = [
        (len(terms.intersection(document.text.lower().split())), document)
        for document in allowed
    ]
    ranked = [
        document
        for score, document in sorted(scored, key=lambda item: item[0], reverse=True)
        if score > 0
    ]
    if not ranked:
        raise NoRelevantSources("no relevant sources")
    selected = tuple(document.id for document in ranked[:max_sources])
    return Answer(text="fake answer; inspect cited sources", source_ids=selected)
