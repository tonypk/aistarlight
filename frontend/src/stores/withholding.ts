import { defineStore } from 'pinia'
import { ref } from 'vue'
import { withholdingApi } from '../api/withholding'
import type {
  Vendor,
  WithholdingCertificate,
  EwtSummary,
  EwtRate,
  VendorCreateData,
  VendorUpdateData,
} from '../types/withholding'

export const useWithholdingStore = defineStore('withholding', () => {
  const vendors = ref<Vendor[]>([])
  const vendorTotal = ref(0)
  const certificates = ref<WithholdingCertificate[]>([])
  const certificateTotal = ref(0)
  const ewtSummary = ref<EwtSummary | null>(null)
  const ewtRates = ref<EwtRate[]>([])
  const loading = ref(false)

  async function fetchVendors(page = 1, limit = 50, search?: string) {
    loading.value = true
    try {
      const res = await withholdingApi.listVendors(page, limit, search)
      vendors.value = res.data.data
      vendorTotal.value = res.data.meta?.total ?? res.data.data.length
    } finally {
      loading.value = false
    }
  }

  async function createVendor(data: VendorCreateData) {
    const res = await withholdingApi.createVendor(data)
    const created = res.data.data as Vendor
    vendors.value = [created, ...vendors.value]
    return created
  }

  async function updateVendor(id: string, data: VendorUpdateData) {
    const res = await withholdingApi.updateVendor(id, data)
    const updated = res.data.data as Vendor
    vendors.value = vendors.value.map(s => s.id === id ? updated : s)
    return updated
  }

  async function deleteVendor(id: string) {
    await withholdingApi.deleteVendor(id)
    vendors.value = vendors.value.filter(s => s.id !== id)
  }

  async function classifyEwt(sessionId: string) {
    loading.value = true
    try {
      const res = await withholdingApi.classifyEwt(sessionId)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchCertificates(page = 1, limit = 50, period?: string) {
    loading.value = true
    try {
      const res = await withholdingApi.listCertificates(page, limit, period)
      certificates.value = res.data.data
      certificateTotal.value = res.data.meta?.total ?? res.data.data.length
    } finally {
      loading.value = false
    }
  }

  async function generateCertificates(sessionId: string) {
    loading.value = true
    try {
      const res = await withholdingApi.generateCertificates(sessionId)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function downloadCertificate(certId: string, filename?: string) {
    const res = await withholdingApi.downloadCertificate(certId)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename || `BIR2307_${certId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  async function fetchEwtSummary(period: string) {
    const res = await withholdingApi.getEwtSummary(period)
    ewtSummary.value = res.data.data
    return res.data.data
  }

  async function fetchEwtRates() {
    const res = await withholdingApi.listEwtRates()
    ewtRates.value = res.data.data
  }

  async function downloadSawt(period: string, format: 'csv' | 'pdf' = 'csv') {
    const res = await withholdingApi.downloadSawt(period, format)
    const ext = format === 'pdf' ? 'pdf' : 'csv'
    const mimeType = format === 'pdf' ? 'application/pdf' : 'text/csv'
    const url = window.URL.createObjectURL(new Blob([res.data], { type: mimeType }))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `SAWT_${period}.${ext}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  return {
    vendors,
    vendorTotal,
    /** @deprecated Use vendors instead */
    get suppliers() { return vendors.value },
    /** @deprecated Use vendorTotal instead */
    get supplierTotal() { return vendorTotal.value },
    certificates,
    certificateTotal,
    ewtSummary,
    ewtRates,
    loading,
    fetchVendors,
    createVendor,
    updateVendor,
    deleteVendor,
    /** @deprecated Use fetchVendors instead */
    fetchSuppliers: fetchVendors,
    classifyEwt,
    fetchCertificates,
    generateCertificates,
    downloadCertificate,
    fetchEwtSummary,
    fetchEwtRates,
    downloadSawt,
  }
})
