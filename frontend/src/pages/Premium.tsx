import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { getCurrentDomainName } from '../utils/domain';

interface SubscriptionStatus {
  is_premium: boolean;
  premium_expires_at: string | null;
  has_active_premium: boolean;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  subscription_status?: string;
  current_period_end?: number;
  cancel_at_period_end?: boolean;
}

const Premium: React.FC = () => {
  const { user, token } = useAuth();
  const { success, error: showError } = useToast();
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  const domainName = getCurrentDomainName();

  useEffect(() => {
    fetchSubscriptionStatus();
  }, []);

  const authFetch = async (url: string, options: RequestInit = {}) => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return fetch(`${apiUrl}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await authFetch('/api/stripe/subscription-status');
      if (response.ok) {
        const data = await response.json();
        setSubscriptionStatus(data);
      }
    } catch (error) {
      console.error('Error fetching subscription status:', error);
      showError('Failed to load subscription status');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async () => {
    if (!user) return;
    
    setProcessing(true);
    try {
      const response = await authFetch(`/api/stripe/create-checkout-session?redirect_origin=${encodeURIComponent(window.location.origin)}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        window.location.href = data.checkout_url;
      } else {
        const errorData = await response.json();
        showError(errorData.detail || 'Failed to create checkout session');
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      showError('Failed to start checkout process');
    } finally {
      setProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your current billing period.')) {
      return;
    }

    setProcessing(true);
    try {
      const response = await authFetch('/api/stripe/cancel-subscription', {
        method: 'POST',
      });
      
      if (response.ok) {
        success('Subscription will be canceled at the end of your billing period');
        fetchSubscriptionStatus();
      } else {
        const errorData = await response.json();
        showError(errorData.detail || 'Failed to cancel subscription');
      }
    } catch (error) {
      console.error('Error canceling subscription:', error);
      showError('Failed to cancel subscription');
    } finally {
      setProcessing(false);
    }
  };

  const handleReactivateSubscription = async () => {
    setProcessing(true);
    try {
      const response = await authFetch('/api/stripe/reactivate-subscription', {
        method: 'POST',
      });
      
      if (response.ok) {
        success('Subscription reactivated successfully');
        fetchSubscriptionStatus();
      } else {
        const errorData = await response.json();
        showError(errorData.detail || 'Failed to reactivate subscription');
      }
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      showError('Failed to reactivate subscription');
    } finally {
      setProcessing(false);
    }
  };

  const handleManageBilling = async () => {
    setProcessing(true);
    try {
  const response = await authFetch(`/api/stripe/customer-portal?redirect_origin=${encodeURIComponent(window.location.origin)}`);
      
      if (response.ok) {
        const data = await response.json();
        window.location.href = data.portal_url;
      } else {
        const errorData = await response.json();
        showError(errorData.detail || 'Failed to access billing portal');
      }
    } catch (error) {
      console.error('Error accessing billing portal:', error);
      showError('Failed to access billing portal');
    } finally {
      setProcessing(false);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-300">Loading subscription details...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              {domainName} Premium
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Unlock premium features and get access to exclusive domains like kitsune-chan.page
            </p>
          </div>

          {/* Current Status */}
          {subscriptionStatus && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                Current Status
              </h2>
              <div className="flex items-center space-x-4">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  subscriptionStatus.has_active_premium 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                }`}>
                  {subscriptionStatus.has_active_premium ? 'Premium Active' : 'Free Plan'}
                </div>
                
                {subscriptionStatus.current_period_end && (
                  <span className="text-gray-600 dark:text-gray-300">
                    {subscriptionStatus.cancel_at_period_end 
                      ? `Expires: ${formatDate(subscriptionStatus.current_period_end)}`
                      : `Renews: ${formatDate(subscriptionStatus.current_period_end)}`
                    }
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Pricing Plans */}
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Free Plan */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">Free</h3>
                <div className="mt-2">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">$0</span>
                  <span className="text-gray-600 dark:text-gray-300">/month</span>
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-700 dark:text-gray-300">1GB storage</span>
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-700 dark:text-gray-300">Standard domains</span>
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-700 dark:text-gray-300">Basic profile customization</span>
                </li>
              </ul>
              
              <div className="text-center">
                <span className="text-gray-500 dark:text-gray-400">Current Plan</span>
              </div>
            </div>

            {/* Premium Plan */}
            <div className="bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg shadow-md p-8 text-white relative">
              <div className="absolute top-4 right-4">
                <span className="bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-semibold">
                  POPULAR
                </span>
              </div>
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold">Premium</h3>
                <div className="mt-2">
                  <span className="text-4xl font-bold">2.99€</span>
                  <span className="text-purple-200">/month</span>
                </div>
              </div>
              
              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Everything in Free</span>
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Access to kitsune-chan.page</span>
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Premium domains</span>
                </li>
                <li className="flex items-center">
                  <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Priority support</span>
                </li>
              </ul>
              
              <div className="text-center">
                {!subscriptionStatus?.has_active_premium ? (
                  <button
                    onClick={handleUpgrade}
                    disabled={processing}
                    className="w-full bg-white text-purple-600 font-semibold py-3 px-6 rounded-lg hover:bg-gray-100 transition duration-200 disabled:opacity-50"
                  >
                    {processing ? 'Processing...' : 'Upgrade to Premium'}
                  </button>
                ) : (
                  <div className="space-y-2">
                    <div className="text-green-400 font-semibold">✓ Active</div>
                    <div className="space-y-2">
                      {subscriptionStatus.cancel_at_period_end ? (
                        <button
                          onClick={handleReactivateSubscription}
                          disabled={processing}
                          className="w-full bg-white text-purple-600 font-semibold py-2 px-4 rounded hover:bg-gray-100 transition duration-200 disabled:opacity-50"
                        >
                          {processing ? 'Processing...' : 'Reactivate'}
                        </button>
                      ) : (
                        <button
                          onClick={handleCancelSubscription}
                          disabled={processing}
                          className="w-full bg-red-500 text-white font-semibold py-2 px-4 rounded hover:bg-red-600 transition duration-200 disabled:opacity-50"
                        >
                          {processing ? 'Processing...' : 'Cancel Subscription'}
                        </button>
                      )}
                      <button
                        onClick={handleManageBilling}
                        disabled={processing}
                        className="w-full bg-transparent border border-white text-white font-semibold py-2 px-4 rounded hover:bg-white hover:text-purple-600 transition duration-200 disabled:opacity-50"
                      >
                        {processing ? 'Processing...' : 'Manage Billing'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Features Comparison */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              Why Go Premium?
            </h2>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Exclusive Domains
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Get access to premium domains like kitsune-chan.page for your files
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Priority Support
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Get faster response times and priority customer support
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Support Development
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Help us maintain and improve the platform for everyone
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

export default Premium;