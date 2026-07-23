import { useEffect, useRef, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '../services/chatApi'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { useChatSocket } from '../hooks/useChatSocket'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import {
  MessageSquare, Send, Search, Circle, ChevronLeft,
  Trash2, Users, Wifi, WifiOff,
} from 'lucide-react'
import { cn } from '../utils/cn'
import { formatDistanceToNow, format, isToday, isYesterday } from 'date-fns'
import toast from 'react-hot-toast'

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatMsgTime(dateStr) {
  const d = new Date(dateStr)
  if (isToday(d)) return format(d, 'HH:mm')
  if (isYesterday(d)) return `Yesterday ${format(d, 'HH:mm')}`
  return format(d, 'dd MMM HH:mm')
}

function formatConvTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isToday(d)) return format(d, 'HH:mm')
  return format(d, 'dd MMM')
}

const roleColor = {
  student: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  faculty: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  dept_admin: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  management: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
  super_admin: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
}

// ── Avatar ────────────────────────────────────────────────────────────────────

function Avatar({ name, size = 'md', online }) {
  const initials = (name || '?')[0].toUpperCase()
  const sz = size === 'sm' ? 'h-8 w-8 text-xs' : 'h-10 w-10 text-sm'
  return (
    <div className="relative shrink-0">
      <div className={cn('rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold', sz)}>
        {initials}
      </div>
      {online !== undefined && (
        <span className={cn(
          'absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-background',
          online ? 'bg-green-500' : 'bg-muted-foreground/40'
        )} />
      )}
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function Chat() {
  const { user } = useAuthStore()
  const { send, } = useChatSocket()
  const qc = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()

  const {
    conversations, messages, onlineUsers, wsReady,
    setConversations, setMessages, appendMessage,
    upsertConversation, markConversationRead,
    setActivePartner, activePartnerId, decrementUnread,
  } = useChatStore()

  const [search, setSearch] = useState('')
  const [msgInput, setMsgInput] = useState('')
  const [showNewChat, setShowNewChat] = useState(false)
  const [partnerSearch, setPartnerSearch] = useState('')
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const messagesEndRef = useRef(null)
  const messagesTopRef = useRef(null)
  const inputRef = useRef(null)

  // Open conversation from URL param ?with=userId
  const urlPartnerId = searchParams.get('with') ? parseInt(searchParams.get('with')) : null

  // ── Load conversations list ───────────────────────────────────────────────
  const { isLoading: loadingConvs } = useQuery({
    queryKey: ['chat-conversations'],
    queryFn: chatApi.getConversations,
    onSuccess: (data) => setConversations(data),
    refetchInterval: 30000,
  })

  // ── Load allowed partners (for new chat) ─────────────────────────────────
  const { data: partners = [] } = useQuery({
    queryKey: ['chat-partners'],
    queryFn: chatApi.getPartners,
    enabled: showNewChat,
  })

  // ── Open conversation ─────────────────────────────────────────────────────
  const openConversation = useCallback(async (partnerId) => {
    setActivePartner(partnerId)
    setSearchParams({ with: partnerId })
    setShowNewChat(false)
    setHasMore(true)

    if (!messages[partnerId]) {
      const history = await chatApi.getHistory(partnerId)
      setMessages(partnerId, history)
    }

    // Mark as read
    const conv = conversations.find((c) => c.partner_id === partnerId)
    if (conv?.unread_count > 0) {
      chatApi.markRead(partnerId).catch(() => {})
      decrementUnread(conv.unread_count)
      markConversationRead(partnerId)
    }

    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    inputRef.current?.focus()
  }, [messages, conversations]) // eslint-disable-line

  // Open from URL on mount
  useEffect(() => {
    if (urlPartnerId && urlPartnerId !== activePartnerId) {
      openConversation(urlPartnerId)
    }
  }, [urlPartnerId]) // eslint-disable-line

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (activePartnerId) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages[activePartnerId]?.length]) // eslint-disable-line

  // ── Send message ──────────────────────────────────────────────────────────
  const sendMutation = useMutation({
    mutationFn: ({ recipientId, content }) => chatApi.sendMessage(recipientId, content),
    onSuccess: (msg) => {
      appendMessage(activePartnerId, msg)
      upsertConversation(msg, user.id)
    },
    onError: () => toast.error('Failed to send message'),
  })

  const handleSend = () => {
    const content = msgInput.trim()
    if (!content || !activePartnerId) return

    // Try WebSocket first, fall back to REST
    const sent = send({ type: 'message', recipient_id: activePartnerId, content })
    if (!sent) {
      sendMutation.mutate({ recipientId: activePartnerId, content })
    }
    setMsgInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ── Load older messages ───────────────────────────────────────────────────
  const loadMore = async () => {
    if (!activePartnerId || loadingMore || !hasMore) return
    const current = messages[activePartnerId] || []
    if (current.length === 0) return
    setLoadingMore(true)
    try {
      const older = await chatApi.getHistory(activePartnerId, { limit: 50, beforeId: current[0].id })
      if (older.length === 0) { setHasMore(false); return }
      useChatStore.getState().prependMessages(activePartnerId, older)
    } finally {
      setLoadingMore(false)
    }
  }

  // ── Delete message ────────────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: chatApi.deleteMessage,
    onSuccess: (_, msgId) => {
      if (!activePartnerId) return
      useChatStore.setState((s) => ({
        messages: {
          ...s.messages,
          [activePartnerId]: (s.messages[activePartnerId] || []).filter((m) => m.id !== msgId),
        },
      }))
    },
  })

  // ── Filtered conversations ────────────────────────────────────────────────
  const filteredConvs = conversations.filter((c) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      c.partner_name?.toLowerCase().includes(q) ||
      c.partner_username?.toLowerCase().includes(q)
    )
  })

  const filteredPartners = partners.filter((p) => {
    if (!partnerSearch) return true
    const q = partnerSearch.toLowerCase()
    return p.full_name?.toLowerCase().includes(q) || p.username?.toLowerCase().includes(q)
  })

  const activeMessages = messages[activePartnerId] || []
  const activeConv = conversations.find((c) => c.partner_id === activePartnerId)
  const activePartnerOnline = onlineUsers.has(activePartnerId)

  return (
    <div className="flex h-[calc(100vh-4rem)] -mx-4 sm:-mx-6 lg:-mx-8 -my-6 overflow-hidden">

      {/* ── Sidebar: conversation list ── */}
      <div className={cn(
        'w-full sm:w-80 border-r flex flex-col bg-card shrink-0',
        activePartnerId ? 'hidden sm:flex' : 'flex'
      )}>
        {/* Header */}
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              Messages
            </h2>
            <div className="flex items-center gap-2">
              {wsReady
                ? <Wifi className="h-4 w-4 text-green-500" title="Connected" />
                : <WifiOff className="h-4 w-4 text-muted-foreground" title="Reconnecting…" />
              }
              <Button size="sm" variant="outline" onClick={() => setShowNewChat(true)}>
                New
              </Button>
            </div>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9 h-8 text-sm"
              placeholder="Search conversations…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto">
          {loadingConvs && filteredConvs.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground text-sm">Loading…</div>
          ) : filteredConvs.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <MessageSquare className="h-10 w-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No conversations yet</p>
              <button
                onClick={() => setShowNewChat(true)}
                className="text-primary text-sm mt-2 hover:underline"
              >
                Start one
              </button>
            </div>
          ) : (
            filteredConvs.map((conv) => (
              <button
                key={conv.partner_id}
                onClick={() => openConversation(conv.partner_id)}
                className={cn(
                  'w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors text-left',
                  activePartnerId === conv.partner_id && 'bg-primary/5 border-r-2 border-primary'
                )}
              >
                <Avatar
                  name={conv.partner_name || conv.partner_username}
                  online={onlineUsers.has(conv.partner_id)}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className={cn('text-sm truncate', conv.unread_count > 0 ? 'font-semibold' : 'font-medium')}>
                      {conv.partner_name || conv.partner_username}
                    </p>
                    <span className="text-xs text-muted-foreground shrink-0 ml-1">
                      {formatConvTime(conv.last_message_at)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <p className={cn('text-xs truncate', conv.unread_count > 0 ? 'text-foreground' : 'text-muted-foreground')}>
                      {conv.last_message || 'No messages yet'}
                    </p>
                    {conv.unread_count > 0 && (
                      <span className="ml-1 shrink-0 h-5 min-w-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold flex items-center justify-center px-1">
                        {conv.unread_count > 99 ? '99+' : conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* ── Main: message thread ── */}
      <div className={cn(
        'flex-1 flex flex-col min-w-0',
        !activePartnerId ? 'hidden sm:flex' : 'flex'
      )}>
        {!activePartnerId ? (
          /* Empty state */
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-20" />
              <p className="font-medium">Select a conversation</p>
              <p className="text-sm mt-1">or start a new one</p>
            </div>
          </div>
        ) : (
          <>
            {/* Thread header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b bg-card shrink-0">
              <button
                onClick={() => { setActivePartner(null); setSearchParams({}) }}
                className="sm:hidden text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <Avatar
                name={activeConv?.partner_name || activeConv?.partner_username}
                online={activePartnerOnline}
              />
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">
                  {activeConv?.partner_name || activeConv?.partner_username}
                </p>
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <span className={cn(
                    'inline-block h-1.5 w-1.5 rounded-full',
                    activePartnerOnline ? 'bg-green-500' : 'bg-muted-foreground/40'
                  )} />
                  {activePartnerOnline ? 'Online' : 'Offline'}
                  {activeConv?.partner_role && (
                    <span className={cn('ml-2 px-1.5 py-0.5 rounded-full text-[10px] font-medium', roleColor[activeConv.partner_role])}>
                      {activeConv.partner_role.replace('_', ' ')}
                    </span>
                  )}
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
              {/* Load more */}
              {hasMore && activeMessages.length >= 50 && (
                <div className="text-center mb-2">
                  <button
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="text-xs text-primary hover:underline disabled:opacity-50"
                  >
                    {loadingMore ? 'Loading…' : 'Load older messages'}
                  </button>
                </div>
              )}

              {activeMessages.length === 0 ? (
                <div className="flex-1 flex items-center justify-center py-16 text-muted-foreground text-sm">
                  No messages yet. Say hello!
                </div>
              ) : (
                activeMessages.map((msg, idx) => {
                  const isMine = msg.sender_id === user.id
                  const prev = activeMessages[idx - 1]
                  const showAvatar = !isMine && (!prev || prev.sender_id !== msg.sender_id)
                  const showTime =
                    !prev ||
                    new Date(msg.created_at) - new Date(prev.created_at) > 5 * 60 * 1000

                  return (
                    <div key={msg.id}>
                      {showTime && (
                        <div className="text-center my-3">
                          <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                            {formatMsgTime(msg.created_at)}
                          </span>
                        </div>
                      )}
                      <div className={cn('flex items-end gap-2 group', isMine ? 'justify-end' : 'justify-start')}>
                        {!isMine && (
                          <div className="w-7 shrink-0">
                            {showAvatar && (
                              <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-xs">
                                {(msg.sender_name || msg.sender_username || '?')[0].toUpperCase()}
                              </div>
                            )}
                          </div>
                        )}
                        <div className={cn('max-w-[70%] relative', isMine ? 'items-end' : 'items-start')}>
                          <div className={cn(
                            'px-3 py-2 rounded-2xl text-sm leading-relaxed break-words',
                            isMine
                              ? 'bg-primary text-primary-foreground rounded-br-sm'
                              : 'bg-muted rounded-bl-sm'
                          )}>
                            {msg.content}
                          </div>
                          {/* Read receipt */}
                          {isMine && (
                            <p className="text-[10px] text-muted-foreground mt-0.5 text-right">
                              {msg.is_read ? '✓✓' : '✓'}
                            </p>
                          )}
                          {/* Delete button */}
                          {isMine && (
                            <button
                              onClick={() => deleteMutation.mutate(msg.id)}
                              className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-background border rounded-full p-0.5 text-muted-foreground hover:text-red-500"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t bg-card shrink-0">
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={msgInput}
                  onChange={(e) => {
                    setMsgInput(e.target.value)
                    // Auto-grow
                    e.target.style.height = 'auto'
                    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message… (Enter to send)"
                  className="flex-1 resize-none rounded-xl border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 min-h-[40px] max-h-[120px] overflow-y-auto"
                />
                <Button
                  size="icon"
                  onClick={handleSend}
                  disabled={!msgInput.trim() || sendMutation.isPending}
                  className="h-10 w-10 rounded-xl shrink-0"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              {!wsReady && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-1 flex items-center gap-1">
                  <WifiOff className="h-3 w-3" /> Reconnecting… messages will still be delivered
                </p>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── New Chat Modal ── */}
      {showNewChat && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-xl shadow-xl w-full max-w-sm">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold flex items-center gap-2">
                <Users className="h-4 w-4" />
                New Conversation
              </h3>
              <button onClick={() => setShowNewChat(false)} className="text-muted-foreground hover:text-foreground">
                ✕
              </button>
            </div>
            <div className="p-3 border-b">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9 h-8 text-sm"
                  placeholder="Search people…"
                  value={partnerSearch}
                  onChange={(e) => setPartnerSearch(e.target.value)}
                  autoFocus
                />
              </div>
            </div>
            <div className="max-h-72 overflow-y-auto">
              {filteredPartners.length === 0 ? (
                <p className="p-4 text-center text-sm text-muted-foreground">No contacts found</p>
              ) : (
                filteredPartners.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => openConversation(p.id)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors text-left"
                  >
                    <Avatar name={p.full_name || p.username} size="sm" online={onlineUsers.has(p.id)} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{p.full_name || p.username}</p>
                      <p className="text-xs text-muted-foreground">@{p.username}</p>
                    </div>
                    <span className={cn('text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0', roleColor[p.role])}>
                      {p.role.replace('_', ' ')}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
