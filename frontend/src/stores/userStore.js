import { create } from 'zustand'

export const useUserStore = create((set) => ({
  profile: null,
  
  setProfile: (profile) => set({ profile }),
  
  updateProfile: (updates) =>
    set((state) => ({
      profile: state.profile ? { ...state.profile, ...updates } : null,
    })),
  
  clearProfile: () => set({ profile: null }),
}))
