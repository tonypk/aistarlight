"""BIR Form 2550M template definition and field mapping.

This defines the official structure of BIR Form 2550M for reference
and validation purposes.
"""

BIR_2550M_SECTIONS = {
    "taxpayer_info": {
        "tin": {"label": "TIN", "required": True},
        "rdo_code": {"label": "RDO Code", "required": True},
        "company_name": {"label": "Taxpayer's Name", "required": True},
        "address": {"label": "Registered Address", "required": True},
        "zip_code": {"label": "Zip Code", "required": True},
        "contact": {"label": "Contact Number", "required": False},
        "email": {"label": "Email Address", "required": False},
        "period": {"label": "For the Month of", "required": True},
    },
    "part1_sales": {
        "line1_vatable_sales": {
            "label": "Vatable Sales/Receipts",
            "line": 1,
        },
        "line2_exempt_sales": {
            "label": "Sales to Government",
            "line": 2,
        },
        "line3_zero_rated_sales": {
            "label": "Zero-Rated Sales",
            "line": 3,
        },
        "line4_exempt_sales_other": {
            "label": "Exempt Sales",
            "line": 4,
        },
        "line5_total_sales": {
            "label": "Total Sales/Receipts (Sum of Lines 1 to 4)",
            "line": 5,
            "computed": True,
        },
    },
    "part2_output_vat": {
        "line6_output_vat": {
            "label": "Output VAT (Line 1 x 12%)",
            "line": 6,
            "computed": True,
        },
    },
    "part3_input_vat": {
        "line7_input_vat_purchases": {
            "label": "Input VAT on Purchases of Goods Other than Capital Goods",
            "line": 7,
        },
        "line8_input_vat_capital": {
            "label": "Input VAT on Purchases of Capital Goods",
            "line": 8,
        },
        "line9_input_vat_services": {
            "label": "Input VAT on Purchases of Services",
            "line": 9,
        },
        "line10_input_vat_imports": {
            "label": "Input VAT on Importation of Goods Other than Capital Goods",
            "line": 10,
        },
        "line11_total_input_vat": {
            "label": "Total Input VAT (Sum of Lines 7 to 10)",
            "line": 11,
            "computed": True,
        },
    },
    "part4_tax_payable": {
        "line12_vat_payable": {
            "label": "VAT Payable (Line 6 minus Line 11)",
            "line": 12,
            "computed": True,
        },
        "line13_tax_credit": {
            "label": "Less: Tax Credit/Payments",
            "line": 13,
        },
        "line14_net_vat": {
            "label": "Net VAT Payable (Line 12 minus Line 13)",
            "line": 14,
            "computed": True,
        },
        "line15_penalties": {
            "label": "Add: Penalties",
            "line": 15,
        },
        "line16_total_amount_due": {
            "label": "Total Amount Due (Line 14 plus Line 15)",
            "line": 16,
            "computed": True,
        },
    },
}
