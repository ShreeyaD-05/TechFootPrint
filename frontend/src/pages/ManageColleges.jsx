import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { adminApi } from '../services/adminApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import {
  Building2, PlusCircle, Pencil, Trash2, Search, Users,
  GraduationCap, X, ChevronRight, MapPin, Hash, TrendingUp,
  ToggleLeft, ToggleRight, Eye,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

const TIERS = ['free', 'basic', 'premium', 'enterprise']

const emptyForm = {
  name: '', code: '', location: '', admin_notes: '',
  max_students: '', subscription_tier: 'free',
}

const emptyEditForm = {
  name: '', location: '', admin_notes: '',
  max_students: '', subscription_tier: 'free', is_active: true,
}

// ── College Form Modal ────────────────────────────────────────────────────────
function CollegeFormModal({ title, form, setForm, onSubmit, onClose, isPending, isEdit }) {
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
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1 col-span-2">
                <label className="text-sm font-medium">College Name *</label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. MIT College of Engineering"
                  required
                />
              </div>
              {!isEdit && (
                <div className="space-y-1">
                  <label className="text-sm font-medium">College Code *</label>
                  <Input
                    value={form.code}
                    onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                    placeholder="e.g. MITCOE"
                    required
                  />
                </div>
              )}
              <div className="space-y-1">
                <label className="text-sm font-medium">Location</label>
                <Input
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  placeholder="e.g. Pune, Maharashtra"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Max Students</label>
                <Input
                  type="number"
                  value={form.max_students}
                  onChange={(e) => setForm({ ...form, max_students: e.target.value })}
                  placeholder="e.g. 1000"
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium">Subscription Tier</label>
                <select
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                  value={form.subscription_tier}
                  onChange={(e) => setForm({ ...form, subscription_tier: e.target.value })}
                >
                  {TIERS.map((t) => (
                    <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
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
              <div className="space-y-1 col-span-2">
                <label className="text-sm font-medium">Admin Notes</label>
                <textarea
                  className="w-full border rounded-md px-3 py-2 text-sm bg-background min-h-[80px] resize-none"
                  value={form.admin_notes}
                  onChange={(e) => setForm({ ...form, admin_notes: e.target.value })}
                  placeholder="Internal notes about this college…"
                />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <Button type="submit" className="flex-1" disabled={isPending}>
                {isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create College'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

// ── College Detail Drawer ─────────────────────────────────────────────────────
function CollegeDetailDrawer({ college, onClose, onManageFaculty }) {
  const { data: faculty = [], isLoading } = useQuery({
    queryKey: ['admin-faculty', college.id],
    queryFn: () => adminApi.getAllFaculty(college.id),
  })

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[85vh] flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between shrink-0">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              {college.name}
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Code: <span className="font-mono">{college.code}</span>
              {college.location && <> · {college.location}</>}
            </p>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto space-y-4">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-muted/40 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-blue-600">{college.total_students ?? 0}</p>
              <p className="text-xs text-muted-foreground">Students</p>
            </div>
            <div className="bg-muted/40 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-purple-600">{college.total_faculty ?? 0}</p>
              <p className="text-xs text-muted-foreground">Faculty</p>
            </div>
            <div className="bg-muted/40 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-green-600">{college.max_students ?? '∞'}</p>
              <p className="text-xs text-muted-foreground">Max Students</p>
            </div>
          </div>

          {/* Faculty list */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold">Faculty Members ({faculty.length})</h3>
              <Button size="sm" variant="outline" onClick={onManageFaculty}>
                <GraduationCap className="h-3.5 w-3.5 mr-1" />
                Manage Faculty
              </Button>
            </div>
            {isLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : faculty.length === 0 ? (
              <div className="text-center py-6 text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                <GraduationCap className="h-8 w-8 mx-auto mb-1 opacity-30" />
                No faculty assigned yet
              </div>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {faculty.map((f) => (
                  <div key={f.id} className="flex items-center gap-3 p-2 rounded-lg border">
                    <div className="h-8 w-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-700 dark:text-purple-300 font-semibold text-xs shrink-0">
                      {(f.full_name || f.username)?.[0]?.toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{f.full_name || f.username}</p>
                      <p className="text-xs text-muted-foreground">{f.email}</p>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">{f.department || f.role}</span>
                    <Badge variant={f.is_active ? 'success' : 'secondary'} className="shrink-0">
                      {f.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Notes */}
          {college.admin_notes && (
            <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
              <p className="text-xs font-medium text-amber-700 dark:text-amber-300 mb-1">Admin Notes</p>
              <p className="text-sm text-amber-800 dark:text-amber-200">{college.admin_notes}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ManageColleges() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [filterTier, setFilterTier] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [detailTarget, setDetailTarget] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [createForm, setCreateForm] = useState(emptyForm)
  const [editForm, setEditForm] = useState(emptyEditForm)

  const { data: colleges = [], isLoading } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
  })

  const createMutation = useMutation({
    mutationFn: adminApi.createCollege,
    onSuccess: () => {
      qc.invalidateQueries(['admin-colleges'])
      qc.invalidateQueries(['admin-dashboard'])
      setShowCreate(false)
      setCreateForm(emptyForm)
      toast.success('College created successfully!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to create college'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => adminApi.updateCollege(id, data),
    onSuccess: () => {
      qc.invalidateQueries(['admin-colleges'])
      qc.invalidateQueries(['admin-dashboard'])
      setEditTarget(null)
      toast.success('College updated successfully!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update college'),
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteCollege,
    onSuccess: () => {
      qc.invalidateQueries(['admin-colleges'])
      qc.invalidateQueries(['admin-dashboard'])
      setConfirmDelete(null)
      toast.success('College deactivated')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to deactivate'),
  })

  const openEdit = (college) => {
    setEditTarget(college)
    setEditForm({
      name: college.name,
      location: college.location || '',
      admin_notes: college.admin_notes || '',
      max_students: college.max_students || '',
      subscription_tier: college.subscription_tier,
      is_active: college.is_active,
    })
  }

  const handleCreate = (e) => {
    e.preventDefault()
    createMutation.mutate({
      ...createForm,
      max_students: parseInt(createForm.max_students) || null,
    })
  }

  const handleUpdate = (e) => {
    e.preventDefault()
    updateMutation.mutate({
      id: editTarget.id,
      data: {
        ...editForm,
        max_students: parseInt(editForm.max_students) || null,
      },
    })
  }

  const tierColor = {
    free: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    basic: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    premium: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    enterprise: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  }

  const filtered = colleges.filter((c) => {
    const q = search.toLowerCase()
    const matchSearch = !search || c.name?.toLowerCase().includes(q) || c.code?.toLowerCase().includes(q) || c.location?.toLowerCase().includes(q)
    const matchTier = !filterTier || c.subscription_tier === filterTier
    const matchStatus = !filterStatus || (filterStatus === 'active' ? c.is_active : !c.is_active)
    return matchSearch && matchTier && matchStatus
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" />
            Manage Colleges
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create, edit, and manage all registered colleges
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <PlusCircle className="h-4 w-4 mr-2" />
          Add College
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Total Colleges</p>
          <p className="text-2xl font-bold mt-1">{colleges.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Active</p>
          <p className="text-2xl font-bold mt-1 text-green-600">{colleges.filter((c) => c.is_active).length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Total Students</p>
          <p className="text-2xl font-bold mt-1 text-blue-600">{colleges.reduce((s, c) => s + (c.total_students || 0), 0)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Total Faculty</p>
          <p className="text-2xl font-bold mt-1 text-purple-600">{colleges.reduce((s, c) => s + (c.total_faculty || 0), 0)}</p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search by name, code, location…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterTier}
          onChange={(e) => setFilterTier(e.target.value)}
        >
          <option value="">All Tiers</option>
          {TIERS.map((t) => <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
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
          <CardTitle>Colleges ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading…</div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Building2 className="h-10 w-10 mx-auto mb-2 opacity-40" />
              <p>No colleges found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/30">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium">College</th>
                    <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Location</th>
                    <th className="text-left px-4 py-3 font-medium">Students / Faculty</th>
                    <th className="text-left px-4 py-3 font-medium">Tier</th>
                    <th className="text-left px-4 py-3 font-medium">Status</th>
                    <th className="text-right px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {filtered.map((college) => (
                    <tr key={college.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                            <Building2 className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{college.name}</p>
                            <p className="text-xs text-muted-foreground font-mono">{college.code}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {college.location || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1 text-blue-600">
                            <Users className="h-3.5 w-3.5" />
                            {college.total_students ?? 0}
                          </span>
                          <span className="flex items-center gap-1 text-purple-600">
                            <GraduationCap className="h-3.5 w-3.5" />
                            {college.total_faculty ?? 0}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn('text-xs font-medium px-2 py-1 rounded-full capitalize', tierColor[college.subscription_tier] || 'bg-secondary text-secondary-foreground')}>
                          {college.subscription_tier}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={college.is_active ? 'success' : 'secondary'}>
                          {college.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setDetailTarget(college)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="View Details"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => openEdit(college)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setConfirmDelete(college)}
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

      {/* Create Modal */}
      {showCreate && (
        <CollegeFormModal
          title="Create New College"
          form={createForm}
          setForm={setCreateForm}
          onSubmit={handleCreate}
          onClose={() => { setShowCreate(false); setCreateForm(emptyForm) }}
          isPending={createMutation.isPending}
          isEdit={false}
        />
      )}

      {/* Edit Modal */}
      {editTarget && (
        <CollegeFormModal
          title={`Edit — ${editTarget.name}`}
          form={editForm}
          setForm={setEditForm}
          onSubmit={handleUpdate}
          onClose={() => setEditTarget(null)}
          isPending={updateMutation.isPending}
          isEdit={true}
        />
      )}

      {/* Detail Drawer */}
      {detailTarget && (
        <CollegeDetailDrawer
          college={detailTarget}
          onClose={() => setDetailTarget(null)}
          onManageFaculty={() => { setDetailTarget(null); navigate('/admin/faculty') }}
        />
      )}

      {/* Confirm Deactivate */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-sm">
            <CardHeader>
              <CardTitle className="text-red-600">Deactivate College?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                This will deactivate <strong>{confirmDelete.name}</strong>. All associated users will still exist but the college will be marked inactive.
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
