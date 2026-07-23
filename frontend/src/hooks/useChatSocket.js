/**
 * useChatSocket — manages the WebSocket lifecycle.
 *
 * Call once at the app root (inside DashboardLayout) so the socket
 * stays alive while the user is logged in.
 */
import { useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'

const WS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  .replace(/^http/, 'ws')

const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT = 10

export function useChatSocket() {
  const { token, isAuthenticated } = useAuthStore()
  const {
    appendMessage,
    upsertConversation,
    setOnline,
    markConversationRead,
    setWsReady,
    incrementUnread,
    activePartnerId,
  } = useChatStore()

  const wsRef = useRef(null)
  const reconnectCount = useRef(0)
  const reconnectTimer = useRef(null)
  const mountedRef = useRef(true)

  // Expose send so components can call it
  const send = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
      return true
    }
    return false
  }, [])

  const connect = useCallback(() => {
    if (!token || !isAuthenticated) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const url = `${WS_BASE}/chat/ws?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      reconnectCount.current = 0
      setWsReady(true)
      // Keepalive ping every 25 s
      ws._pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'ping' }))
      }, 25000)
    }

    ws.onmessage = (event) => {
      let data
      try { data = JSON.parse(event.data) } catch { return }

      const currentUserId = useAuthStore.getState().user?.id

      if (data.type === 'new_message') {
        const msg = data.message
        const partnerId =
          msg.sender_id === currentUserId ? msg.recipient_id : msg.sender_id

        appendMessage(partnerId, msg)
        upsertConversation(msg, currentUserId)

        // Only increment badge if not currently viewing this conversation
        if (msg.sender_id !== currentUserId && activePartnerId !== partnerId) {
          incrementUnread()
        }
      } else if (data.type === 'read_receipt') {
        markConversationRead(data.sender_id)
      } else if (data.type === 'presence') {
        setOnline(data.user_id, data.online)
      }
      // pong / error — ignore
    }

    ws.onerror = () => { /* handled by onclose */ }

    ws.onclose = () => {
      clearInterval(ws._pingInterval)
      setWsReady(false)
      if (!mountedRef.current) return
      if (reconnectCount.current < MAX_RECONNECT) {
        reconnectCount.current++
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }
  }, [token, isAuthenticated]) // eslint-disable-line

  useEffect(() => {
    mountedRef.current = true
    if (isAuthenticated && token) connect()
    return () => {
      mountedRef.current = false
      clearTimeout(reconnectTimer.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect on intentional close
        wsRef.current.close()
      }
      setWsReady(false)
    }
  }, [isAuthenticated, token]) // eslint-disable-line

  return { send }
}
