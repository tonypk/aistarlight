"""Unit tests for report editor recalculation functions."""

from decimal import Decimal

from backend.services.report_editor import (
    recalculate_bir_0619e,
    recalculate_bir_1601c,
    recalculate_bir_2550m,
)


class TestRecalculateBIR2550M:
    """recalculate_bir_2550m() tests."""

    def test_recalculates_totals_from_line_items(self):
        data = {
            "line_1_vatable_sales": "100000",
            "line_2_sales_to_government": "50000",
            "line_3_zero_rated_sales": "30000",
            "line_4_exempt_sales": "20000",
            "line_7_input_vat_goods": "4800",
            "line_8_input_vat_capital": "600",
            "line_9_input_vat_services": "1200",
            "line_10_input_vat_imports": "360",
            "line_13_less_tax_credits": "0",
            "line_15_add_penalties": "0",
        }
        result = recalculate_bir_2550m(data)

        assert result["line_5_total_sales"] == "200000"
        assert result["line_6_output_vat"] == "12000.00"
        assert result["line_6a_output_vat_government"] == "2500.00"
        assert result["line_6b_total_output_vat"] == "14500.00"
        assert result["line_11_total_input_vat"] == "6960"
        assert Decimal(result["line_12_vat_payable"]) == Decimal("7540.00")
        assert Decimal(result["line_14_net_vat_payable"]) == Decimal("7540.00")
        assert Decimal(result["line_16_total_amount_due"]) == Decimal("7540.00")

    def test_does_not_mutate_input(self):
        data = {"line_1_vatable_sales": "100000"}
        original = dict(data)
        recalculate_bir_2550m(data)

        assert data == original

    def test_handles_missing_fields_as_zero(self):
        result = recalculate_bir_2550m({})

        assert Decimal(result["line_5_total_sales"]) == Decimal("0")
        assert Decimal(result["line_16_total_amount_due"]) == Decimal("0")

    def test_override_single_field_recalculates_chain(self):
        """Changing one input field cascades through all dependent fields."""
        data = {
            "line_1_vatable_sales": "200000",  # changed from 100000
            "line_2_sales_to_government": "0",
            "line_3_zero_rated_sales": "0",
            "line_4_exempt_sales": "0",
        }
        result = recalculate_bir_2550m(data)

        assert result["line_5_total_sales"] == "200000"
        assert result["line_6_output_vat"] == "24000.00"
        assert result["line_6b_total_output_vat"] == "24000.00"

    def test_tax_credit_carried_forward(self):
        """When input > output, tax credit is carried forward."""
        data = {
            "line_1_vatable_sales": "10000",
            "line_7_input_vat_goods": "50000",
        }
        result = recalculate_bir_2550m(data)

        # Output: 1200, Input: 50000, Payable: -48800
        assert Decimal(result["line_14_net_vat_payable"]) == Decimal("0")
        assert Decimal(result["tax_credit_carried_forward"]) == Decimal("48800.00")

    def test_legacy_keys_updated(self):
        data = {"line_1_vatable_sales": "100000"}
        result = recalculate_bir_2550m(data)

        assert result["vatable_sales"] == "100000"
        assert result["total_sales"] == result["line_5_total_sales"]
        assert result["output_vat"] == result["line_6_output_vat"]


class TestRecalculateBIR1601C:
    """recalculate_bir_1601c() tests."""

    def test_basic_recalculation(self):
        data = {
            "line_1_total_compensation": "500000",
            "line_2_statutory_minimum_wage": "100000",
            "line_3_nontaxable_13th_month": "50000",
            "line_4_nontaxable_deminimis": "10000",
            "line_5_sss_gsis_phic_hdmf": "20000",
            "line_6_other_nontaxable": "5000",
            "line_9_tax_withheld": "30000",
            "line_10_adjustment": "2000",
            "line_12_surcharge": "0",
            "line_13_interest": "0",
            "line_14_compromise": "0",
        }
        result = recalculate_bir_1601c(data)

        assert result["line_7_total_nontaxable"] == "185000"
        assert result["line_8_taxable_compensation"] == "315000"
        assert result["line_11_total_tax_remitted"] == "32000"
        assert result["line_15_total_penalties"] == "0"
        assert result["line_16_total_amount_due"] == "32000"

    def test_taxable_comp_floored_at_zero(self):
        data = {
            "line_1_total_compensation": "50000",
            "line_2_statutory_minimum_wage": "100000",
        }
        result = recalculate_bir_1601c(data)
        assert result["line_8_taxable_compensation"] == "0"

    def test_does_not_mutate_input(self):
        data = {"line_1_total_compensation": "100000"}
        original = dict(data)
        recalculate_bir_1601c(data)
        assert data == original


class TestRecalculateBIR0619E:
    """recalculate_bir_0619e() tests."""

    def test_basic_recalculation(self):
        data = {
            "line_2_total_taxes_withheld": "50000",
            "line_3_adjustment": "5000",
            "line_5_surcharge": "1000",
            "line_6_interest": "500",
            "line_7_compromise": "200",
        }
        result = recalculate_bir_0619e(data)

        assert result["line_4_tax_still_due"] == "45000"
        assert result["line_8_total_penalties"] == "1700"
        assert result["line_9_total_amount_due"] == "46700"

    def test_tax_still_due_floored_at_zero(self):
        data = {
            "line_2_total_taxes_withheld": "1000",
            "line_3_adjustment": "5000",
        }
        result = recalculate_bir_0619e(data)
        assert result["line_4_tax_still_due"] == "0"

    def test_does_not_mutate_input(self):
        data = {"line_2_total_taxes_withheld": "50000"}
        original = dict(data)
        recalculate_bir_0619e(data)
        assert data == original
