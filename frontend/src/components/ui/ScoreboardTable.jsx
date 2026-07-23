import { cn } from '../../utils/cn'
import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react'

/**
 * Scoreboard / Leaderboard table component
 * Props: data (array), columns (array), title, loading
 */
export default function ScoreboardTable({ data = [], title, loading, className, emptyMessage = 'No data available' }) {
  if (loading) {
    return (
      <div className={cn('bi-section', className)}>
        {title && <div className="bi-section-header"><p className="bi-section-title">{title}</p></div>}
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-secondary rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('bi-section', className)}>
      {title && (
        <div className="bi-section-header">
          <div className="flex items-center gap-2">
            <Trophy className="h-4 w-4 text-amber-500" />
            <p className="bi-section-title">{title}</p>
          </div>
          <span className="text-xs text-muted-foreground">{data.length} entries</span>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full bi-table">
          <thead>
            <tr>
              <th className="w-12 text-center">#</th>
              <th>Student</th>
              <th className="text-right">Solved</th>
              <th className="text-right hidden sm:table-cell">Easy</th>
              <th className="text-right hidden sm:table-cell">Medium</th>
              <th className="text-right hidden sm:table-cell">Hard</th>
              <th className="text-right">Streak</th>
              <th className="hidden md:table-cell">Tier</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-8 text-muted-foreground text-sm">{emptyMessage}</td></tr>
            ) : data.map((row, i) => (
              <tr key={row.user_id || i} className="hover:bg-secondary/30 transition-colors">
                <td className="text-center">
                  <RankBadge rank={i + 1} />
                </td>
                <td>
                  <div className="flex items-center gap-2.5">
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold shrink-0">
                      {(row.name || row.username || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{row.name || row.username}</p>
                      {row.department && <p className="text-xs text-muted-foreground">{row.department}</p>}
                    </div>
                  </div>
                </td>
                <td className="text-right font-semibold text-sm">{row.total_solved ?? 0}</td>
                <td className="text-right text-sm text-emerald-600 dark:text-emerald-400 hidden sm:table-cell">{row.easy_solved ?? 0}</td>
                <td className="text-right text-sm text-amber-600 dark:text-amber-400 hidden sm:table-cell">{row.medium_solved ?? 0}</td>
                <td className="text-right text-sm text-red-500 hidden sm:table-cell">{row.hard_solved ?? 0}</td>
                <td className="text-right">
                  <span className="text-sm font-medium flex items-center justify-end gap-1">
                    🔥 {row.streak ?? 0}
                  </span>
                </td>
                <td className="hidden md:table-cell">
                  <TierBadge tier={row.skill_tier || getTier(row.total_solved)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function RankBadge({ rank }) {
  if (rank === 1) return <span className="text-amber-500 font-bold text-sm">🥇</span>
  if (rank === 2) return <span className="text-slate-400 font-bold text-sm">🥈</span>
  if (rank === 3) return <span className="text-amber-700 font-bold text-sm">🥉</span>
  return <span className="text-muted-foreground text-sm font-medium">{rank}</span>
}

function TierBadge({ tier }) {
  const map = {
    Beginner: 'tier-beginner',
    Novice: 'tier-novice',
    Intermediate: 'tier-intermediate',
    Advanced: 'tier-advanced',
    Expert: 'tier-expert',
  }
  return (
    <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full', map[tier] || 'tier-beginner')}>
      {tier || 'Beginner'}
    </span>
  )
}

function getTier(total) {
  if (!total || total < 25) return 'Beginner'
  if (total < 75) return 'Novice'
  if (total < 150) return 'Intermediate'
  if (total < 300) return 'Advanced'
  return 'Expert'
}
