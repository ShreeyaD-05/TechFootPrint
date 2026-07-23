import { create } from 'zustand'

export const useAnalyticsStore = create((set) => ({
  analytics: null,
  heatmapData: null,
  
  setAnalytics: (analytics) => set({ analytics }),
  
  setHeatmapData: (heatmapData) => set({ heatmapData }),
  
  clearAnalytics: () =>
    set({
      analytics: null,
      heatmapData: null,
    }),
}))
