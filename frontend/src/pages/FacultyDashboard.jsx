import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { dashboardApi } from '../services/dashboardApi'
import { mentoringApi } from '../services/mentoringApi'
import KPICard from '../components/ui/KPICard'
import ScoreboardTable from '../components/ui/ScoreboardTable'
import SkillRadar from '../components/ui/SkillRadar'
import { suggestionsApi } from '../services/suggestionsApi'
import {
  Users, TrendingUp, AlertCircle, MessageSquare, Target,
  Flame, Search, Send, Eye, Award, ChevronRight, X, Brain
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend, Cell
} from 'recharts'
import toast from 'react-hot-toast'
import { cn } from '../utils/cn'

export default function FacultyDashboard() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackForm, setFeedbackForm] = useState({ student_id: null, feedback_type: 'comment', title: '', content: '', priority: 'normal' })

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['faculty-dashboard'],
    queryFn: dashboardApi.getFacultyOverview,
    refetchInterval: 120000,
  })

  const { data: studentDetails, isLoading: loadingStudent } = useQuery({
    queryKey: ['student-details', selectedStudent],
    queryFn: () => dashboardApi.getStudentDetails(selectedStudent),
    enabled: !!selectedStudent,
  })

  const { data: studentSkill } = useQuery({
    queryKey: ['student-skill', selectedStudent],
    queryFn: () => suggestionsApi.getSkillAnalysis(),
    enabled: !!selectedStudent,
    staleTime: 300000,
  })

  const sendFeedback = useMutation({
    mutationFn: mentoringApi.createFeedback,
    onSuccess: () => { toast.success('Feedback sent'); setShowFeedback(false); qc.invalidateQueries(['faculty-dashboard']) },
    onError: () => toast.error('Failed to send feedback'),
  })

  const stats = dashboard?.overview || {}
  const students = dashboard?.students || []
  const filtered = students.filter(s =>
    !search || s.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    s.username?.toLowerCase().includes(search.toLowerCase())
  )

  // Scoreboard data — normalize to ScoreboardTable expected shape
  const scoreboard = [...students]
    .sort((a, b) => (b.problems_solved || 0) - (a.problems_solved || 0))
    .slice(0, 20)
    .map(s => ({
      user_id: s.id,
      name: s.full_name || s.username,
      username: s.username,
      total_solved: s.problems_solved || 0,
      streak: s.current_streak || 0,
    }))

  // Performance chart
  const perfData = students.slice(0, 10).map(s => ({
    name: s.full_name?.split(' ')[0] || s.username,
    solved: s.problems_solved || 0,
    streak: s.current_streak || 0,
  }))

  const needsAttention = students.filter(s => (s.current_streak || 0) === 0 || (s.problems_solved || 0) < 10)

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Faculty Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">Monitor and mentor your assigned students</p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="My Students" value={stats.total_students ?? 0} icon={Users} color="blue" loading={isLoading} />
        <KPICard title="Avg. Problems" value={stats.avg_problems ?? 0} icon={TrendingUp} color="green" loading={isLoading} />
        <KPICard title="Needs Attention" value={needsAttention.length} icon={AlertCircle} color="red" loading={isLoading} />
        <KPICard title="Active Students" value={stats.active_students ?? 0} icon={Flame} color="amber" loading={isLoading} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Scoreboard + Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Scoreboard */}
          <ScoreboardTable
            title="Student Scoreboard"
            data={scoreboard}
            loading={isLoading}
          />

          {/* Performance chart */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Top 10 Performance</p>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={perfData} margin={{ top: 5, right: 5, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} angle={-30} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="solved" name="Problems Solved" fill="hsl(var(--primary))" radius={[4,4,0,0]} />
                  <Bar dataKey="streak" name="Streak (days)" fill="#10b981" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Needs attention */}
          {needsAttention.length > 0 && (
            <div className="bi-section border-l-4 border-l-red-400">
              <div className="bi-section-header">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <p className="bi-section-title text-red-600 dark:text-red-400">Needs Attention ({needsAttention.length})</p>
                </div>
              </div>
              <div className="divide-y divide-border">
                {needsAttention.slice(0, 5).map((s, i) => (
                  <div key={i} className="flex items-center justify-between px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 text-xs font-bold">
                        {(s.full_name || s.username || '?')[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{s.full_name || s.username}</p>
                        <p className="text-xs text-muted-foreground">{s.problems_solved || 0} solved · {s.current_streak || 0}d streak</p>
                      </div>
                    </div>
                    <button
                      onClick={() => { setFeedbackForm(f => ({ ...f, student_id: s.id })); setShowFeedback(true) }}
                      className="text-xs font-medium text-primary hover:underline flex items-center gap-1"
                    >
                      <MessageSquare className="h-3 w-3" /> Feedback
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Student search + detail */}
        <div className="space-y-5">
          {/* Search */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Student Lookup</p>
            </div>
            <div className="p-4 space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search students..."
                  className="w-full pl-9 pr-4 py-2 text-sm bg-secondary rounded-lg border border-transparent focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/30"
                />
              </div>
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {filtered.slice(0, 15).map((s, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedStudent(s.id)}
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors',
                      selectedStudent === s.id ? 'bg-primary/10 text-primary' : 'hover:bg-secondary'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold">
                        {(s.full_name || s.username || '?')[0].toUpperCase()}
                      </div>
                      <span className="text-sm font-medium truncate">{s.full_name || s.username}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{s.problems_solved || 0}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Student detail */}
          {selectedStudent && (
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Student Profile</p>
                <button onClick={() => setSelectedStudent(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>
              <div className="p-4 space-y-4">
                {loadingStudent ? (
                  <div className="space-y-2">
                    {[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-secondary rounded animate-pulse" />)}
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: 'Total', value: studentDetails?.overview?.total_problems || 0 },
                        { label: 'Streak', value: `${studentDetails?.overview?.current_streak || 0}d` },
                        { label: 'Easy', value: studentDetails?.overview?.easy_solved || 0 },
                        { label: 'Hard', value: studentDetails?.overview?.hard_solved || 0 },
                      ].map(m => (
                        <div key={m.label} className="bg-secondary rounded-lg p-3 text-center">
                          <p className="text-lg font-bold">{m.value}</p>
                          <p className="text-xs text-muted-foreground">{m.label}</p>
                        </div>
                      ))}
                    </div>
                    <SkillRadar data={studentSkill?.radar_data || []} />
                    <button
                      onClick={() => { setFeedbackForm(f => ({ ...f, student_id: selectedStudent })); setShowFeedback(true) }}
                      className="w-full flex items-center justify-center gap-2 bg-primary text-white text-sm font-medium py-2 rounded-lg hover:bg-primary/90 transition-colors"
                    >                      <MessageSquare className="h-4 w-4" /> Send Feedback
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedback && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-card rounded-xl border border-border shadow-xl w-full max-w-md animate-fade-in">
            <div className="flex items-center justify-between p-5 border-b border-border">
              <h2 className="font-semibold">Send Feedback</h2>
              <button onClick={() => setShowFeedback(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Type</label>
                <div className="flex gap-2 mt-1.5">
                  {['comment', 'task', 'recommendation'].map(t => (
                    <button
                      key={t}
                      onClick={() => setFeedbackForm(f => ({ ...f, feedback_type: t }))}
                      className={cn('text-xs font-medium px-3 py-1.5 rounded-lg capitalize transition-colors',
                        feedbackForm.feedback_type === t ? 'bg-primary text-white' : 'bg-secondary hover:bg-secondary/80'
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Title</label>
                <input
                  value={feedbackForm.title}
                  onChange={e => setFeedbackForm(f => ({ ...f, title: e.target.value }))}
                  placeholder="Feedback title..."
                  className="mt-1.5 w-full px-3 py-2 text-sm bg-secondary rounded-lg border border-transparent focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Message</label>
                <textarea
                  value={feedbackForm.content}
                  onChange={e => setFeedbackForm(f => ({ ...f, content: e.target.value }))}
                  placeholder="Write your feedback..."
                  rows={4}
                  className="mt-1.5 w-full px-3 py-2 text-sm bg-secondary rounded-lg border border-transparent focus:border-primary focus:outline-none resize-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Priority</label>
                <select
                  value={feedbackForm.priority}
                  onChange={e => setFeedbackForm(f => ({ ...f, priority: e.target.value }))}
                  className="mt-1.5 w-full px-3 py-2 text-sm bg-secondary rounded-lg border border-transparent focus:border-primary focus:outline-none"
                >
                  {['low', 'normal', 'high', 'urgent'].map(p => (
                    <option key={p} value={p} className="capitalize">{p}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => sendFeedback.mutate(feedbackForm)}
                disabled={sendFeedback.isPending || !feedbackForm.content}
                className="w-full flex items-center justify-center gap-2 bg-primary text-white text-sm font-medium py-2.5 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Send className="h-4 w-4" />
                {sendFeedback.isPending ? 'Sending...' : 'Send Feedback'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
