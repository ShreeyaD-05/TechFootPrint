import apiClient from './apiClient'

export const collegeApi = {
  // My College overview
  getOverview: async (collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get('/college/overview', { params })
    return response.data
  },

  getAssignmentsSummary: async (collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get('/college/assignments-summary', { params })
    return response.data
  },

  // Faculty list for assignment dropdown
  getFacultyList: async (collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get('/faculty/faculty-list', { params })
    return response.data
  },

  // Assign / unassign student to faculty
  assignStudentToFaculty: async (studentId, facultyId, collegeId = null) => {
    const params = { faculty_id: facultyId }
    if (collegeId) params.college_id = collegeId
    const response = await apiClient.post(`/faculty/students/${studentId}/assign-faculty`, {}, { params })
    return response.data
  },

  unassignStudentFaculty: async (studentId, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.delete(`/faculty/students/${studentId}/assign-faculty`, { params })
    return response.data
  },

  getStudentAssignedFaculty: async (studentId, collegeId = null) => {
    const params = collegeId ? { college_id: collegeId } : {}
    const response = await apiClient.get(`/faculty/students/${studentId}/assigned-faculty`, { params })
    return response.data
  },

  // Bulk assign
  bulkAssignFaculty: async ({ facultyId, batchYear, department, collegeId }) => {
    const params = { faculty_id: facultyId }
    if (batchYear) params.batch_year = batchYear
    if (department) params.department = department
    if (collegeId) params.college_id = collegeId
    const response = await apiClient.post('/faculty/students/bulk-assign-faculty', {}, { params })
    return response.data
  },
}
