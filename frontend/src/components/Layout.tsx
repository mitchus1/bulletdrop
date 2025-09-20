import { ReactNode } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { Link } from 'react-router-dom'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout, isAuthenticated } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to={isAuthenticated ? "/dashboard" : "/"} className="text-xl font-bold text-gray-900 dark:text-white transition-colors duration-300">BulletDrop</Link>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <Link to="/dashboard" className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-300">
                    Dashboard
                  </Link>
                  <Link to="/uploads" className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-300">
                    Uploads
                  </Link>
                  <Link to={`/profile/${user?.username}`} className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-300">
                    Profile
                  </Link>
                  
                  {/* Enhanced Admin Status - Only show for admin users */}
                  {user?.is_admin && (
                    <Link 
                      to="/admin" 
                      className="relative group flex items-center space-x-2 px-3 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-500 dark:to-indigo-500 hover:from-purple-700 hover:to-indigo-700 dark:hover:from-purple-600 dark:hover:to-indigo-600 text-white font-medium transition-all duration-300 transform hover:scale-105 hover:shadow-lg"
                      title="Admin Dashboard"
                    >
                      {/* Animated Crown Icon */}
                      <svg 
                        className="w-5 h-5 text-yellow-300 group-hover:text-yellow-200 transition-all duration-300 animate-pulse" 
                        fill="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path d="M5 16L3 7l3.5 1L12 4l5.5 4L21 7l-2 9H5zm7-2.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
                      </svg>
                      
                      {/* Admin Text with Gradient */}
                      <span className="bg-gradient-to-r from-yellow-200 to-yellow-100 bg-clip-text text-transparent group-hover:from-yellow-100 group-hover:to-white transition-all duration-300">
                        Admin
                      </span>
                      
                      {/* Subtle Animation Ring */}
                      <div className="absolute -inset-1 bg-gradient-to-r from-purple-400 to-indigo-400 rounded-lg opacity-30 group-hover:opacity-50 transition-opacity duration-300 blur-sm"></div>
                      
                      {/* Floating Sparkles */}
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-300 rounded-full animate-ping opacity-75"></div>
                      <div className="absolute -bottom-1 -left-1 w-1.5 h-1.5 bg-purple-300 rounded-full animate-bounce delay-300 opacity-60"></div>
                    </Link>
                  )}
                  
                  {/* Theme Toggle Button */}
                  <button
                    onClick={toggleTheme}
                    className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-300 group"
                    title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
                  >
                    {theme === 'light' ? (
                      <svg className="w-5 h-5 text-gray-700 dark:text-gray-300 group-hover:text-yellow-500 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-gray-700 dark:text-gray-300 group-hover:text-yellow-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    )}
                  </button>
                  
                  <button
                    onClick={handleLogout}
                    className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-300"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-300">
                    Login
                  </Link>
                  <Link to="/register" className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors duration-300">
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="transition-colors duration-300">{children}</main>
    </div>
  )
}