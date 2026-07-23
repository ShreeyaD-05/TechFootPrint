import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../services/adminApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import {
  Users, UserPlus, Pencil, Trash2, KeyRound, Search,
  X, Shield, GraduationCap, Building2, Filter,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'
import { format } from 'date-fns'

const ROLES = [
  { value: 'student', label: 'Student', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  { value: 'faculty', label: 'Faculty', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  { value: 'dept_admin', label: 'Dept. Admin', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300' },
  { value: 'management', label: 'Management', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' },
  { value: 'super_admin', label: 'Super Admin', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' },
]

const roleColor = Object.fromEntries(ROLES.map((r) => [r.value, r.color]))
const roleLabel = Object.fromEntries(ROLES.map((r) => [r.value, r.label]))

const emptyCreateForm = {
  username: '', email: '', password: '', full_name: '',
  role: 'student', college_id: '', department: '', batch_year: '', enrollment_number: '',
}

const emptyEditForm = {
  full_name: '', role: 'student', college_id: '',
  department: '', batch_year: '', enrollment_number: '', is_active: true,
}

// ── User Form Modal ───────────────────────────────────────────────────────────
function UserFormModal({ title, form, setForm, onSubmit, onClose, isPending, isEdit, colleges }) {
  const isStudent = form.role === 'student'
  const isFaculty = ['faculty', 'dept_admin', 'management'].includes(form.role)

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-card z-10">
          <CardTitle>{title}</CardTitle>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            {/* Basic info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Full Name</label>
                <Input
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  placeholder="John Doe"
                />
              </div>
              {!isEdit && (
                <div className="space-y-1">
                  <label className="text-sm font-medium">Username *</label>
                  <Input
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    required
                  />
                </div>
              )}
            </div>

            {!isEdit && (
              <>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Email *</label>
                  <Input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Password *</label>
                  <Input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    placeholder="Min 8 characters"
                  />
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium">Role *</label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  {ROLES.filter((r) => r.value !== 'super_admin').map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">College</label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                  value={form.college_id}
                  onChange={(e) => setForm({ ...form, college_id: e.target.value })}
                >
                  <option value="">No College</option>
                  {colleges.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {(isStudent || isFaculty) && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Department</label>
                <Input
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  placeholder="e.g. Computer Science"
                />
              </div>
            )}

            {isStudent && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Batch Year</label>
                  <Input
                    type="number"
                    value={form.batch_year}
                    onChange={(e) => setForm({ ...form, batch_year: e.target.value })}
                    placeholder="e.g. 2025"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium">Enrollment No.</label>
                  <Input
                    value={form.enrollment_number}
                    onChange={(e) => setForm({ ...form, enrollment_number: e.target.value })}
                    placeholder="e.g. CS2025001"
                  />
                </div>
              </div>
            )}

            {isEdit && (
              <div className="space-y-1">
                <label className="text-sm font-medium">Status</label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                  value={form.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setForm({ ...form, is_active: e.target.value === 'active' })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            )}

            <div className="flex gap-2 pt-2">
              <Button type="submit" className="flex-1" disabled={isPending}>
                {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create User'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ManageUsers() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [filterRole, setFilterRole] = useState('')
  const [filterCollege, setFilterCollege] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [createForm, setCreateForm] = useState(emptyCreateForm)
  const [editForm, setEditForm] = useState(emptyEditForm)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users', filterRole, filterCollege],
    queryFn: () => adminApi.getAllUsers({
      role: filterRole || undefined,
      college_id: filterCollege || undefined,
    }),
  })

  const { data: colleges = [] } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
  })

  const createMutation = useMutation({
    mutationFn: adminApi.createUser,
    onSuccess: () => {
      qc.invalidateQueries(['admin-users'])
      qc.invalidateQueries(['admin-dashboard'])
      setShowCreate(false)
      setCreateForm(emptyCreateForm)
      toast.success('User created successfully!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to create user'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => adminApi.updateUser(id, data),
    onSuccess: () => {
      qc.invalidateQueries(['admin-users'])
      setEditTarget(null)
      toast.success('User updated successfully!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update user'),
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      qc.invalidateQueries(['admin-users'])
      qc.invalidateQueries(['admin-dashboard'])
      setConfirmDelete(null)
      toast.success('User deactivated')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to deactivate'),
  })

  const openEdit = (user) => {
    setEditTarget(user)
    setEditForm({
      full_name: user.full_name || '',
      role: user.role,
      college_id: user.college_id || '',
      department: user.department || '',
      batch_year: user.batch_year || '',
      enrollment_number: user.enrollment_number || '',
      is_active: user.is_active,
    })
  }

  const handleCreate = (e) => {
    e.preventDefault()
    createMutation.mutate({
      ...createForm,
      college_id: parseInt(createForm.college_id) || null,
      batch_year: parseInt(createForm.batch_year) || null,
    })
  }

  const handleUpdate = (e) => {
    e.preventDefault()
    updateMutation.mutate({
      id: editTarget.id,
      data: {
        ...editForm,
        college_id: parseInt(editForm.college_id) || null,
        batch_year: parseInt(editForm.batch_year) || null,
      },
    })
  }

  const collegeMap = Object.fromEntries(colleges.map((c) => [c.id, c.name]))

  // Client-side search + status filter (role/college already filtered server-side)
  const filtered = users.filter((u) => {
    const q = search.toLowerCase()
    const matchSearch = !search ||
      u.username?.toLowerCase().includes(q) ||
      u.email?.toLowerCase().includes(q) ||
      u.full_name?.toLowerCase().includes(q)
    const matchStatus = !filterStatus || (filterStatus === 'active' ? u.is_active : !u.is_active)
    return matchSearch && matchStatus
  })

  // Role counts
  const roleCounts = ROLES.reduce((acc, r) => {
    acc[r.value] = users.filter((u) => u.role === r.value).length
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" />
            Manage Users
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            View and manage all platform users
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Add User
        </Button>
      </div>

      {/* Role stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {ROLES.map((r) => (
          <button
            key={r.value}
            onClick={() => setFilterRole(filterRole === r.value ? '' : r.value)}
            className={cn(
              'p-3 rounded-lg border text-left transition-all',
              filterRole === r.value ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
            )}
          >
            <p className="text-xs text-muted-foreground">{r.label}</p>
            <p className="text-xl font-bold mt-0.5">{roleCounts[r.value] || 0}</p>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search by name, email, username…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
        >
          <option value="">All Roles</option>
          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterCollege}
          onChange={(e) => setFilterCollege(e.target.value)}
        >
          <option value="">All Colleges</option>
          {colleges.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Users className="h-10 w-10 mx-auto mb-2 opacity-40" />
              <p>No users found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/30">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium">User</th>
                    <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Email</th>
                    <th className="text-left px-4 py-3 font-medium">Role</th>
                    <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">College</th>
                    <th className="text-left px-4 py-3 font-medium hidden lg:table-cell">Dept / Batch</th>
                    <th className="text-left px-4 py-3 font-medium">Status</th>
                    <th className="text-right px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filtered.map((user) => (
                    <tr key={user.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className={cn(
                            'h-8 w-8 rounded-full flex items-center justify-center font-semibold text-xs shrink-0',
                            roleColor[user.role] || 'bg-secondary text-secondary-foreground'
                          )}>
                            {(user.full_name || user.username)?.[0]?.toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{user.full_name || user.username}</p>
                            <p className="text-xs text-muted-foreground">@{user.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{user.email}</td>
                      <td className="px-4 py-3">
                        <span className={cn('text-xs font-medium px-2 py-1 rounded-full', roleColor[user.role] || 'bg-secondary text-secondary-foreground')}>
                          {roleLabel[user.role] || user.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">
                        {user.college_id ? (
                          <span className="flex items-center gap-1">
                            <Building2 className="h-3 w-3" />
                            {collegeMap[user.college_id] || `#${user.college_id}`}
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell">
                        {user.department || '—'}
                        {user.batch_year && <span className="text-xs ml-1">({user.batch_year})</span>}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={user.is_active ? 'success' : 'secondary'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openEdit(user)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          {user.role !== 'super_admin' && (
                            <button
                              onClick={() => setConfirmDelete(user)}
                              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-muted-foreground hover:text-red-600"
                              title="Deactivate"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal */}
      {showCreate && (
        <UserFormModal
          title="Create New User"
          form={createForm}
          setForm={setCreateForm}
          onSubmit={handleCreate}
          onClose={() => { setShowCreate(false); setCreateForm(emptyCreateForm) }}
          isPending={createMutation.isPending}
          isEdit={false}
          colleges={colleges}
        />
      )}

      {/* Edit Modal */}
      {editTarget && (
        <UserFormModal
          title={`Edit — ${editTarget.full_name || editTarget.username}`}
          form={editForm}
          setForm={setEditForm}
          onSubmit={handleUpdate}
          onClose={() => setEditTarget(null)}
          isPending={updateMutation.isPending}
          isEdit={true}
          colleges={colleges}
        />
      )}

      {/* Confirm Deactivate */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <CardTitle className="text-red-600">Deactivate User?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                This will deactivate <strong>{confirmDelete.full_name || confirmDelete.username}</strong>.
                They will no longer be able to log in.
              </p>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  className="flex-1"
                  onClick={() => deleteMutation.mutate(confirmDelete.id)}
                  disabled={deleteMutation.isPending}
                >
                  Deactivate
                </Button>
                <Button variant="outline" onClick={() => setConfirmDelete(null)}>Cancel</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
