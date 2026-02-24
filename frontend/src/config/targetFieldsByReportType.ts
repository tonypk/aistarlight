export interface TargetField {
  value: string
  label: string
  group?: string
}

export interface ReportTypeOption {
  value: string
  label: string
}

export const REPORT_TYPES: ReportTypeOption[] = [
  { value: 'BIR_2550M', label: 'BIR 2550M — Monthly VAT' },
  { value: 'BIR_2550Q', label: 'BIR 2550Q — Quarterly VAT' },
  { value: 'BIR_1601C', label: 'BIR 1601C — Withholding on Compensation' },
  { value: 'BIR_0619E', label: 'BIR 0619E — Expanded Withholding' },
  { value: 'Bank_Statement', label: 'Bank Statement' },
]

// BIR 2550M/Q fields cover: VAT return + SLS (Sales) + SLP (Purchases) + SLI (Importations)
// Per RR 16-2005 Section 4.114-3, as amended by RR 1-2012
const vatFields: TargetField[] = [
  // --- Common / General ---
  { value: 'date', label: 'Date', group: 'General' },
  { value: 'taxable_month', label: 'Taxable Month', group: 'General' },
  { value: 'description', label: 'Description', group: 'General' },
  { value: 'tin', label: 'TIN (Taxpayer ID)', group: 'General' },
  { value: 'registered_name', label: 'Registered Name', group: 'General' },
  { value: 'supplier_name', label: 'Supplier/Customer Name', group: 'General' },
  { value: 'address', label: 'Address', group: 'General' },
  { value: 'invoice_number', label: 'Invoice/Receipt/OR Number', group: 'General' },

  // --- Amount Fields ---
  { value: 'amount', label: 'Amount', group: 'Amounts' },
  { value: 'gross_amount', label: 'Gross Amount (VAT inclusive)', group: 'Amounts' },
  { value: 'vat_amount', label: 'VAT Amount', group: 'Amounts' },
  { value: 'taxable_amount', label: 'Taxable Amount (VAT exclusive)', group: 'Amounts' },
  { value: 'exempt_amount', label: 'Exempt Amount', group: 'Amounts' },
  { value: 'zero_rated_amount', label: 'Zero-Rated Amount', group: 'Amounts' },

  // --- VAT Classification ---
  { value: 'vat_type', label: 'VAT Type (vatable/exempt/zero_rated/government)', group: 'Classification' },
  { value: 'category', label: 'Category (goods/services/capital/imports)', group: 'Classification' },

  // --- SLP: Summary List of Purchases (RR 16-2005 Sec 4.114-3) ---
  { value: 'gross_purchase', label: 'Gross Purchase Amount', group: 'SLP (Purchases)' },
  { value: 'exempt_purchase', label: 'Exempt Purchase Amount', group: 'SLP (Purchases)' },
  { value: 'zero_rated_purchase', label: 'Zero-Rated Purchase Amount', group: 'SLP (Purchases)' },
  { value: 'taxable_purchase', label: 'Taxable Purchase Amount', group: 'SLP (Purchases)' },
  { value: 'purchase_services', label: 'Purchase of Services Amount', group: 'SLP (Purchases)' },
  { value: 'purchase_goods', label: 'Purchase of Goods (non-capital)', group: 'SLP (Purchases)' },
  { value: 'purchase_capital_goods', label: 'Purchase of Capital Goods', group: 'SLP (Purchases)' },
  { value: 'input_tax', label: 'Input Tax (Creditable)', group: 'SLP (Purchases)' },
  { value: 'gross_taxable_purchase', label: 'Gross Taxable Purchase', group: 'SLP (Purchases)' },

  // --- SLS: Summary List of Sales (RR 16-2005 Sec 4.114-3) ---
  { value: 'gross_sales', label: 'Gross Sales Amount', group: 'SLS (Sales)' },
  { value: 'exempt_sales', label: 'Exempt Sales Amount', group: 'SLS (Sales)' },
  { value: 'zero_rated_sales', label: 'Zero-Rated Sales Amount', group: 'SLS (Sales)' },
  { value: 'taxable_sales', label: 'Taxable Sales Amount', group: 'SLS (Sales)' },
  { value: 'output_tax', label: 'Output Tax (12%)', group: 'SLS (Sales)' },
  { value: 'gross_taxable_sales', label: 'Gross Taxable Sales', group: 'SLS (Sales)' },

  // --- SLI: Summary List of Importations (RR 16-2005 Sec 4.114-3) ---
  { value: 'import_entry_number', label: 'Import Entry Number', group: 'SLI (Importations)' },
  { value: 'assessment_date', label: 'Assessment/Release Date', group: 'SLI (Importations)' },
  { value: 'importation_date', label: 'Date of Importation', group: 'SLI (Importations)' },
  { value: 'country_of_origin', label: 'Country of Origin', group: 'SLI (Importations)' },
  { value: 'landed_cost', label: 'Total Landed Cost', group: 'SLI (Importations)' },
  { value: 'dutiable_value', label: 'Dutiable Value', group: 'SLI (Importations)' },
  { value: 'customs_charges', label: 'Charges Before Release from Customs', group: 'SLI (Importations)' },
  { value: 'taxable_imports', label: 'Taxable Imports Amount', group: 'SLI (Importations)' },
  { value: 'exempt_imports', label: 'Exempt Imports Amount', group: 'SLI (Importations)' },
  { value: 'vat_paid', label: 'VAT Paid on Imports', group: 'SLI (Importations)' },
  { value: 'vat_payment_date', label: 'Date of VAT Payment', group: 'SLI (Importations)' },

  // --- EWT (Expanded Withholding Tax on purchases) ---
  { value: 'ewt_rate', label: 'EWT Rate (%)', group: 'EWT' },
  { value: 'ewt_amount', label: 'EWT Amount', group: 'EWT' },
  { value: 'atc_code', label: 'ATC Code', group: 'EWT' },
]

export const TARGET_FIELDS: Record<string, TargetField[]> = {
  BIR_2550M: vatFields,
  BIR_2550Q: vatFields,
  BIR_1601C: [
    { value: 'employee_name', label: 'Employee Name' },
    { value: 'tin', label: 'TIN' },
    { value: 'total_compensation', label: 'Total Compensation' },
    { value: 'statutory_minimum_wage', label: 'Statutory Minimum Wage' },
    { value: 'basic_pay', label: 'Basic Pay' },
    { value: 'overtime_pay', label: 'Overtime Pay' },
    { value: 'holiday_pay', label: 'Holiday Pay' },
    { value: 'nontaxable_13th_month', label: '13th Month (Non-taxable)' },
    { value: 'nontaxable_deminimis', label: 'De Minimis Benefits' },
    { value: 'sss_gsis_phic_hdmf', label: 'SSS/GSIS/PhilHealth/HDMF (combined)' },
    { value: 'sss', label: 'SSS Contribution' },
    { value: 'philhealth', label: 'PhilHealth Contribution' },
    { value: 'pagibig', label: 'Pag-IBIG/HDMF Contribution' },
    { value: 'other_nontaxable', label: 'Other Non-taxable' },
    { value: 'taxable_compensation', label: 'Taxable Compensation' },
    { value: 'tax_withheld', label: 'Tax Withheld' },
  ],
  BIR_0619E: [
    { value: 'payee_name', label: 'Payee Name' },
    { value: 'tin', label: 'TIN' },
    { value: 'address', label: 'Payee Address' },
    { value: 'atc_code', label: 'ATC Code' },
    { value: 'nature_of_income', label: 'Nature of Income' },
    { value: 'income_payment', label: 'Income Payment' },
    { value: 'ewt_rate', label: 'EWT Rate (%)' },
    { value: 'tax_withheld', label: 'Tax Withheld' },
  ],
  Bank_Statement: [
    { value: 'date', label: 'Date' },
    { value: 'description', label: 'Description' },
    { value: 'amount', label: 'Amount' },
    { value: 'debit', label: 'Debit' },
    { value: 'credit', label: 'Credit' },
    { value: 'reference', label: 'Reference' },
    { value: 'balance', label: 'Balance' },
  ],
}
