"""Unit tests for the tax calculation engine."""

from decimal import Decimal

import pytest

from backend.services.tax_engine import (
    calculate_bir_0619e,
    calculate_bir_1601c,
    calculate_bir_1701,
    calculate_bir_1702,
    calculate_bir_2550m,
    calculate_bir_2550q,
    get_supported_forms,
)


class TestBIR2550M:
    """BIR 2550M (Monthly VAT) calculator tests."""

    def test_basic_calculation(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(sample_sales_data, sample_purchases_data)

        assert result["line_1_vatable_sales"] == "100000"
        assert result["line_2_sales_to_government"] == "50000"
        assert result["line_3_zero_rated_sales"] == "30000"
        assert result["line_4_exempt_sales"] == "20000"
        assert result["line_5_total_sales"] == "200000"

    def test_output_vat_calculation(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(sample_sales_data, sample_purchases_data)

        # Line 6: 100000 * 0.12 = 12000
        assert result["line_6_output_vat"] == "12000.00"
        # Line 6A: 50000 * 0.05 = 2500
        assert result["line_6a_output_vat_government"] == "2500.00"
        # Line 6B: 12000 + 2500 = 14500
        assert result["line_6b_total_output_vat"] == "14500.00"

    def test_input_vat_classification(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(sample_sales_data, sample_purchases_data)

        assert result["line_7_input_vat_goods"] == "4800"
        assert result["line_8_input_vat_capital"] == "600"
        assert result["line_9_input_vat_services"] == "1200"
        assert result["line_10_input_vat_imports"] == "360"
        assert result["line_11_total_input_vat"] == "6960"

    def test_vat_payable(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(sample_sales_data, sample_purchases_data)

        # 14500 - 6960 = 7540
        assert Decimal(result["line_12_vat_payable"]) == Decimal("7540.00")
        assert Decimal(result["line_14_net_vat_payable"]) == Decimal("7540.00")
        assert Decimal(result["line_16_total_amount_due"]) == Decimal("7540.00")

    def test_with_tax_credits(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(
            sample_sales_data, sample_purchases_data, tax_credits="5000"
        )

        # 7540 - 5000 = 2540
        assert Decimal(result["line_13_less_tax_credits"]) == Decimal("5000")
        assert Decimal(result["line_14_net_vat_payable"]) == Decimal("2540.00")

    def test_with_penalties(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(
            sample_sales_data, sample_purchases_data, penalties="1000"
        )

        # 7540 + 1000 = 8540
        assert Decimal(result["line_15_add_penalties"]) == Decimal("1000")
        assert Decimal(result["line_16_total_amount_due"]) == Decimal("8540.00")

    def test_excess_input_vat_creates_tax_credit(self):
        """When input VAT > output VAT, net payable = 0 and credit is carried forward."""
        sales = [{"amount": 10000, "vat_type": "vatable"}]
        purchases = [{"amount": 200000, "vat_amount": 24000, "category": "goods"}]

        result = calculate_bir_2550m(sales, purchases)

        # Output: 10000 * 0.12 = 1200
        # Input: 24000
        # Payable: 1200 - 24000 = -22800
        assert Decimal(result["line_14_net_vat_payable"]) == Decimal("0")
        assert Decimal(result["tax_credit_carried_forward"]) == Decimal("22800.00")

    def test_empty_data(self):
        result = calculate_bir_2550m([], [])

        assert Decimal(result["line_5_total_sales"]) == Decimal("0")
        assert Decimal(result["line_11_total_input_vat"]) == Decimal("0")
        assert Decimal(result["line_16_total_amount_due"]) == Decimal("0")

    def test_input_vat_fallback_to_amount_times_rate(self):
        """When vat_amount is 0, use amount * VAT_RATE as input VAT."""
        purchases = [{"amount": 10000, "vat_amount": 0, "category": "goods"}]
        result = calculate_bir_2550m([], purchases)

        # 10000 * 0.12 = 1200
        assert result["line_7_input_vat_goods"] == "1200.00"

    def test_legacy_compatibility_keys(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550m(sample_sales_data, sample_purchases_data)

        assert result["vatable_sales"] == result["line_1_vatable_sales"]
        assert result["total_sales"] == result["line_5_total_sales"]
        assert result["output_vat"] == result["line_6_output_vat"]
        assert result["total_input_vat"] == result["line_11_total_input_vat"]
        assert result["vat_payable"] == result["line_12_vat_payable"]
        assert result["net_vat_payable"] == result["line_14_net_vat_payable"]


class TestBIR2550Q:
    """BIR 2550Q (Quarterly VAT) — delegates to 2550M."""

    def test_returns_same_calculations(self, sample_sales_data, sample_purchases_data):
        monthly = calculate_bir_2550m(sample_sales_data, sample_purchases_data)
        quarterly = calculate_bir_2550q(sample_sales_data, sample_purchases_data)

        assert quarterly["line_5_total_sales"] == monthly["line_5_total_sales"]
        assert quarterly["line_16_total_amount_due"] == monthly["line_16_total_amount_due"]

    def test_has_form_type_tag(self, sample_sales_data, sample_purchases_data):
        result = calculate_bir_2550q(sample_sales_data, sample_purchases_data)
        assert result["form_type"] == "BIR_2550Q"


class TestBIR1601C:
    """BIR 1601-C (Monthly Withholding Tax on Compensation) tests."""

    def test_basic_calculation(self, sample_compensation_data):
        result = calculate_bir_1601c(sample_compensation_data)

        # Total nontaxable: 100000 + 50000 + 10000 + 20000 + 5000 = 185000
        assert result["line_7_total_nontaxable"] == "185000"
        # Taxable: 500000 - 185000 = 315000
        assert result["line_8_taxable_compensation"] == "315000"
        # Tax remitted: 30000 + 2000 = 32000
        assert result["line_11_total_tax_remitted"] == "32000"
        # Penalties: 0
        assert result["line_15_total_penalties"] == "0"
        # Total due: 32000 + 0 = 32000
        assert result["line_16_total_amount_due"] == "32000"

    def test_nontaxable_exceeds_compensation(self):
        """When nontaxable > total compensation, taxable = 0 (not negative)."""
        data = {
            "total_compensation": "50000",
            "statutory_minimum_wage": "100000",
        }
        result = calculate_bir_1601c(data)

        assert result["line_8_taxable_compensation"] == "0"

    def test_with_penalties(self):
        data = {
            "total_compensation": "100000",
            "tax_withheld": "10000",
            "surcharge": "2500",
            "interest": "1200",
            "compromise": "300",
        }
        result = calculate_bir_1601c(data)

        assert result["line_15_total_penalties"] == "4000"
        # 10000 + 4000 = 14000
        assert result["line_16_total_amount_due"] == "14000"

    def test_empty_data(self):
        result = calculate_bir_1601c({})

        assert result["line_1_total_compensation"] == "0"
        assert result["line_16_total_amount_due"] == "0"


class TestBIR0619E:
    """BIR 0619-E (Monthly EWT Remittance) tests."""

    def test_basic_calculation(self, sample_ewt_data):
        result = calculate_bir_0619e(sample_ewt_data)

        assert result["line_1_total_amount_of_income_payments"] == "1000000"
        assert result["line_2_total_taxes_withheld"] == "50000"
        assert result["line_3_adjustment"] == "5000"
        # Tax still due: 50000 - 5000 = 45000
        assert result["line_4_tax_still_due"] == "45000"
        assert result["line_9_total_amount_due"] == "45000"

    def test_adjustment_exceeds_withheld(self):
        """When adjustment > withheld, tax still due = 0 (not negative)."""
        data = {
            "total_taxes_withheld": "5000",
            "adjustment": "10000",
        }
        result = calculate_bir_0619e(data)

        assert result["line_4_tax_still_due"] == "0"

    def test_with_penalties(self):
        data = {
            "total_taxes_withheld": "50000",
            "surcharge": "12500",
            "interest": "6000",
            "compromise": "1000",
        }
        result = calculate_bir_0619e(data)

        assert result["line_8_total_penalties"] == "19500"
        # 50000 + 19500 = 69500
        assert result["line_9_total_amount_due"] == "69500"

    def test_empty_data(self):
        result = calculate_bir_0619e({})

        assert result["line_1_total_amount_of_income_payments"] == "0"
        assert result["line_9_total_amount_due"] == "0"


class TestBIR1701:
    """BIR 1701 (Annual Income Tax — Individual) tests."""

    def test_basic_osd_calculation(self):
        data = {
            "gross_sales_receipts": "1000000",
            "cost_of_sales": "300000",
            "deduction_method": "osd",
        }
        result = calculate_bir_1701(data)

        assert result["gross_income_from_business"] == "700000"
        assert result["total_gross_income"] == "700000"
        # OSD = 40% of 1,000,000 = 400,000
        assert result["osd_amount"] == "400000.00"
        assert result["total_deductions"] == "400000.00"
        # Net taxable = 700,000 - 400,000 = 300,000
        assert result["net_taxable_income"] == "300000.00"

    def test_graduated_tax_bracket_250k(self):
        """Income <= 250k should be tax-free."""
        data = {"gross_sales_receipts": "250000", "deduction_method": "itemized", "itemized_deductions": "0"}
        result = calculate_bir_1701(data)
        assert result["income_tax_due"] == "0"

    def test_graduated_tax_bracket_400k(self):
        """Income 300k: 15% of (300k - 250k) = 7,500."""
        data = {"gross_sales_receipts": "300000", "deduction_method": "itemized", "itemized_deductions": "0"}
        result = calculate_bir_1701(data)
        assert Decimal(result["income_tax_due"]) == Decimal("7500.00")

    def test_graduated_tax_bracket_800k(self):
        """Income 600k: 22,500 + 20% of (600k - 400k) = 22,500 + 40,000 = 62,500."""
        data = {"gross_sales_receipts": "600000", "deduction_method": "itemized", "itemized_deductions": "0"}
        result = calculate_bir_1701(data)
        assert Decimal(result["income_tax_due"]) == Decimal("62500.00")

    def test_itemized_deductions(self):
        data = {
            "gross_sales_receipts": "1000000",
            "cost_of_sales": "200000",
            "deduction_method": "itemized",
            "itemized_deductions": "150000",
        }
        result = calculate_bir_1701(data)
        # Gross income = 800,000, deductions = 150,000, net = 650,000
        assert result["net_taxable_income"] == "650000"
        assert result["osd_amount"] == "0"

    def test_tax_credits_reduce_payable(self):
        data = {
            "gross_sales_receipts": "500000",
            "deduction_method": "itemized",
            "itemized_deductions": "0",
            "creditable_withholding_tax": "20000",
            "quarterly_payments": "10000",
        }
        result = calculate_bir_1701(data)
        # Tax due on 500k: 22,500 + 20% of (500k - 400k) = 22,500 + 20,000 = 42,500
        assert Decimal(result["income_tax_due"]) == Decimal("42500.00")
        assert result["total_tax_credits"] == "30000"
        # 42,500 - 30,000 = 12,500
        assert Decimal(result["tax_payable"]) == Decimal("12500.00")

    def test_empty_data(self):
        result = calculate_bir_1701({})
        assert result["total_amount_due"] == "0"


class TestBIR1702:
    """BIR 1702 (Annual Income Tax — Corporate) tests."""

    def test_basic_rcit_calculation(self):
        data = {
            "gross_income": "5000000",
            "cost_of_sales": "2000000",
            "deduction_method": "itemized",
            "itemized_deductions": "500000",
        }
        result = calculate_bir_1702(data)

        # Gross profit = 3,000,000
        assert result["gross_profit"] == "3000000"
        # Net taxable = 3,000,000 - 500,000 = 2,500,000
        assert result["net_taxable_income"] == "2500000"
        # RCIT = 25% of 2,500,000 = 625,000
        assert Decimal(result["rcit_amount"]) == Decimal("625000.00")
        # MCIT = 1% of 5,000,000 = 50,000
        assert Decimal(result["mcit_amount"]) == Decimal("50000.00")
        # RCIT > MCIT, so tax due = 625,000
        assert Decimal(result["income_tax_due"]) == Decimal("625000.00")

    def test_sme_rate(self):
        data = {
            "gross_income": "2000000",
            "cost_of_sales": "500000",
            "deduction_method": "itemized",
            "itemized_deductions": "200000",
            "is_sme": "true",
        }
        result = calculate_bir_1702(data)

        # Net taxable = 1,500,000 - 200,000 = 1,300,000
        assert result["net_taxable_income"] == "1300000"
        assert result["rcit_rate"] == "0.20"
        # RCIT = 20% of 1,300,000 = 260,000
        assert Decimal(result["rcit_amount"]) == Decimal("260000.00")

    def test_mcit_exceeds_rcit(self):
        """When MCIT > RCIT, MCIT applies."""
        data = {
            "gross_income": "10000000",
            "cost_of_sales": "8000000",
            "deduction_method": "itemized",
            "itemized_deductions": "1500000",
        }
        result = calculate_bir_1702(data)

        # Gross profit = 2,000,000, Net = 2,000,000 - 1,500,000 = 500,000
        # RCIT = 25% of 500,000 = 125,000
        # MCIT = 1% of 10,000,000 = 100,000
        # RCIT > MCIT, so RCIT applies
        assert Decimal(result["income_tax_due"]) == Decimal("125000.00")

    def test_osd_corporate(self):
        data = {
            "gross_income": "3000000",
            "cost_of_sales": "1000000",
            "deduction_method": "osd",
        }
        result = calculate_bir_1702(data)

        # OSD = 40% of gross income (3,000,000) = 1,200,000
        assert result["osd_amount"] == "1200000.00"
        # Net taxable = 2,000,000 - 1,200,000 = 800,000
        assert result["net_taxable_income"] == "800000.00"

    def test_excess_mcit_carryforward(self):
        data = {
            "gross_income": "5000000",
            "cost_of_sales": "2000000",
            "deduction_method": "itemized",
            "itemized_deductions": "500000",
            "excess_mcit_prior": "50000",
        }
        result = calculate_bir_1702(data)

        # RCIT = 625,000, MCIT = 50,000, RCIT > MCIT so RCIT applies
        # RCIT - excess MCIT = 625,000 - 50,000 = 575,000
        assert Decimal(result["income_tax_due"]) == Decimal("575000.00")

    def test_empty_data(self):
        result = calculate_bir_1702({})
        assert Decimal(result["total_amount_due"]) == Decimal("0")


class TestGetSupportedForms:
    """get_supported_forms() function tests."""

    def test_returns_all_forms(self):
        forms = get_supported_forms()
        assert "BIR_2550M" in forms
        assert "BIR_2550Q" in forms
        assert "BIR_1601C" in forms
        assert "BIR_0619E" in forms

    def test_active_forms_have_active_status(self):
        forms = get_supported_forms()
        assert forms["BIR_2550M"]["status"] == "active"
        assert forms["BIR_2550Q"]["status"] == "active"

    def test_1701_1702_are_active(self):
        forms = get_supported_forms()
        assert forms["BIR_1701"]["status"] == "active"
        assert forms["BIR_1702"]["status"] == "active"

    def test_stub_forms_have_coming_soon_status(self):
        forms = get_supported_forms()
        assert forms["BIR_2316"]["status"] == "coming_soon"

    def test_each_form_has_required_fields(self):
        forms = get_supported_forms()
        for form_type, info in forms.items():
            assert "name" in info, f"{form_type} missing name"
            assert "frequency" in info, f"{form_type} missing frequency"
            assert "status" in info, f"{form_type} missing status"
