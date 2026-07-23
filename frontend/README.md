# DevAnalytics Frontend

Modern developer analytics dashboard built with React + Vite, TailwindCSS, and Shadcn UI.

## Tech Stack

- **Framework**: React 18 + Vite
- **Language**: JavaScript (JSX)
- **Styling**: TailwindCSS
- **UI Components**: Shadcn UI (custom implementation)
- **State Management**: Zustand
- **Server State**: TanStack Query
- **Forms**: React Hook Form
- **Charts**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router v6

## Features

- ✅ Clean, minimal developer-focused UI
- ✅ Dark/Light mode support
- ✅ Responsive design
- ✅ Authentication (Login/Register)
- ✅ Dashboard with analytics
- ✅ Platform connections management
- ✅ Interactive charts and visualizations
- ✅ Optimistic updates
- ✅ Loading states and skeletons
- ✅ Toast notifications

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── ui/             # Shadcn UI components
│   ├── StatCard.jsx
│   ├── PlatformCard.jsx
│   ├── Sidebar.jsx
│   └── Navbar.jsx
├── pages/              # Page components
│   ├── Landing.jsx
│   ├── Auth/
│   │   ├── Login.jsx
│   │   └── Register.jsx
│   ├── Dashboard.jsx
│   ├── Platforms.jsx
│   ├── Problems.jsx
│   ├── Analytics.jsx
│   ├── Portfolio.jsx
│   └── Settings.jsx
├── layouts/            # Layout components
│   ├── DashboardLayout.jsx
│   └── AuthLayout.jsx
├── stores/             # Zustand stores
│   ├── authStore.js
│   ├── themeStore.js
│   ├── platformStore.js
│   └── analyticsStore.js
├── services/           # API services
│   ├── apiClient.js
│   ├── authApi.js
│   ├── platformApi.js
│   └── analyticsApi.js
├── utils/              # Utility functions
│   └── cn.js
├── App.jsx
├── main.jsx
└── index.css
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Design System

### Colors

The app uses a semantic color system with CSS variables:

- `primary` - Main brand color
- `secondary` - Secondary actions
- `accent` - Highlights
- `muted` - Subtle backgrounds
- `destructive` - Errors and warnings

### Components

All UI components follow Shadcn UI patterns:

- **Button** - Multiple variants (default, outline, ghost, etc.)
- **Card** - Container with header, content, footer
- **Input** - Form inputs with validation
- **Badge** - Status indicators

### Typography

- Headings: Bold, tracking-tight
- Body: Regular weight
- Muted text: Lower opacity for secondary info

## State Management

### Zustand Stores

- **authStore** - User authentication state
- **themeStore** - Dark/light mode
- **platformStore** - Connected platforms
- **analyticsStore** - Analytics data

### TanStack Query

Used for all API calls with:
- Automatic caching
- Background refetching
- Optimistic updates
- Loading/error states

## API Integration

All API calls go through `apiClient.js` which:
- Adds authentication headers
- Handles token refresh
- Manages error responses
- Redirects on 401

## Routing

Protected routes require authentication:
- `/dashboard` - Main dashboard
- `/platforms` - Platform management
- `/problems` - Problem tracker
- `/analytics` - Analytics
- `/portfolio` - User portfolio
- `/settings` - Settings

Public routes:
- `/` - Landing page
- `/login` - Login
- `/register` - Register
- `/p/:username` - Public portfolio

## Styling Guidelines

### TailwindCSS Usage

```jsx
// Use semantic classes
<div className="bg-card text-card-foreground">

// Responsive design
<div className="grid md:grid-cols-2 lg:grid-cols-3">

// Dark mode
<div className="bg-white dark:bg-gray-900">
```

### Component Patterns

```jsx
// Always use cn() for className merging
import { cn } from '@/utils/cn'

<div className={cn('base-classes', conditionalClass && 'extra-class', className)} />
```

## Form Handling

Using React Hook Form:

```jsx
const { register, handleSubmit, formState: { errors } } = useForm()

<Input
  {...register('field', { required: 'Field is required' })}
/>
{errors.field && <p className="text-destructive">{errors.field.message}</p>}
```

## Charts

Using Recharts for data visualization:

```jsx
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

## Best Practices

1. **Component Organization**
   - Keep components small and focused
   - Extract reusable logic to custom hooks
   - Use composition over prop drilling

2. **State Management**
   - Use Zustand for global state
   - Use TanStack Query for server state
   - Keep local state in components when possible

3. **Performance**
   - Lazy load routes
   - Memoize expensive calculations
   - Use React.memo for pure components

4. **Accessibility**
   - Use semantic HTML
   - Add ARIA labels
   - Ensure keyboard navigation

## Contributing

1. Follow the existing code style
2. Use meaningful component and variable names
3. Add comments for complex logic
4. Test responsive design
5. Ensure dark mode compatibility

## License

MIT
