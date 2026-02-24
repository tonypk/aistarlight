import { defineStore } from "pinia";
import { ref, computed } from "vue";

interface SheetData {
  columns: string[];
  row_count: number;
  preview: Record<string, unknown>[];
}

export const useUploadStore = defineStore("upload", () => {
  const fileId = ref<string | null>(null);
  const filename = ref<string | null>(null);
  const columns = ref<string[]>([]);
  const sampleRows = ref<Record<string, unknown>[]>([]);
  const sheets = ref<Record<string, SheetData>>({});
  const confirmedMappings = ref<Record<string, string>>({});
  const reportType = ref("BIR_2550M");

  const hasFile = computed(() => !!fileId.value);
  const hasMappings = computed(
    () => Object.keys(confirmedMappings.value).length > 0,
  );

  function setUploadResult(data: {
    file_id: string;
    filename: string;
    columns: string[];
    sample_rows: Record<string, unknown>[];
    sheets: Record<string, SheetData>;
  }) {
    fileId.value = data.file_id;
    filename.value = data.filename;
    columns.value = [...data.columns];
    sampleRows.value = [...data.sample_rows];
    sheets.value = { ...data.sheets };
    confirmedMappings.value = {};
  }

  function setMappings(mappings: Record<string, string>) {
    confirmedMappings.value = { ...mappings };
  }

  function setReportType(type: string) {
    reportType.value = type;
  }

  function clear() {
    fileId.value = null;
    filename.value = null;
    columns.value = [];
    sampleRows.value = [];
    sheets.value = {};
    confirmedMappings.value = {};
    // reportType intentionally NOT reset — user selects it before upload
  }

  return {
    fileId,
    filename,
    columns,
    sampleRows,
    sheets,
    confirmedMappings,
    reportType,
    hasFile,
    hasMappings,
    setUploadResult,
    setMappings,
    setReportType,
    clear,
  };
});
