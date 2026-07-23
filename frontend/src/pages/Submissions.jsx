import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Code2, Search, Filter, ExternalLink, Calendar, Clock } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'
import { submissionsApi } from '../services/api'

const STATUS_COLORS = {
  'Accepted': '#10b981',
  'Wrong Answer': '#ef4444',
  'Time Limit Exceeded': '#f59e0b',
  'Runtime Error': '#8b5cf6',
  'Compilation Error': '#6b7280'
}

export default function Submissions() {
  const [searchTerm, setSearchTerm] = useState('')
  const [platformFilter, setPlatformFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const { data: stats, error: statsError } = useQuery({
    queryKey: ['submission-stats'],
    queryFn: () => submissionsApi.getStats(30),
    retry: 1
  })

  const { data: submissions, isLoading, error } = useQuery({
    queryKey: ['submissions', searchTerm, platformFilter, difficultyFilter, statusFilter, page],
    queryFn: () => submissionsApi.getAll({
      skip: (page - 1) * 20,
      limit: 20,
      ...(searchTerm && { search: searchTerm }),
      ...(platformFilter && { platform: platformFilter }),
      ...(difficultyFilter && { difficulty: difficultyFilter }),
      ...(statusFilter && { status: statusFilter })
    }),
    retry: 1
  })

  const statusData = stats ? [
    { name: 'Accepted', value: stats.accepted, color: STATUS_COLORS['Accepted'] },
    { name: 'Wrong Answer', value: stats.wrong_answer, color: STATUS_COLORS['Wrong Answer'] },
    { name: 'TLE', value: stats.time_limit_exceeded, color: STATUS_COLORS['Time Limit Exceeded'] },
    { name: 'Runtime Error', value: stats.runtime_error, color: STATUS_COLORS['Runtime Error'] }
  ] : []

  const platformData = stats ? Object.entries(stats.by_platform).map(([name, value]) => ({
    name,
    submissions: value
  })) : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">My Submissions</h1>
        <p className="text-muted-foreground">Track all your problem submissions across platforms</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Submissions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_submissions}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Accepted</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.accepted}</div>
              <p className="text-xs text-muted-foreground">
                {stats.total_submissions > 0 ? Math.round((stats.accepted / stats.total_submissions) * 100) : 0}% acceptance rate
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Wrong Answer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.wrong_answer}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Time Limit Exceeded</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats.time_limit_exceeded}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts */}
      {stats && (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Submission Status</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => value > 0 ? `${name}: ${value}` : ''}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>By Platform</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={platformData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="submissions" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-5">
            <div className="md:col-span-2 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search problems..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <select
              value={platformFilter}
              onChange={(e) => setPlatformFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Platforms</option>
              <option value="leetcode">LeetCode</option>
              <option value="codeforces">Codeforces</option>
              <option value="codechef">CodeChef</option>
              <option value="hackerrank">HackerRank</option>
            </select>
            
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">All Status</option>
              <option value="Accepted">Accepted</option>
              <option value="Wrong Answer">Wrong Answer</option>
              <option value="Time Limit Exceeded">TLE</option>
              <option value="Runtime Error">Runtime Error</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Submissions List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Submissions</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />
              ))}
            </div>
          ) : submissions?.submissions?.length === 0 ? (
            <div className="text-center py-12">
              <Code2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No submissions found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {submissions?.submissions?.map((submission) => (
                <div
                  key={submission.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-medium">{submission.problem_title || submission.problem_id}</h4>
                      <Badge variant="secondary" className="capitalize">{submission.platform}</Badge>
                      {submission.difficulty && (
                        <Badge
                          variant={
                            submission.difficulty === 'easy' ? 'success' :
                            submission.difficulty === 'medium' ? 'warning' : 'destructive'
                          }
                        >
                          {submission.difficulty}
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(submission.submission_time).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(submission.submission_time).toLocaleTimeString()}
                      </span>
                      {submission.language && <span>• {submission.language}</span>}
                      {submission.runtime && <span>• Runtime: {submission.runtime}</span>}
                      {submission.memory && <span>• Memory: {submission.memory}</span>}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={submission.status === 'Accepted' ? 'success' : 'destructive'}
                      className="min-w-[120px] justify-center"
                    >
                      {submission.status}
                    </Badge>
                    
                    {submission.submission_url && (
                      <a
                        href={submission.submission_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Pagination */}
          {submissions && submissions.total > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded-lg disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {page} of {Math.ceil(submissions.total / 20)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= Math.ceil(submissions.total / 20)}
                className="px-4 py-2 border rounded-lg disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
