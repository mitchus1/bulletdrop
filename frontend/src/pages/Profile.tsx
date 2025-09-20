import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

interface UserProfile {
  id: number
  username: string
  email: string
  avatar_url?: string
  bio?: string
  github_username?: string
  discord_username?: string
  telegram_username?: string
  instagram_username?: string
  background_image?: string
  background_color?: string
  favorite_song?: string
  created_at: string
  upload_count: number
  storage_used: number
  storage_limit: number
}

// Spiderweb animation component
const SpiderwebBackground = ({ mousePosition, isDark }: { mousePosition: { x: number; y: number }, isDark: boolean }) => {
  return (
    <svg
      className="absolute inset-0 w-full h-full opacity-20 pointer-events-none"
      style={{ 
        transform: `translate(${mousePosition.x * 0.02}px, ${mousePosition.y * 0.02}px)`,
        transition: 'transform 0.1s ease-out'
      }}
    >
      <defs>
        <radialGradient id="webGradient" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={isDark ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.8)"} />
          <stop offset="100%" stopColor={isDark ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.1)"} />
        </radialGradient>
      </defs>
      
      {/* Central web pattern */}
      <g stroke="url(#webGradient)" strokeWidth="1" fill="none">
        {/* Concentric circles */}
        {[60, 120, 180, 240].map((radius, i) => (
          <circle
            key={`circle-${i}`}
            cx="50%"
            cy="50%"
            r={radius}
            opacity={1 - i * 0.2}
            className="animate-pulse"
            style={{ animationDelay: `${i * 0.5}s`, animationDuration: '3s' }}
          />
        ))}
        
        {/* Radial lines */}
        {Array.from({ length: 12 }).map((_, i) => {
          const angle = (i * 30) * (Math.PI / 180);
          const x2 = 50 + Math.cos(angle) * 40;
          const y2 = 50 + Math.sin(angle) * 40;
          return (
            <line
              key={`line-${i}`}
              x1="50%"
              y1="50%"
              x2={`${x2}%`}
              y2={`${y2}%`}
              opacity={0.6}
              className="animate-pulse"
              style={{ animationDelay: `${i * 0.1}s`, animationDuration: '2s' }}
            />
          );
        })}
      </g>
    </svg>
  );
};

// Floating particles component
const FloatingParticles = () => {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 20 }).map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-white rounded-full opacity-60 animate-pulse"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${2 + Math.random() * 2}s`
          }}
        />
      ))}
    </div>
  );
};

export default function Profile() {
  const { username } = useParams<{ username: string }>()
  const { user: currentUser, token } = useAuth()
  const { theme, setTheme } = useTheme()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState<Partial<UserProfile>>({})
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const headerRef = useRef<HTMLDivElement>(null)

  const isOwnProfile = currentUser?.username === username
  const isDark = theme === 'dark'

  // Track mouse movement for interactive effects
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (headerRef.current) {
        const rect = headerRef.current.getBoundingClientRect();
        setMousePosition({
          x: ((e.clientX - rect.left) / rect.width - 0.5) * 100,
          y: ((e.clientY - rect.top) / rect.height - 0.5) * 100
        });
      }
    };

    const header = headerRef.current;
    if (header) {
      header.addEventListener('mousemove', handleMouseMove);
      return () => header.removeEventListener('mousemove', handleMouseMove);
    }
  }, []);

  // Helper function to get social media URLs
  const getSocialUrl = (platform: string, username: string) => {
    const urls = {
      github: `https://github.com/${username}`,
      discord: `https://discord.com/users/${username}`,
      telegram: `https://t.me/${username}`,
      instagram: `https://instagram.com/${username}`
    };
    return urls[platform as keyof typeof urls] || '#';
  };

  useEffect(() => {
    if (username) {
      fetchProfile()
    }
  }, [username])

  const fetchProfile = async () => {
    try {
      const response = await fetch(`http://localhost:8000/users/${username}`)

      if (!response.ok) {
        if (response.status === 404) {
          setError('User not found')
        } else {
          setError('Failed to load profile')
        }
        return
      }

      const profileData = await response.json()
      setProfile(profileData)
      setFormData(profileData)
    } catch (error) {
      setError('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = () => {
    setEditing(true)
    setFormData(profile || {})
  }

  const handleCancel = () => {
    setEditing(false)
    setFormData(profile || {})
  }

  const handleSave = async () => {
    if (!token) return

    try {
      const response = await fetch('http://localhost:8000/users/me', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      const updatedProfile = await response.json()
      setProfile(updatedProfile)
      setEditing(false)
    } catch (error) {
      setError('Failed to update profile')
    }
  }

  const handleInputChange = (field: keyof UserProfile, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const storagePercentage = profile ? (profile.storage_used / profile.storage_limit) * 100 : 0

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900 min-h-screen">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg mb-6"></div>
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900 min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600 dark:text-gray-400">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Go Home
          </button>
        </div>
      </div>
    )
  }

  if (!profile) return null

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300">
      {/* Theme Settings - Only for own profile */}
      {isOwnProfile && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6 dark:shadow-gray-900 transform transition-all duration-300 hover:shadow-xl hover:scale-[1.01]">
          <h2 className="text-xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Theme Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Choose your preferred theme
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setTheme('light')}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                    theme === 'light'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-white to-gray-100 rounded-full border border-gray-300 flex items-center justify-center">
                      <svg className="w-4 h-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    </div>
                    <div className="text-left">
                      <div className="font-medium text-gray-900 dark:text-white">Light Mode</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">Clean and bright</div>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => setTheme('dark')}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                    theme === 'dark'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg'
                      : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-gray-800 to-gray-900 rounded-full border border-gray-600 flex items-center justify-center">
                      <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                      </svg>
                    </div>
                    <div className="text-left">
                      <div className="font-medium text-gray-900 dark:text-white">Dark Mode</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">Easy on the eyes</div>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Header with stunning effects */}
      <div
        ref={headerRef}
        className="relative h-64 rounded-xl mb-6 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-500 overflow-hidden shadow-2xl transform transition-all duration-300 hover:scale-[1.02] hover:shadow-3xl dark:shadow-gray-800"
        style={{
          backgroundColor: profile.background_color || undefined,
          backgroundImage: profile.background_image ? `url(${profile.background_image})` : undefined,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        {/* Spiderweb effect */}
        <SpiderwebBackground mousePosition={mousePosition} isDark={isDark} />
        
        {/* Floating particles */}
        <FloatingParticles />
        
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-transparent to-black/40 animate-pulse"></div>
        
        {/* Glowing border effect */}
        <div className="absolute inset-0 rounded-xl border-2 border-white/20 animate-pulse"></div>
        
        {/* Profile content */}
        <div className="absolute bottom-6 left-6 text-white z-10">
          <div className="flex items-center space-x-6">
            {profile.avatar_url ? (
              <div className="relative group">
                <img
                  src={profile.avatar_url}
                  alt={profile.username}
                  className="w-20 h-20 rounded-full border-4 border-white shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:border-yellow-300 group-hover:shadow-yellow-300/50"
                />
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 opacity-0 group-hover:opacity-30 transition-opacity duration-300"></div>
              </div>
            ) : (
              <div className="relative group">
                <div className="w-20 h-20 rounded-full bg-gradient-to-r from-gray-300 to-gray-400 border-4 border-white flex items-center justify-center shadow-lg transition-all duration-300 group-hover:scale-110 group-hover:border-yellow-300 group-hover:shadow-yellow-300/50">
                  <span className="text-gray-600 font-bold text-2xl">
                    {profile.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 opacity-0 group-hover:opacity-30 transition-opacity duration-300"></div>
              </div>
            )}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent drop-shadow-lg">
                {profile.username}
              </h1>
              <p className="text-sm opacity-90 backdrop-blur-sm bg-black/20 px-3 py-1 rounded-full">
                Member since {new Date(profile.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
        
        {/* Edit button with enhanced styling */}
        {isOwnProfile && !editing && (
          <button
            onClick={handleEdit}
            className="absolute top-6 right-6 bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-xl backdrop-blur-md border border-white/20 transition-all duration-300 hover:scale-105 hover:shadow-lg group"
          >
            <span className="flex items-center space-x-2">
              <svg className="w-4 h-4 transition-transform group-hover:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Edit Profile</span>
            </span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {/* Enhanced Bio Section */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6 transform transition-all duration-300 hover:shadow-xl hover:scale-[1.01] dark:shadow-gray-900">
            <h2 className="text-xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">About</h2>
            {editing ? (
              <textarea
                value={formData.bio || ''}
                onChange={(e) => handleInputChange('bio', e.target.value)}
                placeholder="Tell people about yourself..."
                className="w-full h-24 p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
              />
            ) : (
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {profile.bio || 'No bio provided yet.'}
              </p>
            )}
          </div>

          {/* Enhanced Social Links with clickable functionality */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6 transform transition-all duration-300 hover:shadow-xl hover:scale-[1.01] dark:shadow-gray-900">
            <h2 className="text-xl font-semibold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Social Links</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { field: 'github_username', name: 'GitHub', icon: '🐙', color: 'from-gray-700 to-gray-900' },
                { field: 'discord_username', name: 'Discord', icon: '🎮', color: 'from-indigo-500 to-purple-600' },
                { field: 'telegram_username', name: 'Telegram', icon: '✈️', color: 'from-blue-400 to-blue-600' },
                { field: 'instagram_username', name: 'Instagram', icon: '📸', color: 'from-pink-400 via-red-500 to-yellow-500' }
              ].map(({ field, name, icon, color }) => (
                <div key={field} className="group">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <span className="flex items-center space-x-2">
                      <span className="text-lg">{icon}</span>
                      <span>{name}</span>
                    </span>
                  </label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData[field as keyof UserProfile] as string || ''}
                      onChange={(e) => handleInputChange(field as keyof UserProfile, e.target.value)}
                      placeholder={`Your ${name} username`}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
                    />
                  ) : (
                    <div className="relative">
                      {profile[field as keyof UserProfile] as string ? (
                        <a
                          href={getSocialUrl(field.replace('_username', ''), profile[field as keyof UserProfile] as string)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`block w-full p-3 rounded-lg bg-gradient-to-r ${color} text-white font-medium transition-all duration-300 transform hover:scale-105 hover:shadow-lg group-hover:shadow-xl`}
                        >
                          <span className="flex items-center justify-between">
                            <span>@{profile[field as keyof UserProfile] as string}</span>
                            <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </span>
                        </a>
                      ) : (
                        <div className="w-full p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400 text-center">
                          Not connected
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Customization */}
          {editing && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6 dark:shadow-gray-900">
              <h2 className="text-xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Profile Customization</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Background Color
                  </label>
                  <input
                    type="color"
                    value={formData.background_color || '#3B82F6'}
                    onChange={(e) => handleInputChange('background_color', e.target.value)}
                    className="w-full h-12 border border-gray-300 dark:border-gray-600 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Background Image URL
                  </label>
                  <input
                    type="url"
                    value={formData.background_image || ''}
                    onChange={(e) => handleInputChange('background_image', e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Favorite Song
                  </label>
                  <input
                    type="text"
                    value={formData.favorite_song || ''}
                    onChange={(e) => handleInputChange('favorite_song', e.target.value)}
                    placeholder="Artist - Song Title"
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Sidebar */}
        <div className="space-y-6">
          {/* Enhanced Stats */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 transform transition-all duration-300 hover:shadow-xl hover:scale-[1.02] dark:shadow-gray-900">
            <h2 className="text-xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Stats</h2>
            <div className="space-y-4">
              <div className="group">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Files uploaded</span>
                  <span className="font-bold text-lg text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform duration-300">{profile.upload_count}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000 ease-out transform origin-left"
                    style={{ 
                      width: `${Math.min((profile.upload_count / 100) * 100, 100)}%`
                    }}
                  ></div>
                </div>
              </div>
              
              <div className="group">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Storage used</span>
                  <span className="font-medium group-hover:scale-110 transition-transform duration-300 text-gray-900 dark:text-gray-100">
                    {formatBytes(profile.storage_used)} / {formatBytes(profile.storage_limit)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden shadow-inner">
                  <div
                    className="bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 h-3 rounded-full transition-all duration-1000 ease-out relative overflow-hidden"
                    style={{ width: `${Math.min(storagePercentage, 100)}%` }}
                  >
                    <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 flex justify-between">
                  <span>{storagePercentage.toFixed(1)}% used</span>
                  <span className={`font-medium ${storagePercentage > 90 ? 'text-red-500 animate-pulse' : storagePercentage > 70 ? 'text-yellow-500' : 'text-green-500'}`}>
                    {storagePercentage > 90 ? '🔴 Almost full!' : storagePercentage > 70 ? '🟡 Getting full' : '🟢 Plenty of space'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Favorite Song */}
          {profile.favorite_song && (
            <div className="bg-gradient-to-br from-green-400 via-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white transform transition-all duration-300 hover:shadow-xl hover:scale-[1.02] relative overflow-hidden">
              {/* Animated background */}
              <div className="absolute inset-0 opacity-30">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-pulse"></div>
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute w-2 h-2 bg-white rounded-full opacity-60"
                    style={{
                      left: `${20 + i * 30}%`,
                      top: `${30 + i * 10}%`,
                      animation: `float ${2 + i}s ease-in-out infinite`,
                      animationDelay: `${i * 0.5}s`
                    }}
                  />
                ))}
              </div>
              
              <div className="relative z-10">
                <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                  <span>🎵 Currently Playing</span>
                </h2>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30 group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.69 13.92a1 1 0 01-.429-.876V7.956a1 1 0 01.429-.876l3.693-2.896A1 1 0 019.383 3.076zM12 5v10a2 2 0 001.789 1.987l.211.013A2 2 0 0016 15V5a2 2 0 00-1.789-1.987L14 3a2 2 0 00-2 2z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-lg drop-shadow-lg">{profile.favorite_song}</p>
                    <p className="text-sm opacity-90">Favorite Song</p>
                    {/* Sound waves animation */}
                    <div className="flex items-center space-x-1 mt-2">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <div
                          key={i}
                          className="w-1 bg-white rounded-full opacity-70"
                          style={{
                            height: `${8 + Math.random() * 12}px`,
                            animation: `wave ${0.5 + Math.random() * 0.5}s ease-in-out infinite alternate`,
                            animationDelay: `${i * 0.1}s`
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Buttons */}
      {editing && (
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={handleCancel}
            className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white rounded-lg transition-all duration-300 shadow-lg hover:shadow-xl"
          >
            Save Changes
          </button>
        </div>
      )}
    </div>
  )
}
