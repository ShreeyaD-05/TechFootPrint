# Frontend Setup Guide

Complete guide to set up and run the DevAnalytics frontend.

## Quick Start

```bash
cd frontend-new
npm install
cp .env.example .env
npm run dev
```

Visit `http://localhost:3000`

## Detailed Setup

### 1. Install Dependencies

```bash
npm install
```

This installs:
- React 18 + React DOM
- Vite (build tool)
- React Router v6
- Zustand (state management)
- TanStack Query (server state)
- React Hook Form
- Recharts (charts)
- TailwindCSS
- Lucide React (icons)
- Axios (HTTP client)
- date-fns (date utilities)
- react-hot-toast (notifications)

### 2. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will start on `http://localhost:3000` with:
- Hot Module Replacement (HMR)
- Fast refresh
- Instant updates

### 4. Build for Production

```bash
npm run build
```

This creates an optimized build in `dist/` folder.

Preview the build:

```bash
npm run preview
```

## Project Configuration

### Vite Config (`vite.config.js`)

```javascript
{
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
}
```

### TailwindCSS Config (`tailwind.config.js`)

- Dark mode: class-based
- Custom color system with CSS variables
- Responsive breakpoints
- Custom animations

### PostCSS Config (`postcss.config.js`)

- TailwindCSS processing
- Autoprefixer for browser compatibility

## Development Workflow

### 1. Create New Component

```bash
# Create component file
touch src/components/MyComponent.jsx
```

```jsx
// src/components/MyComponent.jsx
import { cn } from '@/utils/cn'

export function MyComponent({ className, ...props }) {
  return (
    <div className={cn('base-classes', className)} {...props}>
      Content
    </div>
  )
}
```

### 2. Create New Page

```bash
touch src/pages/MyPage.jsx
```

```jsx
// src/pages/MyPage.jsx
export default function MyPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">My Page</h1>
      {/* Content */}
    </div>
  )
}
```

Add route in `App.jsx`:

```jsx
<Route path="/my-page" element={<MyPage />} />
```

### 3. Create API Service

```bash
touch src/services/myApi.js
```

```javascript
import apiClient from './apiClient'

export const myApi = {
  getData: async () => {
    const response = await apiClient.get('/my-endpoint')
    return response.data
  },
}
```

### 4. Use TanStack Query

```jsx
import { useQuery } from '@tanstack/react-query'
import { myApi } from '@/services/myApi'

function MyComponent() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['my-data'],
    queryFn: myApi.getData,
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return <div>{data}</div>
}
```

### 5. Create Zustand Store

```bash
touch src/stores/myStore.js
```

```javascript
import { create } from 'zustand'

export const useMyStore = create((set) => ({
  value: 0,
  increment: () => set((state) => ({ value: state.value + 1 })),
  decrement: () => set((state) => ({ value: state.value - 1 })),
}))
```

Use in component:

```jsx
import { useMyStore } from '@/stores/myStore'

function MyComponent() {
  const { value, increment } = useMyStore()
  
  return (
    <div>
      <p>{value}</p>
      <button onClick={increment}>Increment</button>
    </div>
  )
}
```

## Styling Guide

### Using TailwindCSS

```jsx
// Spacing
<div className="p-4 m-2 space-y-4">

// Layout
<div className="flex items-center justify-between">
<div className="grid grid-cols-3 gap-4">

// Responsive
<div className="w-full md:w-1/2 lg:w-1/3">

// Colors (use semantic colors)
<div className="bg-card text-card-foreground">
<div className="bg-primary text-primary-foreground">

// Dark mode
<div className="bg-white dark:bg-gray-900">
```

### Using Shadcn UI Components

```jsx
import { Button } from '@/components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

<Button variant="default">Click me</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content
  </CardContent>
</Card>
```

## Form Handling

### React Hook Form

```jsx
import { useForm } from 'react-hook-form'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

function MyForm() {
  const { register, handleSubmit, formState: { errors } } = useForm()

  const onSubmit = (data) => {
    console.log(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <label>Email</label>
        <Input
          type="email"
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email',
            },
          })}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>
      
      <Button type="submit">Submit</Button>
    </form>
  )
}
```

## Charts with Recharts

```jsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const data = [
  { name: 'Jan', value: 400 },
  { name: 'Feb', value: 300 },
]

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="value" fill="#3b82f6" />
  </BarChart>
</ResponsiveContainer>
```

## Notifications

```jsx
import toast from 'react-hot-toast'

// Success
toast.success('Operation successful!')

// Error
toast.error('Something went wrong')

// Loading
const toastId = toast.loading('Processing...')
// Later
toast.success('Done!', { id: toastId })

// Custom
toast.custom((t) => (
  <div className="bg-card p-4 rounded-lg shadow-lg">
    Custom notification
  </div>
))
```

## Dark Mode

Toggle theme:

```jsx
import { useThemeStore } from '@/stores/themeStore'

function ThemeToggle() {
  const { theme, toggleTheme } = useThemeStore()
  
  return (
    <button onClick={toggleTheme}>
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  )
}
```

## Routing

### Protected Routes

```jsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" />
}

// Usage
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

### Navigation

```jsx
import { Link, useNavigate } from 'react-router-dom'

// Link component
<Link to="/dashboard">Dashboard</Link>

// Programmatic navigation
const navigate = useNavigate()
navigate('/dashboard')
```

## Performance Optimization

### Code Splitting

```jsx
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./pages/Dashboard'))

<Suspense fallback={<div>Loading...</div>}>
  <Dashboard />
</Suspense>
```

### Memoization

```jsx
import { useMemo, useCallback } from 'react'

// Expensive calculation
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data)
}, [data])

// Callback
const handleClick = useCallback(() => {
  doSomething(value)
}, [value])
```

## Debugging

### React DevTools

Install React DevTools browser extension for:
- Component tree inspection
- Props and state viewing
- Performance profiling

### TanStack Query DevTools

Add to `App.jsx`:

```jsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

## Common Issues

### Port Already in Use

```bash
# Kill process on port 3000
npx kill-port 3000

# Or use different port
npm run dev -- --port 3001
```

### Module Not Found

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

```bash
# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Deployment

### Build

```bash
npm run build
```

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

### Environment Variables

Set in deployment platform:
- `VITE_API_URL` - Backend API URL

## Resources

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [TailwindCSS Docs](https://tailwindcss.com)
- [TanStack Query Docs](https://tanstack.com/query)
- [Zustand Docs](https://docs.pmnd.rs/zustand)
- [React Hook Form Docs](https://react-hook-form.com)
- [Recharts Docs](https://recharts.org)
