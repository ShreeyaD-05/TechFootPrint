import { Menu, Bell, Search, ChevronDown } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Navbar({ onMenuClick }) {
  const { user } = useAuthStore()
  const [showSearch, setShowSearch] = useState(false)

  return (
    <header className="sticky top-0 z-30 h-14 bg-card/80 backdrop-blur-sm border-b border-border flex items-center px-4 sm:px-6 gap-4">
      {/* Mobile menu */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Search */}
      <div className="flex-1 max-w-md hidden sm:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search problems, topics..."
            className="w-full pl-9 pr-4 py-1.5 text-sm bg-secondary rounded-lg border border-transparent focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/30 placeholder:text-muted-foreground"
          />
        </div>
      </div>

      <div className="flex-1 sm:flex-none" />

      {/* Right actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <button className="relative p-1.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-primary rounded-full" />
        </button>

        {/* User avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-xs">
            {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <span className="text-sm font-medium hidden sm:block">{user?.full_name || user?.username}</span>
        </div>
      </div>
    </header>
  )
}
