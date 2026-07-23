import apiClient from './apiClient'

export const userApi = {
  getProfile: async () => {
    const response = await apiClient.get('/users/profile')
    return response.data
  },

  createProfile: async (profileData) => {
    const response = await apiClient.post('/users/profile', profileData)
    return response.data
  },

  updateProfile: async (profileData) => {
    const response = await apiClient.put('/users/profile', profileData)
    return response.data
  },

  changePassword: async ({ current_password, new_password }) => {
    const response = await apiClient.post('/auth/change-password', {
      current_password,
      new_password,
    })
    return response.data
  },
}
