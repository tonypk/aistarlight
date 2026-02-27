export interface TargetField {
  value: string;
  label: string;
  group?: string;
}

export interface ReportTypeOption {
  value: string;
  label: string;
}

// Philippines report types (BIR forms)
export const REPORT_TYPES_PH: ReportTypeOption[] = [
  { value: "BIR_2550M", label: "BIR 2550M — Monthly VAT" },
  { value: "BIR_2550Q", label: "BIR 2550Q — Quarterly VAT" },
  { value: "BIR_1601C", label: "BIR 1601C — Withholding on Compensation" },
  { value: "BIR_0619E", label: "BIR 0619E — Expanded Withholding" },
  { value: "BIR_1701", label: "BIR 1701 — Annual ITR (Individuals)" },
  { value: "BIR_1702", label: "BIR 1702 — Annual ITR (Corporations)" },
  { value: "BIR_2316", label: "BIR 2316 — Certificate of Compensation" },
  { value: "Bank_Statement", label: "Bank Statement" },
];

// Singapore report types (IRAS forms)
export const REPORT_TYPES_SG: ReportTypeOption[] = [
  { value: "IRAS_GST_F5", label: "GST F5 — GST Return" },
  { value: "IRAS_FORM_C", label: "Form C — Corporate Income Tax" },
  { value: "IRAS_FORM_CS", label: "Form C-S — Simplified Corporate Tax" },
  { value: "IRAS_FORM_B", label: "Form B — Individual Income Tax" },
  { value: "IRAS_IR8A", label: "IR8A — Employer Remuneration Return" },
  { value: "IRAS_S45", label: "S45 — Withholding Tax" },
  { value: "IRAS_ECI", label: "ECI — Estimated Chargeable Income" },
  { value: "Bank_Statement", label: "Bank Statement" },
];

// Get report types based on jurisdiction
export function getReportTypes(jurisdiction: string): ReportTypeOption[] {
  return jurisdiction === "SG" ? REPORT_TYPES_SG : REPORT_TYPES_PH;
}

// Default export for backward compatibility
export const REPORT_TYPES = REPORT_TYPES_PH;

// ===========================================================================
// BIR 2550M/2550Q VAT Return — Official Form Fields
// Per BIR Form 2550M/2550Q, RR 16-2005, RR 1-2012
// Organized by: Sales (Output) → Purchases (Input) → VAT Deductions → Details
// ===========================================================================
const vatFields: TargetField[] = [
  // --- 1. Sales / Output VAT (销售/输出 VAT) ---
  { value: "sales_date", label: "Sales Date", group: "Sales (Output)" },
  {
    value: "sales_invoice_number",
    label: "Invoice/Receipt/OR Number",
    group: "Sales (Output)",
  },
  { value: "customer_name", label: "Customer Name", group: "Sales (Output)" },
  { value: "customer_tin", label: "Customer TIN", group: "Sales (Output)" },
  {
    value: "customer_address",
    label: "Customer Address",
    group: "Sales (Output)",
  },
  {
    value: "gross_sales",
    label: "Gross Sales Amount",
    group: "Sales (Output)",
  },
  {
    value: "vatable_sales",
    label: "Vatable Sales/Receipts",
    group: "Sales (Output)",
  },
  {
    value: "sales_to_government",
    label: "Sales to Government",
    group: "Sales (Output)",
  },
  {
    value: "zero_rated_sales",
    label: "Zero-Rated Sales/Receipts",
    group: "Sales (Output)",
  },
  {
    value: "exempt_sales",
    label: "Exempt Sales/Receipts",
    group: "Sales (Output)",
  },
  {
    value: "total_sales",
    label: "Total Sales/Receipts (Exclusive of VAT)",
    group: "Sales (Output)",
  },
  {
    value: "output_tax",
    label: "Output Tax for the Period",
    group: "Sales (Output)",
  },

  // --- 2. Purchases / Input VAT (采购/进项 VAT) ---
  {
    value: "supplier_name",
    label: "Supplier Name",
    group: "Purchases (Input)",
  },
  { value: "supplier_tin", label: "Supplier TIN", group: "Purchases (Input)" },
  {
    value: "supplier_address",
    label: "Supplier Address",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_date",
    label: "Purchase Date",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_invoice_number",
    label: "Purchase Invoice/OR Number",
    group: "Purchases (Input)",
  },
  {
    value: "gross_purchase",
    label: "Gross Purchase Amount",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_capital_goods_below_1m",
    label: "Capital Goods (≤ ₱1M)",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_capital_goods_above_1m",
    label: "Capital Goods (> ₱1M)",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_domestic_goods",
    label: "Domestic Purchase of Goods (non-capital)",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_importation",
    label: "Importation of Goods",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_domestic_services",
    label: "Domestic Purchase of Services",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_non_resident_services",
    label: "Services by Non-Residents",
    group: "Purchases (Input)",
  },
  {
    value: "purchase_not_qualified",
    label: "Purchases Not Qualified for Input Tax",
    group: "Purchases (Input)",
  },
  { value: "input_tax", label: "Input VAT Amount", group: "Purchases (Input)" },
  {
    value: "input_tax_capital_goods",
    label: "Input Tax on Capital Goods",
    group: "Purchases (Input)",
  },
  {
    value: "input_tax_domestic_goods",
    label: "Input Tax on Domestic Goods",
    group: "Purchases (Input)",
  },
  {
    value: "input_tax_importation",
    label: "Input Tax on Imported Goods",
    group: "Purchases (Input)",
  },
  {
    value: "input_tax_domestic_services",
    label: "Input Tax on Domestic Services",
    group: "Purchases (Input)",
  },
  {
    value: "input_tax_non_resident_services",
    label: "Input Tax on Non-Resident Services",
    group: "Purchases (Input)",
  },

  // --- 3. VAT Deductions / Adjustments (VAT 抵扣细分) ---
  {
    value: "input_tax_carried_over",
    label: "Input Tax Carried Over from Previous Period",
    group: "VAT Deductions",
  },
  {
    value: "deferred_input_tax_capital",
    label: "Deferred Input Tax — Capital Goods (over ₱1M)",
    group: "VAT Deductions",
  },
  {
    value: "transitional_input_tax",
    label: "Transitional Input Tax",
    group: "VAT Deductions",
  },
  {
    value: "presumptive_input_tax",
    label: "Presumptive Input Tax",
    group: "VAT Deductions",
  },
  {
    value: "other_input_tax",
    label: "Other Allowable Input Tax",
    group: "VAT Deductions",
  },
  {
    value: "total_allowable_input_tax",
    label: "Total Allowable Input Tax",
    group: "VAT Deductions",
  },

  // --- 4. Common / Detail Fields (通用/明细) ---
  { value: "tin", label: "TIN (Taxpayer ID)", group: "Details" },
  { value: "registered_name", label: "Registered Name", group: "Details" },
  { value: "address", label: "Address", group: "Details" },
  { value: "description", label: "Description / Remarks", group: "Details" },
  { value: "taxable_month", label: "Taxable Month/Quarter", group: "Details" },

  // --- 5. Importation Details (SLI 进口明细) ---
  {
    value: "import_entry_number",
    label: "Import Entry Number",
    group: "Importation (SLI)",
  },
  {
    value: "importation_date",
    label: "Date of Importation",
    group: "Importation (SLI)",
  },
  {
    value: "assessment_date",
    label: "Assessment/Release Date",
    group: "Importation (SLI)",
  },
  {
    value: "country_of_origin",
    label: "Country of Origin",
    group: "Importation (SLI)",
  },
  {
    value: "landed_cost",
    label: "Total Landed Cost",
    group: "Importation (SLI)",
  },
  {
    value: "dutiable_value",
    label: "Dutiable Value",
    group: "Importation (SLI)",
  },
  {
    value: "customs_charges",
    label: "Charges Before Release from Customs",
    group: "Importation (SLI)",
  },
  {
    value: "vat_paid_imports",
    label: "VAT Paid on Imports",
    group: "Importation (SLI)",
  },

  // --- 6. EWT (Expanded Withholding Tax) ---
  { value: "ewt_rate", label: "EWT Rate (%)", group: "EWT" },
  { value: "ewt_amount", label: "EWT Amount", group: "EWT" },
  { value: "atc_code", label: "ATC Code", group: "EWT" },
];

export const TARGET_FIELDS: Record<string, TargetField[]> = {
  BIR_2550M: vatFields,
  BIR_2550Q: vatFields,
  BIR_1601C: [
    { value: "employee_name", label: "Employee Name" },
    { value: "tin", label: "TIN" },
    { value: "total_compensation", label: "Total Compensation" },
    { value: "statutory_minimum_wage", label: "Statutory Minimum Wage" },
    { value: "basic_pay", label: "Basic Pay" },
    { value: "overtime_pay", label: "Overtime Pay" },
    { value: "holiday_pay", label: "Holiday Pay" },
    { value: "nontaxable_13th_month", label: "13th Month (Non-taxable)" },
    { value: "nontaxable_deminimis", label: "De Minimis Benefits" },
    {
      value: "sss_gsis_phic_hdmf",
      label: "SSS/GSIS/PhilHealth/HDMF (combined)",
    },
    { value: "sss", label: "SSS Contribution" },
    { value: "philhealth", label: "PhilHealth Contribution" },
    { value: "pagibig", label: "Pag-IBIG/HDMF Contribution" },
    { value: "other_nontaxable", label: "Other Non-taxable" },
    { value: "taxable_compensation", label: "Taxable Compensation" },
    { value: "tax_withheld", label: "Tax Withheld" },
  ],
  // ===========================================================================
  // BIR 0619-E — Monthly Remittance of Creditable Withholding Tax (Expanded)
  // Transaction-level fields for EWT on supplier/service payments
  // ===========================================================================
  BIR_0619E: [
    // --- Supplier / Payee Info ---
    {
      value: "supplier_name",
      label: "Supplier / Payee Name",
      group: "Payee Info",
    },
    { value: "supplier_tin", label: "Supplier TIN", group: "Payee Info" },
    {
      value: "supplier_address",
      label: "Supplier Address",
      group: "Payee Info",
    },

    // --- Invoice / Transaction Details ---
    {
      value: "invoice_date",
      label: "Invoice / Payment Date",
      group: "Transaction",
    },
    {
      value: "invoice_number",
      label: "Invoice / OR Number",
      group: "Transaction",
    },
    {
      value: "description",
      label: "Description / Remarks",
      group: "Transaction",
    },
    {
      value: "expense_category",
      label: "Expense Category",
      group: "Transaction",
    },

    // --- Withholding Tax Core (per ATC line) ---
    {
      value: "atc_code",
      label: "ATC Code (e.g. WI158, WC160)",
      group: "Withholding Tax",
    },
    {
      value: "nature_of_income",
      label: "Nature of Income Payment",
      group: "Withholding Tax",
    },
    {
      value: "tax_base",
      label: "Tax Base (Gross Amount)",
      group: "Withholding Tax",
    },
    {
      value: "ewt_rate",
      label: "Withholding Tax Rate (%)",
      group: "Withholding Tax",
    },
    {
      value: "tax_withheld",
      label: "Tax Required to be Withheld",
      group: "Withholding Tax",
    },

    // --- Summary (for aggregated data) ---
    {
      value: "total_tax_withheld",
      label: "Total Tax Withheld",
      group: "Summary",
    },
    {
      value: "tax_remitted_previous",
      label: "Tax Remitted in Previous Month(s)",
      group: "Summary",
    },
    { value: "tax_still_due", label: "Tax Still Due", group: "Summary" },
    { value: "penalty_surcharge", label: "Surcharge", group: "Summary" },
    { value: "penalty_interest", label: "Interest", group: "Summary" },
    { value: "penalty_compromise", label: "Compromise", group: "Summary" },
    {
      value: "total_amount_payable",
      label: "Total Amount Payable",
      group: "Summary",
    },
  ],
  // ===========================================================================
  // BIR 1701 — Annual Income Tax Return for Individuals
  // (Self-Employed, Professionals, Mixed Income Earners)
  // Per TRAIN Law (RA 10963), RR 8-2018
  // ===========================================================================
  BIR_1701: [
    // --- 1. Taxpayer Information ---
    { value: "tin", label: "TIN (Taxpayer ID)", group: "Taxpayer Info" },
    {
      value: "registered_name",
      label: "Registered Name",
      group: "Taxpayer Info",
    },
    {
      value: "trade_name",
      label: "Trade/Business Name",
      group: "Taxpayer Info",
    },
    { value: "rdo_code", label: "RDO Code", group: "Taxpayer Info" },
    { value: "address", label: "Address", group: "Taxpayer Info" },
    { value: "zip_code", label: "ZIP Code", group: "Taxpayer Info" },
    {
      value: "taxpayer_type",
      label: "Taxpayer Type (Single Proprietor/Professional/Mixed)",
      group: "Taxpayer Info",
    },
    { value: "taxable_year", label: "Taxable Year", group: "Taxpayer Info" },

    // --- 2. Gross Income (Revenue) ---
    {
      value: "income_date",
      label: "Date of Income/Receipt",
      group: "Gross Income",
    },
    {
      value: "income_source",
      label: "Source/Client Name",
      group: "Gross Income",
    },
    {
      value: "or_si_number",
      label: "OR/SI/Receipt Number",
      group: "Gross Income",
    },
    {
      value: "gross_sales_receipts",
      label: "Gross Sales/Receipts/Revenue/Fees",
      group: "Gross Income",
    },
    {
      value: "sales_returns",
      label: "Sales Returns/Allowances/Discounts",
      group: "Gross Income",
    },
    { value: "net_sales", label: "Net Sales/Receipts", group: "Gross Income" },
    {
      value: "cost_of_sales",
      label: "Cost of Sales/Services",
      group: "Gross Income",
    },
    {
      value: "gross_income",
      label: "Gross Income from Operation",
      group: "Gross Income",
    },
    {
      value: "other_taxable_income",
      label: "Other Taxable Income (Non-Operating)",
      group: "Gross Income",
    },
    {
      value: "compensation_income",
      label: "Compensation Income (Mixed Income Earner)",
      group: "Gross Income",
    },
    {
      value: "total_gross_income",
      label: "Total Gross Income",
      group: "Gross Income",
    },

    // --- 3. Allowable Deductions ---
    { value: "expense_date", label: "Expense Date", group: "Deductions" },
    {
      value: "expense_description",
      label: "Expense Description",
      group: "Deductions",
    },
    {
      value: "expense_category",
      label: "Expense Category/Account",
      group: "Deductions",
    },
    { value: "expense_amount", label: "Expense Amount", group: "Deductions" },
    {
      value: "deduction_method",
      label: "Deduction Method (OSD/Itemized)",
      group: "Deductions",
    },
    {
      value: "optional_standard_deduction",
      label: "OSD (40% of Gross Sales/Receipts)",
      group: "Deductions",
    },
    {
      value: "salaries_wages",
      label: "Salaries, Wages & Benefits",
      group: "Deductions",
    },
    { value: "rent_expense", label: "Rent/Lease", group: "Deductions" },
    {
      value: "depreciation",
      label: "Depreciation/Amortization",
      group: "Deductions",
    },
    {
      value: "utilities",
      label: "Utilities (Light, Water, Phone)",
      group: "Deductions",
    },
    { value: "taxes_licenses", label: "Taxes & Licenses", group: "Deductions" },
    { value: "insurance", label: "Insurance", group: "Deductions" },
    {
      value: "professional_fees",
      label: "Professional Fees",
      group: "Deductions",
    },
    {
      value: "repairs_maintenance",
      label: "Repairs & Maintenance",
      group: "Deductions",
    },
    {
      value: "representation",
      label: "Representation & Entertainment",
      group: "Deductions",
    },
    {
      value: "transportation",
      label: "Transportation & Travel",
      group: "Deductions",
    },
    { value: "communication", label: "Communication", group: "Deductions" },
    { value: "supplies", label: "Supplies", group: "Deductions" },
    { value: "bad_debts", label: "Bad Debts", group: "Deductions" },
    {
      value: "interest_expense",
      label: "Interest Expense",
      group: "Deductions",
    },
    {
      value: "other_deductions",
      label: "Other Deductions",
      group: "Deductions",
    },
    {
      value: "total_deductions",
      label: "Total Allowable Deductions",
      group: "Deductions",
    },

    // --- 4. Tax Computation ---
    {
      value: "taxable_income",
      label: "Net Taxable Income",
      group: "Tax Computation",
    },
    {
      value: "income_tax_due",
      label: "Income Tax Due",
      group: "Tax Computation",
    },

    // --- 5. Tax Credits & Payment ---
    {
      value: "prior_year_excess_credits",
      label: "Prior Year's Excess Credits",
      group: "Tax Credits",
    },
    {
      value: "quarterly_tax_payments",
      label: "Quarterly Tax Payments (1701Q)",
      group: "Tax Credits",
    },
    {
      value: "creditable_withholding_tax",
      label: "Creditable Withholding Tax (BIR 2307)",
      group: "Tax Credits",
    },
    {
      value: "tax_withheld_per_2316",
      label: "Tax Withheld per BIR 2316",
      group: "Tax Credits",
    },
    {
      value: "foreign_tax_credits",
      label: "Foreign Tax Credits",
      group: "Tax Credits",
    },
    {
      value: "other_tax_credits",
      label: "Other Tax Credits/Payments",
      group: "Tax Credits",
    },
    {
      value: "total_tax_credits",
      label: "Total Tax Credits/Payments",
      group: "Tax Credits",
    },
    {
      value: "tax_payable",
      label: "Tax Payable/(Overpayment)",
      group: "Tax Credits",
    },
    { value: "penalty_surcharge", label: "Surcharge", group: "Tax Credits" },
    { value: "penalty_interest", label: "Interest", group: "Tax Credits" },
    { value: "penalty_compromise", label: "Compromise", group: "Tax Credits" },
    {
      value: "total_amount_payable",
      label: "Total Amount Payable",
      group: "Tax Credits",
    },
  ],

  // ===========================================================================
  // BIR 1702 — Annual Income Tax Return for Corporations/Partnerships
  // Per TRAIN Law (RA 10963), CREATE Law (RA 11534)
  // Regular Tax: 25% (20% for MSME ≤ ₱5M net income & ≤ ₱100M assets)
  // MCIT: 1% (until 2023-06-30) / 2% thereafter
  // ===========================================================================
  BIR_1702: [
    // --- 1. Corporate Information ---
    { value: "tin", label: "TIN (Taxpayer ID)", group: "Corporate Info" },
    {
      value: "registered_name",
      label: "Registered Name",
      group: "Corporate Info",
    },
    {
      value: "trade_name",
      label: "Trade/Business Name",
      group: "Corporate Info",
    },
    { value: "rdo_code", label: "RDO Code", group: "Corporate Info" },
    { value: "address", label: "Registered Address", group: "Corporate Info" },
    { value: "zip_code", label: "ZIP Code", group: "Corporate Info" },
    {
      value: "sec_registration",
      label: "SEC/DTI Registration No.",
      group: "Corporate Info",
    },
    {
      value: "industry_classification",
      label: "PSIC/Industry Classification",
      group: "Corporate Info",
    },
    {
      value: "taxable_year",
      label: "Taxable Year/Fiscal Year",
      group: "Corporate Info",
    },
    {
      value: "tax_regime",
      label: "Tax Regime (Regular/Special/Exempt)",
      group: "Corporate Info",
    },

    // --- 2. Revenue / Gross Income ---
    {
      value: "revenue_date",
      label: "Revenue/Transaction Date",
      group: "Revenue",
    },
    {
      value: "revenue_source",
      label: "Revenue Source/Client Name",
      group: "Revenue",
    },
    { value: "or_si_number", label: "OR/SI/Invoice Number", group: "Revenue" },
    {
      value: "gross_sales_receipts",
      label: "Gross Sales/Receipts/Revenue",
      group: "Revenue",
    },
    {
      value: "sales_returns",
      label: "Sales Returns/Allowances/Discounts",
      group: "Revenue",
    },
    { value: "net_sales", label: "Net Sales/Revenue", group: "Revenue" },
    {
      value: "cost_of_sales",
      label: "Cost of Sales/Services",
      group: "Revenue",
    },
    {
      value: "gross_income",
      label: "Gross Income from Operations",
      group: "Revenue",
    },
    {
      value: "other_income",
      label: "Other Income (Non-Operating)",
      group: "Revenue",
    },
    {
      value: "total_gross_income",
      label: "Total Gross Income",
      group: "Revenue",
    },

    // --- 3. Operating Expenses ---
    {
      value: "expense_date",
      label: "Expense Date",
      group: "Operating Expenses",
    },
    {
      value: "expense_description",
      label: "Expense Description",
      group: "Operating Expenses",
    },
    {
      value: "expense_category",
      label: "Expense Category/Account",
      group: "Operating Expenses",
    },
    {
      value: "expense_amount",
      label: "Expense Amount",
      group: "Operating Expenses",
    },
    {
      value: "salaries_wages",
      label: "Salaries, Wages & Employee Benefits",
      group: "Operating Expenses",
    },
    { value: "rent_expense", label: "Rent/Lease", group: "Operating Expenses" },
    {
      value: "depreciation",
      label: "Depreciation/Amortization",
      group: "Operating Expenses",
    },
    { value: "utilities", label: "Utilities", group: "Operating Expenses" },
    {
      value: "taxes_licenses",
      label: "Taxes & Licenses",
      group: "Operating Expenses",
    },
    { value: "insurance", label: "Insurance", group: "Operating Expenses" },
    {
      value: "professional_fees",
      label: "Professional/Outside Service Fees",
      group: "Operating Expenses",
    },
    {
      value: "repairs_maintenance",
      label: "Repairs & Maintenance",
      group: "Operating Expenses",
    },
    {
      value: "representation",
      label: "Representation & Entertainment",
      group: "Operating Expenses",
    },
    {
      value: "transportation",
      label: "Transportation & Travel",
      group: "Operating Expenses",
    },
    {
      value: "communication",
      label: "Communication",
      group: "Operating Expenses",
    },
    { value: "supplies", label: "Supplies", group: "Operating Expenses" },
    { value: "bad_debts", label: "Bad Debts", group: "Operating Expenses" },
    {
      value: "interest_expense",
      label: "Interest Expense",
      group: "Operating Expenses",
    },
    {
      value: "charitable_contributions",
      label: "Charitable Contributions",
      group: "Operating Expenses",
    },
    {
      value: "research_development",
      label: "Research & Development",
      group: "Operating Expenses",
    },
    {
      value: "other_deductions",
      label: "Other Deductions",
      group: "Operating Expenses",
    },
    {
      value: "total_operating_expenses",
      label: "Total Operating Expenses",
      group: "Operating Expenses",
    },

    // --- 4. Tax Computation ---
    {
      value: "net_income_before_tax",
      label: "Net Income Before Tax",
      group: "Tax Computation",
    },
    {
      value: "taxable_income",
      label: "Net Taxable Income",
      group: "Tax Computation",
    },
    {
      value: "regular_income_tax",
      label: "Regular Income Tax (25%/20%)",
      group: "Tax Computation",
    },
    {
      value: "mcit",
      label: "MCIT (Minimum Corporate Income Tax)",
      group: "Tax Computation",
    },
    {
      value: "income_tax_due",
      label: "Income Tax Due (Higher of Regular/MCIT)",
      group: "Tax Computation",
    },

    // --- 5. Tax Credits & Payment ---
    {
      value: "prior_year_excess_credits",
      label: "Prior Year's Excess Credits",
      group: "Tax Credits",
    },
    {
      value: "excess_mcit",
      label: "Excess MCIT from Prior Year(s)",
      group: "Tax Credits",
    },
    {
      value: "quarterly_tax_payments",
      label: "Quarterly Tax Payments (1702Q)",
      group: "Tax Credits",
    },
    {
      value: "creditable_withholding_tax",
      label: "Creditable Withholding Tax (BIR 2307)",
      group: "Tax Credits",
    },
    {
      value: "foreign_tax_credits",
      label: "Foreign Tax Credits",
      group: "Tax Credits",
    },
    {
      value: "other_tax_credits",
      label: "Other Tax Credits/Payments",
      group: "Tax Credits",
    },
    {
      value: "total_tax_credits",
      label: "Total Tax Credits/Payments",
      group: "Tax Credits",
    },
    {
      value: "tax_payable",
      label: "Tax Payable/(Overpayment)",
      group: "Tax Credits",
    },
    { value: "penalty_surcharge", label: "Surcharge", group: "Tax Credits" },
    { value: "penalty_interest", label: "Interest", group: "Tax Credits" },
    { value: "penalty_compromise", label: "Compromise", group: "Tax Credits" },
    {
      value: "total_amount_payable",
      label: "Total Amount Payable",
      group: "Tax Credits",
    },
  ],

  // ===========================================================================
  // BIR 2316 — Certificate of Compensation Payment/Tax Withheld
  // Annual certificate issued by employer to employee
  // Per RR 11-2018, TRAIN Law (RA 10963)
  // ===========================================================================
  BIR_2316: [
    // --- 1. Employer Information ---
    { value: "employer_tin", label: "Employer TIN", group: "Employer Info" },
    { value: "employer_name", label: "Employer Name", group: "Employer Info" },
    {
      value: "employer_address",
      label: "Employer Address",
      group: "Employer Info",
    },
    {
      value: "employer_zip_code",
      label: "Employer ZIP Code",
      group: "Employer Info",
    },
    { value: "rdo_code", label: "RDO Code", group: "Employer Info" },

    // --- 2. Employee Information ---
    { value: "employee_tin", label: "Employee TIN", group: "Employee Info" },
    { value: "employee_name", label: "Employee Name", group: "Employee Info" },
    {
      value: "employee_address",
      label: "Employee Address",
      group: "Employee Info",
    },
    {
      value: "employee_zip_code",
      label: "Employee ZIP Code",
      group: "Employee Info",
    },
    { value: "date_of_birth", label: "Date of Birth", group: "Employee Info" },
    { value: "nationality", label: "Nationality", group: "Employee Info" },
    { value: "civil_status", label: "Civil Status", group: "Employee Info" },
    {
      value: "employment_status",
      label: "Employment Status (Regular/Contractual/MWE)",
      group: "Employee Info",
    },
    { value: "date_hired", label: "Date Hired", group: "Employee Info" },
    {
      value: "date_separated",
      label: "Date of Separation (if applicable)",
      group: "Employee Info",
    },

    // --- 3. Gross Compensation (Present Employer) ---
    {
      value: "basic_salary",
      label: "Basic Salary (Annual)",
      group: "Compensation",
    },
    { value: "overtime_pay", label: "Overtime Pay", group: "Compensation" },
    { value: "holiday_pay", label: "Holiday Pay", group: "Compensation" },
    {
      value: "night_differential",
      label: "Night Shift Differential",
      group: "Compensation",
    },
    { value: "hazard_pay", label: "Hazard Pay", group: "Compensation" },
    {
      value: "thirteenth_month_pay",
      label: "13th Month Pay",
      group: "Compensation",
    },
    {
      value: "other_benefits",
      label: "Other Benefits/Bonuses",
      group: "Compensation",
    },
    {
      value: "gross_compensation",
      label: "Gross Compensation Income",
      group: "Compensation",
    },

    // --- 4. Non-Taxable Compensation ---
    {
      value: "nontaxable_13th_month",
      label: "13th Month Pay & Other Benefits (≤ ₱90K)",
      group: "Non-Taxable",
    },
    {
      value: "nontaxable_deminimis",
      label: "De Minimis Benefits",
      group: "Non-Taxable",
    },
    {
      value: "sss_gsis_contribution",
      label: "SSS/GSIS Contribution",
      group: "Non-Taxable",
    },
    {
      value: "philhealth_contribution",
      label: "PhilHealth Contribution",
      group: "Non-Taxable",
    },
    {
      value: "pagibig_contribution",
      label: "Pag-IBIG/HDMF Contribution",
      group: "Non-Taxable",
    },
    { value: "union_dues", label: "Union Dues", group: "Non-Taxable" },
    {
      value: "other_nontaxable",
      label: "Other Non-Taxable Compensation",
      group: "Non-Taxable",
    },
    {
      value: "total_nontaxable",
      label: "Total Non-Taxable Compensation",
      group: "Non-Taxable",
    },

    // --- 5. Taxable Compensation & Tax ---
    {
      value: "taxable_compensation",
      label: "Net Taxable Compensation",
      group: "Tax Computation",
    },
    {
      value: "income_tax_due",
      label: "Income Tax Due",
      group: "Tax Computation",
    },
    {
      value: "tax_withheld_jan_nov",
      label: "Tax Withheld (January–November)",
      group: "Tax Computation",
    },
    {
      value: "tax_withheld_december",
      label: "Tax Withheld (December — Adjustment Month)",
      group: "Tax Computation",
    },
    {
      value: "total_tax_withheld",
      label: "Total Tax Withheld for the Year",
      group: "Tax Computation",
    },
    {
      value: "tax_adjustment",
      label: "Year-End Tax Adjustment (Over/Under)",
      group: "Tax Computation",
    },

    // --- 6. Previous Employer (if applicable) ---
    {
      value: "prev_employer_tin",
      label: "Previous Employer TIN",
      group: "Previous Employer",
    },
    {
      value: "prev_employer_name",
      label: "Previous Employer Name",
      group: "Previous Employer",
    },
    {
      value: "prev_gross_compensation",
      label: "Previous Employer Gross Compensation",
      group: "Previous Employer",
    },
    {
      value: "prev_nontaxable",
      label: "Previous Employer Non-Taxable",
      group: "Previous Employer",
    },
    {
      value: "prev_taxable_compensation",
      label: "Previous Employer Taxable Compensation",
      group: "Previous Employer",
    },
    {
      value: "prev_tax_withheld",
      label: "Previous Employer Tax Withheld",
      group: "Previous Employer",
    },
  ],

  // ===========================================================================
  // IRAS GST F5 — Goods and Services Tax Return (Singapore)
  // Boxes 1-11 per IRAS GST F5 form
  // ===========================================================================
  IRAS_GST_F5: [
    { value: "sales_date", label: "Sales/Supply Date", group: "Supplies" },
    { value: "invoice_number", label: "Invoice Number", group: "Supplies" },
    { value: "customer_name", label: "Customer Name", group: "Supplies" },
    {
      value: "standard_rated_supplies",
      label: "Standard-Rated Supplies",
      group: "Supplies",
    },
    {
      value: "zero_rated_supplies",
      label: "Zero-Rated Supplies",
      group: "Supplies",
    },
    { value: "exempt_supplies", label: "Exempt Supplies", group: "Supplies" },
    {
      value: "total_supplies",
      label: "Total Value of Supplies",
      group: "Supplies",
    },
    {
      value: "supply_type",
      label: "Supply Type (standard/zero/exempt)",
      group: "Supplies",
    },
    { value: "purchase_date", label: "Purchase Date", group: "Purchases" },
    { value: "supplier_name", label: "Supplier Name", group: "Purchases" },
    {
      value: "taxable_purchases",
      label: "Taxable Purchases",
      group: "Purchases",
    },
    {
      value: "gst_amount",
      label: "GST Amount (Input Tax)",
      group: "Purchases",
    },
    {
      value: "input_tax_claimed",
      label: "Input Tax Claimed",
      group: "Purchases",
    },
    {
      value: "bad_debt_relief",
      label: "Bad Debt Relief",
      group: "Adjustments",
    },
    {
      value: "pre_registration_input_tax",
      label: "Pre-Registration Input Tax",
      group: "Adjustments",
    },
    {
      value: "tourist_refund",
      label: "Tourist Refund Scheme",
      group: "Adjustments",
    },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "period", label: "Accounting Period", group: "Details" },
  ],

  // ===========================================================================
  // IRAS Form C — Corporate Income Tax (Singapore)
  // Full form for companies with revenue > S$5M
  // ===========================================================================
  IRAS_FORM_C: [
    { value: "revenue", label: "Revenue", group: "Income" },
    { value: "cost_of_sales", label: "Cost of Sales", group: "Income" },
    { value: "other_income", label: "Other Income", group: "Income" },
    {
      value: "operating_expenses",
      label: "Operating Expenses",
      group: "Expenses",
    },
    {
      value: "non_deductible_expenses",
      label: "Non-Deductible Expenses",
      group: "Expenses",
    },
    {
      value: "capital_allowances",
      label: "Capital Allowances",
      group: "Deductions",
    },
    { value: "donations", label: "Qualifying Donations", group: "Deductions" },
    {
      value: "losses_carried_forward",
      label: "Losses Carried Forward",
      group: "Deductions",
    },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "period", label: "Year of Assessment", group: "Details" },
  ],

  // ===========================================================================
  // IRAS Form C-S — Simplified Corporate Tax (Singapore)
  // For companies with revenue <= S$5M
  // ===========================================================================
  IRAS_FORM_CS: [
    { value: "revenue", label: "Revenue", group: "Income" },
    { value: "total_expenses", label: "Total Expenses", group: "Expenses" },
    {
      value: "tax_adjustments",
      label: "Tax Adjustments",
      group: "Adjustments",
    },
    {
      value: "capital_allowances",
      label: "Capital Allowances",
      group: "Deductions",
    },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "period", label: "Year of Assessment", group: "Details" },
  ],

  // ===========================================================================
  // IRAS Form B — Individual Income Tax (Singapore)
  // Progressive tax brackets 0% - 24%
  // ===========================================================================
  IRAS_FORM_B: [
    { value: "employment_income", label: "Employment Income", group: "Income" },
    {
      value: "trade_income",
      label: "Trade / Business Income",
      group: "Income",
    },
    { value: "rental_income", label: "Rental Income", group: "Income" },
    { value: "other_income", label: "Other Income", group: "Income" },
    {
      value: "total_reliefs",
      label: "Total Personal Reliefs",
      group: "Reliefs",
    },
    { value: "donations", label: "Qualifying Donations", group: "Reliefs" },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN / NRIC", group: "Details" },
    { value: "period", label: "Year of Assessment", group: "Details" },
  ],

  // ===========================================================================
  // IRAS IR8A — Return of Employee's Remuneration (Singapore)
  // Employer files for each employee
  // ===========================================================================
  IRAS_IR8A: [
    { value: "employee_name", label: "Employee Name", group: "Employee Info" },
    {
      value: "employee_id",
      label: "Employee ID / NRIC",
      group: "Employee Info",
    },
    {
      value: "gross_salary",
      label: "Gross Salary / Wages",
      group: "Remuneration",
    },
    { value: "bonus", label: "Bonus", group: "Remuneration" },
    { value: "director_fees", label: "Director Fees", group: "Remuneration" },
    {
      value: "other_allowances",
      label: "Other Allowances",
      group: "Remuneration",
    },
    {
      value: "benefits_in_kind",
      label: "Benefits-in-Kind",
      group: "Remuneration",
    },
    { value: "employer_cpf", label: "Employer CPF Contribution", group: "CPF" },
    { value: "employee_cpf", label: "Employee CPF Contribution", group: "CPF" },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "period", label: "Year of Assessment", group: "Details" },
  ],

  // ===========================================================================
  // IRAS S45 — Withholding Tax on Non-Resident Payments (Singapore)
  // Payer withholds tax on payments to non-residents
  // ===========================================================================
  IRAS_S45: [
    {
      value: "payee_name",
      label: "Payee / Non-Resident Name",
      group: "Payee Info",
    },
    {
      value: "payee_country",
      label: "Payee Country of Residence",
      group: "Payee Info",
    },
    { value: "payment_date", label: "Payment Date", group: "Payment" },
    { value: "payment_amount", label: "Payment Amount", group: "Payment" },
    {
      value: "income_type",
      label: "Income Type (INT/ROY/TECH/DIR/RENT/SFC)",
      group: "Payment",
    },
    {
      value: "custom_rate",
      label: "Treaty Rate (if applicable)",
      group: "Payment",
    },
    { value: "description", label: "Description / Remarks", group: "Details" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "period", label: "Payment Period", group: "Details" },
  ],

  IRAS_ECI: [
    { value: "revenue", label: "Revenue / Turnover", group: "Income" },
    { value: "other_income", label: "Other Income", group: "Income" },
    {
      value: "total_expenses",
      label: "Total Allowable Expenses",
      group: "Expenses",
    },
    {
      value: "adjusted_profit",
      label: "Adjusted Profit After Deductions",
      group: "Income",
    },
    {
      value: "capital_allowances",
      label: "Capital Allowances",
      group: "Deductions",
    },
    {
      value: "trade_losses",
      label: "Trade Losses Brought Forward",
      group: "Deductions",
    },
    { value: "donations", label: "Approved Donations", group: "Deductions" },
    {
      value: "estimated_chargeable_income",
      label: "Estimated Chargeable Income",
      group: "Tax",
    },
    { value: "estimated_tax", label: "Estimated Tax Payable", group: "Tax" },
    { value: "uen", label: "UEN", group: "Details" },
    { value: "company_name", label: "Company Name", group: "Details" },
    {
      value: "financial_year_end",
      label: "Financial Year End",
      group: "Details",
    },
  ],

  Bank_Statement: [
    { value: "date", label: "Date" },
    { value: "description", label: "Description" },
    { value: "amount", label: "Amount" },
    { value: "debit", label: "Debit" },
    { value: "credit", label: "Credit" },
    { value: "reference", label: "Reference" },
    { value: "balance", label: "Balance" },
  ],
};
