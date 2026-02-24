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

    // Convert to JSON (array of objects with header row as keys)
    const rawRows: Record<string, unknown>[] = XLSX.utils.sheet_to_json(
      worksheet,
      {
        defval: null, // Default value for empty cells
        raw: false, // Return formatted strings (dates as strings, etc.)
      },
    );

    if (rawRows.length === 0) continue;

    // Extract column names from first row keys
    const columns = Object.keys(rawRows[0]);

    // Clean rows: trim strings, skip fully empty rows
    const cleanedRows: Record<string, unknown>[] = [];
    for (const row of rawRows) {
      if (isEmptyRow(row)) continue;
      const cleaned: Record<string, unknown> = {};
      for (const col of columns) {
        const val = row[col];
        cleaned[col] = typeof val === "string" ? val.trim() : val;
      }
      cleanedRows.push(cleaned);
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

function isEmptyRow(row: Record<string, unknown>): boolean {
  return Object.values(row).every(
    (v) =>
      v === null ||
      v === undefined ||
      (typeof v === "string" && v.trim() === ""),
  );
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
