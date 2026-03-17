import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async () => {
    setLoading(true)
    setError('')

    // Step 1 — get CSRF token
    await fetch('/api-auth/login/', { credentials: 'include' })
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1]

    // Step 2 — submit login
    const response = await fetch('/api-auth/login/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken || ''
      },
      body: new URLSearchParams({
        username,
        password,
        next: '/portfolio'
      }),
      redirect: 'manual'
    })

    if (response.status === 200 || response.status === 0 || response.type === 'opaqueredirect') {
      navigate('/portfolio')
    } else {
      setError('Invalid username or password')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center">
      <div className="w-full max-w-md">

        {/* LOGO */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center font-bold text-2xl mx-auto mb-4">D</div>
          <h1 className="text-3xl font-black text-white">Desis Portfolio</h1>
          <p className="text-gray-400 mt-2">Sign in to your account</p>
        </div>

        {/* FORM CARD */}
        <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl p-8 border border-gray-800">

          {/* Error */}
          {error && (
            <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              🚨 {error}
            </div>
          )}

          {/* Username */}
          <div className="mb-4">
            <label className="text-sm text-gray-400 mb-2 block">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter your username"
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Password */}
          <div className="mb-6">
            <label className="text-sm text-gray-400 mb-2 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter your password"
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Button */}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold py-3 rounded-xl transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In →'}
          </button>

        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          Desis Portfolio Intelligence Platform
        </p>
      </div>
    </div>
  )
}
