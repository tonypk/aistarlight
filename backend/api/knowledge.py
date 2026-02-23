from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import get_current_user, get_session
from backend.models.knowledge import KnowledgeChunk
from backend.models.tenant import User
from backend.schemas.common import ok

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """List knowledge base entries."""
    query = select(KnowledgeChunk).order_by(KnowledgeChunk.category, KnowledgeChunk.created_at)
    count_query = select(func.count()).select_from(KnowledgeChunk)

    if category:
        query = query.where(KnowledgeChunk.category == category)
        count_query = count_query.where(KnowledgeChunk.category == category)

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    chunks = result.scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return ok(
        [
            {
                "id": str(c.id),
                "category": c.category,
                "source": c.source,
                "content": c.content,
                "has_embedding": c.embedding is not None,
                "created_at": c.created_at.isoformat(),
            }
            for c in chunks
        ],
        meta={"total": total, "page": page, "limit": limit},
    )


@router.get("/stats")
async def knowledge_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Get knowledge base statistics."""
    total_result = await db.execute(select(func.count()).select_from(KnowledgeChunk))
    total = total_result.scalar()

    # Count by category
    cat_query = (
        select(KnowledgeChunk.category, func.count())
        .group_by(KnowledgeChunk.category)
        .order_by(KnowledgeChunk.category)
    )
    cat_result = await db.execute(cat_query)
    categories = {row[0] or "uncategorized": row[1] for row in cat_result.fetchall()}

    # Count with embeddings
    emb_result = await db.execute(
        select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.embedding.isnot(None))
    )
    with_embeddings = emb_result.scalar()

    return ok({
        "total": total,
        "with_embeddings": with_embeddings,
        "categories": categories,
    })
