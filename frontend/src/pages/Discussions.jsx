import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { MessageSquare, ThumbsUp, CheckCircle, Plus, Search, Filter } from 'lucide-react'
import { Link } from 'react-router-dom'
import { discussionsApi } from '../services/api'

export default function Discussions() {
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('recent')
  const [filterSolved, setFilterSolved] = useState(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['discussions', searchTerm, sortBy, filterSolved],
    queryFn: () => discussionsApi.getAll({
      sort_by: sortBy,
      ...(searchTerm && { search: searchTerm }),
      ...(filterSolved !== null && { is_solved: filterSolved })
    }),
    retry: 1
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="py-12 text-center">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 text-red-500 opacity-50" />
            <p className="text-red-600 font-medium">{error.message}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Please try refreshing the page or logging in again
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const discussions = data?.discussions || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Peer Discussions</h1>
          <p className="text-muted-foreground">Ask questions and help others</p>
        </div>
        <Link to="/discussions/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Discussion
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search discussions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex gap-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-2 border rounded-lg"
              >
                <option value="recent">Recent</option>
                <option value="popular">Popular</option>
                <option value="replies">Most Replies</option>
              </select>
              
              <select
                value={filterSolved === null ? 'all' : filterSolved ? 'solved' : 'unsolved'}
                onChange={(e) => {
                  const val = e.target.value
                  setFilterSolved(val === 'all' ? null : val === 'solved')
                }}
                className="px-4 py-2 border rounded-lg"
              >
                <option value="all">All</option>
                <option value="unsolved">Unsolved</option>
                <option value="solved">Solved</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Discussions List */}
      <div className="space-y-4">
        {discussions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No discussions found</p>
              <p className="text-sm text-muted-foreground mt-2">
                Be the first to start a discussion!
              </p>
            </CardContent>
          </Card>
        ) : (
          discussions.map((discussion) => (
            <Link key={discussion.id} to={`/discussions/${discussion.id}`}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-semibold">{discussion.title}</h3>
                        {discussion.is_solved && (
                          <Badge variant="success" className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Solved
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {discussion.content}
                      </p>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>by {discussion.full_name || discussion.username}</span>
                        <span>•</span>
                        <span>{new Date(discussion.created_at).toLocaleDateString()}</span>
                        {discussion.problem_title && (
                          <>
                            <span>•</span>
                            <span className="text-primary">{discussion.problem_title}</span>
                          </>
                        )}
                      </div>
                      
                      {discussion.tags && discussion.tags.length > 0 && (
                        <div className="flex gap-2 mt-3">
                          {discussion.tags.map((tag, idx) => (
                            <Badge key={idx} variant="secondary">{tag}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex flex-col items-end gap-2 ml-4">
                      <div className="flex items-center gap-1 text-sm">
                        <ThumbsUp className="h-4 w-4" />
                        <span>{discussion.upvotes}</span>
                      </div>
                      <div className="flex items-center gap-1 text-sm">
                        <MessageSquare className="h-4 w-4" />
                        <span>{discussion.reply_count}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
