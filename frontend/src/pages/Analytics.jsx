import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { BarChart3, TrendingUp, Calendar, RefreshCw } from 'lucide-react'
import { analyticsApi } from '../services/analyticsApi'
import toast from 'react-hot-toast'

export default function Analytics() {
  const queryClient = useQueryClient()

  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: analyticsApi.getAnalytics,
  })

  const recalcMutation = useMutation({
    mutationFn: analyticsApi.recalculateAnalytics,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      toast.success('Analytics recalculated')
    },
    onError: () => toast.error('Failed to recalculate analytics'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading analytics...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Deep dive into your coding statistics</p>
        </div>
        <Button onClick={() => recalcMutation.mutate()} disabled={recalcMutation.isPending}>
          <RefreshCw className={`h-4 w-4 mr-2 ${recalcMutation.isPending ? 'animate-spin' : ''}`} />
          Recalculate
        </Button>
      </div>

      {analytics && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Problems</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.total_problems_solved}</div>
                <p className="text-xs text-muted-foreground">Across all platforms</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.current_streak}</div>
                <p className="text-xs text-muted-foreground">Days in a row</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Longest Streak</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics.longest_streak}</div>
                <p className="text-xs text-muted-foreground">Personal best</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm font-medium">
                  {new Date(analytics.last_calculated_at).toLocaleDateString()}
                </div>
                <p className="text-xs text-muted-foreground">
                  {new Date(analytics.last_calculated_at).toLocaleTimeString()}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Difficulty Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { label: 'Easy', value: analytics.easy_solved, color: 'bg-green-500' },
                    { label: 'Medium', value: analytics.medium_solved, color: 'bg-yellow-500' },
                    { label: 'Hard', value: analytics.hard_solved, color: 'bg-red-500' },
                  ].map(({ label, value, color }) => (
                    <div key={label}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{label}</span>
                        <span className="text-sm text-muted-foreground">{value}</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className={`${color} h-2 rounded-full`}
                          style={{
                            width: analytics.total_problems_solved
                              ? `${(value / analytics.total_problems_solved) * 100}%`
                              : '0%',
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Platform Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {analytics.platform_distribution &&
                Object.keys(analytics.platform_distribution).length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(analytics.platform_distribution).map(([platform, count]) => (
                      <div key={platform}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium capitalize">{platform}</span>
                          <span className="text-sm text-muted-foreground">{count}</span>
                        </div>
                        <div className="w-full bg-secondary rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full"
                            style={{
                              width: analytics.total_problems_solved
                                ? `${(count / analytics.total_problems_solved) * 100}%`
                                : '0%',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No platform data available yet
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {analytics.topic_distribution &&
            Object.keys(analytics.topic_distribution).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Topic Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {Object.entries(analytics.topic_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 12)
                      .map(([topic, count]) => (
                        <div key={topic} className="flex flex-col items-center p-4 border rounded-lg">
                          <div className="text-2xl font-bold">{count}</div>
                          <div className="text-sm text-muted-foreground text-center capitalize">
                            {topic.replace(/-/g, ' ')}
                          </div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            )}
        </>
      )}
    </div>
  )
}
