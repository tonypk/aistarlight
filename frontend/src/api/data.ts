import { client } from "./client";
import type { ParsedFileResult } from "../utils/fileParser";

export interface MappingRequest {
  columns: string[];
  sample_rows: Record<string, unknown>[];
  report_type?: string;
  data_category?: string; // sales, purchases, general
}

export interface FieldCandidate {
  target_field: string;
  confidence: number;
  reason: string;
}

export interface ConflictGroup {
  target_field: string;
  columns: string[];
}

export interface MappingResponse {
  mappings: Record<string, string>;
  unmapped: string[];
  confidence: number;
  field_confidence?: Record<string, number>;
  candidates?: Record<string, FieldCandidate[]>;
  conflicts?: ConflictGroup[];
}

export interface MappingCorrectionItem {
  column_name: string;
  old_target: string;
  new_target: string;
  sample_values?: unknown[];
}

export const dataApi = {
  /**
   * Upload raw file to server (for small files < 10MB).
   * Server parses the file.
   */
  upload: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post("/data/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(e.loaded / e.total);
        }
      },
    });
  },

  /**
   * Upload pre-parsed data (for large files).
   * Browser reads the file with SheetJS, extracts pure data, sends JSON.
   * Much smaller payload than raw Excel files.
   */
  uploadParsed: (
    data: ParsedFileResult,
    onProgress?: (progress: number) => void,
  ) => {
    return client.post("/data/upload-parsed", data, {
      timeout: 120000,
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(e.loaded / e.total);
        }
      },
    });
  },

  preview: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post("/data/preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    });
  },

  suggestMapping: (data: MappingRequest) => client.post("/data/mapping", data),

  /** Get saved mapping template for a report type. */
  getTemplate: (reportType: string) => {
    return client.get(`/memory/preferences/${reportType}`, {
      _silentError: true,
    } as never);
  },

  /** Save mapping template for a report type. */
  saveTemplate: (reportType: string, mappings: Record<string, string>) => {
    return client.put(`/memory/preferences/${reportType}`, {
      column_mappings: mappings,
    });
  },

  /** Record user corrections to AI column mappings for future learning. */
  recordMappingCorrections: (
    reportType: string,
    corrections: MappingCorrectionItem[],
  ) => {
    return client.post("/data/mapping/corrections", {
      report_type: reportType,
      corrections,
    });
  },
};
