/**
 * Thin wrappers around the axios apiClient for discussions and submissions.
 * All other services already use apiClient directly.
 */
import apiClient from './apiClient'

// Discussions API
export const discussionsApi = {
  getAll: (params) =>
    apiClient.get('/api/discussions', { params }).then(r => r.data),

  getById: (id) =>
    apiClient.get(`/api/discussions/${id}`).then(r => r.data),

  create: (data) =>
    apiClient.post('/api/discussions', data).then(r => r.data),

  update: (id, data) =>
    apiClient.put(`/api/discussions/${id}`, data).then(r => r.data),

  delete: (id) =>
    apiClient.delete(`/api/discussions/${id}`).then(r => r.data),

  addReply: (id, data) =>
    apiClient.post(`/api/discussions/${id}/replies`, data).then(r => r.data),

  vote: (id, voteType) =>
    apiClient.post(`/api/discussions/${id}/vote`, { vote_type: voteType }).then(r => r.data),

  voteReply: (replyId, voteType) =>
    apiClient.post(`/api/discussions/replies/${replyId}/vote`, { vote_type: voteType }).then(r => r.data),

  getMyPosts: (params) =>
    apiClient.get('/api/discussions/my/posts', { params }).then(r => r.data),

  getOverview: () =>
    apiClient.get('/dashboard/student/discussions/overview').then(r => r.data),
}

// Submissions API
export const submissionsApi = {
  getAll: (params) =>
    apiClient.get('/api/submissions', { params }).then(r => r.data),

  getStats: (days = 30) =>
    apiClient.get('/api/submissions/stats', { params: { days } }).then(r => r.data),

  getByProblem: (platform, problemId) =>
    apiClient.get(`/api/submissions/problem/${platform}/${problemId}`).then(r => r.data),

  getPlatformSummary: () =>
    apiClient.get('/api/submissions/platforms/summary').then(r => r.data),

  getOverview: () =>
    apiClient.get('/dashboard/student/submissions/overview').then(r => r.data),
}

export default apiClient
