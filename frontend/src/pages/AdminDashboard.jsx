import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../services/adminApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { 
  Users, Building2, TrendingUp, UserPlus, PlusCircle, 
  Shield, GraduationCap 
} from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function AdminDashboard() {
  const queryClient = useQueryClient()
  const [showCollegeForm, setShowCollegeForm] = useState(false)
  const [showUserForm, setShowUserForm] = useState(false)
  
  const [collegeForm, setCollegeForm] = useState({
    name: '',
    code: '',
    location: '',
    max_students: null,
    subscription_tier: 'free'
  })
  
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'student',
    college_id: null,
    department: '',
    batch_year: null
  })

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: adminApi.getDashboard,
  })

  const { data: colleges } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
  })

  const createCollegeMutation = useMutation({
    mutationFn: adminApi.createCollege,
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-colleges'])
      queryClient.invalidateQueries(['admin-dashboard'])
      setShowCollegeForm(false)
      setCollegeForm({ name: '', code: '', location: '', max_students: null, subscription_tier: 'free' })
      toast.success('College created successfully!')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create college')
    }
  })

  const createUserMutation = useMutation({
    mutationFn: adminApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-dashboard'])
      setShowUserForm(false)
      setUserForm({
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'student',
        college_id: null,
        department: '',
        batch_year: null
      })
      toast.success('User created successfully!')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create user')
    }
  })

  const handleCreateCollege = (e) => {
    e.preventDefault()
    createCollegeMutation.mutate(collegeForm)
  }

  const handleCreateUser = (e) => {
    e.preventDefault()
    createUserMutation.mutate(userForm)
  }

  if (isLoading) {
    return <div className="p-6">Loading...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-8 w-8 text-primary" />
            Super Admin Dashboard
          </h1>
          <p className="text-muted-foreground">System-wide management and statistics</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowCollegeForm(true)}>
            <PlusCircle className="h-4 w-4 mr-2" />
            Add College
          </Button>
          <Button onClick={() => setShowUserForm(true)} variant="outline">
            <UserPlus className="h-4 w-4 mr-2" />
            Add User
          </Button>
        </div>
      </div>

      {/* System Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {dashboard?.total_students || 0} students, {dashboard?.total_faculty || 0} faculty
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Colleges</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.total_colleges || 0}</div>
            <p className="text-xs text-muted-foreground">Registered institutions</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Problems Solved</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.total_problems_solved || 0}</div>
            <p className="text-xs text-muted-foreground">Across all platforms</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active This Week</CardTitle>
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard?.active_users_week || 0}</div>
            <p className="text-xs text-muted-foreground">Active users</p>
          </CardContent>
        </Card>
      </div>

      {/* Colleges List */}
      <Card>
        <CardHeader>
          <CardTitle>Registered Colleges</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {colleges && colleges.length > 0 ? (
              colleges.map((college) => (
                <div
                  key={college.id}
                  className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent"
                >
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Building2 className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{college.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Code: {college.code} • {college.location || 'No location'}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {college.total_students} students • {college.total_faculty} faculty
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={college.is_active ? 'success' : 'secondary'}>
                      {college.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Badge variant="outline">{college.subscription_tier}</Badge>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Building2 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No colleges registered yet</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Users */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {dashboard?.recent_users && dashboard.recent_users.length > 0 ? (
              dashboard.recent_users.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div>
                    <p className="font-medium">{user.full_name || user.username}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                  <Badge variant="outline" className="capitalize">
                    {user.role.replace('_', ' ')}
                  </Badge>
                </div>
              ))
            ) : (
              <p className="text-center py-4 text-muted-foreground">No recent users</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* College Form Modal */}
      {showCollegeForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Create New College</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateCollege} className="space-y-4">
                <div>
                  <label className="text-sm font-medium">College Name</label>
                  <Input
                    value={collegeForm.name}
                    onChange={(e) => setCollegeForm({ ...collegeForm, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">College Code</label>
                  <Input
                    value={collegeForm.code}
                    onChange={(e) => setCollegeForm({ ...collegeForm, code: e.target.value.toUpperCase() })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Location</label>
                  <Input
                    value={collegeForm.location}
                    onChange={(e) => setCollegeForm({ ...collegeForm, location: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Max Students</label>
                  <Input
                    type="number"
                    value={collegeForm.max_students || ''}
                    onChange={(e) => setCollegeForm({ ...collegeForm, max_students: parseInt(e.target.value) || null })}
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">Create College</Button>
                  <Button type="button" variant="outline" onClick={() => setShowCollegeForm(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* User Form Modal */}
      {showUserForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
          <Card className="w-full max-w-md my-8">
            <CardHeader>
              <CardTitle>Create New User</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateUser} className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Username</label>
                  <Input
                    value={userForm.username}
                    onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Email</label>
                  <Input
                    type="email"
                    value={userForm.email}
                    onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Password</label>
                  <Input
                    type="password"
                    value={userForm.password}
                    onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Full Name</label>
                  <Input
                    value={userForm.full_name}
                    onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Role</label>
                  <select
                    className="w-full p-2 border rounded"
                    value={userForm.role}
                    onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                  >
                    <option value="student">Student</option>
                    <option value="faculty">Faculty</option>
                    <option value="dept_admin">Department Admin</option>
                    <option value="management">Management</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">College</label>
                  <select
                    className="w-full p-2 border rounded"
                    value={userForm.college_id || ''}
                    onChange={(e) => setUserForm({ ...userForm, college_id: parseInt(e.target.value) || null })}
                  >
                    <option value="">Select College</option>
                    {colleges?.map((college) => (
                      <option key={college.id} value={college.id}>
                        {college.name}
                      </option>
                    ))}
                  </select>
                </div>
                {userForm.role === 'student' && (
                  <>
                    <div>
                      <label className="text-sm font-medium">Department</label>
                      <Input
                        value={userForm.department}
                        onChange={(e) => setUserForm({ ...userForm, department: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium">Batch Year</label>
                      <Input
                        type="number"
                        value={userForm.batch_year || ''}
                        onChange={(e) => setUserForm({ ...userForm, batch_year: parseInt(e.target.value) || null })}
                      />
                    </div>
                  </>
                )}
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">Create User</Button>
                  <Button type="button" variant="outline" onClick={() => setShowUserForm(false)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
