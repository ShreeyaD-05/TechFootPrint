import apiClient from './apiClient'

export const mentoringApi = {
  // Mentor Assignments
  assignMentor: async (mentorId, studentId) => {
    const response = await apiClient.post('/mentoring/assignments', {
      mentor_id: mentorId,
      student_id: studentId,
    })
    return response.data
  },

  getMyStudents: async () => {
    const response = await apiClient.get('/mentoring/my-students')
    return response.data
  },

  getMyMentor: async () => {
    const response = await apiClient.get('/mentoring/my-mentor')
    return response.data
  },

  // Feedback
  createFeedback: async (feedbackData) => {
    const response = await apiClient.post('/mentoring/feedback', feedbackData)
    return response.data
  },

  getMyFeedback: async (unreadOnly = false) => {
    const response = await apiClient.get('/mentoring/feedback', {
      params: { unread_only: unreadOnly },
    })
    return response.data
  },

  markFeedbackRead: async (feedbackId) => {
    const response = await apiClient.put(`/mentoring/feedback/${feedbackId}/read`)
    return response.data
  },

  // Goals
  createGoal: async (goalData) => {
    const response = await apiClient.post('/mentoring/goals', goalData)
    return response.data
  },

  getMyGoals: async () => {
    const response = await apiClient.get('/mentoring/goals')
    return response.data
  },

  // Notes
  createNote: async (noteData) => {
    const response = await apiClient.post('/mentoring/notes', noteData)
    return response.data
  },

  getMyNotes: async (problemStatId = null) => {
    const response = await apiClient.get('/mentoring/notes', {
      params: problemStatId ? { problem_stat_id: problemStatId } : {},
    })
    return response.data
  },

  // Student Progress
  getStudentProgress: async (studentId) => {
    const response = await apiClient.get(`/mentoring/students/${studentId}/progress`)
    return response.data
  },
}
