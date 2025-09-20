import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { SkeletonProfile } from '../components/Skeleton'
import ViewCounter from '../components/ViewCounter'
import { useProfileViewTracking } from '../hooks/useViewTracking'

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
  preferred_domain_id?: number
  created_at: string
  upload_count: number
  storage_used: number
  storage_limit: number
  is_premium?: boolean
  premium_expires_at?: string
}

interface Domain {
  id: number
  domain_name: string
  display_name: string
  description?: string
  is_available: boolean
  is_premium: boolean
}

// Matrix rain animation component
const MatrixBackground = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
    {Array.from({ length: 15 }).map((_, i) => (
      <div
        key={i}
        className="absolute text-green-400 font-mono text-xs animate-pulse select-none"
        style={{
          left: `${(i * 7) % 100}%`,
          top: '-20px',
          animation: `matrixRain ${3 + Math.random() * 2}s linear infinite`,
          animationDelay: `${Math.random() * 2}s`
        }}
      >
        {Array.from({ length: 20 }).map((_, j) => (
          <div key={j} className="block">
            {String.fromCharCode(0x30A0 + Math.random() * 96)}
          </div>
        ))}
      </div>
    ))}
  </div>
);

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
  const [domains, setDomains] = useState<Domain[]>([])
  const [loadingDomains, setLoadingDomains] = useState(false)

  const isOwnProfile = currentUser?.username === username

  // Track profile views (only for profiles that aren't the current user's own profile)
  useProfileViewTracking(
    profile?.id, 
    { 
      enabled: !isOwnProfile && !!profile?.id,
      delay: 3000 // 3 second delay for profile views
    }
  )

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
      if (isOwnProfile) {
        fetchDomains()
      }
    }
  }, [username, isOwnProfile])

  const fetchProfile = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/users/${username}`)

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

  const fetchDomains = async () => {
    try {
      setLoadingDomains(true)
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/domains`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      if (response.ok) {
        const domainsData = await response.json()
        setDomains(domainsData)
      }
    } catch (error) {
      console.error('Failed to fetch domains:', error)
    } finally {
      setLoadingDomains(false)
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
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/users/me`, {
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

  const handleInputChange = (field: keyof UserProfile, value: string | number) => {
    if (field === 'preferred_domain_id') {
      // Handle preferred_domain_id as a number
      const numValue = value === '' ? undefined : Number(value)
      setFormData(prev => ({ ...prev, [field]: numValue }))
    } else {
      setFormData(prev => ({ ...prev, [field]: value }))
    }
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
      <div className="bg-gray-50 dark:bg-gray-900 min-h-screen">
        <SkeletonProfile />
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
    <div 
      className="min-h-screen relative overflow-hidden"
      style={{
        backgroundImage: profile.background_image ? `url(${profile.background_image})` : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        backgroundColor: profile.background_color || '#667eea',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Matrix animation overlay */}
      <MatrixBackground />
      
      {/* Dark overlay for better readability */}
      <div className="absolute inset-0 bg-black/20"></div>
      
      {/* Hover navbar */}
      <div className="fixed top-0 left-0 right-0 z-50 transform -translate-y-full hover:translate-y-0 transition-transform duration-300 group">
        <div className="bg-black/80 backdrop-blur-md text-white p-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold">{profile.username}'s Profile</h1>
              {isOwnProfile && (
                <button
                  onClick={handleEdit}
                  className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg text-sm transition-colors"
                >
                  {editing ? 'Editing...' : 'Edit Profile'}
                </button>
              )}
            </div>
            <div className="flex items-center space-x-4">
              {/* Theme toggle */}
              <button
                onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                className="bg-white/20 hover:bg-white/30 p-2 rounded-lg transition-colors"
              >
                {theme === 'light' ? '🌙' : '☀️'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navbar hover indicator */}
      <div className="fixed top-0 left-1/2 transform -translate-x-1/2 w-12 h-1 bg-white/30 hover:bg-white/60 rounded-b-full z-40 transition-all duration-300 hover:w-16 hover:h-2"></div>

      {/* Main content with glassmorphism cards */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Profile Card */}
          <div className="lg:col-span-1 order-1">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              {/* Avatar */}
              <div className="text-center mb-6">
                {profile.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt={profile.username}
                    className="w-32 h-32 rounded-full mx-auto border-4 border-white/30 shadow-lg"
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-white/20 border-4 border-white/30 flex items-center justify-center mx-auto shadow-lg">
                    <span className="text-white font-bold text-4xl">
                      {profile.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                )}
                <h1 className="text-3xl font-bold text-white mt-4 drop-shadow-lg">
                  {profile.username}
                </h1>
                <p className="text-white/80 mt-2">
                  Member since {new Date(profile.created_at).toLocaleDateString()}
                </p>
              </div>

              {/* Stats */}
              <div className="space-y-4 mb-6">
                <div>
                  <div className="flex justify-between text-sm mb-2 text-white/90">
                    <span>Files uploaded</span>
                    <span className="font-bold">{profile.upload_count}</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-blue-400 to-purple-400 h-2 rounded-full transition-all duration-500"
                      style={{ 
                        width: `${Math.min((profile.upload_count / 100) * 100, 100)}%`
                      }}
                    ></div>
                  </div>
                </div>

                {/* Profile Views */}
                <div>
                  <div className="flex justify-between text-sm mb-2 text-white/90">
                    <span>Profile views</span>
                  </div>
                  <ViewCounter 
                    contentType="profile" 
                    contentId={profile.id} 
                    showDetails={true}
                    className="text-white/80"
                  />
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-2 text-white/90">
                    <span>Storage used</span>
                    <span className="font-medium">
                      {formatBytes(profile.storage_used)} / {formatBytes(profile.storage_limit)}
                    </span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-400 to-blue-400 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(storagePercentage, 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-white/70 mt-1">
                    {storagePercentage.toFixed(1)}% used
                  </div>
                </div>
                
                {/* Premium Status */}
                <div>
                  <div className="flex justify-between items-center text-sm mb-2 text-white/90">
                    <span>Account Status</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      profile.is_premium 
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' 
                        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                    }`}>
                      {profile.is_premium ? '👑 Premium' : 'Free'}
                    </span>
                  </div>
                  {profile.is_premium && profile.premium_expires_at && (
                    <div className="text-xs text-white/70">
                      Premium expires: {new Date(profile.premium_expires_at).toLocaleDateString()}
                    </div>
                  )}
                  {!profile.is_premium && (
                    <div className="text-xs text-white/70">
                      Upgrade to Premium for exclusive domains and features
                    </div>
                  )}
                </div>
              </div>

              {/* Favorite Song */}
              {profile.favorite_song && (
                <div className="bg-white/10 rounded-xl p-4 border border-white/20">
                  <h3 className="text-white font-semibold mb-2 flex items-center">
                    🎵 <span className="ml-2">Now Playing</span>
                  </h3>
                  <p className="text-white/90 text-sm">{profile.favorite_song}</p>
                </div>
              )}
            </div>
          </div>

          {/* Content Cards */}
          <div className="lg:col-span-2 order-2 space-y-6">
            
            {/* Bio Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-4">About</h2>
              {editing ? (
                <textarea
                  value={formData.bio || ''}
                  onChange={(e) => handleInputChange('bio', e.target.value)}
                  placeholder="Tell people about yourself..."
                  className="w-full h-32 p-4 bg-white/10 border border-white/20 text-white placeholder-white/60 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                />
              ) : (
                <p className="text-white/90 text-lg leading-relaxed">
                  {profile.bio || 'No bio provided yet.'}
                </p>
              )}
            </div>

            {/* Social Links Card */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-6">Connect</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { field: 'github_username', name: 'GitHub', icon: '🐙', color: 'from-gray-600 to-gray-800' },
                  { field: 'discord_username', name: 'Discord', icon: '🎮', color: 'from-indigo-600 to-purple-600' },
                  { field: 'telegram_username', name: 'Telegram', icon: '✈️', color: 'from-blue-500 to-blue-700' },
                  { field: 'instagram_username', name: 'Instagram', icon: '📸', color: 'from-pink-500 to-red-500' }
                ].map(({ field, name, icon, color }) => (
                  <div key={field}>
                    <label className="block text-sm font-medium text-white/90 mb-2">
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
                        className="w-full p-3 bg-white/10 border border-white/20 text-white placeholder-white/60 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                      />
                    ) : (
                      <div>
                        {profile[field as keyof UserProfile] as string ? (
                          <a
                            href={getSocialUrl(field.replace('_username', ''), profile[field as keyof UserProfile] as string)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`block w-full p-4 bg-gradient-to-r ${color} rounded-xl text-white hover:scale-105 transform transition-all duration-200 shadow-lg hover:shadow-xl`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">@{profile[field as keyof UserProfile] as string}</span>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </div>
                          </a>
                        ) : (
                          <div className="w-full p-4 bg-white/5 rounded-xl text-white/60 text-center border border-white/10">
                            Not connected
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Customization Card - Only when editing */}
            {editing && (
              <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">Customize</h2>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Background Color
                    </label>
                    <input
                      type="color"
                      value={formData.background_color || '#667eea'}
                      onChange={(e) => handleInputChange('background_color', e.target.value)}
                      className="w-full h-12 bg-white/10 border border-white/20 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Background Image URL
                    </label>
                    <input
                      type="url"
                      value={formData.background_image || ''}
                      onChange={(e) => handleInputChange('background_image', e.target.value)}
                      placeholder="https://example.com/image.jpg"
                      className="w-full p-3 bg-white/10 border border-white/20 text-white placeholder-white/60 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Favorite Song
                    </label>
                    <input
                      type="text"
                      value={formData.favorite_song || ''}
                      onChange={(e) => handleInputChange('favorite_song', e.target.value)}
                      placeholder="Artist - Song Title"
                      className="w-full p-3 bg-white/10 border border-white/20 text-white placeholder-white/60 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white/90 mb-2">
                      Preferred Domain
                    </label>
                    {loadingDomains ? (
                      <div className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white/60">
                        Loading domains...
                      </div>
                    ) : (
                      <select
                        value={formData.preferred_domain_id || ''}
                        onChange={(e) => handleInputChange('preferred_domain_id', e.target.value)}
                        className="w-full p-3 bg-white/10 border border-white/20 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-white/30 backdrop-blur-sm"
                      >
                        <option value="">Select a domain...</option>
                        {domains.map((domain) => (
                          <option 
                            key={domain.id} 
                            value={domain.id} 
                            className="bg-gray-800 text-white"
                            disabled={domain.is_premium && !profile?.is_premium}
                          >
                            {domain.display_name || domain.domain_name}
                            {domain.is_premium ? ' 👑 Premium' : ''}
                            {domain.is_premium && !profile?.is_premium ? ' (Premium Required)' : ''}
                          </option>
                        ))}
                      </select>
                    )}
                    <p className="text-sm text-white/60 mt-1">
                      This domain will be used for your ShareX uploads and file URLs
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Edit Buttons */}
            {editing && (
              <div className="flex justify-end space-x-4">
                <button
                  onClick={handleCancel}
                  className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl border border-white/20 transition-colors backdrop-blur-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl transition-colors shadow-lg hover:shadow-xl"
                >
                  Save Changes
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}