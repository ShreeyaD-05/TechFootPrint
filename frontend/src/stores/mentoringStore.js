import { create } from 'zustand'

export const useMentoringStore = create((set) => ({
  students: [],
  mentor: null,
  feedback: [],
  goals: [],
  notes: [],
  
  setStudents: (students) => set({ students }),
  setMentor: (mentor) => set({ mentor }),
  setFeedback: (feedback) => set({ feedback }),
  setGoals: (goals) => set({ goals }),
  setNotes: (notes) => set({ notes }),
  
  addFeedback: (newFeedback) =>
    set((state) => ({ feedback: [newFeedback, ...state.feedback] })),
  
  markFeedbackRead: (feedbackId) =>
    set((state) => ({
      feedback: state.feedback.map((f) =>
        f.id === feedbackId ? { ...f, is_read: true } : f
      ),
    })),
  
  addNote: (note) =>
    set((state) => ({ notes: [note, ...state.notes] })),
  
  clearMentoringData: () =>
    set({
      students: [],
      mentor: null,
      feedback: [],
      goals: [],
      notes: [],
    }),
}))
