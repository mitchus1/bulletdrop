import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ToastProvider } from './contexts/ToastContext'
import { ToastContainer } from './components/Toast'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Uploads from './pages/Uploads'
import Profile from './pages/Profile'
import Settings from './pages/Settings'
import Premium from './pages/Premium'
import PremiumSuccess from './pages/PremiumSuccess'
import AdminDashboard from './pages/AdminDashboard'
import OAuthCallback from './pages/OAuthCallback'
import ShareX from './pages/ShareX'

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/auth/:provider/callback" element={<OAuthCallback />} />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } />
                <Route path="/uploads" element={
                  <ProtectedRoute>
                    <Uploads />
                  </ProtectedRoute>
                } />
                <Route path="/settings" element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                } />
                <Route path="/premium" element={
                  <ProtectedRoute>
                    <Premium />
                  </ProtectedRoute>
                } />
                <Route path="/premium/success" element={
                  <ProtectedRoute>
                    <PremiumSuccess />
                  </ProtectedRoute>
                } />
                <Route path="/sharex" element={
                  <ProtectedRoute>
                    <ShareX />
                  </ProtectedRoute>
                } />
                <Route path="/admin" element={
                  <ProtectedRoute>
                    <AdminDashboard />
                  </ProtectedRoute>
                } />
                <Route path="/profile/:username" element={<Profile />} />
              </Routes>
              <ToastContainer />
            </Layout>
          </Router>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  )
}

export default App