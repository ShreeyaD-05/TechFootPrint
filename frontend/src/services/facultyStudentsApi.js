import apiClient from './apiClient'

export const facultyStudentsApi = {
  // Student CRUD
  getStudents: async (filters = {}) => {
    const response = await apiClient.get('/faculty/students', { params: filters })
    return response.data
  },

  getStudent: async (studentId, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get(`/faculty/students/${studentId}`, { params })
    return response.data
  },

  createStudent: async (studentData, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.post('/faculty/students', studentData, { params })
    return response.data
  },

  updateStudent: async (studentId, studentData, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.put(`/faculty/students/${studentId}`, studentData, { params })
    return response.data
  },

  deleteStudent: async (studentId, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.delete(`/faculty/students/${studentId}`, { params })
    return response.data
  },

  resetStudentPassword: async (studentId, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.post(`/faculty/students/${studentId}/reset-password`, {}, { params })
    return response.data
  },

  // Bulk upload
  bulkUpload: async (file, sendEmails = true, collegeId = null) => {
    const formData = new FormData()
    formData.append('file', file)
    const params = { send_emails: sendEmails }
    if (collegeId) params.college_id = collegeId
    const response = await apiClient.post('/faculty/students/bulk-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    })
    return response.data
  },

  getBulkTemplate: async () => {
    const response = await apiClient.get('/faculty/students/bulk-upload/template')
    return response.data
  },
}
