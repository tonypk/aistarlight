"""RAG knowledge retriever for Philippine tax regulations."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.llm import chat_completion
from backend.repositories.knowledge import KnowledgeRepository


async def retrieve_relevant_knowledge(
    query: str,
    category: str | None = None,
    db: AsyncSession = None,
    limit: int = 5,
) -> list[dict]:
    """Retrieve relevant tax knowledge chunks using semantic search.

    Note: In MVP, falls back to keyword-based search.
    Full vector search requires embedding generation.
    """
    repo = KnowledgeRepository(db)

    # For MVP, retrieve by category
    if category:
        chunks = await repo.find_by_category(category)
    else:
        chunks = await repo.find_all(limit=limit)

    return [
        {
            "content": chunk.content,
            "source": chunk.source,
            "category": chunk.category,
        }
        for chunk in chunks
    ]


async def answer_tax_question(
    question: str,
    context_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> str:
    """Answer a tax question using retrieved knowledge context."""
    context_text = "\n\n".join(
        f"[Source: {c['source']}]\n{c['content']}" for c in context_chunks
    )

    system = f"""You are an expert Philippine tax consultant AI assistant.
Use the following tax regulation context to answer questions accurately.
Always cite the relevant BIR regulation or rule when possible.
If you're not sure, say so rather than guessing.

Context:
{context_text}
"""

    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": question})

    return await chat_completion(messages=messages, system=system)
