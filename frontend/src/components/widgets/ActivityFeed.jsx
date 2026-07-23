import { Clock, Code, Sync, MessageSquare, Target, FileText, User } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function ActivityFeed({ activities = [], limit = 10 }) {
  const getActivityIcon = (type) => {
    const icons = {
      login: User,
      problem_solved: Code,
      platform_sync: Sync,
      feedback_read: MessageSquare,
      goal_completed: Target,
      note_created: FileText,
      profile_updated: User
    }
    const Icon = icons[type] || Clock
    return <Icon className="h-4 w-4" />
  }

  const getActivityColor = (type) => {
    const colors = {
      login: 'text-blue-500',
      problem_solved: 'text-green-500',
      platform_sync: 'text-purple-500',
      feedback_read: 'text-orange-500',
      goal_completed: 'text-yellow-500',
      note_created: 'text-pink-500',
      profile_updated: 'text-gray-500'
    }
    return colors[type] || 'text-gray-500'
  }

  const displayActivities = activities.slice(0, limit)

  if (displayActivities.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
        <p>No recent activity</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {displayActivities.map((activity) => (
        <div
          key={activity.id}
          className="flex items-start gap-3 p-3 rounded-lg hover:bg-accent transition-colors"
        >
          <div className={`mt-0.5 ${getActivityColor(activity.type)}`}>
            {getActivityIcon(activity.type)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{activity.description}</p>
            {activity.platform && (
              <p className="text-xs text-muted-foreground">
                Platform: {activity.platform}
              </p>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              {formatDistanceToNow(new Date(activity.date), { addSuffix: true })}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
