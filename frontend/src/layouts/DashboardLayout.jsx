import { Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import Navbar from '../components/Navbar'
import ChatWidget from '../components/ChatWidget'
import { useChatSocket } from '../hooks/useChatSocket'
import { useChatStore } from '../stores/chatStore'
import { chatApi } from '../services/chatApi'
import { useAuthStore } from '../stores/authStore'

function ChatBootstrap() {
  // Initialize WebSocket and load unread count once on mount
  useChatSocket()
  const { setUnreadTotal, setConversations } = useChatStore()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated) return
    chatApi.getUnreadCount().then(d => setUnreadTotal(d.unread)).catch(() => {})
    chatApi.getConversations().then(setConversations).catch(() => {})
  }, [isAuthenticated]) // eslint-disable-line

  return null
}

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Bootstrap chat (WebSocket + unread count) */}
      <ChatBootstrap />

      {/* Sidebar */}
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Navbar */}
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        {/* Page Content */}
        <main className="py-6 px-4 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>

      {/* Floating chat widget */}
      <ChatWidget />
    </div>
  )
}
