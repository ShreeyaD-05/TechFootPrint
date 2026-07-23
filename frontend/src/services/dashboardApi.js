import apiClient from './apiClient'

export const dashboardApi = {
  // Student Dashboard
  getStudentOverview: () =>
    apiClient.get('/dashboard/student/overview').then(r => r.data),

  getStudentActivity: (days = 30) =>
    apiClient.get('/dashboard/student/activity', { params: { days } }).then(r => r.data),

  getStudentHeatmap: (days = 365) =>
    apiClient.get('/dashboard/student/heatmap', { params: { days } }).then(r => r.data),

  getStudentStreak: () =>
    apiClient.get('/dashboard/student/streak').then(r => r.data),

  // Faculty Dashboard
  getFacultyOverview: () =>
    apiClient.get('/dashboard/faculty/overview').then(r => r.data),

  getStudentDetails: (studentId) =>
    apiClient.get(`/dashboard/faculty/student/${studentId}`).then(r => r.data),

  // Management Dashboard
  getManagementOverview: () =>
    apiClient.get('/dashboard/management/overview').then(r => r.data),

  getBatchDetails: (batchYear) =>
    apiClient.get(`/dashboard/management/batch/${batchYear}`).then(r => r.data),

  getDepartmentDetails: (department) =>
    apiClient.get(`/dashboard/management/department/${department}`).then(r => r.data),

  // College KPIs (BI dashboard)
  getCollegeKPIs: () =>
    apiClient.get('/dashboard/kpi/college').then(r => r.data),

  // Activity Logging
  logActivity: (activityType, platform = null, activityData = null) =>
    apiClient.post('/dashboard/activity/log', null, {
      params: { activity_type: activityType, platform, activity_data: activityData },
    }).then(r => r.data),
}
