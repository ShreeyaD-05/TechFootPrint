import apiClient from './apiClient'

export const portfolioApi = {
  generatePortfolio: async () => {
    const response = await apiClient.post('/portfolio/generate')
    return response.data
  },

  getPublicPortfolio: async (slug) => {
    const response = await apiClient.get(`/portfolio/${slug}`)
    return response.data
  },
}
