import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { authApi } from '../../services/authApi'
import { useAuthStore } from '../../stores/authStore'
import toast from 'react-hot-toast'
import { Code2 } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const { register, handleSubmit, formState: { errors } } = useForm()

  const loginMutation = useMutation({
    mutationFn: ({ username, password }) => authApi.login(username, password),
    onSuccess: async (data) => {
      // Set token first so subsequent requests can use it
      setAuth(null, data.access_token)
      
      try {
        // Now get user data with the token set
        const userData = await authApi.getCurrentUser()
        setAuth(userData, data.access_token)
        toast.success('Welcome back!')
        
        // Role-based redirect
        if (userData.role === 'super_admin') {
          navigate('/admin')
        } else if (userData.role === 'faculty') {
          navigate('/faculty')
        } else if (userData.role === 'management' || userData.role === 'dept_admin') {
          navigate('/management')
        } else {
          navigate('/dashboard')
        }
      } catch (error) {
        toast.error('Failed to fetch user data')
        console.error(error)
      }
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Login failed')
    },
  })

  const onSubmit = (data) => {
    loginMutation.mutate(data)
  }

  return (
    <Card>
      <CardHeader className="space-y-1 text-center">
        <div className="flex justify-center mb-4">
          <div className="h-12 w-12 rounded-lg bg-primary flex items-center justify-center">
            <Code2 className="h-7 w-7 text-primary-foreground" />
          </div>
        </div>
        <CardTitle className="text-2xl">Welcome back</CardTitle>
        <CardDescription>
          Enter your credentials to access your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Username</label>
            <Input
              {...register('username', { required: 'Username is required' })}
              placeholder="Enter your username"
              autoComplete="username"
            />
            {errors.username && (
              <p className="text-sm text-destructive">{errors.username.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <Input
              type="password"
              {...register('password', { required: 'Password is required' })}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          Accounts are created by your college administrator or faculty.
        </div>
      </CardContent>
    </Card>
  )
}