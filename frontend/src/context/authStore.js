import { create } from 'zustand'
import axios from 'axios'

const API_URL = ''

export const useAuthStore = create((set, get) => {
  // Safely get token from localStorage
  const getToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token')
    }
    return null
  }

  const token = getToken()
  const isAuthenticated = !!token

  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  return {
    isAuthenticated,
    user: null,
    token: token || null,

    login: async (email, password) => {
      try {
        const response = await axios.post(`${API_URL}/api/auth/jwt/login`, new URLSearchParams({
          username: email,
          password: password,
        }), {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        })

        const { access_token } = response.data
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access_token)
        }
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

        // Get user info
        const userResponse = await axios.get(`${API_URL}/api/auth/users/me`)

        set({
          isAuthenticated: true,
          token: access_token,
          user: userResponse.data,
        })

        return { success: true }
      } catch (error) {
        console.error('Login error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Login failed',
        }
      }
    },

    register: async (email, password) => {
      try {
        // Register the user
        const registerResponse = await axios.post(`${API_URL}/api/auth/register`, {
          email,
          password,
        })

        // After successful registration, automatically log in
        const loginResponse = await axios.post(`${API_URL}/api/auth/jwt/login`, new URLSearchParams({
          username: email,
          password: password,
        }), {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        })

        const { access_token } = loginResponse.data
        localStorage.setItem('access_token', access_token)
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

        // Get user info
        const userResponse = await axios.get(`${API_URL}/api/auth/users/me`)

        set({
          isAuthenticated: true,
          token: access_token,
          user: userResponse.data,
        })

        return { success: true }
      } catch (error) {
        console.error('Register error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Registration failed',
        }
      }
    },

    logout: () => {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
      }
      delete axios.defaults.headers.common['Authorization']
      set({
        isAuthenticated: false,
        token: null,
        user: null,
      })
    },
  }
})
