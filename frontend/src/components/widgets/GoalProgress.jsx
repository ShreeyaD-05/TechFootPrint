import { Target, Calendar, TrendingUp } from 'lucide-react'
import { Badge } from '../ui/Badge'
import ProgressRing from '../charts/ProgressRing'

export default function GoalProgress({ goals = [], currentProgress = {} }) {
  if (goals.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Target className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>No active goals</p>
        <p className="text-sm">Goals will appear here when assigned</p>
      </div>
    )
  }

  const getGoalProgress = (goal) => {
    const current = currentProgress[goal.type] || 0
    const percentage = (current / goal.target) * 100
    return {
      current,
      percentage: Math.min(percentage, 100),
      remaining: Math.max(goal.target - current, 0)
    }
  }

  const getGoalTypeLabel = (type) => {
    const labels = {
      problems_count: 'Problems',
      streak: 'Day Streak',
      contest: 'Contests'
    }
    return labels[type] || type
  }

  const getDaysUntilDeadline = (deadline) => {
    if (!deadline) return null
    const days = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24))
    return days
  }

  return (
    <div className="space-y-4">
      {goals.map((goal) => {
        const progress = getGoalProgress(goal)
        const daysLeft = getDaysUntilDeadline(goal.deadline)
        const isCompleted = progress.percentage >= 100

        return (
          <div
            key={goal.id}
            className="p-4 rounded-lg border bg-card"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-primary" />
                  <h4 className="font-medium">{getGoalTypeLabel(goal.type)}</h4>
                  {isCompleted && (
                    <Badge variant="success" size="sm">Completed</Badge>
                  )}
                </div>
                {goal.description && (
                  <p className="text-sm text-muted-foreground">{goal.description}</p>
                )}
              </div>
              <ProgressRing
                value={progress.current}
                max={goal.target}
                size={60}
                strokeWidth={6}
                color={isCompleted ? '#10b981' : '#3b82f6'}
                showPercentage={false}
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-medium">
                  {progress.current} / {goal.target}
                </span>
              </div>

              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    isCompleted ? 'bg-green-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>

              {goal.deadline && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {daysLeft !== null && (
                    <span>
                      {daysLeft > 0
                        ? `${daysLeft} days remaining`
                        : daysLeft === 0
                        ? 'Due today'
                        : 'Overdue'}
                    </span>
                  )}
                </div>
              )}

              {!isCompleted && progress.remaining > 0 && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <TrendingUp className="h-3 w-3" />
                  <span>{progress.remaining} more to go</span>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
