/**
 * Browser-side Excel/CSV parser using SheetJS.
 *
 * Reads the raw file in the browser, extracts pure data (no formatting/styles/charts),
 * and returns structured JSON. This makes large files (50-100MB Excel) practical
 * because only the actual cell data is sent to the server.
 */
import * as XLSX from "xlsx";

export interface ParsedSheet {
  columns: string[];
  row_count: number;
  rows: Record<string, unknown>[]; // ALL rows (for backend storage)
  preview: Record<string, unknown>[]; // First 10 rows (for UI display)
}

export interface ParsedFileResult {
  filename: string;
  type: "excel" | "csv";
  sheets: Record<string, ParsedSheet>;
}

const MAX_PREVIEW_ROWS = 10;
const MAX_TOTAL_ROWS = 500_000;

/** Keywords commonly found in column headers of BIR / financial documents. */
const HEADER_KEYWORDS = new Set([
  "name",
  "registered name",
  "tin",
  "address",
  "date",
  "invoice",
  "amount",
  "gross",
  "net",
  "tax",
  "vat",
  "rate",
  "total",
  "description",
  "supplier",
  "customer",
  "buyer",
  "vendor",
  "payee",
  "employee",
  "employer",
  "salary",
  "compensation",
  "purchase",
  "sales",
  "revenue",
  "expense",
  "debit",
  "credit",
  "balance",
  "reference",
  "no.",
  "no",
  "number",
  "code",
  "type",
  "status",
  "remarks",
  "period",
  "month",
  "year",
  "exempt",
  "zero rated",
  "taxable",
  "vatable",
  "input",
  "output",
  "withholding",
  "creditable",
]);

/** Returns true if the string looks like a number rather than a header label. */
function looksNumeric(s: string): boolean {
  const cleaned = s.trim().replace(/[,$₱PHP% ]/g, "");
  if (!cleaned) return false;
  let digitDot = 0;
  for (const c of cleaned) {
    if ((c >= "0" && c <= "9") || c === "." || c === "-") digitDot++;
  }
  return digitDot / cleaned.length > 0.7;
}

/**
 * Detect the most likely header row index from an array-of-arrays.
 * Uses fill ratio, uniqueness, text ratio, and keyword matching.
 */
function detectHeaderRow(rows: unknown[][]): number {
  const scanLimit = Math.min(20, rows.length);
  let totalCols = 0;
  for (const r of rows) {
    if (r.length > totalCols) totalCols = r.length;
  }
  if (totalCols === 0) return 0;

  let bestRow = 0;
  let bestScore = 0;

  for (let i = 0; i < scanLimit; i++) {
    const row = rows[i];
    if (!row || row.length === 0) continue;

    let nonEmpty = 0;
    let numericCount = 0;
    let keywordHits = 0;
    const unique = new Set<string>();

    for (const cell of row) {
      const v = String(cell ?? "").trim();
      if (!v) continue;
      nonEmpty++;
      unique.add(v);

      if (looksNumeric(v)) numericCount++;

      const lower = v.toLowerCase();
      if (HEADER_KEYWORDS.has(lower)) {
        keywordHits++;
      } else {
        for (const kw of HEADER_KEYWORDS) {
          if (lower.includes(kw)) {
            keywordHits++;
            break;
          }
        }
      }
    }

    if (nonEmpty === 0) continue;

    const fillRatio = nonEmpty / totalCols;
    if (fillRatio < 0.3) continue;

    const uniqueness = unique.size / nonEmpty;
    const textRatio = 1 - numericCount / nonEmpty;
    const keywordRatio = keywordHits / nonEmpty;

    const score =
      fillRatio * uniqueness * (0.5 + 0.5 * textRatio) * (1 + keywordRatio);

    if (score > bestScore) {
      bestScore = score;
      bestRow = i;
    }
  }

  return bestRow;
}

/**
 * Parse an Excel or CSV file in the browser.
 * Returns structured data with all rows extracted.
 */
export async function parseFileInBrowser(
  file: File,
  onProgress?: (stage: string) => void,
): Promise<ParsedFileResult> {
  onProgress?.("Reading file...");

  const buffer = await file.arrayBuffer();
  const ext = file.name.split(".").pop()?.toLowerCase() || "";
  const isCSV = ext === "csv";

  onProgress?.("Parsing spreadsheet...");

  const workbook = XLSX.read(buffer, {
    type: "array",
    cellDates: true, // Parse dates properly
    cellNF: false, // Don't need number formats
    cellStyles: false, // Don't need styles (saves memory)
  });

  const sheets: Record<string, ParsedSheet> = {};
  let totalRows = 0;

  for (const sheetName of workbook.SheetNames) {
    onProgress?.(`Processing sheet: ${sheetName}...`);

    const worksheet = workbook.Sheets[sheetName];
    if (!worksheet) continue;

    // Check row count before materializing to prevent OOM
    const ref = worksheet["!ref"];
    if (ref) {
      const range = XLSX.utils.decode_range(ref);
      const estimatedRows = range.e.r - range.s.r;
      if (totalRows + estimatedRows > MAX_TOTAL_ROWS) {
        throw new Error(
          `File contains too many rows (${(totalRows + estimatedRows).toLocaleString()}). Maximum ${MAX_TOTAL_ROWS.toLocaleString()} rows across all sheets.`,
        );
      }
    }

    // Read as array-of-arrays first so we can detect the real header row
    const rawAoA: unknown[][] = XLSX.utils.sheet_to_json(worksheet, {
      header: 1, // array-of-arrays mode
      defval: null,
      raw: false,
    });

    if (rawAoA.length < 2) continue;

    // Smart header detection — find the real header row
    const headerIdx = detectHeaderRow(rawAoA);
    const headerRow = rawAoA[headerIdx] as string[];

    // Build column names from the detected header row
    const columns: string[] = [];
    for (const cell of headerRow) {
      const v = String(cell ?? "").trim();
      columns.push(v || `Column_${columns.length + 1}`);
    }

    // Remove trailing empty columns
    while (
      columns.length > 0 &&
      columns[columns.length - 1].startsWith("Column_")
    ) {
      const last = columns[columns.length - 1];
      // Only remove if it's an auto-generated name at the end
      if (/^Column_\d+$/.test(last)) {
        columns.pop();
      } else {
        break;
      }
    }

    // Build row objects from data rows (after header)
    const dataRows = rawAoA.slice(headerIdx + 1);
    const cleanedRows: Record<string, unknown>[] = [];

    for (const row of dataRows) {
      const arr = row as unknown[];
      // Skip empty rows
      const hasData = arr.some(
        (v) => v !== null && v !== undefined && String(v).trim() !== "",
      );
      if (!hasData) continue;

      const obj: Record<string, unknown> = {};
      for (let c = 0; c < columns.length; c++) {
        const val = c < arr.length ? arr[c] : null;
        obj[columns[c]] = typeof val === "string" ? val.trim() : val;
      }
      cleanedRows.push(obj);
    }

    if (cleanedRows.length === 0) continue;

    totalRows += cleanedRows.length;

    sheets[sheetName] = {
      columns,
      row_count: cleanedRows.length,
      rows: cleanedRows,
      preview: cleanedRows.slice(0, MAX_PREVIEW_ROWS),
    };
  }

  if (Object.keys(sheets).length === 0) {
    throw new Error("File contains no data — all sheets are empty.");
  }

  return {
    filename: file.name,
    type: isCSV ? "csv" : "excel",
    sheets,
  };
}

/**
 * Estimate the JSON size of parsed data (for progress display).
 */
export function estimateJsonSize(parsed: ParsedFileResult): number {
  let totalRows = 0;
  for (const sheet of Object.values(parsed.sheets)) {
    totalRows += sheet.row_count;
  }
  // Rough estimate: ~100 bytes per row on average
  return totalRows * 100;
}
