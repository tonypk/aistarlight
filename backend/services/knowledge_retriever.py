"""RAG knowledge retriever for Philippine tax regulations."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.llm import chat_completion
from backend.repositories.knowledge import KnowledgeRepository


async def _generate_query_embedding(query: str) -> list[float] | None:
    """Generate embedding for a search query."""
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=1024,
        )
        return response.data[0].embedding
    except Exception:
        return None


async def retrieve_relevant_knowledge(
    query: str,
    category: str | None = None,
    db: AsyncSession | None = None,
    limit: int = 5,
) -> list[dict]:
    """Retrieve relevant tax knowledge chunks.

    Tries vector similarity search first (if embeddings exist).
    Falls back to category-based search.
    """
    if db is None:
        return []

    repo = KnowledgeRepository(db)

    # Try vector search first
    embedding = await _generate_query_embedding(query)
    if embedding is not None:
        chunks = await repo.search_similar(embedding, category=category, limit=limit)
        if chunks:
            return [
                {
                    "content": chunk.content,
                    "source": chunk.source,
                    "category": chunk.category,
                }
                for chunk in chunks
            ]

    # Fallback: category-based search
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
