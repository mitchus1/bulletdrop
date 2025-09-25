import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { checkAdminAccess, getAdminStats, getAllUsers, getAllDomains, getRecentActivity, createDomain, updateDomain, deleteDomain } from '../services/admin';
import { useNavigate } from 'react-router-dom';
import AdminUserManagement from '../components/AdminUserManagement';
import AdminStatistics from '../components/AdminStatistics';
import SecurityDashboard from '../components/SecurityDashboard';

interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  verified_users: number;
  total_uploads: number;
  total_storage_used: number;
  total_domains: number;
  available_domains: number;
  premium_domains: number;
}

interface Domain {
  id: number;
  domain_name: string;
  display_name?: string;
  description?: string;
  is_available: boolean;
  is_premium: boolean;
  max_file_size: number;
  created_at: string;
  user_count: number;
  upload_count: number;
}

interface Activity {
  type: string;
  description: string;
  timestamp: string;
  user_id?: number;
  username?: string;
}

const AdminDashboard: React.FC = () => {
  const { theme } = useTheme();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hasAccess, setHasAccess] = useState(false);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'statistics' | 'users' | 'domains' | 'activity' | 'security'>('overview');
  
  // Domain management state
  const [showDomainModal, setShowDomainModal] = useState(false);
  const [editingDomain, setEditingDomain] = useState<Domain | null>(null);
  const [domainFormData, setDomainFormData] = useState({
    domain_name: '',
    display_name: '',
    description: '',
    is_available: true,
    is_premium: false,
    max_file_size: 10 * 1024 * 1024 // 10MB default
  });

  useEffect(() => {
    const checkAccess = async () => {
      const access = await checkAdminAccess();
      if (!access) {
        navigate('/dashboard');
        return;
      }
      setHasAccess(true);
      await loadData();
      setLoading(false);
    };

    checkAccess();
  }, [navigate]);

  const loadData = async () => {
    try {
            const [statsData, , domainsData, activitiesData] = await Promise.all([
        getAdminStats(),
        getAllUsers(), // Still call but don't use result since AdminUserManagement handles this
        getAllDomains(),
        getRecentActivity()
      ]);

      setStats(statsData as AdminStats);
      setDomains(domainsData as Domain[]);
      setActivities(activitiesData as Activity[]);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Domain management functions
  const handleCreateDomain = () => {
    setEditingDomain(null);
    setDomainFormData({
      domain_name: '',
      display_name: '',
      description: '',
      is_available: true,
      is_premium: false,
      max_file_size: 10 * 1024 * 1024
    });
    setShowDomainModal(true);
  };

  const handleEditDomain = (domain: Domain) => {
    setEditingDomain(domain);
    setDomainFormData({
      domain_name: domain.domain_name,
      display_name: domain.display_name || '',
      description: domain.description || '',
      is_available: domain.is_available,
      is_premium: domain.is_premium,
      max_file_size: domain.max_file_size
    });
    setShowDomainModal(true);
  };

  const handleSaveDomain = async () => {
    try {
      if (editingDomain) {
        // Update existing domain
        await updateDomain(editingDomain.id, {
          display_name: domainFormData.display_name,
          description: domainFormData.description,
          is_available: domainFormData.is_available,
          is_premium: domainFormData.is_premium,
          max_file_size: domainFormData.max_file_size
        });
      } else {
        // Create new domain
        await createDomain(domainFormData);
      }
      
      // Refresh domains list
      const domainsData = await getAllDomains();
      setDomains(domainsData as Domain[]);
      setShowDomainModal(false);
    } catch (error) {
      console.error('Failed to save domain:', error);
      alert('Failed to save domain. Please try again.');
    }
  };

  const handleDeleteDomain = async (domain: Domain) => {
    if (confirm(`Are you sure you want to delete domain "${domain.domain_name}"?`)) {
      try {
        await deleteDomain(domain.id);
        // Refresh domains list
        const domainsData = await getAllDomains();
        setDomains(domainsData as Domain[]);
      } catch (error) {
        console.error('Failed to delete domain:', error);
        alert('Failed to delete domain. Please try again.');
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className={`mt-4 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
            Loading admin dashboard...
          </p>
        </div>
      </div>
    );
  }

  if (!hasAccess) {
    return null; // Will redirect
  }

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            Admin Dashboard
          </h1>
          <p className={`mt-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Manage users, domains, and view system statistics
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { key: 'overview', label: 'Overview' },
              { key: 'statistics', label: 'Statistics' },
              { key: 'users', label: 'User Management' },
              { key: 'domains', label: 'Domains' },
              { key: 'activity', label: 'Activity' },
              { key: 'security', label: 'Security' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                  activeTab === tab.key
                    ? `border-blue-500 ${theme === 'dark' ? 'text-blue-400' : 'text-blue-600'}`
                    : `border-transparent ${theme === 'dark' ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'}`
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className={`p-6 rounded-lg shadow ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
                <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Users
                </h3>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Total</span>
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {stats.total_users}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Active</span>
                    <span className="font-semibold text-green-500">{stats.active_users}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Admins</span>
                    <span className="font-semibold text-blue-500">{stats.admin_users}</span>
                  </div>
                </div>
              </div>

              <div className={`p-6 rounded-lg shadow ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
                <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Storage
                </h3>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Total Used</span>
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {formatBytes(stats.total_storage_used)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Total Uploads</span>
                    <span className="font-semibold text-purple-500">{stats.total_uploads}</span>
                  </div>
                </div>
              </div>

              <div className={`p-6 rounded-lg shadow ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
                <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  Domains
                </h3>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Total</span>
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {stats.total_domains}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Available</span>
                    <span className="font-semibold text-green-500">{stats.available_domains}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Premium</span>
                    <span className="font-semibold text-yellow-500">{stats.premium_domains}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className={`p-6 rounded-lg shadow ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
              <h3 className={`text-lg font-medium mb-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                Recent Activity
              </h3>
              <div className="space-y-3">
                {activities.slice(0, 10).map((activity, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      activity.type === 'user_registered' ? 'bg-green-500' :
                      activity.type === 'upload' ? 'bg-blue-500' :
                      'bg-purple-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                        {activity.description}
                      </p>
                      <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>
                        {new Date(activity.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <AdminStatistics />
        )}

        {/* User Management Tab */}
        {activeTab === 'users' && (
          <AdminUserManagement />
        )}

        {/* Domains Tab */}
        {activeTab === 'domains' && (
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden`}>
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                Domain Management
              </h3>
              <button
                onClick={handleCreateDomain}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                Create Domain
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className={theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}>
                  <tr>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Domain
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Status
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Max Size
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Users
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Uploads
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}`}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${theme === 'dark' ? 'bg-gray-800 divide-gray-700' : 'bg-white divide-gray-200'}`}>
                  {domains.map((domain) => (
                    <tr key={domain.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                            {domain.domain_name}
                          </div>
                          {domain.display_name && (
                            <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                              {domain.display_name}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            domain.is_available ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                          }`}>
                            {domain.is_available ? 'Available' : 'Unavailable'}
                          </span>
                          {domain.is_premium && (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100">
                              Premium
                            </span>
                          )}
                        </div>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}`}>
                        {formatFileSize(domain.max_file_size)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}`}>
                        {domain.user_count}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-900'}`}>
                        {domain.upload_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleEditDomain(domain)}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteDomain(domain)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow`}>
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                System Activity (Last 7 Days)
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {activities.map((activity, index) => (
                  <div key={index} className={`flex items-start space-x-4 p-4 rounded-lg ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}`}>
                    <div className={`flex-shrink-0 w-3 h-3 rounded-full mt-1 ${
                      activity.type === 'user_registered' ? 'bg-green-500' :
                      activity.type === 'upload' ? 'bg-blue-500' :
                      'bg-purple-500'
                    }`}></div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {activity.description}
                      </p>
                      <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                        {new Date(activity.timestamp).toLocaleString()}
                        {activity.username && ` • ${activity.username}`}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <SecurityDashboard />
        )}
      </div>

      {/* Domain Modal */}
      {showDomainModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4`}>
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className={`text-lg font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {editingDomain ? 'Edit Domain' : 'Create New Domain'}
              </h3>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className={`block text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-1`}>
                  Domain Name
                </label>
                <input
                  type="text"
                  value={domainFormData.domain_name}
                  onChange={(e) => setDomainFormData({...domainFormData, domain_name: e.target.value})}
                  disabled={!!editingDomain}
                  className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'} ${editingDomain ? 'opacity-50 cursor-not-allowed' : ''}`}
                  placeholder="example.com"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-1`}>
                  Display Name
                </label>
                <input
                  type="text"
                  value={domainFormData.display_name}
                  onChange={(e) => setDomainFormData({...domainFormData, display_name: e.target.value})}
                  className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'}`}
                  placeholder="Friendly name"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-1`}>
                  Description
                </label>
                <textarea
                  value={domainFormData.description}
                  onChange={(e) => setDomainFormData({...domainFormData, description: e.target.value})}
                  rows={3}
                  className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'}`}
                  placeholder="Domain description"
                />
              </div>
              
              <div>
                <label className={`block text-sm font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} mb-1`}>
                  Max File Size (bytes)
                </label>
                <input
                  type="number"
                  value={domainFormData.max_file_size}
                  onChange={(e) => setDomainFormData({...domainFormData, max_file_size: parseInt(e.target.value) || 0})}
                  className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${theme === 'dark' ? 'bg-gray-700 text-white' : 'bg-white text-gray-900'}`}
                  placeholder="10485760"
                />
              </div>
              
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={domainFormData.is_available}
                    onChange={(e) => setDomainFormData({...domainFormData, is_available: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <span className={`ml-2 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Available
                  </span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={domainFormData.is_premium}
                    onChange={(e) => setDomainFormData({...domainFormData, is_premium: e.target.checked})}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <span className={`ml-2 text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Premium
                  </span>
                </label>
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
              <button
                onClick={() => setShowDomainModal(false)}
                className={`px-4 py-2 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-600 ${theme === 'dark' ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-white text-gray-700 hover:bg-gray-50'} transition-colors`}
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDomain}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
              >
                {editingDomain ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;