import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './context/authStore'
import Login from './pages/Login'
import Register from './pages/Register'
import Chat from './pages/Chat'

function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (isAuthenticated) {
    return children
  }

  return <Navigate to="/login" replace />
}

function App() {
  console.log('App component rendered')

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#0d0d0d', width: '100%', height: '100%' }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/chat"
            element={
              <PrivateRoute>
                <Chat />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}

export default App
