import React, { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { apiService } from '../services/api'

const ShareX: React.FC = () => {
  const { token, isAuthenticated } = useAuth()
  const [hasApiKey, setHasApiKey] = useState<boolean>(false)
  const [apiKey, setApiKey] = useState<string | null>(null)
  const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'
  const origin = typeof window !== 'undefined' ? window.location.origin : ''

  const uploaderName = `${new URL(origin).hostname}`
  const uploadEndpoint = `${apiUrl}/api/uploads/sharex`

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const status = await apiService.getApiKeyStatus()
        if (!mounted) return
        setHasApiKey(status.has_api_key)
      } catch (e) {
        // ignore
      }
    }
    if (isAuthenticated) load()
    return () => { mounted = false }
  }, [isAuthenticated])

  const handleGenerateKey = async () => {
    try {
      const res = await apiService.generateApiKey()
      setHasApiKey(true)
      setApiKey(res.api_key)
    } catch (e) {
      console.error('Failed to generate API key', e)
    }
  }

  const handleRevokeKey = async () => {
    try {
      await apiService.revokeApiKey()
      setHasApiKey(false)
      setApiKey(null)
    } catch (e) {
      console.error('Failed to revoke API key', e)
    }
  }

  const generateSxcu = () => {
    const key = apiKey || (hasApiKey ? 'YOUR_API_KEY' : null)
    if (!key) return
    const sxcu = {
      Version: '17.0.0',
      Name: uploaderName,
      DestinationType: 'ImageUploader, FileUploader',
      RequestMethod: 'POST',
      RequestURL: uploadEndpoint,
      Parameters: {},
      Headers: hasApiKey ? { 'X-API-Key': key } : { Authorization: `Bearer ${token}` },
      Body: 'MultipartFormData',
      Arguments: {},
      FileFormName: 'file',
      URL: '{json:url}',
      ThumbnailURL: '{json:thumbnail_url}',
      DeletionURL: '{json:deletion_url}',
      ErrorMessage: '{json:detail}'
    }

    const blob = new Blob([JSON.stringify(sxcu, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${uploaderName}.sxcu`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
          <h1 className="text-3xl font-bold text-white mb-4">ShareX Integration</h1>
          <p className="text-blue-100 mb-6">
            Capture and upload screenshots instantly to your preferred domain using ShareX. Configure it once, then use your hotkey to upload in seconds.
          </p>

          <ol className="list-decimal list-inside space-y-3 text-blue-100">
            <li>
              In Settings, set your <span className="font-semibold text-white">Preferred Domain</span> — ShareX uploads will use this domain.
            </li>
            <li>
              {isAuthenticated ? (
                <>
                  Generate a long-lived <span className="font-semibold text-white">API Key</span> for ShareX or use your current session token.
                </>
              ) : (
                <>
                  <span className="font-semibold text-white">Sign in</span> to generate your personalized .sxcu uploader file.
                </>
              )}
            </li>
            <li>
              Open ShareX → Destinations → Custom Uploader Settings → Import → <span className="font-semibold text-white">Import from file</span> and select the downloaded .sxcu.
            </li>
            <li>
              In ShareX, go to Hotkey Settings and set <span className="font-semibold text-white">Capture region → Upload image to host</span> or your preferred workflow.
            </li>
          </ol>

          <div className="mt-8 flex flex-wrap gap-3 items-center">
            {isAuthenticated && (
              <>
                <button
                  onClick={handleGenerateKey}
                  className="px-5 py-3 rounded-lg text-white font-medium bg-emerald-600 hover:bg-emerald-700 transition-all shadow"
                >
                  {hasApiKey ? 'Regenerate API Key' : 'Generate API Key'}
                </button>
                {hasApiKey && (
                  <button
                    onClick={handleRevokeKey}
                    className="px-5 py-3 rounded-lg text-white font-medium bg-red-600 hover:bg-red-700 transition-all shadow"
                  >
                    Revoke API Key
                  </button>
                )}
                {apiKey && (
                  <div className="text-blue-100 text-sm break-all">
                    Your new API Key: <span className="text-white font-mono">{apiKey}</span>
                  </div>
                )}
              </>
            )}
            <button
              onClick={generateSxcu}
              disabled={!isAuthenticated || (!hasApiKey && !token)}
              className={`px-5 py-3 rounded-lg text-white font-medium transition-all ${
                isAuthenticated && (hasApiKey || token)
                  ? 'bg-indigo-600 hover:bg-indigo-700 shadow-lg hover:shadow-xl'
                  : 'bg-gray-500 cursor-not-allowed'
              }`}
              title={isAuthenticated ? 'Download ShareX uploader file' : 'Sign in to generate your uploader'}
            >
              Download .sxcu uploader
            </button>
            <a
              href="https://getsharex.com/"
              target="_blank"
              rel="noreferrer"
              className="px-5 py-3 rounded-lg bg-white/10 border border-white/20 text-white hover:bg-white/20 transition-all"
            >
              Get ShareX
            </a>
          </div>

          <div className="mt-8 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30 text-yellow-100">
            <div className="font-semibold mb-1">Security note</div>
            The .sxcu file includes credentials (API key or token) to authorize uploads. Keep it private. If it’s ever compromised, revoke your API key or log out to invalidate the session token.
          </div>

          <div className="mt-8 text-blue-100">
            <div className="font-semibold text-white mb-2">Advanced</div>
            <div className="text-sm">
              Endpoint: <code className="bg-black/30 px-2 py-1 rounded">POST {uploadEndpoint}</code>
              <br />
              Header: <code className="bg-black/30 px-2 py-1 rounded">X-API-Key: YOUR_API_KEY</code> or <code className="bg-black/30 px-2 py-1 rounded">Authorization: Bearer YOUR_TOKEN</code>
              <br />
              Form field: <code className="bg-black/30 px-2 py-1 rounded">file</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ShareX
