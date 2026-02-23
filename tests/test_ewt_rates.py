"""Unit tests for EWT rate table and lookup functions."""

from decimal import Decimal

import pytest

from backend.services.ewt_rates import (
    EWT_RATES,
    find_atc_by_keywords,
    get_income_type,
    get_rate,
    list_rates,
)


class TestGetRate:
    """get_rate() function tests."""

    def test_known_atc_codes(self):
        assert get_rate("WI010") == Decimal("0.05")
        assert get_rate("WC010") == Decimal("0.10")
        assert get_rate("WI050") == Decimal("0.02")
        assert get_rate("WI160") == Decimal("0.01")

    def test_unknown_atc_code_raises(self):
        with pytest.raises(ValueError, match="Unknown ATC code"):
            get_rate("INVALID")


class TestGetIncomeType:
    """get_income_type() function tests."""

    def test_known_atc_code(self):
        desc = get_income_type("WI010")
        assert "Professional" in desc

    def test_unknown_atc_code_returns_default(self):
        assert get_income_type("UNKNOWN") == "Other income"


class TestFindATCByKeywords:
    """find_atc_by_keywords() tests."""

    def test_professional_services_corporation(self):
        # "professional consulting" matches both WI010 (score 2) and WC010 (score 2)
        # WC should win for corporation supplier type
        result = find_atc_by_keywords("professional consulting", "corporation")
        assert result is not None
        assert result.startswith("WC")

    def test_professional_services_individual(self):
        result = find_atc_by_keywords("professional consulting fee", "individual")
        assert result is not None
        assert result.startswith("WI")

    def test_rent_keywords(self):
        result = find_atc_by_keywords("office rent payment", "individual")
        assert result == "WI030"

    def test_contractor_keywords(self):
        result = find_atc_by_keywords("construction contractor payment", "corporation")
        # WC050 preferred when supplier_type is corporation
        assert result == "WC050"

    def test_transport_keywords(self):
        result = find_atc_by_keywords("delivery and freight charges", "individual")
        assert result == "WI150"

    def test_no_match_returns_none(self):
        result = find_atc_by_keywords("random unrelated text xyz123", "corporation")
        assert result is None

    def test_advertising_keywords(self):
        result = find_atc_by_keywords("advertising and promotion services", "corporation")
        assert result == "WC060"

    def test_insurance_keywords(self):
        result = find_atc_by_keywords("insurance premium payment", "individual")
        assert result == "WI170"


class TestListRates:
    """list_rates() function tests."""

    def test_returns_all_rates(self):
        rates = list_rates()
        assert len(rates) == len(EWT_RATES)

    def test_each_entry_has_required_fields(self):
        rates = list_rates()
        for entry in rates:
            assert "atc_code" in entry
            assert "description" in entry
            assert "rate" in entry
            assert "category" in entry
            assert isinstance(entry["rate"], float)

    def test_rates_are_valid_percentages(self):
        rates = list_rates()
        for entry in rates:
            assert 0 < entry["rate"] <= 1, f"{entry['atc_code']} rate {entry['rate']} out of range"
