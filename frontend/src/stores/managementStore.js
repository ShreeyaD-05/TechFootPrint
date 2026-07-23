import { create } from 'zustand'

export const useManagementStore = create((set) => ({
  collegeOverview: null,
  batchAnalytics: {},
  departmentAnalytics: {},
  inactiveStudents: [],
  placementReadiness: null,
  
  setCollegeOverview: (overview) => set({ collegeOverview: overview }),
  
  setBatchAnalytics: (batchYear, analytics) =>
    set((state) => ({
      batchAnalytics: { ...state.batchAnalytics, [batchYear]: analytics },
    })),
  
  setDepartmentAnalytics: (department, analytics) =>
    set((state) => ({
      departmentAnalytics: { ...state.departmentAnalytics, [department]: analytics },
    })),
  
  setInactiveStudents: (students) => set({ inactiveStudents: students }),
  
  setPlacementReadiness: (readiness) => set({ placementReadiness: readiness }),
  
  clearManagementData: () =>
    set({
      collegeOverview: null,
      batchAnalytics: {},
      departmentAnalytics: {},
      inactiveStudents: [],
      placementReadiness: null,
    }),
}))
