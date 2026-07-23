import apiClient from './apiClient'

const BASE = '/chat'

export const chatApi = {
  getConversations: () =>
    apiClient.get(`${BASE}/conversations`).then(r => r.data),

  getHistory: (partnerId, { limit = 50, beforeId } = {}) =>
    apiClient.get(`${BASE}/conversations/${partnerId}`, {
      params: { limit, ...(beforeId ? { before_id: beforeId } : {}) },
    }).then(r => r.data),

  sendMessage: (recipientId, content) =>
    apiClient.post(`${BASE}/messages`, { recipient_id: recipientId, content }).then(r => r.data),

  markRead: (partnerId) =>
    apiClient.post(`${BASE}/conversations/${partnerId}/read`).then(r => r.data),

  getUnreadCount: () =>
    apiClient.get(`${BASE}/unread-count`).then(r => r.data),

  getPartners: () =>
    apiClient.get(`${BASE}/partners`).then(r => r.data),

  deleteMessage: (messageId) =>
    apiClient.delete(`${BASE}/messages/${messageId}`).then(r => r.data),
}
