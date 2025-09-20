import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function OAuthCallback() {
  const { provider } = useParams<{ provider: string }>()
  const navigate = useNavigate()
  const { login } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search)
      const code = urlParams.get('code')
      const error = urlParams.get('error')

      if (error) {
        console.error('OAuth error:', error)
        navigate('/login?error=oauth_failed')
        return
      }

      if (!code || !provider) {
        navigate('/login?error=oauth_failed')
        return
      }

      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/auth/oauth/${provider}/callback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        })

        if (!response.ok) {
          throw new Error('OAuth callback failed')
        }

        const tokenData = await response.json()

        // Store token and get user data
        localStorage.setItem('token', tokenData.access_token)

        // Use the auth context to set the user state
        const userResponse = await fetch(`${apiUrl}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${tokenData.access_token}`,
          },
        })

        if (userResponse.ok) {
          await userResponse.json()
          // Manually trigger auth state update
          window.location.href = '/dashboard'
        } else {
          throw new Error('Failed to get user data')
        }
      } catch (error) {
        console.error('OAuth callback error:', error)
        navigate('/login?error=oauth_failed')
      }
    }

    handleCallback()
  }, [provider, navigate, login])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
    </div>
  )
}