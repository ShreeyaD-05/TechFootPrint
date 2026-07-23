import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { platformApi } from '../services/platformApi'
import { Card, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { FileCode, Calendar, Tag, Eye } from 'lucide-react'

export default function Problems() {
  const navigate = useNavigate()
  const [selectedPlatform, setSelectedPlatform] = useState('all')

  const { data: connectedPlatforms } = useQuery({
    queryKey: ['platforms'],
    queryFn: platformApi.getConnectedPlatforms,
  })

  const { data: allProblems, isLoading } = useQuery({
    queryKey: ['all-problems', connectedPlatforms],
    queryFn: async () => {
      if (!connectedPlatforms || connectedPlatforms.length === 0) return []
      
      const problemsPromises = connectedPlatforms.map(async (platform) => {
        try {
          const problems = await platformApi.getPlatformProblems(platform.id)
          return problems.map(p => ({ ...p, platform }))
        } catch (error) {
          console.error(`Failed to fetch problems for ${platform.platform_name}:`, error)
          return []
        }
      })
      
      const problemsArrays = await Promise.all(problemsPromises)
      return problemsArrays.flat()
    },
    enabled: !!connectedPlatforms && connectedPlatforms.length > 0,
  })

  const filteredProblems = allProblems?.filter(problem => 
    selectedPlatform === 'all' || problem.platform.platform_name === selectedPlatform
  ) || []

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'hard':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Problems</h1>
          <p className="text-muted-foreground">
            View all problems you've solved across platforms
          </p>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <Button
          variant={selectedPlatform === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedPlatform('all')}
        >
          All Platforms
        </Button>
        {connectedPlatforms?.map((platform) => (
          <Button
            key={platform.id}
            variant={selectedPlatform === platform.platform_name ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedPlatform(platform.platform_name)}
          >
            {platform.platform_name}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      ) : filteredProblems.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileCode className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No problems found</p>
            <p className="text-sm text-muted-foreground mt-1">
              Connect platforms and sync to see your solved problems
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredProblems.map((problem) => (
            <Card key={`${problem.platform.id}-${problem.id}`} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold">{problem.problem_title}</h3>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getDifficultyColor(problem.difficulty)}`}>
                        {problem.difficulty}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                      <div className="flex items-center gap-1">
                        <FileCode className="h-4 w-4" />
                        <span className="capitalize">{problem.platform.platform_name}</span>
                      </div>
                      {problem.solved_at && (
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          <span>{formatDate(problem.solved_at)}</span>
                        </div>
                      )}
                      {problem.submission_count > 1 && (
                        <span>{problem.submission_count} submissions</span>
                      )}
                    </div>

                    {problem.topics && problem.topics.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap">
                        <Tag className="h-4 w-4 text-muted-foreground" />
                        {problem.topics.slice(0, 5).map((topic, idx) => (
                          <span key={idx} className="px-2 py-1 rounded text-xs bg-muted text-muted-foreground">
                            {topic}
                          </span>
                        ))}
                        {problem.topics.length > 5 && (
                          <span className="text-xs text-muted-foreground">
                            +{problem.topics.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/problems/${problem.platform.id}/${problem.id}`)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Submissions
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
