"""Seed the knowledge_chunks table with Philippine tax knowledge.

Usage:
    python scripts/seed_knowledge.py

Reads from JSON files in knowledge/ph_tax/ directory AND from KNOWLEDGE_DATA below.
Generates embeddings via OpenAI, and inserts into DB.
If OPENAI_API_KEY is not set, inserts without embeddings (category-based retrieval only).
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.core.database import async_session_factory

# Knowledge directory
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge" / "ph_tax"

# Core knowledge entries (supplement JSON files with summarized reference data)
KNOWLEDGE_DATA = [
    {
        "category": "vat",
        "source": "BIR RR No. 16-2005 / TRAIN Law RA 10963",
        "content": (
            "The standard VAT rate in the Philippines is 12%, applied to the sale, barter, "
            "exchange, or lease of goods and properties, and the sale or exchange of services. "
            "VAT-registered persons must file BIR Form 2550M (Monthly VAT Declaration) on or "
            "before the 20th day following the end of each month. Quarterly returns use BIR Form 2550Q, "
            "filed within 25 days after the end of each quarter."
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
            "PHP 1.919M for house and lot). Drugs and medicines for diabetes, hypertension, and "
            "cholesterol are also VAT-exempt. Note: VAT-exempt sellers cannot claim input VAT credits."
        ),
    },
    {
        "category": "vat",
        "source": "NIRC Section 110 / BIR RMC 3-2023",
        "content": (
            "Input VAT is the VAT paid on purchases of goods, properties, or services used in "
            "the course of trade or business. It can be credited against output VAT. Input VAT "
            "on capital goods with aggregate acquisition cost exceeding PHP 1,000,000 in any 12-month "
            "period must be amortized over the useful life of the asset, not exceeding 60 months. "
            "Below PHP 1M, full input VAT is claimable in the month of purchase. Excess input VAT "
            "can be carried forward indefinitely to succeeding periods."
        ),
    },
    {
        "category": "vat",
        "source": "BIR Form 2550M Official Instructions",
        "content": (
            "BIR Form 2550M structure: Part I — Background Information (TIN, RDO, company, period, amendment status). "
            "Part II — Sales: Line 1 Vatable Sales, Line 2 Sales to Government (5% final withholding), "
            "Line 3 Zero-Rated Sales, Line 4 Exempt Sales, Line 5 Total Sales. "
            "Part III — Output Tax: Line 6 Output VAT (Line 1 x 12%), Line 6A Government (Line 2 x 5%), "
            "Line 6B Total Output Tax. "
            "Part IV — Input Tax: Line 7 Goods, Line 8 Capital Goods, Line 9 Services, Line 10 Imports, "
            "Line 11 Total Input Tax. "
            "Part V — Tax Due: Line 12 VAT Payable, Line 13 Less Tax Credits, Line 14 Net VAT Payable, "
            "Line 15 Add Penalties, Line 16 Total Amount Due."
        ),
    },
    {
        "category": "vat",
        "source": "BIR Revenue Regulations / NIRC Section 236",
        "content": (
            "VAT registration is mandatory for businesses with annual gross sales exceeding PHP 3,000,000. "
            "Below this threshold, businesses may opt for Percentage Tax (3% under TRAIN Law). "
            "Once registered for VAT, a taxpayer remains VAT-registered for at least 3 years. "
            "The 8% flat tax option is available for self-employed individuals and professionals "
            "earning under PHP 3M annually, in lieu of graduated income tax + 3% percentage tax."
        ),
    },
    {
        "category": "vat",
        "source": "BIR RR 14-2003 / Sales to Government",
        "content": (
            "Sales of goods and services to national government agencies, local government units, "
            "and GOCCs are subject to 5% Final Withholding VAT. The government buyer withholds 5% "
            "of the gross payment and remits it directly to the BIR. The seller reports these sales "
            "on Line 2 of BIR 2550M and the 5% withheld on Line 6A. The seller may still claim "
            "input VAT on purchases related to government sales. This 5% is considered the seller's "
            "final output VAT on government transactions — no additional 12% is charged."
        ),
    },
    {
        "category": "withholding",
        "source": "BIR RR No. 2-98 / TRAIN Law",
        "content": (
            "Expanded Withholding Tax (EWT) rates: Professional fees (individuals) — 5% if gross "
            "income < PHP 3M, 10% if >= PHP 3M. Professional fees (corporations) — 10%. "
            "Rent on real property — 5%. Services of contractors/subcontractors — 2%. "
            "Talent fees — 10-20%. Commission — 10-15%. Advertising — 2%. "
            "BIR Form 1601-EQ is filed quarterly; BIR Form 0619-E monthly."
        ),
    },
    {
        "category": "income_tax",
        "source": "TRAIN Law RA 10963 / CREATE MORE Act",
        "content": (
            "Corporate income tax rate is 25% on net taxable income. Reduced rate of 20% for domestic "
            "corporations with net taxable income <= PHP 5M AND total assets <= PHP 100M (excluding land). "
            "MCIT (Minimum Corporate Income Tax) is 1% of gross income (reduced from 2% under CREATE MORE Act), "
            "applicable beginning 4th taxable year. MCIT applies when greater than RCIT. "
            "Excess MCIT can be carried forward and credited against RCIT for 3 succeeding years. "
            "Quarterly returns use BIR Form 1702Q; annual uses 1702."
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
            "13th month pay and bonuses up to PHP 90,000 are tax-exempt. "
            "Minimum wage earners are exempt from income tax."
        ),
    },
    {
        "category": "general",
        "source": "BIR / NIRC General Provisions",
        "content": (
            "All taxpayers must register with the BIR using Form 1901 (self-employed) or "
            "Form 1903 (corporations). Registration requires securing a TIN (Tax Identification Number). "
            "Books of accounts must be registered with the BIR and kept for 10 years (NIRC Section 235). "
            "Penalties: 25% surcharge for late filing, 12% interest per year, and compromise penalties. "
            "50% surcharge for willful neglect or fraudulent returns."
        ),
    },
    {
        "category": "general",
        "source": "BIR Calendar / Filing Deadlines",
        "content": (
            "Key BIR filing deadlines: "
            "Monthly VAT (2550M) — 20th of the following month. "
            "Quarterly VAT (2550Q) — 25th of the month following the quarter. "
            "Monthly Withholding Tax (1601C) — 10th of the following month. "
            "Monthly Expanded Withholding (0619-E) — 10th of following month. "
            "Quarterly Income Tax (1701Q/1702Q) — 60 days after quarter-end. "
            "Annual Income Tax (1701/1702) — April 15. "
            "Annual Registration Fee (0605) — January 31. "
            "Annual Information Return (1604-CF) — January 31."
        ),
    },
    {
        "category": "compliance",
        "source": "BIR Compliance Requirements",
        "content": (
            "Required attachments for BIR 2550M: (1) Summary List of Sales (SLS) — CSV format listing "
            "all sales with customer TIN, name, amount, and VAT; (2) Summary List of Purchases (SLP) — "
            "CSV format listing all purchases with supplier TIN, name, amount, and input VAT; "
            "(3) Summary Alphalist of Withholding Taxes (SAWT) if the taxpayer withheld taxes. "
            "All transactions exceeding PHP 1,000 must be itemized. Smaller transactions may be lumped. "
            "Electronic filing via eFPS is mandatory for large taxpayers and top 20,000 corporations."
        ),
    },
]


def load_json_knowledge() -> list[dict]:
    """Load knowledge entries from JSON files in knowledge/ph_tax/ directory."""
    entries = []
    if not KNOWLEDGE_DIR.exists():
        print(f"Knowledge directory not found: {KNOWLEDGE_DIR}")
        return entries

    for json_file in sorted(KNOWLEDGE_DIR.glob("*.json")):
        print(f"  Loading {json_file.name}...")
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        category = data.get("category", "general")
        source = data.get("source", json_file.stem)

        for chunk in data.get("chunks", []):
            title = chunk.get("title", "")
            content = chunk.get("content", "")
            if content:
                entries.append({
                    "category": category,
                    "source": f"{source} — {title}" if title else source,
                    "content": content,
                })

    return entries


async def generate_embedding(text: str, client=None) -> list[float] | None:
    """Generate embedding using OpenAI API."""
    if not settings.openai_api_key:
        return None

    try:
        if client is None:
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


async def generate_embeddings_batch(texts: list[str], client=None) -> list[list[float] | None]:
    """Generate embeddings for multiple texts in a single API call (max 2048 inputs)."""
    if not settings.openai_api_key:
        return [None] * len(texts)

    try:
        if client is None:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)

        results: list[list[float] | None] = [None] * len(texts)
        batch_size = 100  # OpenAI recommends batches of ~100 for efficiency

        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
                dimensions=1024,
            )
            for item in response.data:
                results[start + item.index] = item.embedding

        return results
    except Exception as e:
        print(f"  Warning: batch embedding generation failed: {e}")
        return [None] * len(texts)


async def seed():
    # Collect all knowledge entries
    print("Loading knowledge from JSON files...")
    json_entries = load_json_knowledge()
    all_entries = json_entries + KNOWLEDGE_DATA
    # Deduplicate by content (first 100 chars)
    seen = set()
    unique_entries = []
    for entry in all_entries:
        key = entry["content"][:100]
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    print(f"\nSeeding knowledge base with {len(unique_entries)} entries ({len(json_entries)} from JSON, {len(KNOWLEDGE_DATA)} core)...")
    print(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'configured'}")

    # Category breakdown
    cat_counts: dict[str, int] = {}
    for e in unique_entries:
        cat_counts[e["category"]] = cat_counts.get(e["category"], 0) + 1
    for cat, cnt in sorted(cat_counts.items()):
        print(f"  {cat}: {cnt} entries")

    # Generate embeddings in batch for efficiency
    print("\nGenerating embeddings (batch mode)...")
    openai_client = None
    if settings.openai_api_key:
        from openai import AsyncOpenAI
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    all_texts = [e["content"] for e in unique_entries]
    embeddings = await generate_embeddings_batch(all_texts, openai_client)
    embed_count = sum(1 for emb in embeddings if emb is not None)
    print(f"  Generated {embed_count}/{len(unique_entries)} embeddings")

    async with async_session_factory() as session:
        # Clear existing data
        result = await session.execute(text("SELECT COUNT(*) FROM knowledge_chunks"))
        count = result.scalar()
        if count and count > 0:
            print(f"\nClearing {count} existing entries...")
            await session.execute(text("DELETE FROM knowledge_chunks"))

        print(f"\nInserting {len(unique_entries)} entries...")
        success = 0
        for i, entry in enumerate(unique_entries):
            embedding = embeddings[i]

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
            success += 1

            if (i + 1) % 25 == 0:
                print(f"  [{i+1}/{len(unique_entries)}] inserted...")

        await session.commit()
        print(f"\nDone! Seeded {success} knowledge chunks.")
        print(f"Embeddings: {embed_count}/{success} generated")
        print(f"Categories: {', '.join(sorted(cat_counts.keys()))}")


if __name__ == "__main__":
    asyncio.run(seed())
