import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { User, MapPin, Globe, Github, Linkedin, ExternalLink, Code2, Trophy, Flame } from 'lucide-react'
import { portfolioApi } from '../services/portfolioApi'
import { useAuthStore } from '../stores/authStore'

export default function Portfolio({ isPublic = false }) {
  const { slug } = useParams()
  const { user } = useAuthStore()
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (isPublic && slug) {
      loadPublicPortfolio()
    } else if (!isPublic && user) {
      loadPublicPortfolio(user.username)
    }
  }, [slug, user, isPublic])

  const loadPublicPortfolio = async (portfolioSlug = slug) => {
    try {
      setLoading(true)
      const data = await portfolioApi.getPublicPortfolio(portfolioSlug)
      setPortfolio(data)
    } catch (error) {
      console.error('Failed to load portfolio:', error)
      setError(error.response?.data?.detail || 'Portfolio not found')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading portfolio...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <User className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground mb-2">{error}</p>
            <p className="text-sm text-muted-foreground">
              {!isPublic && 'Create your profile in Settings to generate a portfolio'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Portfolio</h1>
          <p className="text-muted-foreground">Your shareable developer profile</p>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <User className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground mb-2">Portfolio not generated yet</p>
            <p className="text-sm text-muted-foreground">
              Go to Settings to create your profile and generate your portfolio
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { profile, analytics, platforms } = portfolio

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-6">
            {profile.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt={profile.username}
                className="h-24 w-24 rounded-full object-cover"
              />
            ) : (
              <div className="h-24 w-24 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-12 w-12 text-primary" />
              </div>
            )}
            
            <div className="flex-1">
              <h1 className="text-3xl font-bold">{profile.full_name || profile.username}</h1>
              <p className="text-muted-foreground">@{profile.username}</p>
              
              {profile.bio && (
                <p className="mt-3 text-sm">{profile.bio}</p>
              )}
              
              <div className="flex flex-wrap gap-4 mt-4 text-sm text-muted-foreground">
                {profile.location && (
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {profile.location}
                  </div>
                )}
                {profile.website && (
                  <a
                    href={profile.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 hover:text-primary"
                  >
                    <Globe className="h-4 w-4" />
                    Website
                  </a>
                )}
                {profile.github_username && (
                  <a
                    href={`https://github.com/${profile.github_username}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 hover:text-primary"
                  >
                    <Github className="h-4 w-4" />
                    GitHub
                  </a>
                )}
                {profile.linkedin_url && (
                  <a
                    href={profile.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 hover:text-primary"
                  >
                    <Linkedin className="h-4 w-4" />
                    LinkedIn
                  </a>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Problems</CardTitle>
            <Code2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_problems_solved}</div>
            <div className="flex gap-2 mt-2 text-xs">
              <span className="text-green-600">Easy: {analytics.easy_solved}</span>
              <span className="text-yellow-600">Medium: {analytics.medium_solved}</span>
              <span className="text-red-600">Hard: {analytics.hard_solved}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
            <Flame className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.current_streak} days</div>
            <p className="text-xs text-muted-foreground mt-2">
              Keep it going!
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Longest Streak</CardTitle>
            <Trophy className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.longest_streak} days</div>
            <p className="text-xs text-muted-foreground mt-2">
              Personal best
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Connected Platforms */}
      <Card>
        <CardHeader>
          <CardTitle>Connected Platforms</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {platforms && platforms.length > 0 ? (
              platforms.map((platform, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg border">
                  <div>
                    <p className="font-medium capitalize">{platform.name}</p>
                    <p className="text-sm text-muted-foreground">@{platform.username}</p>
                  </div>
                  {platform.last_synced && (
                    <Badge variant="secondary">
                      Synced {new Date(platform.last_synced).toLocaleDateString()}
                    </Badge>
                  )}
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground col-span-2 text-center py-4">
                No platforms connected yet
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Platform Distribution */}
      {analytics.platform_distribution && Object.keys(analytics.platform_distribution).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Platform Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(analytics.platform_distribution).map(([platform, count]) => (
                <div key={platform}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium capitalize">{platform}</span>
                    <span className="text-sm text-muted-foreground">{count} problems</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{
                        width: `${(count / analytics.total_problems_solved) * 100}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Topic Distribution */}
      {analytics.topic_distribution && Object.keys(analytics.topic_distribution).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(analytics.topic_distribution)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 20)
                .map(([topic, count]) => (
                  <Badge key={topic} variant="secondary">
                    {topic}: {count}
                  </Badge>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
