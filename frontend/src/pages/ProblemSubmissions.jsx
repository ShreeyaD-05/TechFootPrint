import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { platformApi } from '../services/platformApi'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ArrowLeft, CheckCircle, XCircle, Clock, Code } from 'lucide-react'

export default function ProblemSubmissions() {
  const { platformId, problemId } = useParams()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['problem-submissions', platformId, problemId],
    queryFn: () => platformApi.getProblemSubmissions(platformId, problemId),
  })

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'accepted':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'wrong_answer':
      case 'wrong answer':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'time_limit_exceeded':
      case 'time limit exceeded':
        return <Clock className="h-5 w-5 text-yellow-500" />
      default:
        return <Code className="h-5 w-5 text-gray-500" />
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  const problem = data?.problem
  const submissions = data?.submissions || []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      {problem && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{problem.title}</CardTitle>
            <div className="flex gap-2 mt-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                problem.difficulty === 'Easy' ? 'bg-green-100 text-green-800' :
                problem.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                problem.difficulty === 'Hard' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {problem.difficulty}
              </span>
              {problem.solved_at && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  Solved: {formatDate(problem.solved_at)}
                </span>
              )}
            </div>
            {problem.topics && problem.topics.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {problem.topics.map((topic, idx) => (
                  <span key={idx} className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-700">
                    {topic}
                  </span>
                ))}
              </div>
            )}
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Submissions ({submissions.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No submissions found for this problem
            </div>
          ) : (
            <div className="space-y-3">
              {submissions.map((submission) => (
                <div
                  key={submission.id}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(submission.status)}
                      <div>
                        <div className="font-medium capitalize">
                          {submission.status?.replace(/_/g, ' ')}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {formatDate(submission.submitted_at)}
                        </div>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      {submission.language && (
                        <div className="font-medium">{submission.language}</div>
                      )}
                      {submission.runtime && (
                        <div className="text-muted-foreground">
                          Runtime: {submission.runtime}
                        </div>
                      )}
                      {submission.memory && (
                        <div className="text-muted-foreground">
                          Memory: {submission.memory}
                        </div>
                      )}
                    </div>
                  </div>
                  {submission.code && (
                    <details className="mt-3">
                      <summary className="cursor-pointer text-sm text-primary hover:underline">
                        View Code
                      </summary>
                      <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-x-auto">
                        <code>{submission.code}</code>
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
