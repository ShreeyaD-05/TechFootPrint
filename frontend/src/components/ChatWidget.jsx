/**
 * ChatWidget — floating mini-chat bubble accessible from any page.
 * Shows unread badge, expands to a compact conversation list + thread.
 */
import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { chatApi } from '../services/chatApi'
import { useChatStore } from '../stores/chatStore'
import { useAuthStore } from '../stores/authStore'
import { useChatSocket } from '../hooks/useChatSocket'
import { MessageSquare, X, Send, ChevronLeft, Maximize2 } from 'lucide-react'
import { cn } from '../utils/cn'
import { format, isToday } from 'date-fns'

function fmtTime(d) {
  const date = new Date(d)
  return isToday(date) ? format(date, 'HH:mm') : format(date, 'dd/MM HH:mm')
}

export default function ChatWidget() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { send } = useChatSocket()

  const {
    conversations, messages, onlineUsers, unreadTotal,
    setMessages, appendMessage, upsertConversation,
    markConversationRead, decrementUnread,
    activePartnerId, setActivePartner,
  } = useChatStore()

  const [open, setOpen] = useState(false)
  const [view, setView] = useState('list') // list | thread
  const [input, setInput] = useState('')
  const endRef = useRef(null)
  const inputRef = useRef(null)

  // Scroll to bottom when thread opens or new message arrives
  useEffect(() => {
    if (view === 'thread' && open) {
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [view, open, messages[activePartnerId]?.length]) // eslint-disable-line

  const openThread = useCallback(async (partnerId) => {
    setActivePartner(partnerId)
    setView('thread')
    if (!messages[partnerId]) {
      const history = await chatApi.getHistory(partnerId, { limit: 30 })
      setMessages(partnerId, history)
    }
    const conv = conversations.find((c) => c.partner_id === partnerId)
    if (conv?.unread_count > 0) {
      chatApi.markRead(partnerId).catch(() => {})
      decrementUnread(conv.unread_count)
      markConversationRead(partnerId)
    }
    setTimeout(() => {
      endRef.current?.scrollIntoView({ behavior: 'smooth' })
      inputRef.current?.focus()
    }, 50)
  }, [messages, conversations]) // eslint-disable-line

  const sendMutation = useMutation({
    mutationFn: ({ recipientId, content }) => chatApi.sendMessage(recipientId, content),
    onSuccess: (msg) => {
      appendMessage(activePartnerId, msg)
      upsertConversation(msg, user.id)
    },
  })

  const handleSend = () => {
    const content = input.trim()
    if (!content || !activePartnerId) return
    const sent = send({ type: 'message', recipient_id: activePartnerId, content })
    if (!sent) sendMutation.mutate({ recipientId: activePartnerId, content })
    setInput('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const activeMessages = messages[activePartnerId] || []
  const activeConv = conversations.find((c) => c.partner_id === activePartnerId)

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2">
      {/* Expanded panel */}
      {open && (
        <div className="w-80 bg-card border rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          style={{ height: '420px' }}>

          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-primary text-primary-foreground shrink-0">
            <div className="flex items-center gap-2">
              {view === 'thread' && (
                <button onClick={() => setView('list')} className="hover:opacity-70">
                  <ChevronLeft className="h-4 w-4" />
                </button>
              )}
              <MessageSquare className="h-4 w-4" />
              <span className="font-semibold text-sm">
                {view === 'thread'
                  ? (activeConv?.partner_name || activeConv?.partner_username || 'Chat')
                  : 'Messages'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  navigate(view === 'thread' && activePartnerId
                    ? `/chat?with=${activePartnerId}`
                    : '/chat')
                  setOpen(false)
                }}
                className="hover:opacity-70"
                title="Open full chat"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => setOpen(false)} className="hover:opacity-70">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* List view */}
          {view === 'list' && (
            <div className="flex-1 overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="p-6 text-center text-muted-foreground text-sm">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p>No conversations yet</p>
                  <button
                    onClick={() => navigate('/chat')}
                    className="text-primary text-xs mt-1 hover:underline"
                  >
                    Start chatting
                  </button>
                </div>
              ) : (
                conversations.slice(0, 20).map((conv) => (
                  <button
                    key={conv.partner_id}
                    onClick={() => openThread(conv.partner_id)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors text-left border-b last:border-0"
                  >
                    <div className="relative shrink-0">
                      <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold text-sm">
                        {(conv.partner_name || conv.partner_username || '?')[0].toUpperCase()}
                      </div>
                      {onlineUsers.has(conv.partner_id) && (
                        <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-green-500 border-2 border-background" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className={cn('text-sm truncate', conv.unread_count > 0 ? 'font-semibold' : 'font-medium')}>
                          {conv.partner_name || conv.partner_username}
                        </p>
                        <span className="text-[10px] text-muted-foreground shrink-0 ml-1">
                          {conv.last_message_at ? fmtTime(conv.last_message_at) : ''}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-muted-foreground truncate">{conv.last_message || ''}</p>
                        {conv.unread_count > 0 && (
                          <span className="ml-1 shrink-0 h-4 min-w-4 rounded-full bg-primary text-primary-foreground text-[9px] font-bold flex items-center justify-center px-1">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}

          {/* Thread view */}
          {view === 'thread' && (
            <>
              <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
                {activeMessages.map((msg, idx) => {
                  const isMine = msg.sender_id === user.id
                  const prev = activeMessages[idx - 1]
                  const showTime = !prev ||
                    new Date(msg.created_at) - new Date(prev.created_at) > 5 * 60 * 1000
                  return (
                    <div key={msg.id}>
                      {showTime && (
                        <div className="text-center my-2">
                          <span className="text-[9px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                            {fmtTime(msg.created_at)}
                          </span>
                        </div>
                      )}
                      <div className={cn('flex', isMine ? 'justify-end' : 'justify-start')}>
                        <div className={cn(
                          'max-w-[80%] px-3 py-1.5 rounded-2xl text-sm break-words',
                          isMine
                            ? 'bg-primary text-primary-foreground rounded-br-sm'
                            : 'bg-muted rounded-bl-sm'
                        )}>
                          {msg.content}
                        </div>
                      </div>
                    </div>
                  )
                })}
                <div ref={endRef} />
              </div>
              <div className="px-3 py-2 border-t shrink-0 flex gap-2">
                <input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Message…"
                  className="flex-1 text-sm border rounded-xl px-3 py-1.5 bg-background focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="h-8 w-8 rounded-xl bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-40 hover:bg-primary/90 transition-colors shrink-0"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Bubble button */}
      <button
        onClick={() => { setOpen((o) => !o); if (!open) setView('list') }}
        className="h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-lg flex items-center justify-center hover:bg-primary/90 transition-all hover:scale-105 active:scale-95"
      >
        {open ? (
          <X className="h-6 w-6" />
        ) : (
          <div className="relative">
            <MessageSquare className="h-6 w-6" />
            {unreadTotal > 0 && (
              <span className="absolute -top-2 -right-2 h-5 min-w-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center px-1">
                {unreadTotal > 99 ? '99+' : unreadTotal}
              </span>
            )}
          </div>
        )}
      </button>
    </div>
  )
}
