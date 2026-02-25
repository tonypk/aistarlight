export interface TargetField {
  value: string;
  label: string;
  group?: string;
}

export interface ReportTypeOption {
  value: string;
  label: string;
}

export const REPORT_TYPES: ReportTypeOption[] = [
  { value: "BIR_2550M", label: "BIR 2550M — Monthly VAT" },
  { value: "BIR_2550Q", label: "BIR 2550Q — Quarterly VAT" },
  { value: "BIR_1601C", label: "BIR 1601C — Withholding on Compensation" },
  { value: "BIR_0619E", label: "BIR 0619E — Expanded Withholding" },
  { value: "Bank_Statement", label: "Bank Statement" },
];

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
