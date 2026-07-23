import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { ArrowLeft, Plus, X } from 'lucide-react'
import { discussionsApi } from '../services/api'
import toast from 'react-hot-toast'

const SUGGESTED_TAGS = ['arrays', 'strings', 'dynamic-programming', 'graphs', 'trees', 'sorting', 'binary-search', 'recursion', 'greedy', 'math', 'hash-table', 'two-pointers', 'sliding-window', 'backtracking', 'optimization']

export default function NewDiscussion() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [tagInput, setTagInput] = useState('')
  const [tags, setTags] = useState([])

  const createMutation = useMutation({
    mutationFn: () => discussionsApi.create({ title, content, tags }),
    onSuccess: (data) => {
      toast.success('Discussion created!')
      navigate(`/discussions/${data.discussion_id}`)
    },
    onError: (err) => {
      toast.error(err.message || 'Failed to create discussion')
    }
  })

  const addTag = (tag) => {
    const clean = tag.trim().toLowerCase().replace(/\s+/g, '-')
    if (clean && !tags.includes(clean) && tags.length < 5) {
      setTags([...tags, clean])
    }
    setTagInput('')
  }

  const removeTag = (tag) => setTags(tags.filter(t => t !== tag))

  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag(tagInput)
    }
  }

  const canSubmit = title.trim().length >= 5 && content.trim().length >= 10

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/discussions')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl font-bold">New Discussion</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ask a question or start a discussion</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Title */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Title <span className="text-red-500">*</span></label>
            <Input
              placeholder="e.g. How to approach Two Sum with O(n) time complexity?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={255}
            />
            <p className="text-xs text-muted-foreground">{title.length}/255 — be specific and clear</p>
          </div>

          {/* Content */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Description <span className="text-red-500">*</span></label>
            <textarea
              className="w-full min-h-[200px] px-3 py-2 text-sm border rounded-lg bg-background resize-y focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Describe your question in detail. Include what you've tried, what's not working, and any relevant code or examples..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">{content.length} characters — minimum 10</p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Tags <span className="text-muted-foreground">(up to 5)</span></label>

            {/* Current tags */}
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1 pr-1">
                    {tag}
                    <button onClick={() => removeTag(tag)} className="hover:text-destructive ml-1">
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}

            {/* Tag input */}
            {tags.length < 5 && (
              <div className="flex gap-2">
                <Input
                  placeholder="Type a tag and press Enter..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagKeyDown}
                  className="flex-1"
                />
                <Button variant="outline" size="sm" onClick={() => addTag(tagInput)} disabled={!tagInput.trim()}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Suggested tags */}
            <div className="flex flex-wrap gap-1 mt-2">
              {SUGGESTED_TAGS.filter(t => !tags.includes(t)).slice(0, 8).map(tag => (
                <button
                  key={tag}
                  onClick={() => addTag(tag)}
                  className="text-xs px-2 py-1 rounded border border-dashed hover:bg-muted transition-colors"
                >
                  + {tag}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => navigate('/discussions')}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!canSubmit || createMutation.isPending}
            >
              {createMutation.isPending ? 'Posting...' : 'Post Discussion'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
