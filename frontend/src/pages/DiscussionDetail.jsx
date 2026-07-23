import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ArrowLeft, ThumbsUp, MessageSquare, CheckCircle, Send } from 'lucide-react'
import { discussionsApi } from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

function ReplyCard({ reply, onVote, currentUserId }) {
  return (
    <div className={`p-4 rounded-lg border ${reply.is_solution ? 'border-green-500 bg-green-50 dark:bg-green-900/10' : ''}`}>
      {reply.is_solution && (
        <div className="flex items-center gap-1 text-green-600 text-xs font-medium mb-2">
          <CheckCircle className="h-3 w-3" />
          Accepted Solution
        </div>
      )}
      <p className="text-sm whitespace-pre-wrap">{reply.content}</p>
      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="font-medium">{reply.full_name || reply.username}</span>
          <span>{new Date(reply.created_at).toLocaleDateString()}</span>
        </div>
        <button
          onClick={() => onVote(reply.id)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors"
        >
          <ThumbsUp className="h-3 w-3" />
          <span>{reply.upvotes}</span>
        </button>
      </div>
    </div>
  )
}

export default function DiscussionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [replyContent, setReplyContent] = useState('')
  const [markAsSolution, setMarkAsSolution] = useState(false)

  const { data: discussion, isLoading, error } = useQuery({
    queryKey: ['discussion', id],
    queryFn: () => discussionsApi.getById(id),
    retry: 1
  })

  const replyMutation = useMutation({
    mutationFn: () => discussionsApi.addReply(id, { content: replyContent, is_solution: markAsSolution }),
    onSuccess: () => {
      toast.success('Reply posted!')
      setReplyContent('')
      setMarkAsSolution(false)
      queryClient.invalidateQueries({ queryKey: ['discussion', id] })
    },
    onError: (err) => toast.error(err.message || 'Failed to post reply')
  })

  const voteMutation = useMutation({
    mutationFn: () => discussionsApi.vote(id, 'upvote'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['discussion', id] })
  })

  const voteReplyMutation = useMutation({
    mutationFn: (replyId) => discussionsApi.voteReply(replyId, 'upvote'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['discussion', id] })
  })

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="h-8 w-32 bg-muted animate-pulse rounded" />
        <div className="h-64 bg-muted animate-pulse rounded-lg" />
        <div className="h-32 bg-muted animate-pulse rounded-lg" />
      </div>
    )
  }

  if (error || !discussion) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-600">{error?.message || 'Discussion not found'}</p>
            <Button variant="outline" className="mt-4" onClick={() => navigate('/discussions')}>
              Back to Discussions
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => navigate('/discussions')}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Discussions
      </Button>

      {/* Main Discussion */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          {/* Title & badges */}
          <div className="flex items-start justify-between gap-4">
            <h1 className="text-xl font-bold leading-tight">{discussion.title}</h1>
            {discussion.is_solved && (
              <Badge variant="success" className="flex items-center gap-1 shrink-0">
                <CheckCircle className="h-3 w-3" />
                Solved
              </Badge>
            )}
          </div>

          {/* Tags */}
          {discussion.tags?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {discussion.tags.map(tag => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          )}

          {/* Content */}
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{discussion.content}</p>

          {/* Meta + vote */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="text-xs text-muted-foreground">
              <span className="font-medium">{discussion.full_name || discussion.username}</span>
              {' · '}
              {new Date(discussion.created_at).toLocaleDateString()}
              {discussion.problem_title && (
                <span className="ml-2 text-primary">· {discussion.problem_title}</span>
              )}
            </div>
            <button
              onClick={() => voteMutation.mutate()}
              className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              <ThumbsUp className={`h-4 w-4 ${discussion.user_voted === 'upvote' ? 'fill-primary text-primary' : ''}`} />
              <span>{discussion.upvotes}</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Replies */}
      <div className="space-y-3">
        <h2 className="font-semibold flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          {discussion.replies?.length || 0} {discussion.replies?.length === 1 ? 'Reply' : 'Replies'}
        </h2>

        {discussion.replies?.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No replies yet — be the first to help!
          </p>
        ) : (
          discussion.replies.map(reply => (
            <ReplyCard
              key={reply.id}
              reply={reply}
              onVote={(replyId) => voteReplyMutation.mutate(replyId)}
              currentUserId={user?.id}
            />
          ))
        )}
      </div>

      {/* Reply Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your Reply</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <textarea
            className="w-full min-h-[120px] px-3 py-2 text-sm border rounded-lg bg-background resize-y focus:outline-none focus:ring-2 focus:ring-ring"
            placeholder="Write a helpful reply..."
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
          />

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={markAsSolution}
                onChange={(e) => setMarkAsSolution(e.target.checked)}
                className="rounded"
              />
              Mark as solution
            </label>

            <Button
              onClick={() => replyMutation.mutate()}
              disabled={!replyContent.trim() || replyMutation.isPending}
              size="sm"
            >
              <Send className="h-4 w-4 mr-2" />
              {replyMutation.isPending ? 'Posting...' : 'Post Reply'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
