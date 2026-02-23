import { client } from './client'

export const receiptsApi = {
  upload: (files: File[], period: string, reportType: string = 'BIR_2550M') => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    formData.append('period', period)
    formData.append('report_type', reportType)
    return client.post('/receipts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 min for large batches
    })
  },
  listBatches: (params?: { page?: number; limit?: number }) =>
    client.get('/receipts/batches', { params }),
  getBatch: (batchId: string) =>
    client.get(`/receipts/batches/${batchId}`),
}
