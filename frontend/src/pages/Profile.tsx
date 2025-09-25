import { useState, useEffect, useMemo, useCallback } from 'react'
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
  matrix_effect_enabled?: boolean
}

// (removed Domain interface; editing and domain selection moved to Settings)

// Advanced Matrix rain animation component
const MatrixBackground = () => {
  const [columns, setColumns] = useState(0)
  const [windowHeight, setWindowHeight] = useState(0)

  useEffect(() => {
    const updateDimensions = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      // Calculate columns based on screen width (approx 40px per column)
      const columnCount = Math.floor(width / 40)
      setColumns(columnCount)
      setWindowHeight(height)
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Calculate characters per column based on screen height
  const charsPerColumn = Math.floor(windowHeight / 20) + 10

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-40">
      {Array.from({ length: columns }).map((_, i) => {
        // More varied positioning with some randomness
        const basePosition = (i / columns) * 100
        const randomOffset = (Math.random() - 0.5) * 5
        const position = Math.max(0, Math.min(95, basePosition + randomOffset))
        
        // More varied animation speeds and delays
        const animationDuration = 2 + Math.random() * 4 // 2-6 seconds
        const animationDelay = Math.random() * 6 // 0-6 seconds delay
        const opacity = 0.5 + Math.random() * 0.5 // Varied opacity

        return (
          <div
            key={`${i}-${columns}`} // Key includes columns to force re-render on resize
            className="absolute text-green-400 font-mono text-xs select-none"
            style={{
              left: `${position}%`,
              top: '-50vh',
              opacity: opacity,
              animation: `matrixRain ${animationDuration}s linear infinite`,
              animationDelay: `${animationDelay}s`,
              fontSize: `${10 + Math.random() * 4}px`, // Varied font sizes
              transform: `rotate(${(Math.random() - 0.5) * 4}deg)` // Slight rotation
            }}
          >
            {Array.from({ length: charsPerColumn }).map((_, j) => {
              // Mix of different character sets for variety
              const charSets = [
                () => String.fromCharCode(0x30A0 + Math.random() * 96), // Katakana
                () => String.fromCharCode(0x0030 + Math.random() * 10), // Numbers
                () => String.fromCharCode(0x0041 + Math.random() * 26), // Letters
                () => String.fromCharCode(0x25A0 + Math.random() * 32), // Geometric shapes
              ]
              const randomCharSet = charSets[Math.floor(Math.random() * charSets.length)]
              
              return (
                <div 
                  key={j} 
                  className="block leading-tight"
                  style={{
                    opacity: Math.max(0.1, 1 - (j / charsPerColumn) * 0.8), // Fade towards bottom
                    animationDelay: `${j * 0.1}s` // Stagger character appearance
                  }}
                >
                  {randomCharSet()}
                </div>
              )
            })}
          </div>
        )
      })}
      
      {/* Additional faster rain drops for more density */}
      {Array.from({ length: Math.floor(columns * 0.3) }).map((_, i) => {
        const position = Math.random() * 100
        const animationDuration = 1 + Math.random() * 2 // Faster drops
        const animationDelay = Math.random() * 8
        
        return (
          <div
            key={`fast-${i}-${columns}`}
            className="absolute text-green-300 font-mono text-xs select-none"
            style={{
              left: `${position}%`,
              top: '-30vh',
              opacity: 0.6,
              animation: `matrixRain ${animationDuration}s linear infinite`,
              animationDelay: `${animationDelay}s`,
              fontSize: '8px',
              filter: 'blur(0.5px)'
            }}
          >
            {Array.from({ length: 5 }).map((_, j) => (
              <div key={j} className="block">
                •
              </div>
            ))}
          </div>
        )
      })}
    </div>
  )
};

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

  // Memoize computed values to prevent unnecessary re-renders
  const isOwnProfile = useMemo(() => {
    return currentUser?.username === username;
  }, [currentUser?.username, username]);

  const { normalizedBg, isYouTubeBg } = useMemo(() => {
    const rawBg = profile?.background_image || '';
    const normalizedBg = normalizeMediaUrl(rawBg);
    const isYouTubeBg = isUrl(rawBg) && /youtube\.com|youtu\.be/.test(rawBg);
    return { normalizedBg, isYouTubeBg };
  }, [profile?.background_image]);

  // Memoize profile ID to prevent useProfileViewTracking from re-firing
  const profileId = useMemo(() => profile?.id, [profile?.id]);

  // Track profile views (only for profiles that aren't the current user's own profile)
  useProfileViewTracking(
    profileId,
    {
      enabled: !isOwnProfile && !!profileId,
      delay: 3000 // 3 second delay for profile views
    }
  );


  // Memoize fetchProfile to prevent unnecessary re-renders
  const fetchProfile = useCallback(async () => {
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
  }, [username]); // Only re-create when username changes

  useEffect(() => {
    if (username) {
      fetchProfile()
    }
  }, [username]) // fetchProfile is stable now


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
    {/* Matrix animation overlay (above video) - only if enabled */}
    {profile?.matrix_effect_enabled !== false && <MatrixBackground />}
      
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
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-6 border border-gray-700/50 shadow-lg">
              {/* Avatar */}
              <div className="text-center mb-6">
                {profile.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt={profile.username}
                    className="w-28 h-28 rounded-xl mx-auto border border-gray-600/50 shadow-lg"
                  />
                ) : (
                  <div className="w-28 h-28 rounded-xl bg-gray-800/60 border border-gray-600/50 flex items-center justify-center mx-auto shadow-lg">
                    <span className="text-gray-200 font-medium text-3xl">
                      {profile.username.charAt(0).toUpperCase()}
                      
                    </span>
                  </div>
                )}
                <h1 className="text-2xl font-medium text-gray-100 mt-4">
                  {profile.username}
                </h1>
                {/* Discord username display (non-clickable) */}
                {profile.discord_username && (
                  <div className="flex items-center justify-center space-x-2 text-sm text-gray-400">
                    <svg className="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.317 4.492c-1.53-.69-3.17-1.2-4.885-1.49a.075.075 0 0 0-.079.036c-.21.369-.444.85-.608 1.23a18.566 18.566 0 0 0-5.487 0 12.36 12.36 0 0 0-.617-1.23A.077.077 0 0 0 8.562 3c-1.714.29-3.354.8-4.885 1.491a.07.07 0 0 0-.032.027C.533 9.093-.32 13.555.099 17.961a.08.08 0 0 0 .031.055 20.03 20.03 0 0 0 5.993 2.98.078.078 0 0 0 .084-.026 13.83 13.83 0 0 0 1.226-1.963.074.074 0 0 0-.041-.104 13.201 13.201 0 0 1-1.872-.878.075.075 0 0 1-.008-.125c.126-.093.252-.19.372-.287a.075.075 0 0 1 .078-.01c3.927 1.764 8.18 1.764 12.061 0a.075.075 0 0 1 .079.009c.12.098.246.195.372.288a.075.075 0 0 1-.006.125c-.598.344-1.22.635-1.873.877a.075.075 0 0 0-.041.105c.36.687.772 1.341 1.225 1.962a.077.077 0 0 0 .084.028 19.963 19.963 0 0 0 6.002-2.981.076.076 0 0 0 .032-.054c.5-5.094-.838-9.52-3.549-13.442a.06.06 0 0 0-.031-.028zM8.02 15.278c-1.182 0-2.157-1.069-2.157-2.38 0-1.312.956-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.956 2.38-2.157 2.38zm7.975 0c-1.183 0-2.157-1.069-2.157-2.38 0-1.312.955-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.946 2.38-2.157 2.38z"/>
                    </svg>
                    <span className="font-mono text-indigo-300">{profile.discord_username}</span>
                  </div>
                )}
                <p className="text-gray-400 text-sm mt-1">
                  Member since {new Date(profile.created_at).toLocaleDateString()}
                </p>
              </div>

              {/* Stats */}
              <div className="space-y-5 mb-6">
                <div>
                  <div className="flex justify-between text-sm mb-2 text-gray-300">
                    <span>Files uploaded</span>
                    <span className="font-medium text-gray-200">{profile.upload_count}</span>
                  </div>
                  <div className="w-full bg-gray-800/60 rounded-lg h-1.5">
                    <div 
                      className="bg-gradient-to-r from-blue-500/80 to-cyan-500/80 h-1.5 rounded-lg transition-all duration-500"
                      style={{ 
                        width: `${Math.min((profile.upload_count / 100) * 100, 100)}%`
                      }}
                    ></div>
                  </div>
                </div>

                {/* Profile Views */}
                <div>
                  <div className="flex justify-between text-sm mb-2 text-gray-300">
                    <span>Profile views</span>
                  </div>
                  {/* Only show ViewCounter for other users' profiles to prevent double analytics requests */}
                  {!isOwnProfile && (
                    <ViewCounter
                      contentType="profile"
                      contentId={profile.id}
                      showDetails={true}
                      className="text-gray-400"
                    />
                  )}
                  {/* For own profile, show a simple message without making additional requests */}
                  {isOwnProfile && (
                    <div className="text-gray-400 text-sm">
                      <span>👁 Profile views are tracked for other users</span>
                    </div>
                  )}
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-2 text-gray-300">
                    <span>Storage used</span>
                    <span className="font-medium text-gray-200">
                      {formatBytes(profile.storage_used)} / {formatBytes(profile.storage_limit)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-800/60 rounded-lg h-1.5">
                    <div
                      className="bg-gradient-to-r from-emerald-500/80 to-teal-500/80 h-1.5 rounded-lg transition-all duration-500"
                      style={{ width: `${Math.min(storagePercentage, 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {storagePercentage.toFixed(1)}% used
                  </div>
                </div>
                
                {/* Premium Status */}
                <div>
                  <div className="flex justify-between items-center text-sm mb-2 text-gray-300">
                    <span>Account Status</span>
                    <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${
                      profile.is_premium 
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                        : 'bg-gray-700/60 text-gray-400 border border-gray-600/40'
                    }`}>
                      {profile.is_premium ? '👑 Premium' : 'Free'}
                    </span>
                  </div>
                  {profile.is_premium && profile.premium_expires_at && (
                    <div className="text-xs text-gray-500">
                      Premium expires: {new Date(profile.premium_expires_at).toLocaleDateString()}
                    </div>
                  )}
                  {!profile.is_premium && (
                    <div className="text-xs text-gray-500">
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
            
            {/* About Card with integrated social links */}
            <div className="bg-black/30 backdrop-blur-sm rounded-lg p-6 border border-gray-700/50 shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-medium text-gray-100">About</h2>
                
                {/* Social Media Icons */}
                <div className="flex items-center space-x-3">
                  {/* GitHub */}
                  {profile.github_username && (
                    <a
                      href={`https://github.com/${profile.github_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-center justify-center w-9 h-9 rounded-lg bg-gray-800/60 border border-gray-600/40 hover:border-gray-500/60 hover:bg-gray-700/60 transition-all duration-200"
                      title={`@${profile.github_username} on GitHub`}
                    >
                      <svg className="w-4 h-4 text-gray-300 group-hover:text-white transition-colors" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                      </svg>
                    </a>
                  )}

                  {/* Discord */}
                  {profile.discord_username && (
                    <div
                      className="group flex items-center justify-center w-9 h-9 rounded-lg bg-gray-800/60 border border-gray-600/40 hover:border-indigo-500/60 hover:bg-indigo-900/40 transition-all duration-200 cursor-default"
                      title={`${profile.discord_username} on Discord`}
                    >
                      <svg className="w-4 h-4 text-gray-300 group-hover:text-indigo-300 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M20.317 4.492c-1.53-.69-3.17-1.2-4.885-1.49a.075.075 0 0 0-.079.036c-.21.369-.444.85-.608 1.23a18.566 18.566 0 0 0-5.487 0 12.36 12.36 0 0 0-.617-1.23A.077.077 0 0 0 8.562 3c-1.714.29-3.354.8-4.885 1.491a.07.07 0 0 0-.032.027C.533 9.093-.32 13.555.099 17.961a.08.08 0 0 0 .031.055 20.03 20.03 0 0 0 5.993 2.98.078.078 0 0 0 .084-.026 13.83 13.83 0 0 0 1.226-1.963.074.074 0 0 0-.041-.104 13.201 13.201 0 0 1-1.872-.878.075.075 0 0 1-.008-.125c.126-.093.252-.19.372-.287a.075.075 0 0 1 .078-.01c3.927 1.764 8.18 1.764 12.061 0a.075.075 0 0 1 .079.009c.12.098.246.195.372.288a.075.075 0 0 1-.006.125c-.598.344-1.22.635-1.873.877a.075.075 0 0 0-.041.105c.36.687.772 1.341 1.225 1.962a.077.077 0 0 0 .084.028 19.963 19.963 0 0 0 6.002-2.981.076.076 0 0 0 .032-.054c.5-5.094-.838-9.52-3.549-13.442a.06.06 0 0 0-.031-.028zM8.02 15.278c-1.182 0-2.157-1.069-2.157-2.38 0-1.312.956-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.956 2.38-2.157 2.38zm7.975 0c-1.183 0-2.157-1.069-2.157-2.38 0-1.312.955-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.946 2.38-2.157 2.38z"/>
                      </svg>
                    </div>
                  )}

                  {/* Telegram */}
                  {profile.telegram_username && (
                    <a
                      href={`https://t.me/${profile.telegram_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-center justify-center w-9 h-9 rounded-lg bg-gray-800/60 border border-gray-600/40 hover:border-blue-500/60 hover:bg-blue-900/40 transition-all duration-200"
                      title={`@${profile.telegram_username} on Telegram`}
                    >
                      <svg className="w-4 h-4 text-gray-300 group-hover:text-blue-300 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 0C5.374 0 0 5.373 0 12s5.374 12 12 12 12-5.373 12-12S18.626 0 12 0zm5.568 8.16c-.169 1.858-.896 6.728-.896 6.728-.377 2.655-1.407 3.113-2.707 1.67-.634-.717-1.64-1.366-3.137-2.27-1.507-.903-1.267-1.39-.634-2.266.17-.244.715-.774 1.931-1.931 1.216-1.157 1.337-1.3.91-1.3-.427 0-2.022 1.216-4.046 2.692-2.025 1.476-3.464 2.233-4.045 2.23-.581-.004-1.631-.437-2.718-.849-1.088-.412-1.952-.63-1.882-1.33.07-.7 1.224-1.413 3.463-2.14C7.918 9.095 9.832 8.256 12 7.68c2.168-.576 4.082-.415 5.568 2.48z"/>
                      </svg>
                    </a>
                  )}

                  {/* Instagram */}
                  {profile.instagram_username && (
                    <a
                      href={`https://instagram.com/${profile.instagram_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-center justify-center w-9 h-9 rounded-lg bg-gray-800/60 border border-gray-600/40 hover:border-pink-500/60 hover:bg-pink-900/40 transition-all duration-200"
                      title={`@${profile.instagram_username} on Instagram`}
                    >
                      <svg className="w-4 h-4 text-gray-300 group-hover:text-pink-300 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                      </svg>
                    </a>
                  )}
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <p className="text-gray-200 leading-relaxed">
                    {profile.bio || 'No bio provided yet.'}
                  </p>
                </div>
                
                
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}