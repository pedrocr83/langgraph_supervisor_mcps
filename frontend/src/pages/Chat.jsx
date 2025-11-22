import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../context/authStore'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [toolStatus, setToolStatus] = useState(null)
  const messagesEndRef = useRef(null)
  const wsRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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
      if (response.data.length > 0) {
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

  const connectWebSocket = (convId) => {
    const token = localStorage.getItem('access_token')
    const wsUrl = API_URL.replace('http', 'ws')
    const ws = new WebSocket(`${wsUrl}/api/chat/ws/${convId}?token=${token}`)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'conversation_id') {
        setConversationId(data.conversation_id)
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
    } catch (error) {
      console.error('Error sending message:', error)
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">🤖 LangGraph Supervisor</h1>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              Start a conversation by typing a message below
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-900 shadow'
                }`}
              >
                {msg.toolName && (
                  <div className="text-xs opacity-75 mb-1">
                    Tool: {msg.toolName}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {!msg.complete && msg.role === 'assistant' && (
                  <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
                )}
              </div>
            </div>
          ))}
          {toolStatus && (
            <div className="flex justify-start">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 text-sm text-yellow-800">
                {toolStatus.calling ? (
                  <>Calling tool: {toolStatus.name}...</>
                ) : (
                  <>
                    <div className="font-semibold">Tool: {toolStatus.name}</div>
                    <pre className="mt-1 text-xs overflow-auto max-h-32">
                      {toolStatus.content}
                    </pre>
                  </>
                )}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="flex space-x-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="What can I do for you?"
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Chat

