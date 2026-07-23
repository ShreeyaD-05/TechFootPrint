import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { collegeApi } from '../services/collegeApi'
import { adminApi } from '../services/adminApi'
import { useAuthStore } from '../stores/authStore'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import {
  Building2, Users, GraduationCap, TrendingUp, BookOpen,
  UserCheck, UserX, BarChart3, Layers, Calendar, X, Link2,
  AlertCircle, CheckCircle, ChevronRight,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

const roleColor = {
  faculty: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  dept_admin: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  management: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
}
const roleLabel = { faculty: 'Faculty', dept_admin: 'Dept. Admin', management: 'Management' }

export default function MyCollege() {
  const { user } = useAuthStore()
  const qc = useQueryClient()
  const isSuperAdmin = user?.role === 'super_admin'

  const [selectedCollegeId, setSelectedCollegeId] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // overview | departments | batches | faculty | assignments
  const [showBulkAssign, setShowBulkAssign] = useState(false)
  const [bulkForm, setBulkForm] = useState({ faculty_id: '', batch_year: '', department: '' })

  const effectiveCollegeId = isSuperAdmin ? selectedCollegeId : undefined

  const { data: colleges = [] } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
    enabled: isSuperAdmin,
  })

  const { data: overview, isLoading } = useQuery({
    queryKey: ['college-overview', effectiveCollegeId],
    queryFn: () => collegeApi.getOverview(effectiveCollegeId),
    enabled: !isSuperAdmin || !!selectedCollegeId,
  })

  const { data: assignmentsSummary = [] } = useQuery({
    queryKey: ['college-assignments', effectiveCollegeId],
    queryFn: () => collegeApi.getAssignmentsSummary(effectiveCollegeId),
    enabled: (!isSuperAdmin || !!selectedCollegeId) && activeTab === 'assignments',
  })

  const bulkAssignMutation = useMutation({
    mutationFn: collegeApi.bulkAssignFaculty,
    onSuccess: (data) => {
      qc.invalidateQueries(['college-overview', effectiveCollegeId])
      qc.invalidateQueries(['college-assignments', effectiveCollegeId])
      setShowBulkAssign(false)
      setBulkForm({ faculty_id: '', batch_year: '', department: '' })
      toast.success(data.message)
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Bulk assign failed'),
  })

  const handleBulkAssign = (e) => {
    e.preventDefault()
    if (!bulkForm.faculty_id) { toast.error('Select a faculty member'); return }
    if (!bulkForm.batch_year && !bulkForm.department) { toast.error('Select batch year or department'); return }
    bulkAssignMutation.mutate({
      facultyId: parseInt(bulkForm.faculty_id),
      batchYear: bulkForm.batch_year ? parseInt(bulkForm.batch_year) : undefined,
      department: bulkForm.department || undefined,
      collegeId: effectiveCollegeId,
    })
  }

  const college = overview?.college
  const stats = overview?.stats || {}
  const departments = overview?.departments || []
  const batches = overview?.batches || []
  const faculty = overview?.faculty || []

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building2 },
    { id: 'departments', label: 'Departments', icon: Layers },
    { id: 'batches', label: 'Batches', icon: Calendar },
    { id: 'faculty', label: 'Faculty', icon: GraduationCap },
    { id: 'assignments', label: 'Assignments', icon: Link2 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" />
            My College
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            {college ? college.name : 'College overview and management'}
          </p>
        </div>
        {activeTab === 'assignments' && (
          <Button onClick={() => setShowBulkAssign(true)}>
            <Link2 className="h-4 w-4 mr-2" />
            Bulk Assign
          </Button>
        )}
      </div>

      {/* Super admin college picker */}
      {isSuperAdmin && (
        <Card className="border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-amber-600 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-1">
                  Select a college to view
                </p>
                <select
                  className="w-full sm:w-80 border rounded-md px-3 py-2 text-sm bg-background"
                  value={selectedCollegeId || ''}
                  onChange={(e) => setSelectedCollegeId(parseInt(e.target.value) || null)}
                >
                  <option value="">— Choose a college —</option>
                  {colleges.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {(!isSuperAdmin || selectedCollegeId) && (
        <>
          {/* Tabs */}
          <div className="flex gap-1 border-b overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors',
                  activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="p-12 text-center text-muted-foreground">Loading…</div>
          ) : (
            <>
              {/* ── Overview Tab ── */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* College info card */}
                  {college && (
                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-start gap-4">
                          <div className="h-14 w-14 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                            <Building2 className="h-7 w-7 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h2 className="text-xl font-bold">{college.name}</h2>
                              <Badge variant={college.is_active ? 'success' : 'secondary'}>
                                {college.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                              <Badge variant="outline" className="capitalize">{college.subscription_tier}</Badge>
                            </div>
                            <p className="text-muted-foreground text-sm mt-1">
                              Code: <span className="font-mono font-medium">{college.code}</span>
                              {college.location && <> · {college.location}</>}
                            </p>
                            {college.max_students && (
                              <p className="text-xs text-muted-foreground mt-1">
                                Max students: {college.max_students}
                              </p>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* KPI grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                    {[
                      { label: 'Students', value: stats.total_students ?? 0, icon: Users, color: 'text-blue-600' },
                      { label: 'Faculty', value: stats.total_faculty ?? 0, icon: GraduationCap, color: 'text-purple-600' },
                      { label: 'Unassigned', value: stats.unassigned_students ?? 0, icon: UserX, color: 'text-red-500' },
                      { label: 'Problems Solved', value: stats.total_problems_solved ?? 0, icon: TrendingUp, color: 'text-green-600' },
                      { label: 'Avg Problems', value: stats.avg_problems_per_student ?? 0, icon: BarChart3, color: 'text-amber-600' },
                      { label: 'Avg Streak', value: stats.avg_streak ?? 0, icon: BookOpen, color: 'text-indigo-600' },
                    ].map((kpi) => (
                      <Card key={kpi.label} className="p-4">
                        <div className="flex items-center gap-2 mb-1">
                          <kpi.icon className={cn('h-4 w-4', kpi.color)} />
                          <p className="text-xs text-muted-foreground">{kpi.label}</p>
                        </div>
                        <p className="text-2xl font-bold">{kpi.value}</p>
                      </Card>
                    ))}
                  </div>

                  {/* Quick previews */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center justify-between">
                          Top Departments
                          <button onClick={() => setActiveTab('departments')} className="text-xs text-primary hover:underline flex items-center gap-1">
                            View all <ChevronRight className="h-3 w-3" />
                          </button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {departments.slice(0, 5).map((d) => (
                          <div key={d.name} className="flex items-center justify-between text-sm">
                            <span className="truncate">{d.name}</span>
                            <span className="font-medium ml-2 shrink-0">{d.student_count} students</span>
                          </div>
                        ))}
                        {departments.length === 0 && <p className="text-muted-foreground text-sm">No departments yet</p>}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center justify-between">
                          Batch Distribution
                          <button onClick={() => setActiveTab('batches')} className="text-xs text-primary hover:underline flex items-center gap-1">
                            View all <ChevronRight className="h-3 w-3" />
                          </button>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {batches.slice(0, 5).map((b) => (
                          <div key={b.year} className="flex items-center justify-between text-sm">
                            <span>Batch {b.year}</span>
                            <span className="font-medium">{b.student_count} students</span>
                          </div>
                        ))}
                        {batches.length === 0 && <p className="text-muted-foreground text-sm">No batch data yet</p>}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* ── Departments Tab ── */}
              {activeTab === 'departments' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Departments ({departments.length})</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {departments.length === 0 ? (
                      <div className="p-8 text-center text-muted-foreground">
                        <Layers className="h-10 w-10 mx-auto mb-2 opacity-40" />
                        <p>No department data yet</p>
                      </div>
                    ) : (
                      <div className="divide-y">
                        {departments.map((d, i) => (
                          <div key={d.name} className="flex items-center justify-between px-6 py-4">
                            <div className="flex items-center gap-3">
                              <span className="text-muted-foreground text-sm w-6">{i + 1}</span>
                              <div>
                                <p className="font-medium">{d.name}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-32 bg-muted rounded-full h-2 hidden sm:block">
                                <div
                                  className="bg-primary h-2 rounded-full"
                                  style={{ width: `${Math.min(100, (d.student_count / (departments[0]?.student_count || 1)) * 100)}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-20 text-right">{d.student_count} students</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* ── Batches Tab ── */}
              {activeTab === 'batches' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Batch Distribution ({batches.length} batches)</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {batches.length === 0 ? (
                      <div className="p-8 text-center text-muted-foreground">
                        <Calendar className="h-10 w-10 mx-auto mb-2 opacity-40" />
                        <p>No batch data yet</p>
                      </div>
                    ) : (
                      <div className="divide-y">
                        {batches.map((b) => (
                          <div key={b.year} className="flex items-center justify-between px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
                                {String(b.year).slice(-2)}
                              </div>
                              <p className="font-medium">Batch {b.year}</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="w-32 bg-muted rounded-full h-2 hidden sm:block">
                                <div
                                  className="bg-primary h-2 rounded-full"
                                  style={{ width: `${Math.min(100, (b.student_count / (batches[0]?.student_count || 1)) * 100)}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium w-20 text-right">{b.student_count} students</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* ── Faculty Tab ── */}
              {activeTab === 'faculty' && (
                <Card>
                  <CardHeader>
                    <CardTitle>Faculty Members ({faculty.length})</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {faculty.length === 0 ? (
                      <div className="p-8 text-center text-muted-foreground">
                        <GraduationCap className="h-10 w-10 mx-auto mb-2 opacity-40" />
                        <p>No faculty members yet</p>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="border-b bg-muted/30">
                            <tr>
                              <th className="text-left px-4 py-3 font-medium">Name</th>
                              <th className="text-left px-4 py-3 font-medium">Email</th>
                              <th className="text-left px-4 py-3 font-medium">Department</th>
                              <th className="text-left px-4 py-3 font-medium">Role</th>
                              <th className="text-right px-4 py-3 font-medium">Assigned Students</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {faculty.map((f) => (
                              <tr key={f.id} className="hover:bg-muted/20">
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-xs shrink-0">
                                      {(f.full_name || f.username)?.[0]?.toUpperCase()}
                                    </div>
                                    <div>
                                      <p className="font-medium">{f.full_name || f.username}</p>
                                      <p className="text-xs text-muted-foreground">@{f.username}</p>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-muted-foreground">{f.email}</td>
                                <td className="px-4 py-3 text-muted-foreground">{f.department || '—'}</td>
                                <td className="px-4 py-3">
                                  <span className={cn('text-xs font-medium px-2 py-1 rounded-full', roleColor[f.role] || 'bg-secondary text-secondary-foreground')}>
                                    {roleLabel[f.role] || f.role}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <span className={cn(
                                    'font-semibold',
                                    f.assigned_students === 0 ? 'text-muted-foreground' : 'text-primary'
                                  )}>
                                    {f.assigned_students}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* ── Assignments Tab ── */}
              {activeTab === 'assignments' && (
                <div className="space-y-4">
                  {/* Summary cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-1">
                        <UserCheck className="h-4 w-4 text-green-600" />
                        <p className="text-xs text-muted-foreground">Assigned Students</p>
                      </div>
                      <p className="text-2xl font-bold">
                        {(stats.total_students ?? 0) - (stats.unassigned_students ?? 0)}
                      </p>
                    </Card>
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-1">
                        <UserX className="h-4 w-4 text-red-500" />
                        <p className="text-xs text-muted-foreground">Unassigned Students</p>
                      </div>
                      <p className="text-2xl font-bold text-red-500">{stats.unassigned_students ?? 0}</p>
                    </Card>
                    <Card className="p-4">
                      <div className="flex items-center gap-2 mb-1">
                        <GraduationCap className="h-4 w-4 text-purple-600" />
                        <p className="text-xs text-muted-foreground">Active Faculty</p>
                      </div>
                      <p className="text-2xl font-bold">{stats.total_faculty ?? 0}</p>
                    </Card>
                  </div>

                  {/* Per-faculty assignment table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Faculty Assignment Load</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      {assignmentsSummary.length === 0 ? (
                        <div className="p-8 text-center text-muted-foreground">
                          <Link2 className="h-10 w-10 mx-auto mb-2 opacity-40" />
                          <p>No assignments yet</p>
                        </div>
                      ) : (
                        <div className="divide-y">
                          {assignmentsSummary
                            .sort((a, b) => b.assigned_count - a.assigned_count)
                            .map((row) => (
                              <div key={row.faculty_id} className="flex items-center justify-between px-6 py-4">
                                <div>
                                  <p className="font-medium">{row.faculty_name}</p>
                                  <p className="text-xs text-muted-foreground">{row.department || 'No department'}</p>
                                </div>
                                <div className="flex items-center gap-3">
                                  <div className="w-24 bg-muted rounded-full h-2 hidden sm:block">
                                    <div
                                      className="bg-primary h-2 rounded-full"
                                      style={{
                                        width: `${Math.min(100, (row.assigned_count / Math.max(...assignmentsSummary.map(r => r.assigned_count), 1)) * 100)}%`
                                      }}
                                    />
                                  </div>
                                  <span className={cn(
                                    'text-sm font-semibold w-16 text-right',
                                    row.assigned_count === 0 ? 'text-muted-foreground' : 'text-primary'
                                  )}>
                                    {row.assigned_count} students
                                  </span>
                                </div>
                              </div>
                            ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* Bulk Assign Modal */}
      {showBulkAssign && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Bulk Assign Students to Faculty</CardTitle>
              <button onClick={() => setShowBulkAssign(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleBulkAssign} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium">Assign to Faculty *</label>
                  <select
                    className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                    value={bulkForm.faculty_id}
                    onChange={(e) => setBulkForm({ ...bulkForm, faculty_id: e.target.value })}
                    required
                  >
                    <option value="">— Select faculty —</option>
                    {faculty.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.full_name || f.username} ({f.assigned_students} assigned)
                      </option>
                    ))}
                  </select>
                </div>

                <p className="text-xs text-muted-foreground">Select batch year, department, or both to filter students:</p>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Batch Year</label>
                    <select
                      className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                      value={bulkForm.batch_year}
                      onChange={(e) => setBulkForm({ ...bulkForm, batch_year: e.target.value })}
                    >
                      <option value="">All batches</option>
                      {batches.map((b) => (
                        <option key={b.year} value={b.year}>Batch {b.year}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Department</label>
                    <select
                      className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                      value={bulkForm.department}
                      onChange={(e) => setBulkForm({ ...bulkForm, department: e.target.value })}
                    >
                      <option value="">All departments</option>
                      {departments.map((d) => (
                        <option key={d.name} value={d.name}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground bg-amber-50 dark:bg-amber-900/20 rounded p-2 text-amber-700 dark:text-amber-300">
                  This will replace existing assignments for matching students.
                </p>

                <div className="flex gap-2">
                  <Button type="submit" className="flex-1" disabled={bulkAssignMutation.isPending}>
                    {bulkAssignMutation.isPending ? 'Assigning…' : 'Assign Students'}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setShowBulkAssign(false)}>
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
