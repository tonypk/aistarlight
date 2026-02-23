import { client } from './client'

export interface MappingRequest {
  columns: string[]
  sample_rows: Record<string, unknown>[]
  report_type?: string
}

export const dataApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  preview: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/data/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  suggestMapping: (data: MappingRequest) => client.post('/data/mapping', data),
}
