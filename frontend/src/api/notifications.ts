import { client } from './client'

export interface NotificationItem {
  id: string
  notification_type: string
  title: string
  message: string
  metadata: Record<string, string> | null
  is_read: boolean
  created_at: string
  read_at: string | null
}

export const notificationsApi = {
  list: (page = 1, limit = 20) =>
    client.get('/notifications', { params: { page, limit } }),

  unreadCount: () => client.get('/notifications/unread-count'),

  markRead: (id: string) => client.patch(`/notifications/${id}/read`),

  markAllRead: () => client.post('/notifications/mark-all-read'),
}
