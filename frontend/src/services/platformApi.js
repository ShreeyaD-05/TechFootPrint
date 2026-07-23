import apiClient from './apiClient'

export const platformApi = {
  getAvailablePlatforms: async () => {
    const response = await apiClient.get('/platforms/available')
    return response.data
  },

  getConnectedPlatforms: async () => {
    const response = await apiClient.get('/platforms/connected')
    return response.data
  },

  connectPlatform: async (platformData) => {
    const response = await apiClient.post('/platforms/connect', platformData)
    return response.data
  },

  syncPlatform: async (platformId) => {
    const response = await apiClient.post(`/platforms/sync/${platformId}`)
    return response.data
  },

  disconnectPlatform: async (platformId) => {
    const response = await apiClient.delete(`/platforms/${platformId}`)
    return response.data
  },

  getPlatformProblems: async (platformId) => {
    const response = await apiClient.get(`/platforms/${platformId}/problems`)
    return response.data
  },

  getProblemSubmissions: async (platformId, problemId) => {
    const response = await apiClient.get(`/platforms/${platformId}/problems/${problemId}/submissions`)
    return response.data
  },
}
