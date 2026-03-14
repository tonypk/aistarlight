import { client } from "./client";
import type {
  VendorCreateData,
  VendorUpdateData,
} from "../types/withholding";

export const withholdingApi = {
  // Vendors
  listVendors: (page = 1, limit = 50, search?: string) =>
    client.get("/withholding/vendors", { params: { page, limit, search } }),

  createVendor: (data: VendorCreateData) =>
    client.post("/withholding/vendors", data),

  updateVendor: (id: string, data: VendorUpdateData) =>
    client.patch(`/withholding/vendors/${id}`, data),

  deleteVendor: (id: string) => client.delete(`/withholding/vendors/${id}`),

  // EWT Classification
  classifyEwt: (sessionId: string) =>
    client.post(`/withholding/sessions/${sessionId}/classify-ewt`),

  // Certificates
  listCertificates: (
    page = 1,
    limit = 50,
    period?: string,
    vendorId?: string,
  ) =>
    client.get("/withholding/certificates", {
      params: { page, limit, period, vendor_id: vendorId },
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
