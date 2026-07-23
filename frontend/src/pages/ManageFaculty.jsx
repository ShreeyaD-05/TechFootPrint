import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '../services/adminApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import {
  Users, UserPlus, Pencil, Trash2, KeyRound, Search,
  GraduationCap, Building2, X, ChevronDown,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

const ROLE_OPTIONS = [
  { value: 'faculty', label: 'Faculty' },
  { value: 'dept_admin', label: 'Department Admin' },
  { value: 'management', label: 'Management' },
]

const roleColor = {
  faculty: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  dept_admin: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  management: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
}

const emptyForm = {
  email: '', username: '', full_name: '', college_id: '', department: '', role: 'faculty',
}

export default function ManageFaculty() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [filterCollege, setFilterCollege] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState(null) // null = create, user obj = edit
  const [form, setForm] = useState(emptyForm)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const { data: faculty = [], isLoading } = useQuery({
    queryKey: ['admin-faculty', filterCollege],
    queryFn: () => adminApi.getAllFaculty(filterCollege || null),
  })

  const { data: colleges = [] } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
  })

  const createMutation = useMutation({
    mutationFn: adminApi.createFaculty,
    onSuccess: () => {
      qc.invalidateQueries(['admin-faculty'])
      qc.invalidateQueries(['admin-dashboard'])
      closeForm()
      toast.success('Faculty created — welcome email sent!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to create faculty'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => adminApi.updateFaculty(id, data),
    onSuccess: () => {
      qc.invalidateQueries(['admin-faculty'])
      closeForm()
      toast.success('Faculty updated successfully')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update faculty'),
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteFaculty,
    onSuccess: () => {
      qc.invalidateQueries(['admin-faculty'])
      qc.invalidateQueries(['admin-dashboard'])
      setConfirmDelete(null)
      toast.success('Faculty member deactivated')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to deactivate'),
  })

  const resetPasswordMutation = useMutation({
    mutationFn: adminApi.resetFacultyPassword,
    onSuccess: (data) => {
      toast.success(data.email_sent ? 'Password reset — new credentials emailed' : 'Password reset (email disabled)')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to reset password'),
  })

  const openCreate = () => {
    setEditTarget(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  const openEdit = (member) => {
    setEditTarget(member)
    setForm({
      email: member.email,
      username: member.username,
      full_name: member.full_name || '',
      college_id: member.college_id || '',
      department: member.department || '',
      role: member.role,
    })
    setShowForm(true)
  }

  const closeForm = () => {
    setShowForm(false)
    setEditTarget(null)
    setForm(emptyForm)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      college_id: parseInt(form.college_id) || null,
    }
    if (editTarget) {
      const { username, ...updatePayload } = payload
      updateMutation.mutate({ id: editTarget.id, data: updatePayload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const filtered = faculty.filter((m) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      m.username?.toLowerCase().includes(q) ||
      m.email?.toLowerCase().includes(q) ||
      m.full_name?.toLowerCase().includes(q) ||
      m.department?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <GraduationCap className="h-6 w-6 text-primary" />
            Manage Faculty
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create and manage faculty accounts across colleges
          </p>
        </div>
        <Button onClick={openCreate}>
          <UserPlus className="h-4 w-4 mr-2" />
          Add Faculty
        </Button>
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
          value={filterCollege}
          onChange={(e) => setFilterCollege(e.target.value)}
        >
          <option value="">All Colleges</option>
          {colleges.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {ROLE_OPTIONS.map((r) => {
          const count = faculty.filter((m) => m.role === r.value).length
          return (
            <Card key={r.value} className="p-4">
              <p className="text-xs text-muted-foreground">{r.label}</p>
              <p className="text-2xl font-bold mt-1">{count}</p>
            </Card>
          )
        })}
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Total</p>
          <p className="text-2xl font-bold mt-1">{faculty.length}</p>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Faculty Members ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Users className="h-10 w-10 mx-auto mb-2 opacity-40" />
              <p>No faculty members found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/30">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium">Name</th>
                    <th className="text-left px-4 py-3 font-medium">Email</th>
                    <th className="text-left px-4 py-3 font-medium">College</th>
                    <th className="text-left px-4 py-3 font-medium">Department</th>
                    <th className="text-left px-4 py-3 font-medium">Role</th>
                    <th className="text-left px-4 py-3 font-medium">Status</th>
                    <th className="text-right px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filtered.map((member) => (
                    <tr key={member.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-xs shrink-0">
                            {(member.full_name || member.username)?.[0]?.toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{member.full_name || member.username}</p>
                            <p className="text-xs text-muted-foreground">@{member.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{member.email}</td>
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <Building2 className="h-3 w-3" />
                          {member.college_name || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{member.department || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={cn('text-xs font-medium px-2 py-1 rounded-full', roleColor[member.role] || 'bg-secondary text-secondary-foreground')}>
                          {ROLE_OPTIONS.find((r) => r.value === member.role)?.label || member.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={member.is_active ? 'success' : 'secondary'}>
                          {member.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openEdit(member)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => resetPasswordMutation.mutate(member.id)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Reset Password"
                          >
                            <KeyRound className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setConfirmDelete(member)}
                            className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-muted-foreground hover:text-red-600"
                            title="Deactivate"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
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

      {/* Create / Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>{editTarget ? 'Edit Faculty Member' : 'Add Faculty Member'}</CardTitle>
              <button onClick={closeForm} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Full Name *</label>
                    <Input
                      value={form.full_name}
                      onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Username *</label>
                    <Input
                      value={form.username}
                      onChange={(e) => setForm({ ...form, username: e.target.value })}
                      required
                      disabled={!!editTarget}
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Email *</label>
                  <Input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">College *</label>
                    <select
                      className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                      value={form.college_id}
                      onChange={(e) => setForm({ ...form, college_id: e.target.value })}
                      required
                    >
                      <option value="">Select College</option>
                      {colleges.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Role *</label>
                    <select
                      className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                    >
                      {ROLE_OPTIONS.map((r) => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Department</label>
                  <Input
                    value={form.department}
                    onChange={(e) => setForm({ ...form, department: e.target.value })}
                    placeholder="e.g. Computer Science"
                  />
                </div>

                {!editTarget && (
                  <p className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
                    A temporary password will be auto-generated and sent to the faculty member's email.
                  </p>
                )}

                <div className="flex gap-2 pt-2">
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={createMutation.isPending || updateMutation.isPending}
                  >
                    {editTarget ? 'Save Changes' : 'Create Faculty'}
                  </Button>
                  <Button type="button" variant="outline" onClick={closeForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Confirm Delete Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <CardTitle className="text-red-600">Deactivate Faculty?</CardTitle>
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
                <Button variant="outline" onClick={() => setConfirmDelete(null)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
