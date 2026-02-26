import { client } from "./client";
import type {
  SupplierCreateData,
  SupplierUpdateData,
} from "../types/withholding";

export const withholdingApi = {
  // Suppliers
  listSuppliers: (page = 1, limit = 50, search?: string) =>
    client.get("/withholding/suppliers", { params: { page, limit, search } }),

  createSupplier: (data: SupplierCreateData) =>
    client.post("/withholding/suppliers", data),

  updateSupplier: (id: string, data: SupplierUpdateData) =>
    client.patch(`/withholding/suppliers/${id}`, data),

  deleteSupplier: (id: string) => client.delete(`/withholding/suppliers/${id}`),

  // EWT Classification
  classifyEwt: (sessionId: string) =>
    client.post(`/withholding/sessions/${sessionId}/classify-ewt`),

  // Certificates
  listCertificates: (
    page = 1,
    limit = 50,
    period?: string,
    supplierId?: string,
  ) =>
    client.get("/withholding/certificates", {
      params: { page, limit, period, supplier_id: supplierId },
    }),

  generateCertificates: (sessionId: string) =>
    client.post(`/withholding/sessions/${sessionId}/generate-certificates`),

  downloadCertificate: (certId: string, format: "pdf" | "csv" = "pdf") =>
    client.get(`/withholding/certificates/${certId}/download`, {
      params: { format },
      responseType: "blob",
    }),

  // SAWT
  getSawt: (period: string) =>
    client.get("/withholding/sawt", { params: { period } }),

  downloadSawt: (period: string, format: "csv" | "pdf" = "csv") =>
    client.get("/withholding/sawt/download", {
      params: { period, format },
      responseType: "blob",
    }),

  // EWT Summary
  getEwtSummary: (period: string) =>
    client.get("/withholding/ewt-summary", { params: { period } }),

  // EWT Rates Reference
  listEwtRates: () => client.get("/withholding/ewt-rates"),
};
