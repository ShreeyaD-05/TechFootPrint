import apiClient from './apiClient'

export const authApi = {
  login: async (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  register: async (userData) => {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  logout: () => {
    // Clear local storage and redirect
    return Promise.resolve()
  },
}
