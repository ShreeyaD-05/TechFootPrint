import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { authApi } from '../../services/authApi'
import toast from 'react-hot-toast'
import { Code2 } from 'lucide-react'

export default function Register() {
  const navigate = useNavigate()
  const { register, handleSubmit, watch, formState: { errors } } = useForm()

  const registerMutation = useMutation({
    mutationFn: (data) => authApi.register(data),
    onSuccess: () => {
      toast.success('Account created successfully! Please login.')
      navigate('/login')
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Registration failed')
    },
  })

  const onSubmit = (data) => {
    const { confirmPassword, ...registerData } = data
    registerMutation.mutate(registerData)
  }

  const password = watch('password')

  return (
    <Card>
      <CardHeader className="space-y-1 text-center">
        <div className="flex justify-center mb-4">
          <div className="h-12 w-12 rounded-lg bg-primary flex items-center justify-center">
            <Code2 className="h-7 w-7 text-primary-foreground" />
          </div>
        </div>
        <CardTitle className="text-2xl">Create an account</CardTitle>
        <CardDescription>
          Start tracking your coding journey today
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Email</label>
            <Input
              type="email"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address',
                },
              })}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Username</label>
            <Input
              {...register('username', {
                required: 'Username is required',
                minLength: {
                  value: 3,
                  message: 'Username must be at least 3 characters',
                },
              })}
              placeholder="johndoe"
              autoComplete="username"
            />
            {errors.username && (
              <p className="text-sm text-destructive">{errors.username.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Full Name (Optional)</label>
            <Input
              {...register('full_name')}
              placeholder="John Doe"
              autoComplete="name"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <Input
              type="password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters',
                },
              })}
              placeholder="Create a password"
              autoComplete="new-password"
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Confirm Password</label>
            <Input
              type="password"
              {...register('confirmPassword', {
                required: 'Please confirm your password',
                validate: (value) =>
                  value === password || 'Passwords do not match',
              })}
              placeholder="Confirm your password"
              autoComplete="new-password"
            />
            {errors.confirmPassword && (
              <p className="text-sm text-destructive">
                {errors.confirmPassword.message}
              </p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Already have an account? </span>
          <Link to="/login" className="text-primary hover:underline font-medium">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
