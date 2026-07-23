import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useThemeStore } from './stores/themeStore'
import { useEffect } from 'react'

// Layouts
import DashboardLayout from './layouts/DashboardLayout'
import AuthLayout from './layouts/AuthLayout'

// Pages
import Landing from './pages/Landing'
import Login from './pages/Auth/Login'
import Dashboard from './pages/Dashboard'
import Platforms from './pages/Platforms'
import Problems from './pages/Problems'
import ProblemSubmissions from './pages/ProblemSubmissions'
import Analytics from './pages/Analytics'
import Portfolio from './pages/Portfolio'
import Settings from './pages/Settings'
import FacultyDashboard from './pages/FacultyDashboard'
import ManagementDashboard from './pages/ManagementDashboard'
import AdminDashboard from './pages/AdminDashboard'
import ManageFaculty from './pages/ManageFaculty'
import ManageStudents from './pages/ManageStudents'
import ManageColleges from './pages/ManageColleges'
import ManageUsers from './pages/ManageUsers'
import MyCollege from './pages/MyCollege'
import Chat from './pages/Chat'
import Discussions from './pages/Discussions'
import Submissions from './pages/Submissions'
import NewDiscussion from './pages/NewDiscussion'
import DiscussionDetail from './pages/DiscussionDetail'
import Suggestions from './pages/Suggestions'

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// Role-based Route Component
const RoleRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, user } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/dashboard" replace />
  }
  
  return children
}

// Public Route Component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore()
  
  if (!isAuthenticated) {
    return children
  }
  
  // Redirect based on role
  if (user?.role === 'super_admin') {
    return <Navigate to="/admin" replace />
  } else if (user?.role === 'faculty') {
    return <Navigate to="/faculty" replace />
  } else if (user?.role === 'management' || user?.role === 'dept_admin') {
    return <Navigate to="/management" replace />
  }
  
  return <Navigate to="/dashboard" replace />
}

function App() {
  const { theme } = useThemeStore()

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Landing />} />
      
      {/* Auth Routes — register removed; accounts are created by admin/faculty */}
      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        {/* Redirect any old /register links to login */}
        <Route path="/register" element={<Navigate to="/login" replace />} />
      </Route>

      {/* Protected Dashboard Routes - Students */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/suggestions" element={<Suggestions />} />
        <Route path="/platforms" element={<Platforms />} />
        <Route path="/problems" element={<Problems />} />
        <Route path="/problems/:platformId/:problemId" element={<ProblemSubmissions />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/discussions" element={<Discussions />} />
        <Route path="/discussions/new" element={<NewDiscussion />} />
        <Route path="/discussions/:id" element={<DiscussionDetail />} />
        <Route path="/submissions" element={<Submissions />} />
        <Route path="/chat" element={<Chat />} />
      </Route>

      {/* Faculty Routes */}
      <Route
        element={
          <RoleRoute allowedRoles={['faculty', 'dept_admin', 'management', 'super_admin']}>
            <DashboardLayout />
          </RoleRoute>
        }
      >
        <Route path="/faculty" element={<FacultyDashboard />} />
        <Route path="/faculty/students" element={<ManageStudents />} />
        <Route path="/my-college" element={<MyCollege />} />
      </Route>

      {/* Management Routes */}
      <Route
        element={
          <RoleRoute allowedRoles={['dept_admin', 'management', 'super_admin']}>
            <DashboardLayout />
          </RoleRoute>
        }
      >
        <Route path="/management" element={<ManagementDashboard />} />
      </Route>

      {/* Super Admin Routes */}
      <Route
        element={
          <RoleRoute allowedRoles={['super_admin']}>
            <DashboardLayout />
          </RoleRoute>
        }
      >
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/colleges" element={<ManageColleges />} />
        <Route path="/admin/users" element={<ManageUsers />} />
        <Route path="/admin/faculty" element={<ManageFaculty />} />
      </Route>

      {/* Public Portfolio */}
      <Route path="/portfolio/:slug" element={<Portfolio isPublic />} />

      {/* 404 */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App