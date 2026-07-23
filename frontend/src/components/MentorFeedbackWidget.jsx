import { useQuery } from '@tanstack/react-query'
import { mentoringApi } from '../services/mentoringApi'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { MessageSquare, AlertCircle, CheckCircle, Target } from 'lucide-react'

export default function MentorFeedbackWidget() {
  const { data: feedback, refetch } = useQuery({
    queryKey: ['my-feedback'],
    queryFn: () => mentoringApi.getMyFeedback(false),
  })

  const { data: mentor } = useQuery({
    queryKey: ['my-mentor'],
    queryFn: mentoringApi.getMyMentor,
  })

  const unreadCount = feedback?.filter((f) => !f.is_read).length || 0

  const handleMarkRead = async (feedbackId) => {
    await mentoringApi.markFeedbackRead(feedbackId)
    refetch()
  }

  const getFeedbackIcon = (type) => {
    switch (type) {
      case 'task':
        return <Target className="h-4 w-4" />
      case 'recommendation':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <MessageSquare className="h-4 w-4" />
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'destructive'
      case 'normal':
        return 'default'
      case 'low':
        return 'secondary'
      default:
        return 'default'
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Mentor Feedback
          </span>
          {unreadCount > 0 && (
            <Badge variant="destructive">{unreadCount} new</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {mentor && (
          <div className="mb-4 p-3 bg-accent rounded-lg">
            <p className="text-sm text-muted-foreground">Your Mentor</p>
            <p className="font-medium">{mentor.full_name || mentor.username}</p>
            <p className="text-sm text-muted-foreground">{mentor.email}</p>
          </div>
        )}

        <div className="space-y-3">
          {feedback && feedback.length > 0 ? (
            feedback.slice(0, 5).map((item) => (
              <div
                key={item.id}
                className={`p-3 rounded-lg border ${
                  !item.is_read ? 'bg-blue-50 border-blue-200' : 'bg-background'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getFeedbackIcon(item.feedback_type)}
                    <span className="font-medium text-sm capitalize">
                      {item.feedback_type}
                    </span>
                  </div>
                  <Badge variant={getPriorityColor(item.priority)} size="sm">
                    {item.priority}
                  </Badge>
                </div>
                {item.title && (
                  <p className="font-medium mb-1">{item.title}</p>
                )}
                <p className="text-sm text-muted-foreground">{item.content}</p>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString()}
                  </p>
                  {!item.is_read && (
                    <button
                      onClick={() => handleMarkRead(item.id)}
                      className="text-xs text-primary hover:underline"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No feedback yet</p>
              <p className="text-sm">Your mentor will provide guidance here</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
