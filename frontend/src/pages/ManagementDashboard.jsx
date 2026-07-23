import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { dashboardApi } from '../services/dashboardApi'
import { suggestionsApi } from '../services/suggestionsApi'
import KPICard from '../components/ui/KPICard'
import ScoreboardTable from '../components/ui/ScoreboardTable'
import {
  Building2, Users, TrendingUp, Trophy, AlertCircle,
  GraduationCap, BarChart3, Activity, Target, ChevronRight, Download
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area
} from 'recharts'
import { cn } from '../utils/cn'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6']

export default function ManagementDashboard() {
  const [activeTab, setActiveTab] = useState('overview')

  const { data: kpis, isLoading: kpiLoading } = useQuery({
    queryKey: ['college-kpis'],
    queryFn: dashboardApi.getCollegeKPIs,
    refetchInterval: 300000,
  })

  const { data: mgmt, isLoading: mgmtLoading } = useQuery({
    queryKey: ['management-overview'],
    queryFn: dashboardApi.getManagementOverview,
    refetchInterval: 300000,
  })

  const { data: batchReadiness } = useQuery({
    queryKey: ['batch-readiness'],
    queryFn: () => suggestionsApi.getBatchReadiness(),
    staleTime: 600000,
  })

  const isLoading = kpiLoading || mgmtLoading
  const placement = kpis?.placement_readiness || {}
  const batchKpis = kpis?.batch_kpis || []

  // Normalize departments — backend may return array or object dict
  const rawDepts = mgmt?.departments
  const departments = Array.isArray(rawDepts)
    ? rawDepts
    : rawDepts && typeof rawDepts === 'object'
      ? Object.entries(rawDepts).map(([name, count]) => ({ name, student_count: count, avg_problems: 0 }))
      : []

  // Normalize batches — backend may return array or object dict
  const rawBatches = mgmt?.batches
  const batches = Array.isArray(rawBatches)
    ? rawBatches
    : rawBatches && typeof rawBatches === 'object'
      ? Object.entries(rawBatches).map(([year, count]) => ({ year: parseInt(year), students: count, avg_problems: 0 }))
      : []

  const topStudents = []  // top students not in management overview; use scoreboard from KPI data

  // Placement donut data
  const placementData = [
    { name: 'Ready (≥150)', value: placement.ready || 0, color: '#10b981' },
    { name: 'Moderate (50-149)', value: placement.moderate || 0, color: '#f59e0b' },
    { name: 'Needs Work (<50)', value: placement.needs_work || 0, color: '#ef4444' },
  ].filter(d => d.value > 0)

  // Dept bar data — normalize field names from both possible shapes
  const deptData = departments.map((d, i) => ({
    name: d.name || d.department || 'Unknown',
    avg: d.avg_problems || 0,
    students: d.students || d.student_count || 0,
    fill: COLORS[i % COLORS.length],
  }))

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building2 },
    { id: 'batches', label: 'Batches', icon: GraduationCap },
    { id: 'departments', label: 'Departments', icon: BarChart3 },
    { id: 'placement', label: 'Placement', icon: Trophy },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Management BI Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">College-wide analytics and KPI scorecard</p>
        </div>
        <button className="flex items-center gap-2 text-sm font-medium bg-secondary hover:bg-secondary/80 px-3 py-2 rounded-lg transition-colors">
          <Download className="h-4 w-4" /> Export Report
        </button>
      </div>

      {/* Top KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Students" value={kpis?.total_students ?? 0} icon={Users} color="blue" loading={isLoading} />
        <KPICard
          title="Active (7 days)"
          value={kpis?.active_7d ?? 0}
          subtitle={`${kpis?.engagement_rate ?? 0}% engagement`}
          icon={Activity}
          color="green"
          loading={isLoading}
        />
        <KPICard
          title="Avg. Problems"
          value={kpis?.avg_problems_per_student ?? 0}
          subtitle="per student"
          icon={TrendingUp}
          color="purple"
          loading={isLoading}
        />
        <KPICard
          title="Placement Ready"
          value={`${placement.ready_pct ?? 0}%`}
          subtitle={`${placement.ready ?? 0} students`}
          icon={Trophy}
          color="amber"
          loading={isLoading}
        />
      </div>

      {/* Secondary KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Problems Solved" value={(kpis?.total_problems_solved ?? 0).toLocaleString()} icon={BarChart3} color="teal" loading={isLoading} />
        <KPICard title="Platform Connections" value={kpis?.platform_connections ?? 0} icon={Target} color="blue" loading={isLoading} />
        <KPICard title="Avg. Streak" value={`${kpis?.avg_streak ?? 0}d`} icon={Activity} color="amber" loading={isLoading} />
        <KPICard title="Needs Attention" value={placement.needs_work ?? 0} icon={AlertCircle} color="red" loading={isLoading} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-secondary p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === t.id ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Placement donut */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Placement Readiness</p>
            </div>
            <div className="p-4">
              {placementData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={placementData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
                        {placementData.map((d, i) => <Cell key={i} fill={d.color} />)}
                      </Pie>
                      <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-2 mt-2">
                    {placementData.map(d => (
                      <div key={d.name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <div className="h-2.5 w-2.5 rounded-full" style={{ background: d.color }} />
                          <span className="text-muted-foreground">{d.name}</span>
                        </div>
                        <span className="font-semibold">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">No data</div>
              )}
            </div>
          </div>

          {/* Dept avg problems */}
          <div className="bi-section lg:col-span-2">
            <div className="bi-section-header">
              <p className="bi-section-title">Avg. Problems by Department</p>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={deptData} margin={{ top: 5, right: 5, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} angle={-20} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="avg" name="Avg Problems" radius={[4,4,0,0]}>
                    {deptData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top students */}
          <div className="lg:col-span-3">
            <ScoreboardTable title="College Scoreboard" data={topStudents} loading={isLoading} />
          </div>
        </div>
      )}

      {activeTab === 'batches' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {batchKpis.map((b, i) => (
              <div key={i} className="bi-section p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="h-5 w-5 text-primary" />
                    <h3 className="font-semibold">Batch {b.batch_year}</h3>
                  </div>
                  <span className="text-xs text-muted-foreground">{b.student_count} students</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-secondary rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-primary">{b.avg_problems}</p>
                    <p className="text-xs text-muted-foreground">Avg Problems</p>
                  </div>
                  <div className="bg-secondary rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-emerald-600">{b.ready_count}</p>
                    <p className="text-xs text-muted-foreground">Ready</p>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Placement readiness</span>
                    <span className="font-medium">{Math.round(b.ready_count / Math.max(b.student_count, 1) * 100)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill bg-emerald-400"
                      style={{ width: `${b.ready_count / Math.max(b.student_count, 1) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'departments' && (
        <div className="space-y-6">
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Department Comparison</p>
            </div>
            <div className="p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={deptData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} />
                  <YAxis tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} />
                  <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="avg" name="Avg Problems" fill="hsl(var(--primary))" radius={[4,4,0,0]} />
                  <Bar dataKey="students" name="Students" fill="#10b981" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {departments.map((d, i) => (
              <div key={i} className="kpi-card">
                <div className="flex items-center gap-2 mb-3">
                  <div className="h-3 w-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                  <p className="font-semibold text-sm">{d.name || d.department}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div><p className="text-lg font-bold">{d.students || d.student_count || 0}</p><p className="text-xs text-muted-foreground">Students</p></div>
                  <div><p className="text-lg font-bold text-primary">{d.avg_problems || 0}</p><p className="text-xs text-muted-foreground">Avg</p></div>
                  <div><p className="text-lg font-bold text-emerald-600">{d.top_performer_count || 0}</p><p className="text-xs text-muted-foreground">Top</p></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'placement' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Readiness Distribution</p>
              </div>
              <div className="p-4">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={placementData} cx="50%" cy="50%" outerRadius={90} paddingAngle={3} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                      {placementData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="space-y-4">
              {[
                { label: 'Ready for Placement', count: placement.ready || 0, pct: placement.ready_pct || 0, color: 'bg-emerald-400', desc: '≥150 problems solved' },
                { label: 'Moderate Progress', count: placement.moderate || 0, pct: Math.round((placement.moderate || 0) / Math.max(kpis?.total_students || 1, 1) * 100), color: 'bg-amber-400', desc: '50–149 problems solved' },
                { label: 'Needs Improvement', count: placement.needs_work || 0, pct: Math.round((placement.needs_work || 0) / Math.max(kpis?.total_students || 1, 1) * 100), color: 'bg-red-400', desc: '<50 problems solved' },
              ].map(r => (
                <div key={r.label} className="kpi-card">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-semibold text-sm">{r.label}</p>
                    <span className="text-2xl font-bold">{r.count}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{r.desc}</p>
                  <div className="progress-bar">
                    <div className={`progress-fill ${r.color}`} style={{ width: `${r.pct}%` }} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{r.pct}% of total</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
