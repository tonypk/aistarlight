import { client } from './client'

export interface MonthlyTrend {
  month: string
  total_reports: number
  filed_count: number
  draft_count: number
}

export interface ActivityItem {
  id: string
  type: string
  description: string
  created_at: string
}

export const dashboardApi = {
  getTrends(months: number = 6) {
    return client.get('/dashboard/trends', { params: { months } })
  },

  getActivity(limit: number = 10) {
    return client.get('/dashboard/activity', { params: { limit } })
  },
}
