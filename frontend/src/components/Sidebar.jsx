import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { useChatStore } from '../stores/chatStore'
import { cn } from '../utils/cn'
import {
  LayoutDashboard, Code2, BarChart3, Link as LinkIcon, User, Settings,
  X, MessageSquare, FileText, Users, Building2, ShieldCheck, Lightbulb,
  Trophy, GraduationCap, TrendingUp, LogOut, Sun, Moon,
  BookOpen, Target, Activity, MessagesSquare,
} from 'lucide-react'

const studentNav = [
  { group: 'Overview', items: [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Suggestions', href: '/suggestions', icon: Lightbulb, badge: 'AI' },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ]},
  { group: 'Practice', items: [
    { name: 'Problems', href: '/problems', icon: Code2 },
    { name: 'Submissions', href: '/submissions', icon: FileText },
    { name: 'Discussions', href: '/discussions', icon: MessageSquare },
  ]},
  { group: 'Profile', items: [
    { name: 'Platforms', href: '/platforms', icon: LinkIcon },
    { name: 'Portfolio', href: '/portfolio', icon: User },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]},
  { group: 'Communication', items: [
    { name: 'Messages', href: '/chat', icon: MessagesSquare, unreadKey: true },
  ]},
]

const facultyNav = [
  { group: 'Overview', items: [
    { name: 'Faculty Dashboard', href: '/faculty', icon: LayoutDashboard },
    { name: 'Manage Students', href: '/faculty/students', icon: Users },
    { name: 'My College', href: '/my-college', icon: Building2 },
  ]},
  { group: 'My Profile', items: [
    { name: 'Dashboard', href: '/dashboard', icon: Activity },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ]},
  { group: 'Communication', items: [
    { name: 'Messages', href: '/chat', icon: MessagesSquare, unreadKey: true },
  ]},
]

const managementNav = [
  { group: 'BI Dashboard', items: [
    { name: 'College Overview', href: '/management', icon: Building2 },
    { name: 'My College', href: '/my-college', icon: Building2 },
    { name: 'Manage Students', href: '/faculty/students', icon: Users },
  ]},
  { group: 'Communication', items: [
    { name: 'Messages', href: '/chat', icon: MessagesSquare, unreadKey: true },
  ]},
  { group: 'System', items: [
    { name: 'Settings', href: '/settings', icon: Settings },
  ]},
]

const adminNav = [
  { group: 'System', items: [
    { name: 'Admin Dashboard', href: '/admin', icon: ShieldCheck },
    { name: 'Colleges', href: '/admin/colleges', icon: Building2 },
    { name: 'Faculty', href: '/admin/faculty', icon: GraduationCap },
    { name: 'Users', href: '/admin/users', icon: Users },
  ]},
  { group: 'Student Management', items: [
    { name: 'Manage Students', href: '/faculty/students', icon: Users },
    { name: 'My College', href: '/my-college', icon: Building2 },
  ]},
  { group: 'Communication', items: [
    { name: 'Messages', href: '/chat', icon: MessagesSquare, unreadKey: true },
  ]},
  { group: 'Settings', items: [
    { name: 'Settings', href: '/settings', icon: Settings },
  ]},
]

function getNavByRole(role) {
  if (role === 'faculty') return facultyNav
  if (role === 'dept_admin' || role === 'management') return managementNav
  if (role === 'super_admin') return adminNav
  return studentNav
}

export default function Sidebar({ open, setOpen }) {
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const { unreadTotal } = useChatStore()
  const navigate = useNavigate()
  const nav = getNavByRole(user?.role)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const roleLabel = {
    student: 'Student',
    faculty: 'Faculty',
    dept_admin: 'Dept. Admin',
    management: 'Management',
    super_admin: 'Super Admin',
  }[user?.role] || 'User'

  const roleColor = {
    student: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    faculty: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    dept_admin: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    management: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    super_admin: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  }[user?.role] || 'bg-secondary text-secondary-foreground'

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setOpen(false)} />
      )}

      <aside className={cn(
        'fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border flex flex-col',
        'transform transition-transform duration-200 ease-in-out lg:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-5 border-b border-border shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shadow-sm">
              <Code2 className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold leading-none">CodeTrack</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">College Analytics</p>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="lg:hidden text-muted-foreground hover:text-foreground p-1 rounded">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* User info */}
        <div className="px-4 py-3 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm shrink-0">
              {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">{user?.full_name || user?.username}</p>
              <span className={cn('text-[10px] font-medium px-1.5 py-0.5 rounded-full', roleColor)}>
                {roleLabel}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
          {nav.map((group) => (
            <div key={group.group}>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground px-3 mb-1.5">
                {group.group}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <NavLink
                    key={item.name}
                    to={item.href}
                    onClick={() => setOpen(false)}
                    className={({ isActive }) => cn(
                      'nav-item',
                      isActive && 'active'
                    )}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span className="flex-1">{item.name}</span>
                    {item.badge && (
                      <span className="text-[9px] font-bold bg-primary text-white px-1.5 py-0.5 rounded-full">
                        {item.badge}
                      </span>
                    )}
                    {item.unreadKey && unreadTotal > 0 && (
                      <span className="text-[9px] font-bold bg-red-500 text-white px-1.5 py-0.5 rounded-full min-w-[18px] text-center">
                        {unreadTotal > 99 ? '99+' : unreadTotal}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer actions */}
        <div className="border-t border-border px-3 py-3 space-y-0.5 shrink-0">
          <button
            onClick={toggleTheme}
            className="nav-item w-full"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
          <button onClick={handleLogout} className="nav-item w-full text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  )
}
