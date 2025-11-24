import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuthStore } from '../context/authStore'
import { useLanguageStore } from '../context/languageStore'
import { shallow } from 'zustand/shallow'
import LanguageSwitcher from '../components/LanguageSwitcher'
import Sidebar from '../components/Sidebar'
import MarkdownRenderer from '../components/MarkdownRenderer'
import axios from 'axios'
import maleIcon from '../icons/male_small.png'
import robotHappyIcon from '../icons/robot_happy_small.png'
import robotConfusedIcon from '../icons/robot_confusion_small.png'
import robotSadIcon from '../icons/robot_sad_small.png'
import robotAngryIcon from '../icons/robot_angry_small.png'

const API_URL = ''

function Chat() {
  const { language, t } = useLanguageStore(
    (state) => ({ language: state.language, t: state.t }),
    shallow
  )
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(false)
  const [toolStatus, setToolStatus] = useState(null)
  const [isThinking, setIsThinking] = useState(false)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const parseMessage = (content) => {
    if (!content) return { emotion: 'happy', cleanContent: '' }
    
    // Try standard format: <emotion>type</emotion>
    const emotionMatch = content.match(/<emotion>(.*?)<\/emotion>/)
    if (emotionMatch) {
      return {
        emotion: emotionMatch[1],
        cleanContent: content.replace(/<emotion>.*?<\/emotion>/g, '').trim()
      }
    }

    // Try fallback format: <type>...</type> or just <type>
    const fallbackMatch = content.match(/<(happy|confused|sad|angry)>/)
    if (fallbackMatch) {
      const emotion = fallbackMatch[1]
      let cleanContent = content.replace(new RegExp(`<${emotion}>`, 'g'), '')
      cleanContent = cleanContent.replace(new RegExp(`<\/${emotion}>`, 'g'), '')
      return { emotion, cleanContent: cleanContent.trim() }
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

  const loadMessages = useCallback(async (convId) => {
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
  }, [])

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/conversations`)
      setConversations(response.data)
    } catch (error) {
      console.error('Error loading conversations:', error)
    }
  }

  useEffect(() => {
    if (!conversationId && conversations.length > 0) {
      const firstConv = conversations[0]
      setConversationId(firstConv.id)
      loadMessages(firstConv.id)
    }
  }, [conversationId, conversations, loadMessages])

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
      alert(t('chat.deleteFailed'))
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
      } else if (data.type === 'tool_call') {
        // Agent is calling a sub-agent - show "communicating" status
        setToolStatus({ name: data.name, calling: true, isCommunicating: true })
        setIsThinking(true)
      } else if (data.type === 'tool') {
        // Tool result received - keep showing it briefly
        setToolStatus({ name: data.name, content: data.content, isCommunicating: false })
      } else if (data.type === 'content') {
        setIsThinking(false)
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
        setIsThinking(false)
        // Reload conversations to update timestamps
        loadConversations()
      } else if (data.type === 'error') {
        setToolStatus(null)
        setLoading(false)
        setIsThinking(false)
        alert(`${t('chat.error')}: ${data.message}`)
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
    setIsThinking(true)

    // Add user message to UI
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    // Use WebSocket if available, otherwise fallback to REST
    const convId = conversationId || 'new'

    // Helper to wait for WebSocket connection
    const waitForConnection = async () => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            connectWebSocket(convId)
        }
        
        // Poll for connection up to 3 seconds (10 attempts * 300ms)
        for (let i = 0; i < 10; i++) {
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                return true
            }
            await new Promise(resolve => setTimeout(resolve, 300))
        }
        return false
    }

    const isConnected = await waitForConnection()

    if (isConnected) {
      wsRef.current.send(
        JSON.stringify({
          type: 'message',
          message: userMessage,
        })
      )
    } else {
      console.warn('WebSocket connection failed, falling back to REST')
      sendViaRest(userMessage, convId)
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
      setIsThinking(false)
      loadConversations()
    } catch (error) {
      console.error('Error sending message:', error)
      setLoading(false)
      setIsThinking(false)
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
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h1 style={{
            fontSize: '20px',
            fontWeight: '600',
            color: 'var(--text-primary)',
            margin: 0,
          }}>
            misteriosAI
          </h1>
          <LanguageSwitcher />
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
                <p>{t('chat.startConversation')}</p>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>{t('chat.askAnything')}</p>
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
                        {t('chat.tool')}: {msg.toolName}
                      </div>
                    )}
                    <div style={{
                      padding: '20px 24px',
                      borderRadius: '16px',
                      borderBottomLeftRadius: msg.role === 'user' ? '4px' : '16px',
                      borderBottomRightRadius: msg.role === 'assistant' ? '4px' : '16px',
                      backgroundColor: msg.role === 'user' ? 'var(--bg-user-msg)' : 'var(--bg-assistant-msg)',
                      color: 'var(--text-primary)',
                      wordBreak: 'break-word',
                      lineHeight: '1.6',
                      fontSize: '16px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                      ...(msg.role === 'user' ? { whiteSpace: 'pre-wrap' } : {}),
                    }}>
                      {msg.role === 'assistant' ? (
                        <MarkdownRenderer content={cleanContent} />
                      ) : (
                        cleanContent
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
            {/* Thinking Animation */}
            {isThinking && !toolStatus && (
              <div style={{
                display: 'flex',
                gap: '12px',
                padding: '8px 0',
                flexDirection: 'row-reverse',
                justifyContent: 'flex-start',
                alignItems: 'flex-end',
              }}>
                <div style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '12px',
                  backgroundColor: 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginBottom: '4px',
                }}>
                  <img
                    src={robotHappyIcon}
                    alt="AI thinking"
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'contain',
                      animation: 'pulse 1.5s ease-in-out infinite'
                    }}
                  />
                </div>
                <div style={{
                  flex: 1,
                  minWidth: 0,
                  maxWidth: '70%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                }}>
                  <div style={{
                    padding: '20px 24px',
                    borderRadius: '16px',
                    borderBottomRightRadius: '4px',
                    backgroundColor: 'var(--bg-assistant-msg)',
                    color: 'var(--text-primary)',
                    fontSize: '16px',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  }}>
                    {t('chat.thinking')}
                    <span style={{ animation: 'blink 1.4s linear infinite' }}>.</span>
                    <span style={{ animation: 'blink 1.4s linear infinite 0.2s' }}>.</span>
                    <span style={{ animation: 'blink 1.4s linear infinite 0.4s' }}>.</span>
                  </div>
                </div>
              </div>
            )}
            {toolStatus && (
              <div style={{
                display: 'flex',
                gap: '12px',
                padding: '8px 0',
                flexDirection: 'row-reverse',
                justifyContent: 'flex-start',
                alignItems: 'flex-end',
              }}>
                <div style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '12px',
                  backgroundColor: 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  marginBottom: '4px',
                  position: 'relative',
                }}>
                  <img
                    src={robotHappyIcon}
                    alt="AI thinking"
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'contain',
                      animation: toolStatus.calling ? 'pulse 1.5s ease-in-out infinite' : 'none'
                    }}
                  />
                  {toolStatus.isCommunicating && (
                    <div style={{
                      position: 'absolute',
                      bottom: '0',
                      right: '0',
                      width: '24px',
                      height: '24px',
                      backgroundColor: 'var(--accent-color)',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      animation: 'bounce 1s ease-in-out infinite',
                      fontSize: '12px',
                    }}>
                      💬
                    </div>
                  )}
                </div>
                <div style={{
                  flex: 1,
                  minWidth: 0,
                  maxWidth: '70%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-end',
                }}>
                  <div style={{
                    padding: '20px 24px',
                    borderRadius: '16px',
                    borderBottomRightRadius: '4px',
                    backgroundColor: 'var(--bg-assistant-msg)',
                    color: 'var(--text-primary)',
                    fontSize: '14px',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  }}>
                    {toolStatus.calling ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {toolStatus.isCommunicating ? (
                          <>
                            <span style={{ animation: 'blink 1.4s linear infinite' }}>●</span>
                            <span style={{ animation: 'blink 1.4s linear infinite 0.2s' }}>●</span>
                            <span style={{ animation: 'blink 1.4s linear infinite 0.4s' }}>●</span>
                            <span style={{ marginLeft: '8px' }}>{t('chat.communicating')} {toolStatus.name}...</span>
                          </>
                        ) : (
                          <>🔧 {t('chat.callingTool')}: {toolStatus.name}...</>
                        )}
                      </div>
                    ) : (
                      <>
                        <div style={{ fontWeight: '500', marginBottom: '4px' }}>🔧 {t('chat.tool')}: {toolStatus.name}</div>
                        <pre style={{
                          fontSize: '12px',
                          color: 'var(--text-muted)',
                          overflow: 'auto',
                          maxHeight: '120px',
                          margin: 0,
                          whiteSpace: 'pre-wrap',
                        }}>
                          {toolStatus.content}
                        </pre>
                      </>
                    )}
                  </div>
                </div>
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
                placeholder={t('chat.sendMessage')}
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
                {loading ? t('chat.sending') : t('chat.send')}
              </button>
            </form>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}

export default Chat
