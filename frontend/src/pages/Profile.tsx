import { useState, useEffect } from 'react'
import ReactPlayer from 'react-player'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
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

// (removed Domain interface; editing and domain selection moved to Settings)

// Matrix rain animation component
const MatrixBackground = () => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
    {Array.from({ length: 15 }).map((_, i) => (
      <div
        key={i}
        className="absolute text-green-400 font-mono text-xs animate-pulse select-none"
        style={{
          insetInlineStart: `${(i * 7) % 100}%`,
          insetBlockStart: '-20px',
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
  const { user: currentUser } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [videoBgEnabled, setVideoBgEnabled] = useState(true)
  const [videoReady, setVideoReady] = useState(false)
  const [muted, setMuted] = useState(true)
  

  const isUrl = (val?: string) => !!val && /^https?:\/\//i.test(val)

  const normalizeMediaUrl = (val?: string) => {
    if (!val) return ''
    if (!isUrl(val)) return ''
    try {
      const u = new URL(val)
      const isYouTube = u.hostname.includes('youtube.com') || u.hostname.includes('youtu.be')
      if (!isYouTube) return val

  // Normalize host to privacy-enhanced domain when embedding (still works for watch URLs)
  const host = 'www.youtube-nocookie.com'

      // If v param exists, prefer watch?v=...
      const v = u.searchParams.get('v')
      if (v) {
        // Preserve time-related params if present
        const t = u.searchParams.get('t')
        const start = u.searchParams.get('start')
        const timeQuery = t ? `&t=${encodeURIComponent(t)}` : start ? `&start=${encodeURIComponent(start)}` : ''
        return `https://${host}/watch?v=${v}${timeQuery}`
      }

      // shorts format: /shorts/ID
      const shortsMatch = u.pathname.match(/^\/shorts\/([A-Za-z0-9_-]+)/)
      if (shortsMatch) {
        const id = shortsMatch[1]
        return `https://${host}/watch?v=${id}`
      }

      // embed format: /embed/ID
      const embedMatch = u.pathname.match(/^\/embed\/([A-Za-z0-9_-]+)/)
      if (embedMatch) {
        const id = embedMatch[1]
        return `https://${host}/watch?v=${id}`
      }

      // live format: /live/ID
      const liveMatch = u.pathname.match(/^\/live\/([A-Za-z0-9_-]+)/)
      if (liveMatch) {
        const id = liveMatch[1]
        return `https://${host}/watch?v=${id}`
      }

      // youtu.be short links
      if (u.hostname === 'youtu.be') {
        // pathname like /VIDEOID
        const id = u.pathname.replace(/^\//, '')
        if (id) {
          const t = u.searchParams.get('t')
          const timeQuery = t ? `&t=${encodeURIComponent(t)}` : ''
          return `https://${host}/watch?v=${id}${timeQuery}`
        }
      }

      // m.youtube.com or music.youtube.com or other subdomains
      if (u.hostname.endsWith('.youtube.com')) {
        // If already a watch URL without v param extraction above, return as-is
        // but normalize to www subdomain
        if (u.pathname === '/watch') {
          const v2 = u.searchParams.get('v')
          if (v2) {
            const t = u.searchParams.get('t')
            const start = u.searchParams.get('start')
            const timeQuery = t ? `&t=${encodeURIComponent(t)}` : start ? `&start=${encodeURIComponent(start)}` : ''
            return `https://${host}/watch?v=${v2}${timeQuery}`
          }
        }
      }

      // Fallback: return original
      return val
    } catch {
      return val
    }
  }

  const isOwnProfile = currentUser?.username === username

  // Determine if background image is a YouTube URL
  const rawBg = profile?.background_image || ''
  const normalizedBg = normalizeMediaUrl(rawBg)
  const isYouTubeBg = isUrl(rawBg) && /youtube\.com|youtu\.be/.test(rawBg)

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
    }
  }, [username])

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
    } catch (error) {
      setError('Failed to load profile')
    } finally {
      setLoading(false)
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
      style={
        isYouTubeBg && videoBgEnabled && videoReady
          ? {
              backgroundColor: profile.background_color || '#000',
            }
          : {
              backgroundImage: profile.background_image && !isYouTubeBg
                ? `url(${profile.background_image})`
                : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundColor: profile.background_color || '#667eea',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundAttachment: 'fixed',
            }
      }
    >
      {/* Background YouTube video when background_image is a YouTube URL */}
      {isYouTubeBg && videoBgEnabled && (
        <div className="absolute inset-0 z-0">
          <ReactPlayer
            url={normalizedBg}
            width="100%"
            height="100%"
            playing
            loop
            muted={muted}
            playsinline
            controls={false}
            volume={0.6}
            config={{
              youtube: {
                playerVars: { autoplay: 1, controls: 0, modestbranding: 1, rel: 0, showinfo: 0, mute: 1, enablejsapi: 1, origin: window.location.origin },
                embedOptions: { host: 'https://www.youtube-nocookie.com' }
              },
            }}
            onReady={() => setVideoReady(true)}
            onError={() => setVideoBgEnabled(false)}
            style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
          />
        </div>
      )}
    {/* Matrix animation overlay (above video) */}
    <MatrixBackground />
      
    {/* Dark overlay for better readability, above video */}
    <div className="absolute inset-0 bg-black/20 z-10 pointer-events-none"></div>

      {/* Background audio control */}
      {isYouTubeBg && videoBgEnabled && videoReady && (
        <button
          onClick={() => setMuted((m) => !m)}
          className="fixed bottom-4 right-4 z-50 px-3 py-2 rounded-lg bg-black/50 text-white border border-white/20 backdrop-blur-md hover:bg-black/60 transition"
          aria-label={muted ? 'Unmute background video' : 'Mute background video'}
        >
          {muted ? '🔈 Unmute' : '🔊 Mute'}
        </button>
      )}

      {/* Main content with glassmorphism cards */}
  <div className="relative z-20 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Profile Card */}
          <div className="lg:col-span-1 order-1">
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow-2xl">
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
                        inlineSize: `${Math.min((profile.upload_count / 100) * 100, 100)}%`
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
                      style={{ inlineSize: `${Math.min(storagePercentage, 100)}%` }}
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

              {/* Removed inline music player; background YouTube video is handled globally */}
            </div>
          </div>

          {/* Content Cards */}
          <div className="lg:col-span-2 order-2 space-y-6">
            
            {/* Bio Card */}
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow-2xl">
              <h2 className="text-2xl font-bold text-white mb-4">About</h2>
              <p className="text-white/90 text-lg leading-relaxed">
                {profile.bio || 'No bio provided yet.'}
              </p>
            </div>

            {/* Social Links Card */}
            <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 border border-white/30 shadow-2xl">
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
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}