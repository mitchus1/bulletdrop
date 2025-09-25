import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getSecurityEvents, getSecurityStats, getSecuritySummary, getSecurityEventTypes, testSecurityAlert, clearSecurityEvents } from '../services/admin';
import { useToast } from '../contexts/ToastContext';

interface SecurityEvent {
  event_type: string;
  timestamp: string;
  ip_address: string;
  user_id?: number;
  username?: string;
  details?: any;
  severity: string;
  user_agent?: string;
  endpoint?: string;
  request_method?: string;
}

interface SecurityStats {
  [key: string]: number;
  total_recent_events: number;
}

interface SecuritySummary {
  status: string;
  total_events_today: number;
  high_severity_events_last_hour: number;
  top_event_types: { [key: string]: number };
  recent_critical_events: SecurityEvent[];
  monitoring_active: boolean;
  generated_at: string;
}

const SecurityDashboard: React.FC = () => {
  const { theme } = useTheme();
  const { success, error } = useToast();
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [stats, setStats] = useState<SecurityStats | null>(null);
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'stats'>('overview');

  useEffect(() => {
    loadSecurityData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadSecurityData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSecurityData = async () => {
    try {
      const [eventsData, statsData, summaryData, typesData] = await Promise.all([
        getSecurityEvents({ limit: 100 }),
        getSecurityStats(),
        getSecuritySummary(),
        getSecurityEventTypes()
      ]);

      setEvents(eventsData as SecurityEvent[]);
      setStats(statsData as SecurityStats);
      setSummary(summaryData as SecuritySummary);
      setEventTypes(typesData as string[]);
    } catch (err) {
      console.error('Failed to load security data:', err);
      error('Failed to load security data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterByEventType = async (eventType: string) => {
    setSelectedEventType(eventType);
    try {
      const filteredEvents = await getSecurityEvents({
        limit: 100,
        event_type: eventType || undefined
      });
      setEvents(filteredEvents as SecurityEvent[]);
    } catch (err) {
      console.error('Failed to filter events:', err);
      error('Failed to filter events');
    }
  };

  const handleTestAlert = async () => {
    try {
      await testSecurityAlert('admin_test');
      success('Test security alert generated successfully');
      // Refresh data to show the new test event
      setTimeout(loadSecurityData, 1000);
    } catch (err) {
      console.error('Failed to generate test alert:', err);
      error('Failed to generate test alert');
    }
  };

  const handleClearEvents = async (eventType?: string, olderThanHours?: number) => {
    try {
      await clearSecurityEvents({
        event_type: eventType,
        older_than_hours: olderThanHours
      });
      success(`Cleared security events successfully`);
      // Refresh data to show the cleared events
      setTimeout(loadSecurityData, 1000);
    } catch (err) {
      console.error('Failed to clear security events:', err);
      error('Failed to clear security events');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatEventType = (eventType: string) => {
    return eventType.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  if (loading) {
    return (
      <div className={`p-6 ${theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-6 ${theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Security Monitoring</h2>
          <div className="flex space-x-2">
            <button
              onClick={loadSecurityData}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Refresh
            </button>
            <button
              onClick={handleTestAlert}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              Test Alert
            </button>
            <button
              onClick={() => handleClearEvents()}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Clear All Events
            </button>
          </div>
        </div>

        {/* Status Indicator */}
        {summary && (
          <div className="mt-4 p-4 rounded-lg border">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                summary.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
              }`}></div>
              <span className="font-semibold">
                System Status: {summary.status === 'healthy' ? 'Healthy' : 'Warning'}
              </span>
              <span className="text-sm text-gray-500">
                (Last updated: {formatTimestamp(summary.generated_at)})
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-1">
          {['overview', 'events', 'stats'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 text-sm font-medium rounded-lg ${
                activeTab === tab
                  ? 'bg-purple-500 text-white'
                  : theme === 'dark'
                  ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && summary && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <h3 className="text-sm font-medium text-gray-500">Events Today</h3>
              <p className="text-2xl font-bold">{summary.total_events_today}</p>
            </div>
            <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <h3 className="text-sm font-medium text-gray-500">High Severity (Last Hour)</h3>
              <p className="text-2xl font-bold text-orange-500">{summary.high_severity_events_last_hour}</p>
            </div>
            <div className={`p-4 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <h3 className="text-sm font-medium text-gray-500">Monitoring Status</h3>
              <p className={`text-lg font-semibold ${summary.monitoring_active ? 'text-green-500' : 'text-red-500'}`}>
                {summary.monitoring_active ? 'Active' : 'Inactive'}
              </p>
            </div>
          </div>

          {/* Top Event Types */}
          <div className={`p-6 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <h3 className="text-lg font-semibold mb-4">Top Event Types</h3>
            <div className="space-y-2">
              {Object.entries(summary.top_event_types).map(([eventType, count]) => (
                <div key={eventType} className="flex justify-between items-center">
                  <span className="text-sm">{formatEventType(eventType)}</span>
                  <span className="text-sm font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Critical Events */}
          {summary.recent_critical_events.length > 0 && (
            <div className={`p-6 rounded-lg border border-red-200 ${theme === 'dark' ? 'bg-red-900/20' : 'bg-red-50'}`}>
              <h3 className="text-lg font-semibold mb-4 text-red-600">Recent Critical Events</h3>
              <div className="space-y-2">
                {summary.recent_critical_events.map((event, index) => (
                  <div key={index} className="p-3 rounded-lg bg-red-100 text-red-800 text-sm">
                    <div className="font-medium">{formatEventType(event.event_type)}</div>
                    <div className="text-xs text-red-600">
                      {formatTimestamp(event.timestamp)} - IP: {event.ip_address}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Events Tab */}
      {activeTab === 'events' && (
        <div className="space-y-4">
          {/* Event Type Filter */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium">Filter by Event Type:</label>
              <select
                value={selectedEventType}
                onChange={(e) => handleFilterByEventType(e.target.value)}
                className={`px-3 py-1 rounded-lg border text-sm ${
                  theme === 'dark'
                    ? 'bg-gray-800 border-gray-600 text-white'
                    : 'bg-white border-gray-300 text-gray-900'
                }`}
              >
                <option value="">All Events</option>
                {eventTypes.map((type) => (
                  <option key={type} value={type}>
                    {formatEventType(type)}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              {selectedEventType && (
                <button
                  onClick={() => handleClearEvents(selectedEventType)}
                  className="px-3 py-1 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600 transition-colors"
                >
                  Clear {formatEventType(selectedEventType)} Events
                </button>
              )}
              <button
                onClick={() => handleClearEvents(undefined, 24)}
                className="px-3 py-1 bg-yellow-500 text-white text-sm rounded-lg hover:bg-yellow-600 transition-colors"
              >
                Clear Events &gt;24h
              </button>
            </div>
          </div>

          {/* Events List */}
          <div className={`rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <div className="max-h-96 overflow-y-auto">
              {events.length > 0 ? (
                <div className="divide-y divide-gray-200">
                  {events.map((event, index) => (
                    <div key={index} className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(event.severity)}`}>
                              {event.severity}
                            </span>
                            <span className="font-medium">{formatEventType(event.event_type)}</span>
                          </div>
                          <div className="mt-2 text-sm text-gray-600">
                            <div>IP: {event.ip_address}</div>
                            {event.username && <div>User: {event.username}</div>}
                            {event.endpoint && <div>Endpoint: {event.endpoint}</div>}
                            {event.details && Object.keys(event.details).length > 0 && (
                              <div>Details: {JSON.stringify(event.details)}</div>
                            )}
                          </div>
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatTimestamp(event.timestamp)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  No security events found
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Stats Tab */}
      {activeTab === 'stats' && stats && (
        <div className={`p-6 rounded-lg border ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <h3 className="text-lg font-semibold mb-4">Security Statistics (Current Hour)</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(stats).map(([key, value]) => (
              <div key={key} className="p-4 rounded-lg bg-gray-100 dark:bg-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {formatEventType(key)}
                </div>
                <div className="text-xl font-bold">{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SecurityDashboard;