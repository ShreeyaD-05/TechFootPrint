import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { MessageSquare, ThumbsUp, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { discussionsApi } from '../../services/api'

export default function DiscussionsWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['discussions-overview'],
    queryFn: () => discussionsApi.getOverview(),
    retry: 1
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Discussions</CardTitle>
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
          <CardTitle>Discussions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm text-red-600">{error.message}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const recentDiscussions = data?.recent_discussions || []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Recent Discussions
        </CardTitle>
        <Link to="/discussions">
          <Button variant="ghost" size="sm">
            View All
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {recentDiscussions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No discussions yet</p>
            <Link to="/discussions/new">
              <Button variant="outline" size="sm" className="mt-3">
                Start a Discussion
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recentDiscussions.slice(0, 5).map((discussion) => (
              <Link key={discussion.id} to={`/discussions/${discussion.id}`}>
                <div className="p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-sm line-clamp-1">{discussion.title}</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        by {discussion.username} • {new Date(discussion.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <div className="flex items-center gap-1 text-xs">
                        <ThumbsUp className="h-3 w-3" />
                        <span>{discussion.upvotes}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs">
                        <MessageSquare className="h-3 w-3" />
                        <span>{discussion.reply_count}</span>
                      </div>
                    </div>
                  </div>
                  {discussion.is_solved && (
                    <Badge variant="success" className="mt-2 text-xs">Solved</Badge>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
