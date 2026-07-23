import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { User, Save, ExternalLink, Lock, Eye, EyeOff } from 'lucide-react'
import { userApi } from '../services/userApi'
import { portfolioApi } from '../services/portfolioApi'
import { useUserStore } from '../stores/userStore'
import { useAuthStore } from '../stores/authStore'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'

export default function Settings() {
  const { profile, setProfile } = useUserStore()
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [portfolioUrl, setPortfolioUrl] = useState(null)
  const [formData, setFormData] = useState({
    bio: '',
    avatar_url: '',
    location: '',
    website: '',
    github_username: '',
    linkedin_url: '',
    is_public: true,
  })

  // Password change state
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [showPw, setShowPw] = useState({ current: false, new: false, confirm: false })

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const profileData = await userApi.getProfile()
      setProfile(profileData)
      setFormData({
        bio: profileData.bio || '',
        avatar_url: profileData.avatar_url || '',
        location: profileData.location || '',
        website: profileData.website || '',
        github_username: profileData.github_username || '',
        linkedin_url: profileData.linkedin_url || '',
        is_public: profileData.is_public ?? true,
      })
      if (profileData.portfolio_slug) {
        setPortfolioUrl(`/portfolio/${profileData.portfolio_slug}`)
      }
    } catch (error) {
      if (error.response?.status === 404) {
        console.log('No profile found, user can create one')
      } else {
        console.error('Failed to load profile:', error)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setSaving(true)
      let updatedProfile
      if (profile) {
        updatedProfile = await userApi.updateProfile(formData)
      } else {
        updatedProfile = await userApi.createProfile(formData)
      }
      setProfile(updatedProfile)
      toast.success('Profile saved successfully!')
    } catch (error) {
      console.error('Failed to save profile:', error)
      toast.error('Failed to save profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleGeneratePortfolio = async () => {
    try {
      const result = await portfolioApi.generatePortfolio()
      setPortfolioUrl(result.portfolio_url)
      toast.success('Portfolio generated successfully!')
    } catch (error) {
      console.error('Failed to generate portfolio:', error)
      toast.error(error.response?.data?.detail || 'Failed to generate portfolio. Please create a profile first.')
    }
  }

  const changePasswordMutation = useMutation({
    mutationFn: userApi.changePassword,
    onSuccess: () => {
      toast.success('Password changed successfully!')
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    },
  })

  const handleChangePassword = (e) => {
    e.preventDefault()
    if (pwForm.new_password !== pwForm.confirm_password) {
      toast.error('New passwords do not match')
      return
    }
    if (pwForm.new_password.length < 8) {
      toast.error('New password must be at least 8 characters')
      return
    }
    changePasswordMutation.mutate({
      current_password: pwForm.current_password,
      new_password: pwForm.new_password,
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account and preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profile Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Username</label>
                <Input value={user?.username || ''} disabled />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input value={user?.email || ''} disabled />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Bio</label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleChange}
                className="w-full min-h-[100px] px-3 py-2 border rounded-md bg-background"
                placeholder="Tell us about yourself..."
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Avatar URL</label>
              <Input
                name="avatar_url"
                value={formData.avatar_url}
                onChange={handleChange}
                placeholder="https://example.com/avatar.jpg"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <Input
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="San Francisco, CA"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Website</label>
                <Input
                  name="website"
                  value={formData.website}
                  onChange={handleChange}
                  placeholder="https://yourwebsite.com"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">GitHub Username</label>
                <Input
                  name="github_username"
                  value={formData.github_username}
                  onChange={handleChange}
                  placeholder="yourusername"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">LinkedIn URL</label>
                <Input
                  name="linkedin_url"
                  value={formData.linkedin_url}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/yourprofile"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_public"
                name="is_public"
                checked={formData.is_public}
                onChange={handleChange}
                className="rounded"
              />
              <label htmlFor="is_public" className="text-sm font-medium">
                Make profile public
              </label>
            </div>

            <Button type="submit" disabled={saving}>
              <Save className="h-4 w-4 mr-2" />
              {saving ? 'Saving...' : 'Save Profile'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Change Password
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
            {/* Current password */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Current Password</label>
              <div className="relative">
                <Input
                  type={showPw.current ? 'text' : 'password'}
                  value={pwForm.current_password}
                  onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })}
                  placeholder="Enter current password"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => ({ ...s, current: !s.current }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPw.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* New password */}
            <div className="space-y-2">
              <label className="text-sm font-medium">New Password</label>
              <div className="relative">
                <Input
                  type={showPw.new ? 'text' : 'password'}
                  value={pwForm.new_password}
                  onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
                  placeholder="At least 8 characters"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => ({ ...s, new: !s.new }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPw.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Confirm new password */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Confirm New Password</label>
              <div className="relative">
                <Input
                  type={showPw.confirm ? 'text' : 'password'}
                  value={pwForm.confirm_password}
                  onChange={(e) => setPwForm({ ...pwForm, confirm_password: e.target.value })}
                  placeholder="Repeat new password"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => ({ ...s, confirm: !s.confirm }))}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPw.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {pwForm.confirm_password && pwForm.new_password !== pwForm.confirm_password && (
                <p className="text-xs text-destructive">Passwords do not match</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={changePasswordMutation.isPending}
            >
              <Lock className="h-4 w-4 mr-2" />
              {changePasswordMutation.isPending ? 'Updating…' : 'Update Password'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Portfolio</CardTitle>
        </CardHeader>        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Generate a public portfolio to showcase your coding achievements
          </p>
          <div className="flex gap-4">
            <Button onClick={handleGeneratePortfolio}>
              Generate Portfolio
            </Button>
            {portfolioUrl && (
              <Button variant="outline" onClick={() => window.open(portfolioUrl, '_blank')}>
                <ExternalLink className="h-4 w-4 mr-2" />
                View Portfolio
              </Button>
            )}
          </div>
          {portfolioUrl && (
            <div className="p-4 bg-secondary rounded-md">
              <p className="text-sm font-medium mb-1">Your Portfolio URL:</p>
              <code className="text-sm">{window.location.origin}{portfolioUrl}</code>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
