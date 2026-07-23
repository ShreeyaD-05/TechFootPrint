import { cn } from '../../utils/cn'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

/**
 * KPI Card — primary BI metric display component
 * Props: title, value, subtitle, delta, deltaLabel, icon, color, loading
 * color: 'blue' | 'green' | 'amber' | 'red' | 'purple' | 'teal'
 */
export default function KPICard({
  title,
  value,
  subtitle,
  delta,
  deltaLabel,
  icon: Icon,
  color = 'blue',
  loading = false,
  className,
  onClick,
}) {
  const colorMap = {
    blue:   { bg: 'bg-blue-50 dark:bg-blue-900/20',   icon: 'text-blue-600 dark:text-blue-400',   val: 'text-blue-700 dark:text-blue-300' },
    green:  { bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: 'text-emerald-600 dark:text-emerald-400', val: 'text-emerald-700 dark:text-emerald-300' },
    amber:  { bg: 'bg-amber-50 dark:bg-amber-900/20', icon: 'text-amber-600 dark:text-amber-400', val: 'text-amber-700 dark:text-amber-300' },
    red:    { bg: 'bg-red-50 dark:bg-red-900/20',     icon: 'text-red-600 dark:text-red-400',     val: 'text-red-700 dark:text-red-300' },
    purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', icon: 'text-purple-600 dark:text-purple-400', val: 'text-purple-700 dark:text-purple-300' },
    teal:   { bg: 'bg-teal-50 dark:bg-teal-900/20',   icon: 'text-teal-600 dark:text-teal-400',   val: 'text-teal-700 dark:text-teal-300' },
  }
  const c = colorMap[color] || colorMap.blue

  const DeltaIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus
  const deltaClass = delta > 0 ? 'text-emerald-600 dark:text-emerald-400' : delta < 0 ? 'text-red-500' : 'text-muted-foreground'

  if (loading) {
    return (
      <div className={cn('kpi-card animate-pulse', className)}>
        <div className="h-4 bg-secondary rounded w-24 mb-3" />
        <div className="h-8 bg-secondary rounded w-16 mb-2" />
        <div className="h-3 bg-secondary rounded w-32" />
      </div>
    )
  }

  return (
    <div
      className={cn('kpi-card', onClick && 'cursor-pointer', className)}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex items-start justify-between mb-3">
        <p className="kpi-label">{title}</p>
        {Icon && (
          <div className={cn('h-9 w-9 rounded-lg flex items-center justify-center', c.bg)}>
            <Icon className={cn('h-5 w-5', c.icon)} />
          </div>
        )}
      </div>

      <p className={cn('kpi-value', c.val)}>{value ?? '—'}</p>

      {(subtitle || delta !== undefined) && (
        <div className="flex items-center gap-2 mt-2">
          {delta !== undefined && (
            <span className={cn('flex items-center gap-0.5 text-xs font-semibold', deltaClass)}>
              <DeltaIcon className="h-3 w-3" />
              {Math.abs(delta)}{deltaLabel || '%'}
            </span>
          )}
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        </div>
      )}
    </div>
  )
}
