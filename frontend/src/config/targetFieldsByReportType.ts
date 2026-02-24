export interface TargetField {
  value: string;
  label: string;
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

export const TARGET_FIELDS: Record<string, TargetField[]> = {
  BIR_2550M: [
    { value: "date", label: "Date" },
    { value: "description", label: "Description" },
    { value: "amount", label: "Amount" },
    { value: "vat_amount", label: "VAT Amount" },
    {
      value: "vat_type",
      label: "VAT Type (vatable/exempt/zero_rated/government)",
    },
    { value: "category", label: "Category (goods/services/capital/imports)" },
    { value: "tin", label: "TIN" },
    { value: "invoice_number", label: "Invoice/Receipt Number" },
    { value: "supplier_name", label: "Supplier/Customer Name" },
    { value: "address", label: "Supplier/Customer Address" },
    { value: "gross_amount", label: "Gross Amount (VAT inclusive)" },
    { value: "taxable_amount", label: "Taxable Amount (VAT exclusive)" },
    { value: "ewt_rate", label: "EWT Rate (%)" },
    { value: "ewt_amount", label: "EWT Amount" },
    { value: "atc_code", label: "ATC Code" },
  ],
  BIR_2550Q: [
    { value: "date", label: "Date" },
    { value: "description", label: "Description" },
    { value: "amount", label: "Amount" },
    { value: "vat_amount", label: "VAT Amount" },
    {
      value: "vat_type",
      label: "VAT Type (vatable/exempt/zero_rated/government)",
    },
    { value: "category", label: "Category (goods/services/capital/imports)" },
    { value: "tin", label: "TIN" },
    { value: "invoice_number", label: "Invoice/Receipt Number" },
    { value: "supplier_name", label: "Supplier/Customer Name" },
    { value: "address", label: "Supplier/Customer Address" },
    { value: "gross_amount", label: "Gross Amount (VAT inclusive)" },
    { value: "taxable_amount", label: "Taxable Amount (VAT exclusive)" },
    { value: "ewt_rate", label: "EWT Rate (%)" },
    { value: "ewt_amount", label: "EWT Amount" },
    { value: "atc_code", label: "ATC Code" },
  ],
  BIR_1601C: [
    { value: "employee_name", label: "Employee Name" },
    { value: "tin", label: "TIN" },
    { value: "total_compensation", label: "Total Compensation" },
    { value: "statutory_minimum_wage", label: "Statutory Minimum Wage" },
    { value: "nontaxable_13th_month", label: "13th Month (Non-taxable)" },
    { value: "nontaxable_deminimis", label: "De Minimis Benefits" },
    { value: "sss_gsis_phic_hdmf", label: "SSS/GSIS/PhilHealth/HDMF" },
    { value: "other_nontaxable", label: "Other Non-taxable" },
    { value: "tax_withheld", label: "Tax Withheld" },
    { value: "basic_pay", label: "Basic Pay" },
    { value: "overtime_pay", label: "Overtime Pay" },
    { value: "holiday_pay", label: "Holiday Pay" },
    { value: "sss", label: "SSS Contribution" },
    { value: "philhealth", label: "PhilHealth Contribution" },
    { value: "pagibig", label: "Pag-IBIG/HDMF Contribution" },
    { value: "taxable_compensation", label: "Taxable Compensation" },
  ],
  BIR_0619E: [
    { value: "payee_name", label: "Payee Name" },
    { value: "tin", label: "TIN" },
    { value: "atc_code", label: "ATC Code" },
    { value: "income_payment", label: "Income Payment" },
    { value: "tax_withheld", label: "Tax Withheld" },
    { value: "address", label: "Payee Address" },
    { value: "nature_of_income", label: "Nature of Income" },
    { value: "ewt_rate", label: "EWT Rate (%)" },
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
