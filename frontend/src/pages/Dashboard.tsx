import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import { Upload } from '../types/upload';
import FileUpload from '../components/FileUpload';
import ViewCounter from '../components/ViewCounter';
import TrendingContent from '../components/TrendingContent';
import { useFileViewTracking } from '../hooks/useViewTracking';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [recentUploads, setRecentUploads] = useState<Upload[]>([]);
  const [showUploadWidget, setShowUploadWidget] = useState(false);

  useEffect(() => {
    if (user) {
      loadRecentUploads();
    }
  }, [user]);

  const loadRecentUploads = async () => {
    try {
      const response = await apiService.getUserUploads(1, 5);
      setRecentUploads(response.uploads);
    } catch (error) {
      console.error('Failed to load recent uploads:', error);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const handleUploadComplete = () => {
    loadRecentUploads(); // Refresh recent uploads
    setShowUploadWidget(false);
  };

  const formatStorageSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Component for individual upload cards with view tracking
  const UploadCard = ({ upload }: { upload: Upload }) => {
    // Track views when user clicks to view the file
    useFileViewTracking(upload.id, { enabled: false }); // Disabled auto-tracking for dashboard

    const handleViewClick = () => {
      // Manually track when user actually views the file
      // This prevents accidental view tracking from just browsing dashboard
      window.open(upload.upload_url, '_blank');
    };

    return (
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 transform transition-all duration-300 hover:scale-105 hover:shadow-lg">
        <div className="flex items-center space-x-3">
          {upload.mime_type.startsWith('image/') ? (
            <img
              src={upload.upload_url}
              alt={upload.original_filename}
              className="h-10 w-10 rounded object-cover"
            />
          ) : (
            <div className="h-10 w-10 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center">
              <svg className="h-6 w-6 text-gray-400 dark:text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {upload.original_filename}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(upload.created_at)}
            </p>
            {/* Use ViewCounter component */}
            <ViewCounter 
              contentType="file" 
              contentId={upload.id} 
              compact={true} 
              className="mt-1"
            />
          </div>
        </div>
        <div className="mt-2 flex space-x-2">
          <button
            onClick={() => navigator.clipboard.writeText(upload.upload_url)}
            className="text-xs text-blue-600 hover:text-blue-500 transition-colors duration-300"
          >
            Copy URL
          </button>
          <button
            onClick={handleViewClick}
            className="text-xs text-green-600 hover:text-green-500 transition-colors duration-300"
          >
            View
          </button>
        </div>
      </div>
    );
  };

  const storagePercentage = user ? (user.storage_used / user.storage_limit) * 100 : 0;

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300">
      <div className="md:flex md:items-center md:justify-between mb-8">
        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user?.username}!
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your uploads and account settings
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={handleLogout}
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Logout
          </button>
        </div>
      </div>

  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Upload Count */}
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:scale-105">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Total Uploads
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-white">
                    {user?.upload_count || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Storage Used */}
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:scale-105">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                  </svg>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Storage Used
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-white">
                    {user ? formatStorageSize(user.storage_used) : '0 MB'} / {user ? formatStorageSize(user.storage_limit) : '0 MB'}
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-3">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${Math.min(storagePercentage, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{storagePercentage.toFixed(1)}% used</p>
            </div>
          </div>
        </div>

        {/* Account Status */}
        <div className="bg-white dark:bg-gray-800 overflow-hidden shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:scale-105">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {user?.is_admin ? (
                  <Link
                    to="/admin"
                    className="group relative w-8 h-8 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-md flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-lg cursor-pointer"
                    title="Click to access Admin Dashboard"
                  >
                    <svg className="w-5 h-5 text-yellow-300 group-hover:text-yellow-200 transition-all duration-300 animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M5 16L3 7l3.5 1L12 4l5.5 4L21 7l-2 9H5zm7-2.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
                    </svg>
                    <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-yellow-400 rounded-full animate-ping opacity-75"></div>
                    <div className="absolute -bottom-1 -left-1 w-1 h-1 bg-purple-300 rounded-full animate-bounce delay-300 opacity-60"></div>
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-400 to-indigo-400 rounded-md opacity-30 group-hover:opacity-50 transition-opacity duration-300 blur-sm"></div>
                  </Link>
                ) : (
                  <div className={`w-8 h-8 ${user?.is_verified ? 'bg-green-500' : 'bg-yellow-500'} rounded-md flex items-center justify-center`}>
                    <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Account Status
                  </dt>
                  <dd className="text-lg font-medium text-gray-900 dark:text-white flex items-center space-x-2">
                    {user?.is_admin ? (
                      <Link
                        to="/admin"
                        className="group flex items-center space-x-2 cursor-pointer transition-all duration-300 hover:scale-105"
                        title="Click to access Admin Dashboard"
                      >
                        <span className="bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent font-bold group-hover:from-purple-500 group-hover:to-indigo-500 transition-all duration-300">
                          Admin
                        </span>
                        <span className="text-yellow-500 animate-bounce text-sm">👑</span>
                      </Link>
                    ) : (
                      <span>{user?.is_verified ? 'Verified' : 'Unverified'}</span>
                    )}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:shadow-xl">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => setShowUploadWidget(!showUploadWidget)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 hover:scale-105"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              Upload File
            </button>
            <Link
              to="/uploads"
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 hover:scale-105"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
              </svg>
              View All Uploads
            </Link>
            <Link
              to="/sharex"
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-300 hover:scale-105"
              title="Set up ShareX to upload screenshots here"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M5 3a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2V5a2 2 0 00-2-2H5zm8 4h6a2 2 0 012 2v8a2 2 0 01-2 2h-8a2 2 0 01-2-2v-6"/>
              </svg>
              ShareX Setup
            </Link>
          </div>
        </div>
      </div>

      {/* Upload Widget */}
      {showUploadWidget && (
        <div className="mt-8 bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:shadow-xl">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white mb-4">
              Upload Files
            </h3>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        </div>
      )}

      {/* Recent Uploads */}
      <div className="mt-8 bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:shadow-xl">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Recent Uploads
            </h3>
            {recentUploads.length > 0 && (
              <Link
                to="/uploads"
                className="text-sm text-blue-600 hover:text-blue-500 transition-colors duration-300"
              >
                View all →
              </Link>
            )}
          </div>

          {recentUploads.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No uploads yet</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Get started by uploading your first file.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentUploads.map((upload) => (
                <UploadCard key={upload.id} upload={upload} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Trending Content */}
      <div className="mt-8 bg-white dark:bg-gray-800 shadow-lg dark:shadow-gray-900 rounded-lg transform transition-all duration-300 hover:shadow-xl">
        <div className="px-4 py-5 sm:p-6">
          <TrendingContent 
            timePeriod="24h"
            maxItems={5}
            showProfiles={true}
            showFiles={true}
          />
        </div>
      </div>
    </div>
  );
}