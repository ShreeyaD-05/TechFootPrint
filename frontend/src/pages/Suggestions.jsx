import { useQuery, useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { suggestionsApi } from '../services/suggestionsApi'
import apiClient from '../services/apiClient'
import KPICard from '../components/ui/KPICard'
import SkillRadar from '../components/ui/SkillRadar'
import {
  Lightbulb, Brain, Target, TrendingUp, Zap, Filter,
  ExternalLink, ChevronRight, BookOpen, Award, RefreshCw,
  ThumbsUp, ThumbsDown
} from 'lucide-react'
import { cn } from '../utils/cn'
import toast from 'react-hot-toast'

const STRATEGIES = [
  { id: 'balanced',     label: 'Balanced',      desc: 'Mix of gap-filling & progression', icon: Target },
  { id: 'gap_fill',     label: 'Fill Gaps',      desc: 'Focus on weak topics',             icon: BookOpen },
  { id: 'progression',  label: 'Level Up',       desc: 'Push your difficulty ceiling',     icon: TrendingUp },
  { id: 'contest_prep', label: 'Contest Prep',   desc: 'High-frequency contest patterns',  icon: Zap },
]

const DIFFICULTIES = ['all', 'easy', 'medium', 'hard']
const PLATFORMS = ['all', 'leetcode', 'codeforces']

export default function Suggestions() {
  const [strategy, setStrategy] = useState('balanced')
  const [difficulty, setDifficulty] = useState('all')
  const [platform, setPlatform] = useState('all')
  const [n, setN] = useState(10)

  const params = {
    strategy,
    n,
    ...(difficulty !== 'all' && { difficulty }),
    ...(platform !== 'all' && { platform }),
  }

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['suggestions', params],
    queryFn: () => suggestionsApi.getSuggestions(params),
    staleTime: 60000,
  })

  const suggestions = data?.suggestions || []
  const skill = data?.skill_analysis || {}
  const profile = data?.profile_summary || {}
  const radar = skill.radar_data || []
  const weakTopics = skill.weak_topics || []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-2xl font-bold">AI Problem Suggestions</h1>
          </div>
          <p className="text-muted-foreground text-sm">
            Personalized recommendations powered by your skill profile across all platforms
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 text-sm font-medium bg-secondary hover:bg-secondary/80 px-3 py-2 rounded-lg transition-colors"
        >
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Skill KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Solved" value={profile.total_solved ?? 0} icon={BookOpen} color="blue" loading={isLoading} />
        <KPICard title="Skill Tier" value={skill.skill_tier || '—'} icon={Award} color="purple" loading={isLoading} />
        <KPICard title="Placement Score" value={skill.readiness_score ? `${skill.readiness_score}%` : '—'} icon={Target} color="green" loading={isLoading} />
        <KPICard title="Topic Diversity" value={skill.topic_diversity ?? 0} subtitle="topics practiced" icon={TrendingUp} color="teal" loading={isLoading} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Filters + Suggestions */}
        <div className="lg:col-span-2 space-y-5">
          {/* Strategy selector */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Recommendation Strategy</p>
            </div>
            <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {STRATEGIES.map(s => (
                <button
                  key={s.id}
                  onClick={() => setStrategy(s.id)}
                  className={cn(
                    'flex flex-col items-center gap-2 p-3 rounded-xl border-2 text-center transition-all',
                    strategy === s.id
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-border hover:border-primary/40 text-muted-foreground hover:text-foreground'
                  )}
                >
                  <s.icon className="h-5 w-5" />
                  <div>
                    <p className="text-xs font-semibold">{s.label}</p>
                    <p className="text-[10px] mt-0.5 opacity-70">{s.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            <FilterGroup label="Difficulty" options={DIFFICULTIES} value={difficulty} onChange={setDifficulty} />
            <FilterGroup label="Platform" options={PLATFORMS} value={platform} onChange={setPlatform} />
            <select
              value={n}
              onChange={e => setN(Number(e.target.value))}
              className="text-sm bg-secondary border border-border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary/30"
            >
              {[5, 10, 15, 20].map(v => <option key={v} value={v}>{v} problems</option>)}
            </select>
          </div>

          {/* Suggestions list */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">
                {isFetching ? 'Generating...' : `${suggestions.length} Recommendations`}
              </p>
              <span className="text-xs text-muted-foreground capitalize">{strategy.replace('_', ' ')} strategy</span>
            </div>
            <div className="divide-y divide-border">
              {isLoading || isFetching ? (
                [...Array(5)].map((_, i) => (
                  <div key={i} className="px-5 py-4 animate-pulse">
                    <div className="h-4 bg-secondary rounded w-3/4 mb-2" />
                    <div className="h-3 bg-secondary rounded w-1/2" />
                  </div>
                ))
              ) : suggestions.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground">
                  <Lightbulb className="h-8 w-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No suggestions match your filters. Try adjusting them.</p>
                </div>
              ) : suggestions.map((s, i) => (
                <SuggestionRow key={i} suggestion={s} rank={i + 1} />
              ))}
            </div>
          </div>
        </div>

        {/* Right: Skill analysis */}
        <div className="space-y-5">
          {/* Skill Radar */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Skill Radar</p>
              <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full',
                { Beginner: 'tier-beginner', Novice: 'tier-novice', Intermediate: 'tier-intermediate', Advanced: 'tier-advanced', Expert: 'tier-expert' }[skill.skill_tier] || 'tier-beginner'
              )}>
                {skill.skill_tier || 'Beginner'}
              </span>
            </div>
            <div className="p-4">
              <SkillRadar data={radar} loading={isLoading} />
            </div>
          </div>

          {/* Target difficulty */}
          {skill.target_difficulty && (
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Recommended Level</p>
              </div>
              <div className="p-4 text-center">
                <div className={cn('inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold',
                  { easy: 'diff-easy', medium: 'diff-medium', hard: 'diff-hard' }[skill.target_difficulty] || 'bg-secondary'
                )}>
                  <TrendingUp className="h-4 w-4" />
                  {skill.target_difficulty?.charAt(0).toUpperCase() + skill.target_difficulty?.slice(1)} Problems
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Based on your current skill profile
                </p>
              </div>
            </div>
          )}

          {/* Weak topics */}
          {weakTopics.length > 0 && (
            <div className="bi-section">
              <div className="bi-section-header">
                <p className="bi-section-title">Growth Areas</p>
              </div>
              <div className="p-4 space-y-3">
                {weakTopics.map((t, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="font-medium capitalize">{t.topic.replace(/-/g, ' ')}</span>
                      <PriorityBadge priority={t.priority} />
                    </div>
                    <div className="progress-bar">
                      <div
                        className={cn('progress-fill', {
                          high: 'bg-red-400',
                          medium: 'bg-amber-400',
                          low: 'bg-emerald-400',
                        }[t.priority] || 'bg-primary')}
                        style={{ width: `${Math.max(5, 100 - t.gap_score * 100)}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1">{t.current_count} solved</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Difficulty breakdown */}
          <div className="bi-section">
            <div className="bi-section-header">
              <p className="bi-section-title">Your Breakdown</p>
            </div>
            <div className="p-4 space-y-2">
              {[
                { label: 'Easy', value: profile.easy, color: 'bg-emerald-400', total: profile.total_solved },
                { label: 'Medium', value: profile.medium, color: 'bg-amber-400', total: profile.total_solved },
                { label: 'Hard', value: profile.hard, color: 'bg-red-400', total: profile.total_solved },
              ].map(d => (
                <div key={d.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium">{d.label}</span>
                    <span className="text-muted-foreground">{d.value ?? 0}</span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className={`progress-fill ${d.color}`}
                      style={{ width: `${d.total ? ((d.value || 0) / d.total * 100) : 0}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SuggestionRow({ suggestion: s, rank }) {
  const [feedback, setFeedback] = useState(null)

  const submitFeedback = useMutation({
    mutationFn: (data) => apiClient.post('/api/suggestions/feedback', data).then(r => r.data),
    onSuccess: () => toast.success('Thanks for the feedback!'),
    onError: () => toast.error('Could not save feedback'),
  })

  const handleFeedback = (helpful) => {
    if (feedback !== null) return
    setFeedback(helpful)
    submitFeedback.mutate({
      problem_id: s.problem_id,
      platform: s.platform,
      was_helpful: helpful,
      suggestion_score: s.score,
    })
  }

  const platformUrl = s.url || '#'

  return (
    <div className="px-5 py-4 hover:bg-secondary/30 transition-colors group">
      <div className="flex items-start gap-3">
        <span className="text-sm font-bold text-muted-foreground w-6 shrink-0 mt-0.5">
          {rank <= 3 ? ['🥇','🥈','🥉'][rank-1] : `${rank}.`}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-semibold">{s.title}</p>
            <DiffBadge diff={s.difficulty} />
            <span className="text-xs text-muted-foreground capitalize">{s.platform}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">{s.reason}</p>
          {s.topics?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {s.topics.slice(0, 4).map(t => (
                <span key={t} className="text-[10px] bg-secondary px-1.5 py-0.5 rounded font-medium">{t}</span>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
            {Math.round(s.score * 100)}%
          </span>
          <button
            onClick={() => handleFeedback(true)}
            className={cn('p-1.5 rounded-lg transition-colors', feedback === true ? 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'text-muted-foreground hover:text-emerald-500 hover:bg-secondary')}
            aria-label="Helpful"
          >
            <ThumbsUp className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => handleFeedback(false)}
            className={cn('p-1.5 rounded-lg transition-colors', feedback === false ? 'text-red-500 bg-red-50 dark:bg-red-900/20' : 'text-muted-foreground hover:text-red-500 hover:bg-secondary')}
            aria-label="Not helpful"
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </button>
          <a
            href={platformUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors"
            aria-label="Open problem"
          >
            <ExternalLink className="h-4 w-4 text-muted-foreground hover:text-primary" />
          </a>
        </div>
      </div>
    </div>
  )
}

function FilterGroup({ label, options, value, onChange }) {
  return (
    <div className="flex items-center gap-1 bg-secondary rounded-lg p-1">
      {options.map(o => (
        <button
          key={o}
          onClick={() => onChange(o)}
          className={cn(
            'text-xs font-medium px-2.5 py-1 rounded-md capitalize transition-all',
            value === o ? 'bg-card shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'
          )}
        >
          {o}
        </button>
      ))}
    </div>
  )
}

function DiffBadge({ diff }) {
  const map = { easy: 'diff-easy', medium: 'diff-medium', hard: 'diff-hard' }
  return (
    <span className={cn('text-[10px] font-semibold px-1.5 py-0.5 rounded-full capitalize', map[diff?.toLowerCase()] || 'bg-secondary text-secondary-foreground')}>
      {diff}
    </span>
  )
}

function PriorityBadge({ priority }) {
  const map = { high: 'text-red-500', medium: 'text-amber-500', low: 'text-emerald-500' }
  return <span className={cn('font-semibold capitalize', map[priority] || 'text-muted-foreground')}>{priority}</span>
}
