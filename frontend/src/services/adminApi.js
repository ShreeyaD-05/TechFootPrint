import apiClient from './apiClient'

export const adminApi = {
  // Dashboard
  getDashboard: async () => {
    const response = await apiClient.get('/admin/dashboard')
    return response.data
  },

  getStats: async () => {
    const response = await apiClient.get('/admin/stats')
    return response.data
  },

  // College Management
  getAllColleges: async () => {
    const response = await apiClient.get('/admin/colleges')
    return response.data
  },

  createCollege: async (collegeData) => {
    const response = await apiClient.post('/admin/colleges', collegeData)
    return response.data
  },

  updateCollege: async (collegeId, collegeData) => {
    const response = await apiClient.put(`/admin/colleges/${collegeId}`, collegeData)
    return response.data
  },

  deleteCollege: async (collegeId) => {
    const response = await apiClient.delete(`/admin/colleges/${collegeId}`)
    return response.data
  },

  // User Management
  getAllUsers: async (filters = {}) => {
    const response = await apiClient.get('/admin/users', { params: filters })
    return response.data
  },

  getUser: async (userId) => {
    const response = await apiClient.get(`/admin/users/${userId}`)
    return response.data
  },

  createUser: async (userData) => {
    const response = await apiClient.post('/admin/users', userData)
    return response.data
  },

  updateUser: async (userId, userData) => {
    const response = await apiClient.put(`/admin/users/${userId}`, userData)
    return response.data
  },

  deleteUser: async (userId) => {
    const response = await apiClient.delete(`/admin/users/${userId}`)
    return response.data
  },

  searchUsers: async (query) => {
    const response = await apiClient.get('/admin/users/search', {
      params: { q: query },
    })
    return response.data
  },

  // Faculty Management
  getAllFaculty: async (collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get('/admin/faculty', { params })
    return response.data
  },

  createFaculty: async (facultyData) => {
    const response = await apiClient.post('/admin/faculty', facultyData)
    return response.data
  },

  updateFaculty: async (facultyId, facultyData) => {
    const response = await apiClient.put(`/admin/faculty/${facultyId}`, facultyData)
    return response.data
  },

  deleteFaculty: async (facultyId) => {
    const response = await apiClient.delete(`/admin/faculty/${facultyId}`)
    return response.data
  },

  resetFacultyPassword: async (facultyId) => {
    const response = await apiClient.post(`/admin/faculty/${facultyId}/reset-password`)
    return response.data
  },
}
