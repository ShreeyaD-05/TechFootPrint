import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { FileText, ArrowRight, CheckCircle, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { submissionsApi } from '../../services/api'

export default function SubmissionsWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['submissions-overview'],
    queryFn: () => submissionsApi.getOverview(),
    retry: 1
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Submissions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Submissions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm text-red-600">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const stats = data?.stats || {}
  const recentSubmissions = stats.recent_submissions || []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Recent Submissions
        </CardTitle>
        <Link to="/submissions">
          <Button variant="ghost" size="sm">
            View All
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-3 bg-muted rounded-lg">
            <div className="text-2xl font-bold">{stats.total_submissions || 0}</div>
            <div className="text-xs text-muted-foreground">Total</div>
          </div>
          <div className="text-center p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.accepted || 0}</div>
            <div className="text-xs text-muted-foreground">Accepted</div>
          </div>
          <div className="text-center p-3 bg-red-100 dark:bg-red-900/20 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{stats.wrong_answer || 0}</div>
            <div className="text-xs text-muted-foreground">Wrong</div>
          </div>
        </div>

        {/* Recent Submissions List */}
        {recentSubmissions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No submissions yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentSubmissions.slice(0, 5).map((submission) => (
              <div
                key={submission.id}
                className="flex items-center justify-between p-2 border rounded hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {submission.problem_title || submission.problem_id}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-xs capitalize">
                      {submission.platform}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(submission.submission_time).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <Badge
                  variant={submission.status === 'Accepted' ? 'success' : 'destructive'}
                  className="ml-2 flex items-center gap-1"
                >
                  {submission.status === 'Accepted' ? (
                    <CheckCircle className="h-3 w-3" />
                  ) : (
                    <XCircle className="h-3 w-3" />
                  )}
                  {submission.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
