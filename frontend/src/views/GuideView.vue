<script setup lang="ts">
import { ref } from 'vue'

const activeSection = ref('overview')

const sections = [
  { id: 'overview', title: 'Overview' },
  { id: 'quickstart', title: 'Quick Start' },
  { id: 'receipts', title: 'Receipt Scanner' },
  { id: 'upload', title: 'Upload Data' },
  { id: 'mapping', title: 'Column Mapping' },
  { id: 'classification', title: 'Classification' },
  { id: 'reconciliation', title: 'VAT Reconciliation' },
  { id: 'bank-recon', title: 'Bank Reconciliation' },
  { id: 'reports', title: 'Report Generation' },
  { id: 'edit-report', title: 'Edit Reports' },
  { id: 'corrections', title: 'Corrections & Learning' },
  { id: 'suppliers', title: 'Suppliers' },
  { id: 'withholding', title: 'Withholding Tax' },
  { id: 'chat', title: 'AI Tax Assistant' },
  { id: 'knowledge', title: 'Knowledge Base' },
  { id: 'faq', title: 'FAQ' },
]

function scrollTo(id: string) {
  activeSection.value = id
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="guide-view">
    <div class="guide-header">
      <h2>User Guide</h2>
      <p class="subtitle">AIStarlight Philippine Tax Filing Assistant &mdash; Complete User Manual</p>
    </div>

    <div class="guide-layout">
      <!-- Table of Contents -->
      <nav class="toc">
        <h4>Contents</h4>
        <a
          v-for="s in sections"
          :key="s.id"
          :class="{ active: activeSection === s.id }"
          @click.prevent="scrollTo(s.id)"
          href="#"
        >{{ s.title }}</a>
      </nav>

      <!-- Content -->
      <div class="content">

        <!-- 1. Overview -->
        <section id="overview">
          <h3>1. System Overview</h3>
          <p>AIStarlight is an AI-powered Philippine tax filing assistant that helps you with the following:</p>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="fi">📤</span>
              <div>
                <strong>Data Upload</strong>
                <p>Upload sales and purchase records in Excel or CSV format</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🤖</span>
              <div>
                <strong>AI Column Mapping</strong>
                <p>Automatically recognize column names and map them to BIR form fields</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🏷️</span>
              <div>
                <strong>Transaction Classification</strong>
                <p>AI-powered VAT type classification (Vatable / Exempt / Zero-rated)</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🔍</span>
              <div>
                <strong>VAT Reconciliation</strong>
                <p>Cross-check sales and purchase records, detect anomalies</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">📋</span>
              <div>
                <strong>BIR Reports</strong>
                <p>Auto-calculate and generate BIR 2550M / 2550Q / 1601C / 0619E PDFs</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">📑</span>
              <div>
                <strong>Withholding Tax</strong>
                <p>EWT classification, BIR 2307 certificate generation, SAWT summary</p>
              </div>
            </div>
            <div class="feature-item">
              <span class="fi">🏦</span>
              <div>
                <strong>Bank Reconciliation</strong>
                <p>Auto-match bank statements, PayPal/Stripe/GCash exports with AI analysis</p>
              </div>
            </div>
          </div>

          <div class="info-box">
            <strong>Supported BIR Forms:</strong>
            <ul>
              <li><strong>BIR 2550M</strong> &mdash; Monthly Value-Added Tax Declaration</li>
              <li><strong>BIR 2550Q</strong> &mdash; Quarterly Value-Added Tax Return</li>
              <li><strong>BIR 1601-C</strong> &mdash; Monthly Remittance of Withholding Tax on Compensation</li>
              <li><strong>BIR 0619-E</strong> &mdash; Monthly Remittance of Expanded Withholding Tax</li>
              <li><strong>BIR 2307</strong> &mdash; Certificate of Creditable Tax Withheld at Source</li>
              <li><strong>SAWT</strong> &mdash; Summary Alphalist of Withholding Taxes</li>
            </ul>
          </div>
        </section>

        <!-- 2. Quick Start -->
        <section id="quickstart">
          <h3>2. Quick Start</h3>
          <p>First time using the system? Follow these steps:</p>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>Set Up Company Info</strong>
                <p>Go to <router-link to="/settings">Settings</router-link> and fill in your company name, TIN number, and RDO code. This information will appear on your PDF reports.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>Upload Your Data</strong>
                <p>Go to <router-link to="/upload">Upload Data</router-link> and upload your Excel or CSV file containing sales and purchase records.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>Confirm Column Mapping</strong>
                <p>The AI will automatically recognize your column names. Review and confirm the mapping results.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>Generate Report</strong>
                <p>Go to <router-link to="/reports">Reports</router-link>, select the form type and period, then click "Generate Report".</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">5</span>
              <div>
                <strong>Review and Download PDF</strong>
                <p>Check the calculated results. Edit any fields if needed. Once verified, download the PDF for filing.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. Receipt Scanner -->
        <section id="receipts">
          <h3>3. Receipt Scanner</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Receipt Scanner</strong></p>

          <p>The Receipt Scanner lets you upload receipt photos and automatically extract transaction data using OCR. No manual data entry needed &mdash; just snap photos and let the system do the rest.</p>

          <h4>Supported Image Formats</h4>
          <ul>
            <li>JPEG (.jpg, .jpeg)</li>
            <li>PNG (.png)</li>
            <li>BMP (.bmp)</li>
            <li>TIFF (.tiff, .tif)</li>
            <li>WebP (.webp)</li>
          </ul>

          <h4>How to Use</h4>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>Upload Receipt Photos</strong>
                <p>Drag &amp; drop receipt images into the upload area, or click to browse. You can upload up to 50 images at once.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>Select Period &amp; Report Type</strong>
                <p>Choose the filing period (e.g., 2026-01) and report type (e.g., BIR 2550M). These determine how transactions are grouped.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>Click "Start Processing"</strong>
                <p>The system processes all images automatically: OCR &rarr; field extraction &rarr; transaction creation &rarr; report generation.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>Review Results</strong>
                <p>View extracted data for each receipt: vendor name, TIN, amounts, VAT type, and confidence scores. Navigate to the generated report or transaction list.</p>
              </div>
            </div>
          </div>

          <h4>How OCR Parsing Works</h4>
          <p>The system uses a two-layer approach to maximize accuracy while minimizing cost:</p>
          <ol>
            <li><strong>Layer 1: Rule-based parsing (free, instant)</strong> &mdash; Regex patterns extract TIN numbers, dates, amounts (&#8369; / PHP), VAT type keywords, and receipt numbers. Cross-validates that vatable sales + VAT amount &asymp; total. Fields with confidence &ge; 85% are used directly.</li>
            <li><strong>Layer 2: AI assist (only when needed)</strong> &mdash; Fields with low confidence (e.g., ambiguous vendor category, unclear VAT type) are sent to an AI model for resolution. Typically, standard BIR receipts require zero AI calls.</li>
          </ol>

          <h4>Confidence Scores</h4>
          <ul>
            <li><strong style="color: #16a34a;">&ge; 85%</strong> &mdash; High confidence, auto-accepted</li>
            <li><strong style="color: #ca8a04;">60&ndash;84%</strong> &mdash; Medium confidence, AI-assisted</li>
            <li><strong style="color: #dc2626;">&lt; 60%</strong> &mdash; Low confidence, may need manual review</li>
          </ul>

          <div class="tip-box">
            <strong>Tip:</strong> For best OCR results, ensure receipt photos are well-lit, flat, and in focus. Avoid shadows and wrinkles. The system handles rotated images automatically.
          </div>
        </section>

        <!-- 4. Upload -->
        <section id="upload">
          <h3>4. Upload Data</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Upload Data</strong></p>

          <h4>Supported File Formats</h4>
          <ul>
            <li>Excel files (.xlsx, .xls)</li>
            <li>CSV files (.csv)</li>
            <li>PDF files (.pdf) &mdash; the system will attempt to extract table data</li>
          </ul>

          <h4>Data Requirements</h4>
          <ul>
            <li>The file must contain an <strong>Amount</strong> column</li>
            <li>Recommended columns: Date, Description, VAT Amount, VAT Type</li>
            <li>Sales and purchase data can be in different sheets within the same file</li>
          </ul>

          <div class="tip-box">
            <strong>Tip:</strong> After uploading, you can select a specific sheet name (for multi-sheet files). The system will preview the first few rows for confirmation.
          </div>
        </section>

        <!-- 5. Mapping -->
        <section id="mapping">
          <h3>5. Column Mapping</h3>
          <p>Navigate to: Auto-redirected after upload, or Sidebar &rarr; <strong>Upload Data</strong> &rarr; select file</p>

          <h4>How It Works</h4>
          <ol>
            <li>After uploading, the AI analyzes your column names (e.g., "Sales Amount", "VAT", "Date")</li>
            <li>The AI recommends a mapping from your columns to system fields</li>
            <li>You can manually adjust any mapping</li>
            <li>Once confirmed, the data is parsed and used for subsequent calculations</li>
          </ol>

          <h4>System Field Reference</h4>
          <table class="ref-table">
            <thead>
              <tr><th>Field</th><th>Description</th><th>Required</th></tr>
            </thead>
            <tbody>
              <tr><td>amount</td><td>Transaction amount</td><td>Yes</td></tr>
              <tr><td>vat_amount</td><td>VAT amount</td><td>No (system can calculate at 12%)</td></tr>
              <tr><td>vat_type</td><td>VAT type: vatable / exempt / zero_rated / government</td><td>No (AI can auto-classify)</td></tr>
              <tr><td>date</td><td>Transaction date</td><td>No</td></tr>
              <tr><td>description</td><td>Transaction description</td><td>No (used for AI classification)</td></tr>
              <tr><td>category</td><td>Purchase category: goods / services / capital / imports</td><td>No</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 6. Classification -->
        <section id="classification">
          <h3>6. Transaction Classification</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Classification</strong></p>

          <h4>Create a Reconciliation Session</h4>
          <ol>
            <li>Click "New Session" and enter a session name and period</li>
            <li>Upload your sales data file and purchase data file</li>
            <li>The system parses the files and generates a transaction list</li>
          </ol>

          <h4>AI Auto-Classification</h4>
          <p>Click the "Classify" button and the AI will automatically:</p>
          <ul>
            <li>Identify the VAT type for each transaction (Vatable / Exempt / Zero-rated / Government)</li>
            <li>Classify purchase categories (Goods / Services / Capital / Imports)</li>
            <li>Flag low-confidence classifications for manual review</li>
          </ul>

          <div class="tip-box">
            <strong>Tip:</strong> You can manually override any transaction's classification. The system learns from your corrections to improve future accuracy.
          </div>
        </section>

        <!-- 7. Reconciliation -->
        <section id="reconciliation">
          <h3>7. VAT Reconciliation</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Reconciliation</strong></p>

          <h4>Reconciliation Process</h4>
          <ol>
            <li>After classification is complete, click "Reconcile" to start</li>
            <li>The system cross-checks sales and purchase records</li>
            <li>Generates a VAT summary: Output VAT, Input VAT, Net VAT Payable</li>
            <li>Detects anomalies: amount mismatches, missing transactions, duplicate records</li>
          </ol>

          <h4>After Reconciliation, You Can:</h4>
          <ul>
            <li><strong>Generate BIR Report</strong> &mdash; Create a BIR 2550M/2550Q report directly from reconciliation data</li>
            <li><strong>Export PDF</strong> &mdash; Download a full reconciliation report PDF (VAT summary, match statistics, anomaly list)</li>
            <li><strong>Export CSV</strong> &mdash; Download transaction data as CSV</li>
          </ul>
        </section>

        <!-- 8. Bank Reconciliation -->
        <section id="bank-recon">
          <h3>8. Bank &amp; Billing Reconciliation</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Bank Recon</strong></p>

          <p>Automatically match your bank statements, payment platform exports (PayPal, Stripe, GCash), and POS sales against your accounting records. AI identifies fuzzy matches and explains discrepancies.</p>

          <h4>Supported File Formats</h4>
          <ul>
            <li><strong>CSV / Excel</strong> (.csv, .xlsx, .xls) &mdash; Bank exports, PayPal/Stripe/GCash downloads</li>
            <li><strong>PDF</strong> (.pdf) &mdash; Bank statements with tables (auto-extracted via pdfplumber)</li>
            <li><strong>Images</strong> (.jpg, .png, .bmp, .tiff, .webp) &mdash; Scanned bank statements (OCR extraction)</li>
          </ul>

          <h4>Auto-Detected Bank Formats</h4>
          <table class="ref-table">
            <thead>
              <tr><th>Format</th><th>Description</th></tr>
            </thead>
            <tbody>
              <tr><td>BDO</td><td>Banco de Oro bank statements</td></tr>
              <tr><td>BPI</td><td>Bank of the Philippine Islands</td></tr>
              <tr><td>Metrobank</td><td>Metropolitan Bank statements</td></tr>
              <tr><td>PayPal</td><td>PayPal transaction history exports</td></tr>
              <tr><td>Stripe</td><td>Stripe payment exports</td></tr>
              <tr><td>GCash</td><td>GCash transaction history</td></tr>
              <tr><td>Generic</td><td>Any CSV with date/amount/description columns</td></tr>
            </tbody>
          </table>

          <h4>How to Use</h4>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>Upload Files</strong>
                <p>Drag &amp; drop bank statements, billing exports, or POS files. You can upload multiple files at once (e.g., bank CSV + PayPal export + GCash statement).</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>Configure Settings</strong>
                <p>Select the filing period, set amount tolerance (default PHP 0.01) and date tolerance (default 3 days). Optionally link to an existing reconciliation session to match against your accounting records.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>Review Matching Results</strong>
                <p>The system auto-detects bank formats and matches entries. View matched pairs, unmatched bank entries, and unmatched records with match rate statistics.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>AI Analysis</strong>
                <p>For unmatched entries, AI suggests fuzzy matches (with confidence scores) and explains why entries didn't match &mdash; e.g., bank fees, timing differences, internal transfers. Accept or reject each suggestion.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">5</span>
              <div>
                <strong>Summary &amp; Export</strong>
                <p>View the final reconciliation summary. Export the full results as CSV for your records.</p>
              </div>
            </div>
          </div>

          <h4>AI Suggestion Categories</h4>
          <ul>
            <li><strong style="color: #22c55e;">Likely Match</strong> &mdash; High confidence fuzzy match (amount &amp; date close)</li>
            <li><strong style="color: #eab308;">Possible Match</strong> &mdash; May be a match, needs manual review</li>
            <li><strong style="color: #3b82f6;">Internal Transfer</strong> &mdash; Entry appears to be a transfer between accounts</li>
            <li><strong style="color: #8b5cf6;">Bank Fee</strong> &mdash; Service charges, interest, or bank-specific deductions</li>
            <li><strong style="color: #ef4444;">No Match</strong> &mdash; No corresponding record found</li>
          </ul>

          <div class="tip-box">
            <strong>Tip:</strong> Link a reconciliation session to match bank entries against your classified sales/purchase records. Without a session, the system parses and analyzes bank files only (format detection, entry extraction, AI explanations).
          </div>
        </section>

        <!-- 9. Reports -->
        <section id="reports">
          <h3>9. Report Generation</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Reports</strong></p>

          <h4>Generating a Report</h4>
          <ol>
            <li>Select the <strong>Form Type</strong> (BIR 2550M / 2550Q / 1601C / 0619E)</li>
            <li>Select the <strong>Filing Period</strong> (month or quarter)</li>
            <li>Data source options:
              <ul>
                <li>From an uploaded file (uses column mapping results)</li>
                <li>From a reconciliation session (Reconciliation &rarr; Generate Report)</li>
                <li>Manual data entry</li>
              </ul>
            </li>
            <li>Click "Generate Report" &mdash; the system auto-calculates all fields and generates a PDF</li>
          </ol>

          <h4>Report Workflow</h4>
          <div class="workflow">
            <span class="wf-step">Draft</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Review</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Approved</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Filed</span>
            <span class="wf-arrow">&rarr;</span>
            <span class="wf-step">Archived</span>
          </div>
          <ul>
            <li><strong>Draft</strong> &mdash; Editable, fields can be modified</li>
            <li><strong>Review</strong> &mdash; Submitted for review, still editable</li>
            <li><strong>Approved</strong> &mdash; Approved for filing</li>
            <li><strong>Filed</strong> &mdash; Submitted to BIR</li>
            <li><strong>Archived</strong> &mdash; Stored for record-keeping</li>
          </ul>
        </section>

        <!-- 10. Edit Report -->
        <section id="edit-report">
          <h3>10. Editing Reports</h3>
          <p>Click the "Edit" button in the report list to open the editing page.</p>

          <h4>Editing Features</h4>
          <ul>
            <li>Modify any editable field (e.g., sales amounts, input tax, etc.)</li>
            <li>The system automatically recalculates all dependent fields (e.g., changing Vatable Sales updates Output VAT, Total Sales, VAT Payable, etc.)</li>
            <li>Every edit is logged in the audit trail</li>
            <li>Optimistic locking (version numbers) prevents concurrent edit conflicts</li>
            <li>On first edit, the original calculated data is preserved for comparison</li>
          </ul>

          <div class="warning-box">
            <strong>Note:</strong> After editing, the PDF is automatically regenerated. Reports in "Filed" or "Archived" status cannot be edited.
          </div>
        </section>

        <!-- 11. Corrections & Learning -->
        <section id="corrections">
          <h3>11. Corrections &amp; Learning</h3>
          <p>Navigate to: Any report or transaction view &rarr; <strong>Edit / Correct</strong></p>

          <p>When you correct a transaction's classification or report field, the system doesn't just update the value &mdash; it learns from your correction to improve future accuracy.</p>

          <h4>How Corrections Work</h4>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>Make a Correction</strong>
                <p>Change a transaction's VAT type, category, or amount. The system records what changed and why.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>Rule Auto-Generated</strong>
                <p>If a pattern is detected (e.g., "PLDT" always classified as "services"), the system creates a learned rule for future transactions.</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>Compliance Validation</strong>
                <p>Each correction is checked against BIR regulations. The system flags if a correction might cause compliance issues.</p>
              </div>
            </div>
          </div>

          <h4>Learning Insights</h4>
          <ul>
            <li><strong>Correction History</strong> &mdash; View all corrections made across sessions, with before/after values</li>
            <li><strong>Auto-Learned Rules</strong> &mdash; Rules generated from repeated corrections (e.g., vendor &rarr; category mappings)</li>
            <li><strong>Confidence Improvement</strong> &mdash; Over time, the AI's classification accuracy improves as it learns from your corrections</li>
            <li><strong>Compliance Score</strong> &mdash; Each report gets a compliance score based on validation rules and correction history</li>
          </ul>

          <div class="info-box">
            <strong>How it improves accuracy:</strong> When you correct a classification, the system stores the pattern. Next time a similar transaction appears, the AI uses your previous corrections to make a more accurate initial classification.
          </div>
        </section>

        <!-- 12. Suppliers -->
        <section id="suppliers">
          <h3>12. Supplier Management</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Suppliers</strong></p>

          <h4>Managing Suppliers</h4>
          <ul>
            <li><strong>Add Supplier</strong> &mdash; Enter TIN, name, address, and type (Individual / Corporation)</li>
            <li><strong>Set Default EWT</strong> &mdash; Assign a default withholding tax rate and ATC code per supplier</li>
            <li><strong>Auto-Matching</strong> &mdash; During EWT classification, the system automatically matches existing suppliers</li>
          </ul>

          <h4>Supplier Field Reference</h4>
          <table class="ref-table">
            <thead>
              <tr><th>Field</th><th>Description</th></tr>
            </thead>
            <tbody>
              <tr><td>TIN</td><td>Tax Identification Number</td></tr>
              <tr><td>Name</td><td>Full supplier name</td></tr>
              <tr><td>Type</td><td>Individual or Corporation</td></tr>
              <tr><td>Default EWT Rate</td><td>Default withholding tax rate (e.g., 0.02 = 2%)</td></tr>
              <tr><td>Default ATC Code</td><td>Default Alphanumeric Tax Code (e.g., WC050)</td></tr>
              <tr><td>VAT Registered</td><td>Whether the supplier is VAT-registered</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 13. Withholding Tax -->
        <section id="withholding">
          <h3>13. Withholding Tax (EWT) Management</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Withholding Tax</strong></p>

          <h4>EWT Workflow</h4>
          <div class="steps">
            <div class="step">
              <span class="step-num">1</span>
              <div>
                <strong>Classify EWT</strong>
                <p>In a reconciliation session, click "Classify EWT" to automatically identify ATC codes and withholding tax rates for purchase transactions</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">2</span>
              <div>
                <strong>Generate BIR 2307</strong>
                <p>Click "Generate Certificates" to auto-group by supplier and period, generating BIR 2307 withholding tax certificate PDFs</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">3</span>
              <div>
                <strong>Download SAWT</strong>
                <p>On the Withholding Tax page, select a period and download the SAWT summary (CSV or PDF format)</p>
              </div>
            </div>
            <div class="step">
              <span class="step-num">4</span>
              <div>
                <strong>Generate BIR 0619-E</strong>
                <p>On the Reports page, select BIR 0619-E to auto-summarize monthly EWT amounts</p>
              </div>
            </div>
          </div>

          <h4>Common ATC Code Reference</h4>
          <table class="ref-table">
            <thead>
              <tr><th>ATC Code</th><th>Description</th><th>Rate</th></tr>
            </thead>
            <tbody>
              <tr><td>WC010</td><td>Professional fees &mdash; Corporation</td><td>10%</td></tr>
              <tr><td>WI010</td><td>Professional fees &mdash; Individual (&lt;3M)</td><td>5%</td></tr>
              <tr><td>WI050 / WC050</td><td>Contractors / Subcontractors</td><td>2%</td></tr>
              <tr><td>WI030</td><td>Rent &mdash; Real property</td><td>5%</td></tr>
              <tr><td>WC060</td><td>Advertising / Promotions</td><td>2%</td></tr>
              <tr><td>WI100 / WC100</td><td>Purchase of goods (&gt;3M/year)</td><td>1%</td></tr>
              <tr><td>WI120 / WC120</td><td>Service payments</td><td>2%</td></tr>
            </tbody>
          </table>
        </section>

        <!-- 14. AI Chat -->
        <section id="chat">
          <h3>14. AI Tax Assistant</h3>
          <p>Navigate to: Sidebar &rarr; <strong>AI Chat</strong></p>

          <p>You can ask the AI assistant any Philippine tax-related question in English or Chinese. For example:</p>
          <ul>
            <li>"What is the deadline for filing BIR 2550M?"</li>
            <li>"Under what circumstances can I apply for a VAT refund?"</li>
            <li>"What is the withholding tax rate for professional service fees?"</li>
            <li>"How does the TRAIN Law affect individual income tax?"</li>
            <li>"What is the difference between BIR 2307 and SAWT?"</li>
          </ul>

          <div class="tip-box">
            <strong>Tip:</strong> The AI assistant's answers are based on the Philippine NIRC, TRAIN Law, CREATE Act, and official BIR regulations. The system supports long-term memory &mdash; you can manage the AI's memory on the Memory page.
          </div>
        </section>

        <!-- 15. Knowledge -->
        <section id="knowledge">
          <h3>15. Knowledge Base</h3>
          <p>Navigate to: Sidebar &rarr; <strong>Knowledge</strong></p>

          <p>The knowledge base contains structured data on Philippine tax laws and regulations, used to enhance the AI assistant's accuracy.</p>

          <h4>Built-in Knowledge</h4>
          <ul>
            <li>NIRC (National Internal Revenue Code) &mdash; VAT-related sections</li>
            <li>TRAIN Law (RA 10963) &mdash; Tax Reform highlights</li>
            <li>CREATE Act (RA 11534) &mdash; Corporate income tax incentives</li>
            <li>BIR Revenue Regulations &mdash; EWT, filing rules, etc.</li>
            <li>BIR form filling guides for all supported forms</li>
            <li>Penalties, surcharges, and remedies</li>
          </ul>

          <p>You can search the knowledge base for specific provisions and regulations on the Knowledge page.</p>
        </section>

        <!-- 16. FAQ -->
        <section id="faq">
          <h3>16. Frequently Asked Questions</h3>

          <div class="faq-item">
            <h4>Q: What if the report calculations are incorrect?</h4>
            <p>A: Click "Edit" on the report list to open the editing page and modify the relevant fields. The system will automatically recalculate all dependent fields and regenerate the PDF.</p>
          </div>

          <div class="faq-item">
            <h4>Q: Can I modify a report that has already been submitted?</h4>
            <p>A: Reports in Draft and Review status can be edited. Reports in Approved or later statuses cannot be modified. To make changes, first transition the report back to Draft.</p>
          </div>

          <div class="faq-item">
            <h4>Q: What should I do if file upload fails?</h4>
            <p>A: Please ensure the file format is .xlsx, .xls, .csv, or .pdf, and the file size does not exceed 10MB. For Excel files, make sure the data is in the first sheet or the specified sheet name.</p>
          </div>

          <div class="faq-item">
            <h4>Q: What if the AI classification results are inaccurate?</h4>
            <p>A: Manually override the classification. The system learns from your corrections and improves future accuracy. You can also set default EWT rates and ATC codes for suppliers.</p>
          </div>

          <div class="faq-item">
            <h4>Q: How do I change company information (TIN, RDO)?</h4>
            <p>A: Go to the Settings page. New reports will use the updated information; previously generated reports are not affected.</p>
          </div>

          <div class="faq-item">
            <h4>Q: What is the difference between BIR 2550M and 2550Q?</h4>
            <p>A: BIR 2550M is the monthly VAT declaration and 2550Q is the quarterly VAT return. The calculation logic is the same; the difference is the filing period and data scope.</p>
          </div>

          <div class="faq-item">
            <h4>Q: What bank statement formats are supported for Bank Reconciliation?</h4>
            <p>A: The system auto-detects BDO, BPI, Metrobank, PayPal, Stripe, and GCash formats. You can also upload generic CSV/Excel files with date, amount, and description columns. PDF bank statements and scanned images (via OCR) are also supported.</p>
          </div>

          <div class="faq-item">
            <h4>Q: How does the AI match analysis work?</h4>
            <p>A: After standard matching (by amount and date), unmatched entries are sent to AI in batches. The AI suggests fuzzy matches, identifies bank fees and internal transfers, and explains why entries don't match. You can accept or reject each suggestion.</p>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-view {
  max-width: 1200px;
}

.guide-header {
  margin-bottom: 24px;
}
.guide-header h2 {
  margin-bottom: 4px;
}
.subtitle {
  color: #888;
  font-size: 14px;
}

.guide-layout {
  display: flex;
  gap: 24px;
}

/* Table of Contents */
.toc {
  width: 180px;
  flex-shrink: 0;
  position: sticky;
  top: 24px;
  align-self: flex-start;
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
.toc h4 {
  margin-bottom: 12px;
  color: #374151;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.toc a {
  display: block;
  padding: 6px 10px;
  color: #6b7280;
  text-decoration: none;
  font-size: 13px;
  border-radius: 4px;
  transition: all 0.15s;
}
.toc a:hover {
  color: #4f46e5;
  background: #f5f3ff;
}
.toc a.active {
  color: #4f46e5;
  background: #eef2ff;
  font-weight: 500;
}

/* Content */
.content {
  flex: 1;
  min-width: 0;
}

section {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

section h3 {
  font-size: 18px;
  margin-bottom: 12px;
  color: #111827;
  padding-bottom: 8px;
  border-bottom: 1px solid #f3f4f6;
}

section h4 {
  font-size: 15px;
  margin: 16px 0 8px;
  color: #374151;
}

section p {
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 8px;
}

section ul, section ol {
  padding-left: 20px;
  color: #4b5563;
  line-height: 1.8;
}

section li {
  margin-bottom: 4px;
}

/* Feature Grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.feature-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}
.feature-item .fi {
  font-size: 24px;
  flex-shrink: 0;
}
.feature-item strong {
  display: block;
  font-size: 14px;
  margin-bottom: 2px;
}
.feature-item p {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

/* Steps */
.steps {
  margin: 16px 0;
}
.step {
  display: flex;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f3f4f6;
}
.step:last-child {
  border-bottom: none;
}
.step-num {
  width: 32px;
  height: 32px;
  background: #4f46e5;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.step strong {
  display: block;
  margin-bottom: 4px;
}
.step p {
  font-size: 14px;
  margin: 0;
}

/* Info, Tip, Warning boxes */
.info-box, .tip-box, .warning-box {
  padding: 14px 16px;
  border-radius: 8px;
  margin: 16px 0;
  font-size: 14px;
  line-height: 1.6;
}
.info-box {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
}
.info-box ul {
  margin-top: 8px;
  color: #1e40af;
}
.tip-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}
.warning-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

/* Reference tables */
.ref-table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}
.ref-table th {
  text-align: left;
  padding: 8px 12px;
  background: #f9fafb;
  color: #374151;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}
.ref-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
}

/* Workflow */
.workflow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
  flex-wrap: wrap;
}
.wf-step {
  padding: 6px 14px;
  background: #eef2ff;
  color: #4f46e5;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}
.wf-arrow {
  color: #9ca3af;
  font-size: 18px;
}

/* FAQ */
.faq-item {
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}
.faq-item:last-child {
  border-bottom: none;
}
.faq-item h4 {
  color: #111827;
  margin: 0 0 6px;
}
.faq-item p {
  margin: 0;
  font-size: 14px;
}

/* Responsive */
@media (max-width: 768px) {
  .guide-layout {
    flex-direction: column;
  }
  .toc {
    width: 100%;
    position: static;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .toc h4 {
    width: 100%;
  }
}
</style>
