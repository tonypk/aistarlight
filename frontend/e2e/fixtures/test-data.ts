import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const TEST_USER = {
  email: "dragonai@starlight.com",
  password: "Starlight2026",
  fullName: "Dragon AI",
} as const;

export const TEST_FILES = {
  SLSP_Q4: path.resolve(__dirname, "data/SLSP_Q4.xlsx"),
} as const;

export const REPORT_TYPES = {
  BIR_2550M: "BIR_2550M",
  BIR_2550Q: "BIR_2550Q",
} as const;

export const ROUTES = {
  login: "/login",
  dashboard: "/",
  upload: "/upload",
  mapping: "/mapping",
  classification: "/classification",
  reconciliation: "/reconciliation",
  reports: "/reports",
  accounts: "/accounts",
  journalEntries: "/journal-entries",
  generalLedger: "/general-ledger",
  statements: "/statements",
  taxBridge: "/tax-bridge",
  calendar: "/calendar",
  chat: "/chat",
  settings: "/settings",
  bankReconciliation: "/bank-reconciliation",
  receipts: "/receipts",
  withholding: "/withholding",
  suppliers: "/suppliers",
  compare: "/compare",
  knowledge: "/knowledge",
  memory: "/memory",
  guide: "/guide",
  learning: "/learning",
} as const;

export const TIMEOUTS = {
  aiOperation: 45_000,
  navigation: 10_000,
  upload: 30_000,
} as const;
