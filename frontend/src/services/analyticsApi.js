import apiClient from './apiClient'

export const analyticsApi = {
  getAnalytics: async () => {
    const response = await apiClient.get('/analytics/')
    return response.data
  },

  recalculateAnalytics: async () => {
    const response = await apiClient.post('/analytics/recalculate')
    return response.data
  },

  getHeatmap: async (days = 365) => {
    const response = await apiClient.get(`/analytics/heatmap?days=${days}`)
    return response.data
  },
}
