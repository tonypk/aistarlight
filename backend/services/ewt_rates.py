"""Philippine Expanded Withholding Tax (EWT) rate table.

Based on BIR Revenue Regulations No. 2-98 as amended by TRAIN Law (RA 10963).
Maps ATC (Alphanumeric Tax Code) → rate, description, and category.
"""

from decimal import Decimal

EWT_RATES: dict[str, dict] = {
    # Professional fees
    "WI010": {
        "desc": "Professional fees - Individual (<3M gross)",
        "rate": Decimal("0.05"),
        "category": "services",
        "keywords": ["professional", "consulting", "advisory"],
    },
    "WI020": {
        "desc": "Professional fees - Individual (>=3M gross)",
        "rate": Decimal("0.10"),
        "category": "services",
        "keywords": ["professional", "consulting"],
    },
    "WC010": {
        "desc": "Professional fees - Corporation",
        "rate": Decimal("0.10"),
        "category": "services",
        "keywords": ["professional", "consulting", "audit fee", "legal fee"],
    },
    "WC020": {
        "desc": "Professional fees - Corporation (>720K gross)",
        "rate": Decimal("0.15"),
        "category": "services",
        "keywords": ["professional", "consulting"],
    },
    # Rent
    "WI030": {
        "desc": "Rent - Real property",
        "rate": Decimal("0.05"),
        "category": "services",
        "keywords": ["rent", "lease", "rental"],
    },
    "WI040": {
        "desc": "Rent - Personal property (equipment, vehicles)",
        "rate": Decimal("0.05"),
        "category": "services",
        "keywords": ["equipment rental", "vehicle lease"],
    },
    # Contractors
    "WI050": {
        "desc": "Contractors / Subcontractors - Individual",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["contractor", "subcontractor", "construction", "repair"],
    },
    "WC050": {
        "desc": "Contractors / Subcontractors - Corporation",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["contractor", "subcontractor", "construction"],
    },
    # Advertising
    "WC060": {
        "desc": "Advertising / Promotions",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["advertising", "promotion", "marketing", "media"],
    },
    # Commission / Brokerage
    "WI070": {
        "desc": "Commission / Brokerage - Individual",
        "rate": Decimal("0.10"),
        "category": "services",
        "keywords": ["commission", "brokerage", "broker"],
    },
    "WC070": {
        "desc": "Commission / Brokerage - Corporation",
        "rate": Decimal("0.10"),
        "category": "services",
        "keywords": ["commission", "brokerage"],
    },
    # Goods
    "WI100": {
        "desc": "Purchase of goods (>3M annual)",
        "rate": Decimal("0.01"),
        "category": "goods",
        "keywords": ["purchase", "supply", "goods", "merchandise"],
    },
    "WC100": {
        "desc": "Purchase of goods - Corporation (>3M annual)",
        "rate": Decimal("0.01"),
        "category": "goods",
        "keywords": ["purchase", "supply", "goods"],
    },
    # Service payments
    "WI120": {
        "desc": "Service payments - Individual",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["service", "maintenance", "cleaning", "security"],
    },
    "WC120": {
        "desc": "Service payments - Corporation",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["service", "maintenance", "cleaning", "security"],
    },
    # Transport
    "WI150": {
        "desc": "Transport / Delivery / Freight",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["transport", "delivery", "freight", "shipping", "trucking"],
    },
    # Tolls
    "WI160": {
        "desc": "Toll fees",
        "rate": Decimal("0.01"),
        "category": "services",
        "keywords": ["toll", "tollway"],
    },
    # Insurance
    "WI170": {
        "desc": "Insurance premiums",
        "rate": Decimal("0.02"),
        "category": "services",
        "keywords": ["insurance", "premium"],
    },
}

# Income type descriptions mapped by ATC code
INCOME_TYPES: dict[str, str] = {code: info["desc"] for code, info in EWT_RATES.items()}


def get_rate(atc_code: str) -> Decimal:
    """Get EWT rate for a given ATC code."""
    entry = EWT_RATES.get(atc_code)
    if not entry:
        raise ValueError(f"Unknown ATC code: {atc_code}")
    return entry["rate"]


def get_income_type(atc_code: str) -> str:
    """Get income type description for a given ATC code."""
    return INCOME_TYPES.get(atc_code, "Other income")


def find_atc_by_keywords(description: str, supplier_type: str = "corporation") -> str | None:
    """Find best matching ATC code by keyword matching in description.

    Returns the ATC code or None if no match.
    """
    desc_lower = description.lower()
    type_prefix = "WC" if supplier_type == "corporation" else "WI"

    best_match: str | None = None
    best_score = 0

    for code, info in EWT_RATES.items():
        # Prefer codes matching supplier type
        if not code.startswith(type_prefix) and not code.startswith("W"):
            continue
        score = sum(1 for kw in info["keywords"] if kw in desc_lower)
        if score > best_score:
            best_score = score
            best_match = code

    return best_match if best_score > 0 else None


def list_rates() -> list[dict]:
    """List all EWT rates for reference."""
    return [
        {
            "atc_code": code,
            "description": info["desc"],
            "rate": float(info["rate"]),
            "category": info["category"],
        }
        for code, info in EWT_RATES.items()
    ]
