import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { dashboardApi } from '../services/dashboardApi'
import { suggestionsApi } from '../services/suggestionsApi'
import KPICard from '../components/ui/KPICard'
import SkillRadar from '../components/ui/SkillRadar'
import ActivityHeatmap from '../components/charts/ActivityHeatmap'
import {
  Code2, Flame, Trophy, Target, TrendingUp, Lightbulb,
  ArrowRight, CheckCircle2, Clock, Zap, BarChart3, Link as LinkIcon
} from 'lucide-react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts'

const DIFF_COLORS = { easy: '#10b981', medium: '#f59e0b', hard: '#ef4444' }
const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6']

export default function Dashboard() {
  const { user } = useAuthStore()

  const { data: overview, isLoading } = useQuery({
    queryKey: ['student-dashboard'],
    queryFn: dashboardApi.getStudentOverview,
    refetchInterval: 120000,
  })

  const { data: skillData } = useQuery({
    queryKey: ['skill-analysis'],
    queryFn: suggestionsApi.getSkillAnalysis,
    staleTime: 300000,
  })

  const { data: heatmap } = useQuery({
    queryKey: ['student-heatmap'],
    queryFn: () => dashboardApi.getStudentHeatmap(365),
  })

  const ov = overview?.overview || {}
  const platforms = overview?.platforms || []
  const goals = overview?.goals || []
  const recentSubs = overview?.recent_submissions || []
  const topicMastery = overview?.topic_mastery || []
  const radar = skillData?.radar_data || []
  const weakTopics = skillData?.weak_topics || []
  const tier = skillData?.skill_tier || 'Beginner'
  const readiness = skillData?.readiness_score || 0

  // Convert heatmap array to object format expected by ActivityHeatmap
  const heatmapObj = useMemo(() => {
    const arr = heatmap?.heatmap || []
    if (Array.isArray(arr)) {
      return arr.reduce((acc, item) => {
        if (item?.date) acc[item.date] = item.count || 1
        return acc
      }, {})
    }
    return arr // already object
  }, [heatmap])

  const diffData = [
    { name: 'Easy', value: ov.easy_solved || 0, color: DIFF_COLORS.easy },
    { name: 'Medium', value: ov.medium_solved || 0, color: DIFF_COLORS.medium },
    { name: 'Hard', value: ov.hard_solved || 0, color: DIFF_COLORS.hard },
  ].filter(d => d.value > 0)

  const platformData = platforms.map((p, i) => ({
    name: p.name.charAt(0).toUpperCase() + p.name.slice(1),
    problems: p.total_solved || 0,
    fill: CHART_COLORS[i % CHART_COLORS.length],
  }))

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back, {user?.full_name?.split(' ')[0] || user?.username} 👋
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Here's your coding progress at a glance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <TierBadge tier={tier} />
          <Link
            to="/suggestions"
            className="flex items-center gap-1.5 text-sm font-medium bg-primary text-white px-3 py-1.5 rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Lightbulb className="h-4 w-4" />
            AI Suggestions
          </Link>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Solved"
          value={ov.total_problems || 0}
          subtitle="across all platforms"
          icon={Code2}
          color="blue"
          loading={isLoading}
        />
        <KPICard
          title="Current Streak"
          value={`${ov.current_streak || 0}d`}
          subtitle={`Best: ${ov.longest_streak || 0} days`}
          icon={Flame}
          color="amber"
          loading={isLoading}
        />
        <KPICard
          title="Platforms"
          value={platforms.length}
          subtitle="connected"
          icon={LinkIcon}
          color="purple"
          loading={isLoading}
        />
        <KPICard
          title="Placement Score"
          value={`${readiness}%`}
          subtitle="readiness index"
          icon={Trophy}
          color="green"
          loading={isLoading}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Activity Heatmap */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Activity Heatmap</p>
              <span className="text-xs text-muted-foreground">Last 12 months</span>
            </div>
            <div className="p-4">
              <ActivityHeatmap data={heatmapObj} />
            </div>
          </div>

          {/* Difficulty + Platform charts */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Difficulty Donut */}
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Difficulty Breakdown</p>
              </div>
              <div className="p-4">
                {diffData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie data={diffData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} dataKey="value">
                          {diffData.map((d, i) => <Cell key={i} fill={d.color} />)}
                        </Pie>
                        <Tooltip formatter={(v, n) => [v, n]} contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-4 mt-2">
                      {diffData.map(d => (
                        <div key={d.name} className="flex items-center gap-1.5">
                          <div className="h-2.5 w-2.5 rounded-full" style={{ background: d.color }} />
                          <span className="text-xs text-muted-foreground">{d.name} <strong className="text-foreground">{d.value}</strong></span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
                    No problems solved yet
                  </div>
                )}
              </div>
            </div>

            {/* Platform Bar */}
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">By Platform</p>
              </div>
              <div className="p-4">
                {platformData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={platformData} margin={{ top: 5, right: 5, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} angle={-30} textAnchor="end" />
                      <YAxis tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }} />
                      <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }} />
                      <Bar dataKey="problems" radius={[4, 4, 0, 0]}>
                        {platformData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
                    Connect platforms to see data
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Recent Submissions */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Recent Submissions</p>
              <Link to="/submissions" className="text-xs text-primary hover:underline flex items-center gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="divide-y divide-border">
              {recentSubs.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">No submissions yet</p>
              ) : recentSubs.slice(0, 5).map((s, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-3">
                  <div className="flex items-center gap-3">
                    <StatusDot status={s.status} />
                    <div>
                      <p className="text-sm font-medium">{s.problem_title || s.problem_id}</p>
                      <p className="text-xs text-muted-foreground">{s.platform} · {s.language}</p>
                    </div>
                  </div>
                  <DiffBadge diff={s.difficulty} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Skill Radar */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Skill Radar</p>
              <Link to="/suggestions" className="text-xs text-primary hover:underline">Improve →</Link>
            </div>
            <div className="p-4">
              <SkillRadar data={radar} loading={isLoading} />
            </div>
          </div>

          {/* Weak Topics */}
          {weakTopics.length > 0 && (
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Growth Areas</p>
                <Link to="/suggestions?strategy=gap_fill" className="text-xs text-primary hover:underline">Practice →</Link>
              </div>
              <div className="p-4 space-y-3">
                {weakTopics.slice(0, 5).map((t, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-medium capitalize">{t.topic.replace(/-/g, ' ')}</span>
                      <span className={t.priority === 'high' ? 'text-red-500' : t.priority === 'medium' ? 'text-amber-500' : 'text-muted-foreground'}>
                        {t.priority}
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill bg-primary"
                        style={{ width: `${Math.max(5, 100 - t.gap_score * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Goals */}
          {goals.length > 0 && (
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Active Goals</p>
              </div>
              <div className="p-4 space-y-3">
                {goals.slice(0, 3).map((g, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Target className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium">{g.description || `Solve ${g.target} problems`}</p>
                      {g.deadline && (
                        <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                          <Clock className="h-3 w-3" />
                          Due {new Date(g.deadline).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick links */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Quick Actions</p>
            </div>
            <div className="p-3 grid grid-cols-2 gap-2">
              {[
                { label: 'Sync Platforms', href: '/platforms', icon: Zap, color: 'text-blue-500' },
                { label: 'Discussions', href: '/discussions', icon: BarChart3, color: 'text-purple-500' },
                { label: 'Analytics', href: '/analytics', icon: TrendingUp, color: 'text-emerald-500' },
                { label: 'Portfolio', href: '/portfolio', icon: Trophy, color: 'text-amber-500' },
              ].map(a => (
                <Link
                  key={a.label}
                  to={a.href}
                  className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors text-center"
                >
                  <a.icon className={`h-5 w-5 ${a.color}`} />
                  <span className="text-xs font-medium">{a.label}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function TierBadge({ tier }) {
  const map = {
    Beginner: 'tier-beginner', Novice: 'tier-novice',
    Intermediate: 'tier-intermediate', Advanced: 'tier-advanced', Expert: 'tier-expert',
  }
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${map[tier] || 'tier-beginner'}`}>
      {tier}
    </span>
  )
}

function DiffBadge({ diff }) {
  const map = { easy: 'diff-easy', medium: 'diff-medium', hard: 'diff-hard' }
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${map[diff?.toLowerCase()] || 'bg-secondary text-secondary-foreground'}`}>
      {diff || '—'}
    </span>
  )
}

function StatusDot({ status }) {
  const ok = status === 'accepted' || status === 'Accepted'
  return (
    <div className={`h-2 w-2 rounded-full shrink-0 ${ok ? 'bg-emerald-500' : 'bg-red-400'}`} />
  )
}
