import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { platformApi } from '../services/platformApi'
import { PlatformCard } from '../components/PlatformCard'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import toast from 'react-hot-toast'
import { Plus } from 'lucide-react'

export default function Platforms() {
  const [showAddForm, setShowAddForm] = useState(false)
  const queryClient = useQueryClient()
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  const { data: connectedPlatforms, isLoading } = useQuery({
    queryKey: ['platforms'],
    queryFn: platformApi.getConnectedPlatforms,
  })

  const { data: availablePlatforms } = useQuery({
    queryKey: ['available-platforms'],
    queryFn: platformApi.getAvailablePlatforms,
  })

  const connectMutation = useMutation({
    mutationFn: platformApi.connectPlatform,
    onSuccess: () => {
      queryClient.invalidateQueries(['platforms'])
      toast.success('Platform connected successfully!')
      reset()
      setShowAddForm(false)
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to connect platform')
    },
  })

  const syncMutation = useMutation({
    mutationFn: platformApi.syncPlatform,
    onSuccess: () => {
      queryClient.invalidateQueries(['platforms'])
      queryClient.invalidateQueries(['analytics'])
      toast.success('Sync initiated!')
    },
    onError: () => {
      toast.error('Failed to sync platform')
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: platformApi.disconnectPlatform,
    onSuccess: () => {
      queryClient.invalidateQueries(['platforms'])
      toast.success('Platform disconnected')
    },
    onError: () => {
      toast.error('Failed to disconnect platform')
    },
  })

  const onSubmit = (data) => {
    connectMutation.mutate(data)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Platforms</h1>
          <p className="text-muted-foreground">
            Connect and manage your coding platform accounts
          </p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Connect Platform
        </Button>
      </div>

      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>Connect New Platform</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Platform</label>
                  <select
                    {...register('platform_name', { required: 'Platform is required' })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Select platform</option>
                    {availablePlatforms?.platforms?.map((platform) => (
                      <option key={platform} value={platform}>
                        {platform}
                      </option>
                    ))}
                  </select>
                  {errors.platform_name && (
                    <p className="text-sm text-destructive">{errors.platform_name.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Username</label>
                  <Input
                    {...register('platform_username', { required: 'Username is required' })}
                    placeholder="Your username on this platform"
                  />
                  {errors.platform_username && (
                    <p className="text-sm text-destructive">{errors.platform_username.message}</p>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={connectMutation.isPending}>
                  {connectMutation.isPending ? 'Connecting...' : 'Connect'}
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-muted animate-pulse rounded-lg" />
          ))
        ) : connectedPlatforms && connectedPlatforms.length > 0 ? (
          connectedPlatforms.map((platform) => (
            <PlatformCard
              key={platform.id}
              platform={platform}
              onSync={syncMutation.mutate}
              onDisconnect={disconnectMutation.mutate}
              isLoading={syncMutation.isPending || disconnectMutation.isPending}
            />
          ))
        ) : (
          <Card className="col-span-full">
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">No platforms connected yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Click "Connect Platform" to get started
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
