import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { facultyStudentsApi } from '../services/facultyStudentsApi'
import { adminApi } from '../services/adminApi'
import { collegeApi } from '../services/collegeApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import {
  Users, UserPlus, Pencil, Trash2, KeyRound, Search,
  Upload, Download, X, CheckCircle, AlertCircle, FileSpreadsheet, Building2,
  Link2, UserCheck, GraduationCap, ChevronDown,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'
import { useAuthStore } from '../stores/authStore'

// ── Inline assign-faculty cell ────────────────────────────────────────────────
function AssignedFacultyCell({ student, facultyList, onAssign, onUnassign, isAssigning, isUnassigning }) {
  const [open, setOpen] = useState(false)
  const [currentFaculty, setCurrentFaculty] = useState(null)
  const [loaded, setLoaded] = useState(false)

  const handleOpen = async () => {
    if (!loaded) {
      try {
        const data = await collegeApi.getStudentAssignedFaculty(student.id)
        setCurrentFaculty(data.assigned ? data.mentor : null)
      } catch {
        setCurrentFaculty(null)
      }
      setLoaded(true)
    }
    setOpen((o) => !o)
  }

  const handleAssign = (facultyId) => {
    onAssign(student.id, facultyId)
    setOpen(false)
    setLoaded(false) // force reload next open
  }

  const handleUnassign = () => {
    onUnassign(student.id)
    setCurrentFaculty(null)
    setOpen(false)
    setLoaded(false)
  }

  return (
    <div className="relative">
      <button
        onClick={handleOpen}
        className={cn(
          'flex items-center gap-1.5 text-xs px-2 py-1 rounded-md border transition-colors',
          currentFaculty
            ? 'border-purple-200 bg-purple-50 text-purple-700 dark:border-purple-800 dark:bg-purple-900/20 dark:text-purple-300'
            : 'border-dashed border-muted-foreground/30 text-muted-foreground hover:border-primary/50 hover:text-primary'
        )}
      >
        <GraduationCap className="h-3 w-3 shrink-0" />
        <span className="truncate max-w-[100px]">
          {loaded
            ? (currentFaculty ? (currentFaculty.full_name || currentFaculty.username) : 'Assign')
            : 'Assign'}
        </span>
        <ChevronDown className="h-3 w-3 shrink-0" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-full mt-1 z-20 bg-card border rounded-lg shadow-lg w-52 py-1 max-h-56 overflow-y-auto">
            {currentFaculty && (
              <>
                <div className="px-3 py-2 text-xs text-muted-foreground border-b">
                  Currently: <span className="font-medium text-foreground">{currentFaculty.full_name || currentFaculty.username}</span>
                </div>
                <button
                  onClick={handleUnassign}
                  disabled={isUnassigning}
                  className="w-full text-left px-3 py-2 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                >
                  <X className="h-3 w-3" /> Remove assignment
                </button>
                <div className="border-t my-1" />
              </>
            )}
            {facultyList.length === 0 ? (
              <p className="px-3 py-2 text-xs text-muted-foreground">No faculty in this college</p>
            ) : (
              facultyList.map((f) => (
                <button
                  key={f.id}
                  onClick={() => handleAssign(f.id)}
                  disabled={isAssigning}
                  className={cn(
                    'w-full text-left px-3 py-2 text-xs hover:bg-muted/50 flex items-center gap-2',
                    currentFaculty?.id === f.id && 'bg-primary/5 font-medium'
                  )}
                >
                  <div className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-[10px] shrink-0">
                    {(f.full_name || f.username)?.[0]?.toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate">{f.full_name || f.username}</p>
                    <p className="text-muted-foreground truncate">{f.department || f.role}</p>
                  </div>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}

const emptyForm = {
  email: '', username: '', full_name: '', department: '', batch_year: '', enrollment_number: '',
  faculty_id: '',  // for single create — assign faculty at creation time
}

export default function ManageStudents() {
  const qc = useQueryClient()
  const fileInputRef = useRef(null)
  const { user } = useAuthStore()
  const isSuperAdmin = user?.role === 'super_admin'

  // super_admin must pick a college first
  const [selectedCollegeId, setSelectedCollegeId] = useState(null)

  const [search, setSearch] = useState('')
  const [filterDept, setFilterDept] = useState('')
  const [filterBatch, setFilterBatch] = useState('')
  const [activeTab, setActiveTab] = useState('list')
  const [showForm, setShowForm] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [bulkFile, setBulkFile] = useState(null)
  const [bulkResult, setBulkResult] = useState(null)
  const [sendEmails, setSendEmails] = useState(true)

  // Assign to faculty
  const [assignTarget, setAssignTarget] = useState(null) // student being assigned
  const [assignFacultyId, setAssignFacultyId] = useState('')

  // Only needed for super_admin
  const { data: colleges = [] } = useQuery({
    queryKey: ['admin-colleges'],
    queryFn: adminApi.getAllColleges,
    enabled: isSuperAdmin,
  })

  // Effective college_id to pass to API
  const effectiveCollegeId = isSuperAdmin ? selectedCollegeId : undefined
  const canOperate = !isSuperAdmin || !!selectedCollegeId

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['faculty-students', effectiveCollegeId, filterDept, filterBatch, search],
    queryFn: () =>
      facultyStudentsApi.getStudents({
        department: filterDept || undefined,
        batch_year: filterBatch || undefined,
        search: search || undefined,
        college_id: effectiveCollegeId,
      }),
    enabled: canOperate,
  })

  const { data: template } = useQuery({
    queryKey: ['bulk-template'],
    queryFn: facultyStudentsApi.getBulkTemplate,
  })

  // Faculty list for assignment dropdown
  const { data: facultyList = [] } = useQuery({
    queryKey: ['college-faculty-list', effectiveCollegeId],
    queryFn: () => collegeApi.getFacultyList(effectiveCollegeId),
    enabled: canOperate,
  })

  const assignFacultyMutation = useMutation({
    mutationFn: ({ studentId, facultyId }) =>
      collegeApi.assignStudentToFaculty(studentId, facultyId, effectiveCollegeId),
    onSuccess: (data) => {
      qc.invalidateQueries(['faculty-students'])
      qc.invalidateQueries(['college-overview'])
      setAssignTarget(null)
      setAssignFacultyId('')
      toast.success(data.message)
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Assignment failed'),
  })

  const unassignFacultyMutation = useMutation({
    mutationFn: (studentId) => collegeApi.unassignStudentFaculty(studentId, effectiveCollegeId),
    onSuccess: () => {
      qc.invalidateQueries(['faculty-students'])
      qc.invalidateQueries(['college-overview'])
      toast.success('Assignment removed')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to remove assignment'),
  })

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const { faculty_id, ...studentData } = data
      const student = await facultyStudentsApi.createStudent(studentData, effectiveCollegeId)
      // If a faculty was selected, assign immediately
      if (faculty_id) {
        await collegeApi.assignStudentToFaculty(student.id, parseInt(faculty_id), effectiveCollegeId)
      }
      return student
    },
    onSuccess: () => {
      qc.invalidateQueries(['faculty-students'])
      qc.invalidateQueries(['college-overview'])
      closeForm()
      toast.success('Student created — welcome email sent!')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to create student'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => facultyStudentsApi.updateStudent(id, data, effectiveCollegeId),
    onSuccess: () => {
      qc.invalidateQueries(['faculty-students'])
      closeForm()
      toast.success('Student updated')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update student'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => facultyStudentsApi.deleteStudent(id, effectiveCollegeId),
    onSuccess: () => {
      qc.invalidateQueries(['faculty-students'])
      setConfirmDelete(null)
      toast.success('Student deactivated')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to deactivate'),
  })

  const resetPasswordMutation = useMutation({
    mutationFn: (id) => facultyStudentsApi.resetStudentPassword(id, effectiveCollegeId),
    onSuccess: (data) => {
      toast.success(data.email_sent ? 'Password reset — new credentials emailed' : 'Password reset (email disabled)')
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to reset password'),
  })

  const bulkMutation = useMutation({
    mutationFn: ({ file, sendEmails }) => facultyStudentsApi.bulkUpload(file, sendEmails, effectiveCollegeId),
    onSuccess: (data) => {
      qc.invalidateQueries(['faculty-students'])
      setBulkResult(data)
      setBulkFile(null)
      if (data.created > 0) toast.success(`${data.created} student(s) created successfully`)
      if (data.failed > 0) toast.error(`${data.failed} row(s) failed — check the error report`)
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Bulk upload failed'),
  })

  const openCreate = () => {
    setEditTarget(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  const openEdit = (student) => {
    setEditTarget(student)
    setForm({
      email: student.email,
      username: student.username,
      full_name: student.full_name || '',
      department: student.department || '',
      batch_year: student.batch_year || '',
      enrollment_number: student.enrollment_number || '',
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
      batch_year: parseInt(form.batch_year) || null,
    }
    if (editTarget) {
      const { username, ...updatePayload } = payload
      updateMutation.mutate({ id: editTarget.id, data: updatePayload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const handleBulkUpload = () => {
    if (!bulkFile) return
    bulkMutation.mutate({ file: bulkFile, sendEmails })
  }

  // Generate downloadable CSV template
  const downloadTemplate = () => {
    const cols = template?.columns || [
      { name: 'email' }, { name: 'username' }, { name: 'full_name' },
      { name: 'department' }, { name: 'batch_year' }, { name: 'enrollment_number' },
    ]
    const header = cols.map((c) => c.name).join(',')
    const example = cols.map((c) => c.example || '').join(',')
    const csv = `${header}\n${example}\n`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'student_bulk_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Unique departments and batch years for filters
  const departments = [...new Set(students.map((s) => s.department).filter(Boolean))]
  const batchYears = [...new Set(students.map((s) => s.batch_year).filter(Boolean))].sort((a, b) => b - a)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" />
            Manage Students
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Add, edit, and manage students in your college
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { setActiveTab('bulk'); setBulkResult(null) }}>
            <Upload className="h-4 w-4 mr-2" />
            Bulk Upload
          </Button>
          <Button onClick={openCreate} disabled={!canOperate}>
            <UserPlus className="h-4 w-4 mr-2" />
            Add Student
          </Button>
        </div>
      </div>

      {/* Super admin college picker */}
      {isSuperAdmin && (
        <Card className="border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-amber-600 shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-1">
                  Select a college to manage its students
                </p>
                <select
                  className="w-full sm:w-80 border rounded-md px-3 py-2 text-sm bg-background"
                  value={selectedCollegeId || ''}
                  onChange={(e) => {
                    setSelectedCollegeId(parseInt(e.target.value) || null)
                    setFilterDept('')
                    setFilterBatch('')
                    setSearch('')
                  }}
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

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Total Students</p>
          <p className="text-2xl font-bold mt-1">{students.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Active</p>
          <p className="text-2xl font-bold mt-1">{students.filter((s) => s.is_active).length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Departments</p>
          <p className="text-2xl font-bold mt-1">{departments.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Batches</p>
          <p className="text-2xl font-bold mt-1">{batchYears.length}</p>
        </Card>
      </div>

      {/* Bulk Upload Panel */}
      {activeTab === 'bulk' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Bulk Student Upload
            </CardTitle>
            <button onClick={() => setActiveTab('list')} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted/40 rounded-lg p-4 text-sm space-y-2">
              <p className="font-medium">Required columns in your Excel file:</p>
              <div className="flex flex-wrap gap-2">
                {(template?.columns || []).map((col) => (
                  <span
                    key={col.name}
                    className={cn(
                      'px-2 py-0.5 rounded text-xs font-mono',
                      col.required
                        ? 'bg-primary/10 text-primary'
                        : 'bg-muted text-muted-foreground'
                    )}
                  >
                    {col.name}{col.required ? ' *' : ''}
                  </span>
                ))}
              </div>
              <p className="text-muted-foreground text-xs">{template?.instructions}</p>
            </div>

            <Button variant="outline" size="sm" onClick={downloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              Download CSV Template
            </Button>

            <div
              className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const f = e.dataTransfer.files[0]
                if (f) setBulkFile(f)
              }}
            >
              <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              {bulkFile ? (
                <p className="font-medium">{bulkFile.name}</p>
              ) : (
                <>
                  <p className="font-medium">Drop your Excel file here</p>
                  <p className="text-sm text-muted-foreground">or click to browse (.xlsx, .xls)</p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => setBulkFile(e.target.files[0])}
              />
            </div>

            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={sendEmails}
                onChange={(e) => setSendEmails(e.target.checked)}
                className="rounded"
              />
              Send welcome emails with credentials to each student
            </label>

            <Button
              onClick={handleBulkUpload}
              disabled={!bulkFile || bulkMutation.isPending}
              className="w-full"
            >
              {bulkMutation.isPending ? 'Uploading…' : 'Upload & Create Students'}
            </Button>

            {/* Bulk Result */}
            {bulkResult && (
              <div className="space-y-3 mt-4">
                <div className="flex gap-4">
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-4 w-4" />
                    <span className="font-medium">{bulkResult.created} created</span>
                  </div>
                  {bulkResult.failed > 0 && (
                    <div className="flex items-center gap-2 text-red-600">
                      <AlertCircle className="h-4 w-4" />
                      <span className="font-medium">{bulkResult.failed} failed</span>
                    </div>
                  )}
                  <div className="text-muted-foreground text-sm">
                    {bulkResult.emails_sent} email(s) sent
                  </div>
                </div>

                {bulkResult.errors?.length > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-sm">
                    <p className="font-medium text-red-700 dark:text-red-400 mb-2">Errors:</p>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {bulkResult.errors.map((err, i) => (
                        <p key={i} className="text-red-600 dark:text-red-400 text-xs">
                          Row {err.row}: {err.email || 'unknown'} — {err.reason}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search by name, email, username, enrollment…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterDept}
          onChange={(e) => setFilterDept(e.target.value)}
        >
          <option value="">All Departments</option>
          {departments.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <select
          className="border rounded-md px-3 py-2 text-sm bg-background"
          value={filterBatch}
          onChange={(e) => setFilterBatch(e.target.value)}
        >
          <option value="">All Batches</option>
          {batchYears.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {/* Students Table */}
      <Card>
        <CardHeader>
          <CardTitle>Students ({students.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading…</div>
          ) : students.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Users className="h-10 w-10 mx-auto mb-2 opacity-40" />
              <p>No students found</p>
              <p className="text-xs mt-1">Add students individually or use bulk upload</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/30">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium">Student</th>
                    <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Email</th>
                    <th className="text-left px-4 py-3 font-medium hidden sm:table-cell">Dept / Batch</th>
                    <th className="text-left px-4 py-3 font-medium">Assigned Faculty</th>
                    <th className="text-left px-4 py-3 font-medium">Status</th>
                    <th className="text-right px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {students.map((student) => (
                    <tr key={student.id} className="hover:bg-muted/20 transition-colors">
                      {/* Student name */}
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-700 dark:text-blue-300 font-semibold text-xs shrink-0">
                            {(student.full_name || student.username)?.[0]?.toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium">{student.full_name || student.username}</p>
                            <p className="text-xs text-muted-foreground">@{student.username}</p>
                          </div>
                        </div>
                      </td>

                      {/* Email */}
                      <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">
                        {student.email}
                      </td>

                      {/* Dept / Batch */}
                      <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">
                        <p>{student.department || '—'}</p>
                        {student.batch_year && (
                          <p className="text-xs">Batch {student.batch_year}</p>
                        )}
                      </td>

                      {/* Assigned Faculty */}
                      <td className="px-4 py-3">
                        <AssignedFacultyCell
                          student={student}
                          facultyList={facultyList}
                          effectiveCollegeId={effectiveCollegeId}
                          onAssign={(studentId, facultyId) =>
                            assignFacultyMutation.mutate({ studentId, facultyId })
                          }
                          onUnassign={(studentId) =>
                            unassignFacultyMutation.mutate(studentId)
                          }
                          isAssigning={assignFacultyMutation.isPending}
                          isUnassigning={unassignFacultyMutation.isPending}
                        />
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <Badge variant={student.is_active ? 'success' : 'secondary'}>
                          {student.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => openEdit(student)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Edit"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => resetPasswordMutation.mutate(student.id)}
                            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground"
                            title="Reset Password"
                          >
                            <KeyRound className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setConfirmDelete(student)}
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
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between sticky top-0 bg-card z-10">
              <CardTitle>{editTarget ? 'Edit Student' : 'Add Student'}</CardTitle>
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
                    <label className="text-sm font-medium">Department</label>
                    <Input
                      value={form.department}
                      onChange={(e) => setForm({ ...form, department: e.target.value })}
                      placeholder="e.g. Computer Science"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Batch Year</label>
                    <Input
                      type="number"
                      value={form.batch_year}
                      onChange={(e) => setForm({ ...form, batch_year: e.target.value })}
                      placeholder="e.g. 2025"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium">Enrollment Number</label>
                  <Input
                    value={form.enrollment_number}
                    onChange={(e) => setForm({ ...form, enrollment_number: e.target.value })}
                    placeholder="e.g. CS2025001"
                  />
                </div>

                {!editTarget && (
                  <div className="space-y-1">
                    <label className="text-sm font-medium">Assign to Faculty</label>
                    <select
                      className="w-full border rounded-md px-3 py-2 text-sm bg-background"
                      value={form.faculty_id}
                      onChange={(e) => setForm({ ...form, faculty_id: e.target.value })}
                    >
                      <option value="">— No assignment (assign later) —</option>
                      {facultyList.map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.full_name || f.username}
                          {f.department ? ` (${f.department})` : ''}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-muted-foreground">Optional — you can assign later from the table</p>
                  </div>
                )}

                {!editTarget && (
                  <p className="text-xs text-muted-foreground bg-muted/50 rounded p-2">
                    A temporary password will be auto-generated and sent to the student's email.
                  </p>
                )}

                <div className="flex gap-2 pt-2">
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={createMutation.isPending || updateMutation.isPending}
                  >
                    {editTarget ? 'Save Changes' : 'Create Student'}
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
              <CardTitle className="text-red-600">Deactivate Student?</CardTitle>
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
