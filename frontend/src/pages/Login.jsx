import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../context/authStore'
import robotHappyIcon from '../icons/robot_happy_small.png'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((state) => state.login)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const result = await login(email, password)

    if (result.success) {
      navigate('/chat')
    } else {
      setError(result.error)
    }

    setLoading(false)
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      backgroundColor: 'var(--bg-primary)', 
      padding: '1rem' 
    }}>
      <div style={{ 
        maxWidth: '32rem', 
        width: '100%', 
        backgroundColor: 'var(--bg-secondary)', 
        padding: '2.5rem', 
        borderRadius: '16px', 
        border: '1px solid var(--border-color)',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        {/* Header with Logo and Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '16px',
            marginBottom: '1rem'
          }}>
            <img 
              src={robotHappyIcon} 
              alt="misteriosAI" 
              style={{ width: '64px', height: '64px', objectFit: 'contain' }}
            />
            <h1 style={{ 
              fontSize: '2rem', 
              fontWeight: '600', 
              color: 'var(--text-primary)', 
              margin: 0 
            }}>
              misteriosAI
            </h1>
          </div>
          <p style={{ 
            fontSize: '1rem', 
            color: 'var(--text-secondary)', 
            marginTop: '0.5rem',
            lineHeight: '1.6'
          }}>
            O seu assistente inteligente para Misterios Lda
          </p>
        </div>

        {/* Capabilities Description */}
        <div style={{ 
          backgroundColor: 'var(--bg-tertiary)', 
          padding: '1.25rem', 
          borderRadius: '12px', 
          marginBottom: '2rem',
          border: '1px solid var(--border-color)'
        }}>
          <h3 style={{ 
            fontSize: '0.875rem', 
            fontWeight: '600', 
            color: 'var(--text-primary)', 
            marginTop: 0,
            marginBottom: '0.75rem'
          }}>
            O que é o misteriosAI?
          </h3>
          <p style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            margin: 0,
            lineHeight: '1.6'
          }}>
            O misteriosAI é um assistente pessoal inteligente alimentado por tecnologia de IA avançada. 
            Ajuda-o a aceder e gerir dados da empresa através de capacidades especializadas:
          </p>
          <ul style={{ 
            fontSize: '0.875rem', 
            color: 'var(--text-secondary)', 
            marginTop: '0.75rem',
            marginBottom: 0,
            paddingLeft: '1.25rem',
            lineHeight: '1.8'
          }}>
            <li><strong style={{ color: 'var(--text-primary)' }}>Acesso ao Primavera ERP:</strong> Consultar vendas, inventário, finanças e dados empresariais</li>
            <li><strong style={{ color: 'var(--text-primary)' }}>Gestão de Ficheiros:</strong> Pesquisar e aceder a documentos do SharePoint/OneDrive</li>
            <li><strong style={{ color: 'var(--text-primary)' }}>Assistência em Tempo Real:</strong> Obter respostas instantâneas com respostas em streaming</li>
          </ul>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{ 
              backgroundColor: '#7f1d1d', 
              border: '1px solid #991b1b', 
              color: '#fecaca', 
              padding: '0.75rem 1rem', 
              borderRadius: '8px', 
              marginBottom: '1.5rem',
              fontSize: '0.875rem'
            }}>
              {error}
            </div>
          )}
          
          <div style={{ marginBottom: '1rem' }}>
            <label htmlFor="email" style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              color: 'var(--text-primary)' 
            }}>
              Endereço de email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              style={{ 
                width: '100%', 
                padding: '0.75rem 1rem', 
                backgroundColor: 'var(--bg-input)', 
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)', 
                borderRadius: '8px', 
                fontSize: '0.875rem',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              placeholder="Endereço de email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
            />
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="password" style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem', 
              fontWeight: '500', 
              color: 'var(--text-primary)' 
            }}>
              Palavra-passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              style={{ 
                width: '100%', 
                padding: '0.75rem 1rem', 
                backgroundColor: 'var(--bg-input)', 
                color: 'var(--text-primary)',
                border: '1px solid var(--border-color)', 
                borderRadius: '8px', 
                fontSize: '0.875rem',
                outline: 'none',
                transition: 'border-color 0.2s'
              }}
              placeholder="Palavra-passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-color)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <button
              type="submit"
              disabled={loading}
              style={{ 
                width: '100%', 
                padding: '0.875rem 1rem', 
                backgroundColor: loading ? 'var(--bg-tertiary)' : 'var(--accent-color)', 
                color: loading ? 'var(--text-muted)' : 'white', 
                border: 'none', 
                borderRadius: '8px', 
                fontSize: '0.875rem', 
                fontWeight: '500', 
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.target.style.backgroundColor = 'var(--accent-hover)'
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.target.style.backgroundColor = 'var(--accent-color)'
                }
              }}
            >
              {loading ? 'A iniciar sessão...' : 'Iniciar Sessão'}
            </button>
          </div>

          <div style={{ textAlign: 'center' }}>
            <Link
              to="/register"
              style={{ 
                fontSize: '0.875rem', 
                fontWeight: '500', 
                color: 'var(--accent-color)', 
                textDecoration: 'none',
                transition: 'color 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.color = 'var(--accent-hover)'}
              onMouseLeave={(e) => e.target.style.color = 'var(--accent-color)'}
            >
              Não tem uma conta? Registar
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
