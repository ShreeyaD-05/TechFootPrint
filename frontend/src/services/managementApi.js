import apiClient from './apiClient'

export const managementApi = {
  // College Overview
  getCollegeOverview: async () => {
    const response = await apiClient.get('/management/overview')
    return response.data
  },

  // Batch Analytics
  getBatchAnalytics: async (batchYear) => {
    const response = await apiClient.get(`/management/batch/${batchYear}`)
    return response.data
  },

  // Department Analytics
  getDepartmentAnalytics: async (department) => {
    const response = await apiClient.get(`/management/department/${department}`)
    return response.data
  },

  // Inactive Students
  getInactiveStudents: async (days = 7) => {
    const response = await apiClient.get('/management/inactive-students', {
      params: { days },
    })
    return response.data
  },

  // Placement Readiness
  getPlacementReadiness: async (batchYear) => {
    const response = await apiClient.get(`/management/placement-readiness/${batchYear}`)
    return response.data
  },

  // Batch Mentor Assignment
  assignBatchMentor: async (mentorId, batchYear) => {
    const response = await apiClient.post('/management/assign-batch-mentor', null, {
      params: { mentor_id: mentorId, batch_year: batchYear },
    })
    return response.data
  },
}
