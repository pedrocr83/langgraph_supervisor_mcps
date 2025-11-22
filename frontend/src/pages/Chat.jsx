import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../context/authStore'
import Sidebar from '../components/Sidebar'
import axios from 'axios'
import maleIcon from '../icons/male_small.png'
import robotHappyIcon from '../icons/robot_happy_small.png'
import robotConfusedIcon from '../icons/robot_confusion_small.png'
import robotSadIcon from '../icons/robot_sad_small.png'
import robotAngryIcon from '../icons/robot_angry_small.png'

const API_URL = ''

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(false)
  const [toolStatus, setToolStatus] = useState(null)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const parseMessage = (content) => {
    // Try standard format: <emotion>type</emotion>
    const emotionMatch = content.match(/<emotion>(.*?)<\/emotion>/)
    if (emotionMatch) {
      return {
        emotion: emotionMatch[1],
        cleanContent: content.replace(/<emotion>.*?<\/emotion>/, '')
      }
    }

    // Try fallback format: <type>...</type> or just <type>
    const fallbackMatch = content.match(/<(happy|confused|sad|angry)>/)
    if (fallbackMatch) {
      const emotion = fallbackMatch[1]
      let cleanContent = content.replace(new RegExp(`<${emotion}>`), '')
      cleanContent = cleanContent.replace(new RegExp(`<\/${emotion}>`), '')
      return { emotion, cleanContent }
    }

    return { emotion: 'happy', cleanContent: content }
  }

  const getRobotIcon = (emotion) => {
    switch (emotion) {
      case 'confused': return robotConfusedIcon
      case 'sad': return robotSadIcon
      case 'angry': return robotAngryIcon
      default: return robotHappyIcon
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Load conversations on mount
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/conversations`)
      setConversations(response.data)
      if (response.data.length > 0 && !conversationId) {
        const firstConv = response.data[0]
        setConversationId(firstConv.id)
        loadMessages(firstConv.id)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    }
  }

  const loadMessages = async (convId) => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/conversations/${convId}/messages`)
      const formattedMessages = response.data.map((msg) => ({
        role: msg.role,
        content: msg.content,
        toolName: msg.tool_name,
      }))
      setMessages(formattedMessages)
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }

  const handleNewChat = () => {
    setConversationId(null)
    setMessages([])
    // Close existing WebSocket if any
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  const handleSelectConversation = (convId) => {
    if (convId === conversationId) return
    setConversationId(convId)
    loadMessages(convId)
    // Close existing WebSocket and reconnect to new conversation
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }

  const handleDeleteConversation = async (convId) => {
    try {
      await axios.delete(`${API_URL}/api/chat/conversations/${convId}`)

      // Remove from conversations list
      const updatedConversations = conversations.filter(c => c.id !== convId)
      setConversations(updatedConversations)

      // If we deleted the active conversation, switch to another or create new
      if (convId === conversationId) {
        if (updatedConversations.length > 0) {
          handleSelectConversation(updatedConversations[0].id)
        } else {
          handleNewChat()
        }
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
      alert('Failed to delete conversation')
    }
  }

  const connectWebSocket = (convId) => {
    const token = localStorage.getItem('access_token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}`
    const ws = new WebSocket(`${wsUrl}/api/chat/ws/${convId}?token=${token}`)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'conversation_id') {
        setConversationId(data.conversation_id)
        // Reload conversations to include the new one
        loadConversations()
      } else if (data.type === 'content') {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.complete) {
            return [
              ...prev.slice(0, -1),
              {
                ...lastMsg,
                content: lastMsg.content + data.content,
              },
            ]
          } else {
            return [
              ...prev,
              {
                role: 'assistant',
                content: data.content,
                complete: false,
              },
            ]
          }
        })
      } else if (data.type === 'tool') {
        setToolStatus({ name: data.name, content: data.content })
      } else if (data.type === 'tool_call') {
        setToolStatus({ name: data.name, calling: true })
      } else if (data.type === 'done') {
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg) {
            return [
              ...prev.slice(0, -1),
              {
                ...lastMsg,
                complete: true,
              },
            ]
          }
          return prev
        })
        setToolStatus(null)
        setLoading(false)
        // Reload conversations to update timestamps
        loadConversations()
      } else if (data.type === 'error') {
        setToolStatus(null)
        setLoading(false)
        alert(`Error: ${data.message}`)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setLoading(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    wsRef.current = ws
    return ws
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to UI
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    // Use WebSocket if available, otherwise fallback to REST
    const convId = conversationId || 'new'

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWebSocket(convId)
      // Wait a bit for connection
      setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: 'message',
              message: userMessage,
            })
          )
        } else {
          // Fallback to REST API
          sendViaRest(userMessage, convId)
        }
      }, 500)
    } else {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          message: userMessage,
        })
      )
    }
  }

  const sendViaRest = async (message, convId) => {
    try {
      const response = await axios.post(`${API_URL}/api/chat/`, {
        message,
        conversation_id: convId === 'new' ? null : convId,
      })

      setConversationId(response.data.conversation_id)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.data.message, complete: true },
      ])
      setLoading(false)
      loadConversations()
    } catch (error) {
      console.error('Error sending message:', error)
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        onLogout={logout}
      />

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <header style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--border-color)',
          backgroundColor: 'var(--bg-secondary)',
        }}>
          <h1 style={{
            fontSize: '20px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            margin: 0,
          }}>
            misteriosAI
          </h1>
        </header>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          backgroundColor: 'var(--bg-chat)',
        }}>
          <div style={{ maxWidth: '100%', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px', padding: '0 40px' }}>
            {messages.length === 0 && (
              <div style={{
                textAlign: 'center',
                color: 'var(--text-muted)',
                marginTop: '80px',
                fontSize: '16px',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>💬</div>
                <p>Start a conversation with misteriosAI</p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>Ask me anything!</p>
              </div>
            )}
            {messages.map((msg, idx) => {
              const { emotion, cleanContent } = msg.role === 'assistant'
                ? parseMessage(msg.content)
                : { emotion: 'happy', cleanContent: msg.content }

              return (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    gap: '12px',
                    padding: '8px 0',
                    flexDirection: msg.role === 'user' ? 'row' : 'row-reverse',
                    justifyContent: 'flex-start',
                    alignItems: 'flex-end',
                  }}
                >
                  <div style={{
                    width: '96px',
                    height: '96px',
                    borderRadius: '12px',
                    backgroundColor: 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginBottom: '4px', // Align with bottom of bubble
                  }}>
                    <img
                      src={msg.role === 'user' ? maleIcon : getRobotIcon(emotion)}
                      alt={msg.role}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />
                  </div>
                  <div style={{
                    flex: 1,
                    minWidth: 0,
                    maxWidth: '70%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: msg.role === 'user' ? 'flex-start' : 'flex-end',
                  }}>
                    {msg.toolName && (
                      <div style={{
                        fontSize: '12px',
                        color: 'var(--text-muted)',
                        marginBottom: '4px',
                        alignSelf: msg.role === 'user' ? 'flex-start' : 'flex-end',
                      }}>
                        Tool: {msg.toolName}
                      </div>
                    )}
                    <div style={{
                      padding: '20px 24px',
                      borderRadius: '16px',
                      borderBottomLeftRadius: msg.role === 'user' ? '4px' : '16px',
                      borderBottomRightRadius: msg.role === 'assistant' ? '4px' : '16px',
                      backgroundColor: msg.role === 'user' ? 'var(--bg-user-msg)' : 'var(--bg-assistant-msg)',
                      color: 'var(--text-primary)',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      lineHeight: '1.6',
                      fontSize: '16px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    }}>
                      {cleanContent}
                    </div>
                  </div>
                </div>
              )
            })}
            {toolStatus && (
              <div style={{
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: 'var(--bg-tertiary)',
                border: '1px solid var(--border-color)',
                fontSize: '14px',
                color: 'var(--text-secondary)',
              }}>
                {toolStatus.calling ? (
                  <>🔧 Calling tool: {toolStatus.name}...</>
                ) : (
                  <>
                    <div style={{ fontWeight: '500', marginBottom: '4px' }}>🔧 Tool: {toolStatus.name}</div>
                    <pre style={{
                      fontSize: '12px',
                      color: 'var(--text-muted)',
                      overflow: 'auto',
                      maxHeight: '120px',
                      margin: 0,
                    }}>
                      {toolStatus.content}
                    </pre>
                  </>
                )}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div style={{
          padding: '16px 24px',
          backgroundColor: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border-color)',
        }}>
          <div style={{ maxWidth: '100%', margin: '0 auto', padding: '0 40px' }}>
            <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px' }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Send a message..."
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '14px 16px',
                  backgroundColor: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  fontSize: '15px',
                  outline: 'none',
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                style={{
                  padding: '14px 28px',
                  backgroundColor: loading || !input.trim() ? 'var(--bg-tertiary)' : 'var(--accent-color)',
                  color: loading || !input.trim() ? 'var(--text-muted)' : 'white',
                  border: 'none',
                  borderRadius: '12px',
                  fontSize: '15px',
                  fontWeight: '500',
                  cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                }}
                onMouseEnter={(e) => {
                  if (!loading && input.trim()) {
                    e.target.style.backgroundColor = 'var(--accent-hover)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!loading && input.trim()) {
                    e.target.style.backgroundColor = 'var(--accent-color)'
                  }
                }}
              >
                {loading ? 'Sending...' : 'Send'}
              </button>
            </form>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  )
}

export default Chat
