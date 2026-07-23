import { create } from 'zustand'

export const usePlatformStore = create((set) => ({
  connectedPlatforms: [],
  
  setConnectedPlatforms: (platforms) =>
    set({ connectedPlatforms: platforms }),
  
  addPlatform: (platform) =>
    set((state) => ({
      connectedPlatforms: [...state.connectedPlatforms, platform],
    })),
  
  removePlatform: (platformId) =>
    set((state) => ({
      connectedPlatforms: state.connectedPlatforms.filter(
        (p) => p.id !== platformId
      ),
    })),
  
  updatePlatform: (platformId, updates) =>
    set((state) => ({
      connectedPlatforms: state.connectedPlatforms.map((p) =>
        p.id === platformId ? { ...p, ...updates } : p
      ),
    })),
}))
