import { create } from 'zustand'

/**
 * Global chat state.
 *
 * conversations  — list of ChatConversationSummary (sidebar)
 * messages       — { [partnerId]: ChatMessageResponse[] }
 * onlineUsers    — Set of user IDs currently online
 * unreadTotal    — badge count for nav
 * activePartnerId — currently open conversation (null = none)
 * wsReady        — WebSocket connected
 */
export const useChatStore = create((set, get) => ({
  conversations: [],
  messages: {},          // partnerId → message[]
  onlineUsers: new Set(),
  unreadTotal: 0,
  activePartnerId: null,
  wsReady: false,

  setConversations: (list) => set({ conversations: list }),

  setMessages: (partnerId, msgs) =>
    set((s) => ({ messages: { ...s.messages, [partnerId]: msgs } })),

  appendMessage: (partnerId, msg) =>
    set((s) => {
      const existing = s.messages[partnerId] || []
      // Deduplicate by id
      if (existing.some((m) => m.id === msg.id)) return s
      return { messages: { ...s.messages, [partnerId]: [...existing, msg] } }
    }),

  prependMessages: (partnerId, older) =>
    set((s) => {
      const existing = s.messages[partnerId] || []
      const ids = new Set(existing.map((m) => m.id))
      const fresh = older.filter((m) => !ids.has(m.id))
      return { messages: { ...s.messages, [partnerId]: [...fresh, ...existing] } }
    }),

  markConversationRead: (partnerId) =>
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.partner_id === partnerId ? { ...c, unread_count: 0 } : c
      ),
      messages: {
        ...s.messages,
        [partnerId]: (s.messages[partnerId] || []).map((m) =>
          m.recipient_id === s.currentUserId ? { ...m, is_read: true } : m
        ),
      },
    })),

  upsertConversation: (msg, currentUserId) =>
    set((s) => {
      const partnerId =
        msg.sender_id === currentUserId ? msg.recipient_id : msg.sender_id
      const existing = s.conversations.find((c) => c.partner_id === partnerId)
      const isIncoming = msg.sender_id !== currentUserId
      const updated = {
        partner_id: partnerId,
        partner_name: isIncoming ? msg.sender_name : existing?.partner_name,
        partner_username: isIncoming ? msg.sender_username : existing?.partner_username,
        partner_role: existing?.partner_role || '',
        last_message: msg.content,
        last_message_at: msg.created_at,
        unread_count: isIncoming
          ? (existing?.unread_count || 0) + 1
          : existing?.unread_count || 0,
      }
      const rest = s.conversations.filter((c) => c.partner_id !== partnerId)
      return { conversations: [updated, ...rest] }
    }),

  setOnline: (userId, online) =>
    set((s) => {
      const next = new Set(s.onlineUsers)
      online ? next.add(userId) : next.delete(userId)
      return { onlineUsers: next }
    }),

  setUnreadTotal: (n) => set({ unreadTotal: n }),
  incrementUnread: () => set((s) => ({ unreadTotal: s.unreadTotal + 1 })),
  decrementUnread: (by = 1) =>
    set((s) => ({ unreadTotal: Math.max(0, s.unreadTotal - by) })),

  setActivePartner: (id) => set({ activePartnerId: id }),
  setWsReady: (v) => set({ wsReady: v }),
}))
