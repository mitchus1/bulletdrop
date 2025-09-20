import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useToast } from '../contexts/ToastContext'

interface Domain {
  id: number
  domain_name: string
  display_name: string
  description?: string
  is_available: boolean
  is_premium: boolean
}

interface ProfileData {
  bio?: string
  github_username?: string
  discord_username?: string
  telegram_username?: string
  instagram_username?: string
  background_image?: string
  background_color?: string
  favorite_song?: string
  preferred_domain_id?: number
}

interface AccountData {
  email: string
  username: string
}

interface PasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

interface OAuthStatus {
  is_oauth_user: boolean
  oauth_providers: string[]
  has_password: boolean
}

export default function Settings() {
  const { user, token } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const { success, error } = useToast()
  
  const [activeTab, setActiveTab] = useState('account')
  const [loading, setLoading] = useState(false)
  const [domainsLoading, setDomainsLoading] = useState(false)
  const [domains, setDomains] = useState<Domain[]>([])
  const [oauthStatus, setOauthStatus] = useState<OAuthStatus | null>(null)
  
  // Form states
  const [profileData, setProfileData] = useState<ProfileData>({})
  const [accountData, setAccountData] = useState<AccountData>({
    email: user?.email || '',
    username: user?.username || ''
  })
  const [passwordData, setPasswordData] = useState<PasswordData>({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  useEffect(() => {
    if (user) {
      setProfileData({
        bio: user.bio || '',
        github_username: user.github_username || '',
        discord_username: user.discord_username || '',
        telegram_username: user.telegram_username || '',
        instagram_username: user.instagram_username || '',
        background_image: user.background_image || '',
        background_color: user.background_color || '',
        favorite_song: user.favorite_song || '',
        preferred_domain_id: user.preferred_domain_id
      })
      setAccountData({
        email: user.email,
        username: user.username
      })
    }
  }, [user])

  useEffect(() => {
    if (token) {
      fetchDomains()
      fetchOAuthStatus()
    }
  }, [token])

  const fetchDomains = async () => {
    if (!token) return
    
    setDomainsLoading(true)
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/domains`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        // The API returns {domains: [...]} so we need to access data.domains
        const domainsArray = data.domains || data
        // Ensure data is an array
        setDomains(Array.isArray(domainsArray) ? domainsArray : [])
      } else {
        console.error('Failed to fetch domains:', response.status)
        setDomains([])
      }
    } catch (error) {
      console.error('Error fetching domains:', error)
      setDomains([])
    } finally {
      setDomainsLoading(false)
    }
  }

  const fetchOAuthStatus = async () => {
    if (!token) return
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/users/me/oauth-status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setOauthStatus(data)
      }
    } catch (err) {
      console.error('Failed to fetch OAuth status:', err)
    }
  }

  const updateProfile = async () => {
    if (!token) return
    
    setLoading(true)
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/users/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      })

      if (response.ok) {
        success('Profile updated successfully!')
      } else {
        throw new Error('Failed to update profile')
      }
    } catch (err) {
      error('Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const updateAccount = async () => {
    if (!token) return
    
    setLoading(true)
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/users/me/account`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(accountData),
      })

      if (response.ok) {
        success('Account updated successfully!')
      } else {
        throw new Error('Failed to update account')
      }
    } catch (err) {
      error('Failed to update account')
    } finally {
      setLoading(false)
    }
  }

  const changePassword = async () => {
    if (!token) return
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      error('Passwords do not match')
      return
    }

    if (passwordData.new_password.length < 6) {
      error('Password must be at least 6 characters')
      return
    }

    // For OAuth users, current password is not required
    const isOAuthUser = oauthStatus?.is_oauth_user || false
    if (!isOAuthUser && !passwordData.current_password) {
      error('Current password is required')
      return
    }
    
    setLoading(true)
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      const body: any = {
        new_password: passwordData.new_password
      }
      
      // Only include current_password if it's provided or if user is not an OAuth user
      if (passwordData.current_password || !isOAuthUser) {
        body.current_password = passwordData.current_password
      }
      
      const response = await fetch(`${apiUrl}/users/me/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })

      if (response.ok) {
        const result = await response.json()
        success(result.message || 'Password updated successfully!')
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: ''
        })
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to change password')
      }
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'account', label: 'Account', icon: '👤' },
    { id: 'profile', label: 'Profile', icon: '✏️' },
    { id: 'appearance', label: 'Appearance', icon: '🎨' },
    { id: 'security', label: 'Security', icon: '🔒' },
  ]

  const isPremiumDomain = (domain: Domain) => domain.is_premium && !user?.is_premium && !user?.is_admin

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-8">
            <h1 className="text-3xl font-bold text-white">Settings</h1>
            <p className="text-blue-100 mt-2">Manage your account and customize your experience</p>
          </div>

          <div className="flex flex-col lg:flex-row">
            {/* Sidebar */}
            <div className="lg:w-64 bg-gray-50 dark:bg-gray-700 border-r border-gray-200 dark:border-gray-600">
              <nav className="p-4 space-y-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-4 py-3 text-left rounded-lg transition-colors duration-200 ${
                      activeTab === tab.id
                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-l-4 border-blue-500'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
                    }`}
                  >
                    <span className="text-xl">{tab.icon}</span>
                    <span className="font-medium">{tab.label}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Content */}
            <div className="flex-1 p-6">
              {/* Account Tab */}
              {activeTab === 'account' && (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Account Information</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Username
                        </label>
                        <input
                          type="text"
                          value={accountData.username}
                          onChange={(e) => setAccountData(prev => ({ ...prev, username: e.target.value }))}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Email
                        </label>
                        <input
                          type="email"
                          value={accountData.email}
                          onChange={(e) => setAccountData(prev => ({ ...prev, email: e.target.value }))}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                    </div>
                    <button
                      onClick={updateAccount}
                      disabled={loading}
                      className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
                    >
                      {loading ? 'Updating...' : 'Update Account'}
                    </button>
                  </div>

                  {/* Premium Status */}
                  <div className="border-t border-gray-200 dark:border-gray-600 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Premium Status</h3>
                    <div className="flex items-center space-x-4">
                      {user?.is_premium ? (
                        <div className="flex items-center space-x-2 text-yellow-600 dark:text-yellow-400">
                          <span className="text-2xl">👑</span>
                          <span className="font-medium">Premium Active</span>
                          {user.premium_expires_at && (
                            <span className="text-sm text-gray-500">
                              (Expires: {new Date(user.premium_expires_at).toLocaleDateString()})
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
                          <span className="text-2xl">🆓</span>
                          <span className="font-medium">Free Account</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Profile Information</h2>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Bio
                    </label>
                    <textarea
                      value={profileData.bio || ''}
                      onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                      rows={4}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      placeholder="Tell us about yourself..."
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        GitHub Username
                      </label>
                      <input
                        type="text"
                        value={profileData.github_username || ''}
                        onChange={(e) => setProfileData(prev => ({ ...prev, github_username: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        placeholder="octocat"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Discord Username
                      </label>
                      <input
                        type="text"
                        value={profileData.discord_username || ''}
                        onChange={(e) => setProfileData(prev => ({ ...prev, discord_username: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        placeholder="username#1234"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Telegram Username
                      </label>
                      <input
                        type="text"
                        value={profileData.telegram_username || ''}
                        onChange={(e) => setProfileData(prev => ({ ...prev, telegram_username: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        placeholder="@username"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Instagram Username
                      </label>
                      <input
                        type="text"
                        value={profileData.instagram_username || ''}
                        onChange={(e) => setProfileData(prev => ({ ...prev, instagram_username: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        placeholder="username"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Favorite Song
                    </label>
                    <input
                      type="text"
                      value={profileData.favorite_song || ''}
                      onChange={(e) => setProfileData(prev => ({ ...prev, favorite_song: e.target.value }))}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      placeholder="Artist - Song Title"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Preferred Upload Domain
                    </label>
                    <select
                      value={profileData.preferred_domain_id || ''}
                      onChange={(e) => setProfileData(prev => ({ ...prev, preferred_domain_id: e.target.value ? Number(e.target.value) : undefined }))}
                      disabled={domainsLoading}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white disabled:opacity-50"
                    >
                      <option value="">{domainsLoading ? 'Loading domains...' : 'Default'}</option>
                      {!domainsLoading && (domains || []).map((domain) => (
                        <option
                          key={domain.id}
                          value={domain.id}
                          disabled={isPremiumDomain(domain)}
                        >
                          {domain.display_name}
                          {domain.is_premium && ' 👑'}
                          {isPremiumDomain(domain) && ' (Premium Required)'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={updateProfile}
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
                  >
                    {loading ? 'Updating...' : 'Update Profile'}
                  </button>
                </div>
              )}

              {/* Appearance Tab */}
              {activeTab === 'appearance' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Appearance</h2>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Theme
                    </label>
                    <div className="flex items-center space-x-4">
                      <button
                        onClick={toggleTheme}
                        className="flex items-center space-x-3 px-6 py-3 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                      >
                        {theme === 'light' ? (
                          <>
                            <span className="text-2xl">🌙</span>
                            <span>Switch to Dark Mode</span>
                          </>
                        ) : (
                          <>
                            <span className="text-2xl">☀️</span>
                            <span>Switch to Light Mode</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Background Image URL
                    </label>
                    <input
                      type="url"
                      value={profileData.background_image || ''}
                      onChange={(e) => setProfileData(prev => ({ ...prev, background_image: e.target.value }))}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      placeholder="https://example.com/image.jpg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Background Color
                    </label>
                    <div className="flex items-center space-x-4">
                      <input
                        type="color"
                        value={profileData.background_color || '#000000'}
                        onChange={(e) => setProfileData(prev => ({ ...prev, background_color: e.target.value }))}
                        className="w-16 h-10 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer"
                      />
                      <input
                        type="text"
                        value={profileData.background_color || ''}
                        onChange={(e) => setProfileData(prev => ({ ...prev, background_color: e.target.value }))}
                        className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        placeholder="#000000"
                      />
                    </div>
                  </div>

                  <button
                    onClick={updateProfile}
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors duration-200"
                  >
                    {loading ? 'Updating...' : 'Update Appearance'}
                  </button>
                </div>
              )}

              {/* Security Tab */}
              {activeTab === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Security</h2>
                  
                  {/* Show OAuth info if applicable */}
                  {oauthStatus?.is_oauth_user && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                      <div className="flex items-center">
                        <span className="text-blue-600 dark:text-blue-400 text-xl mr-3">ℹ️</span>
                        <div>
                          <h4 className="font-medium text-blue-800 dark:text-blue-200">OAuth Account</h4>
                          <p className="text-blue-700 dark:text-blue-300 text-sm">
                            You signed up with {oauthStatus.oauth_providers.join(', ')}. 
                            {!oauthStatus.has_password ? 
                              ' Set a password to enable password-based login.' : 
                              ' You already have a password set. To change it, enter your current password below.'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <div className="flex items-center">
                      <span className="text-yellow-600 dark:text-yellow-400 text-xl mr-3">⚠️</span>
                      <div>
                        <h4 className="font-medium text-yellow-800 dark:text-yellow-200">
                          {oauthStatus?.is_oauth_user && !oauthStatus.has_password ? 'Set Password' : 'Password Change'}
                        </h4>
                        <p className="text-yellow-700 dark:text-yellow-300 text-sm">
                          Make sure to use a strong password with at least 6 characters.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-6">
                    {/* Only show current password field for non-OAuth users or OAuth users who already have a password */}
                    {(!oauthStatus?.is_oauth_user || oauthStatus?.has_password) && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Current Password
                        </label>
                        <input
                          type="password"
                          value={passwordData.current_password}
                          onChange={(e) => setPasswordData(prev => ({ ...prev, current_password: e.target.value }))}
                          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                    )}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={passwordData.confirm_password}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, confirm_password: e.target.value }))}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>

                  <button
                    onClick={changePassword}
                    disabled={
                      loading || 
                      !passwordData.new_password || 
                      !passwordData.confirm_password ||
                      // For non-OAuth users or OAuth users with existing password, require current password
                      ((!oauthStatus?.is_oauth_user || oauthStatus?.has_password) && !passwordData.current_password)
                    }
                    className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors duration-200"
                  >
                    {loading ? 
                      (oauthStatus?.is_oauth_user && !oauthStatus?.has_password ? 'Setting...' : 'Changing...') : 
                      (oauthStatus?.is_oauth_user && !oauthStatus?.has_password ? 'Set Password' : 'Change Password')
                    }
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}