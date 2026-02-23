"""Shared test fixtures for AIStarlight."""

import pytest


@pytest.fixture
def sample_sales_data() -> list[dict]:
    """Typical mixed sales data for VAT calculations."""
    return [
        {"amount": 100000, "vat_type": "vatable"},
        {"amount": 50000, "vat_type": "government"},
        {"amount": 30000, "vat_type": "zero_rated"},
        {"amount": 20000, "vat_type": "exempt"},
    ]


@pytest.fixture
def sample_purchases_data() -> list[dict]:
    """Typical mixed purchase data for VAT input tax."""
    return [
        {"amount": 40000, "vat_amount": 4800, "category": "goods"},
        {"amount": 10000, "vat_amount": 1200, "category": "services"},
        {"amount": 5000, "vat_amount": 600, "category": "capital"},
        {"amount": 3000, "vat_amount": 360, "category": "imports"},
    ]


@pytest.fixture
def sample_compensation_data() -> dict:
    """Typical 1601-C compensation data."""
    return {
        "total_compensation": "500000",
        "statutory_minimum_wage": "100000",
        "nontaxable_13th_month": "50000",
        "nontaxable_deminimis": "10000",
        "sss_gsis_phic_hdmf": "20000",
        "other_nontaxable": "5000",
        "tax_withheld": "30000",
        "adjustment": "2000",
        "surcharge": "0",
        "interest": "0",
        "compromise": "0",
    }


@pytest.fixture
def sample_ewt_data() -> dict:
    """Typical 0619-E EWT remittance data."""
    return {
        "total_income_payments": "1000000",
        "total_taxes_withheld": "50000",
        "adjustment": "5000",
        "surcharge": "0",
        "interest": "0",
        "compromise": "0",
    }
