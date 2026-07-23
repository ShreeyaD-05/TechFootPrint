import apiClient from './apiClient'

export const suggestionsApi = {
  getSuggestions: (params = {}) =>
    apiClient.get('/api/suggestions', { params }).then(r => r.data),

  getSkillAnalysis: () =>
    apiClient.get('/api/suggestions/skill-analysis').then(r => r.data),

  getBatchReadiness: (params = {}) =>
    apiClient.get('/api/suggestions/batch-readiness', { params }).then(r => r.data),
}
