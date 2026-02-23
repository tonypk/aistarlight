"""Seed the knowledge_chunks table with Philippine tax knowledge.

Usage:
    python scripts/seed_knowledge.py

Reads from KNOWLEDGE_DATA below, generates embeddings via OpenAI, and inserts into DB.
If OPENAI_API_KEY is not set, inserts without embeddings (category-based retrieval only).
"""

import asyncio
import json
import os
import sys
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.database import async_session_factory

# Philippine tax knowledge base
KNOWLEDGE_DATA = [
    {
        "category": "vat",
        "source": "BIR RR No. 16-2005 / TRAIN Law RA 10963",
        "content": (
            "The standard VAT rate in the Philippines is 12%, applied to the sale, barter, "
            "exchange, or lease of goods and properties, and the sale or exchange of services. "
            "VAT-registered persons must file BIR Form 2550M (Monthly VAT Declaration) on or "
            "before the 20th day following the end of each month. Quarterly returns use BIR Form 2550Q."
        ),
    },
    {
        "category": "vat",
        "source": "NIRC Section 109 / TRAIN Law",
        "content": (
            "VAT-exempt transactions include: sale of agricultural and marine food products "
            "in their original state; educational services by accredited institutions; sale or "
            "importation of agricultural inputs; services by banks under BSP supervision; sale "
            "of real property not primarily held for sale (under PHP 3.199M for residential lots, "
            "PHP 1.919M for house and lot). Raw materials and packaging for export are zero-rated."
        ),
    },
    {
        "category": "vat",
        "source": "NIRC Section 110 / BIR RMC 3-2023",
        "content": (
            "Input VAT is the VAT paid on purchases of goods, properties, or services used in "
            "the course of trade or business. It can be credited against output VAT. Input VAT "
            "on capital goods (depreciable assets > PHP 1M) is amortized over the useful life "
            "of the asset, not exceeding 60 months. Excess input VAT can be carried forward to "
            "succeeding periods."
        ),
    },
    {
        "category": "vat",
        "source": "BIR Form 2550M Instructions",
        "content": (
            "BIR Form 2550M requires: Part I — Taxpayer Information (TIN, RDO code, company name). "
            "Part II — Computation of Tax: Line 1: Vatable Sales/Receipts. Line 2: Sales to Government. "
            "Line 3: Zero-Rated Sales. Line 4: Exempt Sales. Line 14A: Output Tax (12% of Line 1). "
            "Line 15: Less - Allowable Input Tax. Line 16: VAT Payable. "
            "Payment must be made to an Authorized Agent Bank (AAB) within the jurisdiction of the RDO."
        ),
    },
    {
        "category": "vat",
        "source": "BIR Revenue Regulations",
        "content": (
            "VAT registration is mandatory for businesses with annual gross sales exceeding PHP 3,000,000. "
            "Below this threshold, businesses may opt for Percentage Tax (3% under TRAIN Law). "
            "Once registered for VAT, a taxpayer remains VAT-registered for at least 3 years. "
            "The 8% flat tax option is available for self-employed/professionals earning under PHP 3M."
        ),
    },
    {
        "category": "withholding",
        "source": "BIR RR No. 2-98 / TRAIN Law",
        "content": (
            "Expanded Withholding Tax (EWT) rates: Professional fees (individuals) — 5% if gross "
            "income < PHP 3M, 10% if >= PHP 3M. Professional fees (corporations) — 10%. "
            "Rent on real property — 5%. Services of contractors/subcontractors — 2%. "
            "Talent fees — 10-20%. Commission — 10-15%. "
            "BIR Form 1601-EQ is filed quarterly; BIR Form 0619-E monthly."
        ),
    },
    {
        "category": "income_tax",
        "source": "TRAIN Law RA 10963 / NIRC",
        "content": (
            "Corporate income tax rate is 25% on net taxable income (20% for domestic corporations "
            "with net taxable income <= PHP 5M AND total assets <= PHP 100M). "
            "MCIT (Minimum Corporate Income Tax) is 1% of gross income, applicable beginning "
            "4th taxable year. Quarterly returns use BIR Form 1702Q; annual uses 1702."
        ),
    },
    {
        "category": "income_tax",
        "source": "TRAIN Law / BIR RR 8-2018",
        "content": (
            "Individual income tax rates under TRAIN Law (effective 2023+): "
            "0% for income up to PHP 250,000; 15% for PHP 250,001-400,000; "
            "20% for PHP 400,001-800,000; 25% for PHP 800,001-2,000,000; "
            "30% for PHP 2,000,001-8,000,000; 35% for over PHP 8,000,000. "
            "13th month pay and bonuses up to PHP 90,000 are tax-exempt."
        ),
    },
    {
        "category": "general",
        "source": "BIR / NIRC General Provisions",
        "content": (
            "All taxpayers must register with the BIR using Form 1901 (self-employed) or "
            "Form 1903 (corporations). Registration requires securing a TIN (Tax Identification Number). "
            "Books of accounts must be registered with the BIR and kept for 10 years. "
            "Penalties: 25% surcharge for late filing, 12% interest per year, and compromise penalties."
        ),
    },
    {
        "category": "general",
        "source": "BIR Calendar",
        "content": (
            "Key BIR filing deadlines: "
            "Monthly VAT (2550M) — 20th of the following month. "
            "Quarterly VAT (2550Q) — 25th of the month following the quarter. "
            "Monthly Withholding Tax (1601C) — 10th of the following month. "
            "Quarterly Income Tax (1701Q/1702Q) — 60 days after quarter-end. "
            "Annual Income Tax (1701/1702) — April 15. "
            "Annual Registration Fee (0605) — January 31."
        ),
    },
]


async def generate_embedding(text: str) -> list[float] | None:
    """Generate embedding using OpenAI API."""
    if not settings.openai_api_key:
        return None

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=1024,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  Warning: embedding generation failed: {e}")
        return None


async def seed():
    print(f"Seeding knowledge base with {len(KNOWLEDGE_DATA)} entries...")
    print(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'configured'}")

    async with async_session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_chunks"))
        count = result.scalar()
        if count and count > 0:
            print(f"Knowledge base already has {count} entries. Clearing and re-seeding...")
            await session.execute(text("DELETE FROM knowledge_chunks"))

        for i, entry in enumerate(KNOWLEDGE_DATA):
            print(f"  [{i+1}/{len(KNOWLEDGE_DATA)}] {entry['category']}: {entry['source'][:50]}...")

            embedding = await generate_embedding(entry["content"])

            if embedding:
                await session.execute(
                    text(
                        "INSERT INTO knowledge_chunks (id, source, category, content, embedding, metadata, created_at) "
                        "VALUES (:id, :source, :category, :content, :embedding, :metadata, NOW())"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "source": entry["source"],
                        "category": entry["category"],
                        "content": entry["content"],
                        "embedding": "[" + ",".join(str(x) for x in embedding) + "]",
                        "metadata": json.dumps({}),
                    },
                )
            else:
                await session.execute(
                    text(
                        "INSERT INTO knowledge_chunks (id, source, category, content, metadata, created_at) "
                        "VALUES (:id, :source, :category, :content, :metadata, NOW())"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "source": entry["source"],
                        "category": entry["category"],
                        "content": entry["content"],
                        "metadata": json.dumps({}),
                    },
                )

        await session.commit()
        print(f"Done! Seeded {len(KNOWLEDGE_DATA)} knowledge chunks.")
        has_embeddings = settings.openai_api_key != ""
        print(f"Embeddings: {'generated' if has_embeddings else 'skipped (no OPENAI_API_KEY)'}")


if __name__ == "__main__":
    asyncio.run(seed())
