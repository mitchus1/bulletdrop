import { apiService } from './api';

// Admin authentication check
export const checkAdminAccess = async (): Promise<boolean> => {
  try {
    await apiService.adminRequest('/stats');
    return true;
  } catch (error) {
    return false;
  }
};

// User management
export const getAllUsers = async (params?: {
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
  is_admin?: boolean;
}) => {
  const searchParams = new URLSearchParams();
  if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
  if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
  if (params?.search) searchParams.append('search', params.search);
  if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
  if (params?.is_admin !== undefined) searchParams.append('is_admin', params.is_admin.toString());
  
  return await apiService.adminRequest(`/users?${searchParams.toString()}`);
};

export const getUserById = async (userId: number) => {
  return await apiService.adminRequest(`/users/${userId}`);
};

export const updateUser = async (userId: number, updates: {
  is_active?: boolean;
  is_admin?: boolean;
  is_verified?: boolean;
  storage_limit?: number;
}) => {
  return await apiService.adminRequest(`/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates)
  });
};

export const deleteUser = async (userId: number) => {
  return await apiService.adminRequest(`/users/${userId}`, {
    method: 'DELETE'
  });
};

// Domain management
export const getAllDomains = async () => {
  return await apiService.adminRequest('/domains');
};

export const createDomain = async (domainData: {
  domain_name: string;
  display_name?: string;
  description?: string;
  is_available?: boolean;
  is_premium?: boolean;
  max_file_size?: number;
}) => {
  return await apiService.adminRequest('/domains', {
    method: 'POST',
    body: JSON.stringify(domainData)
  });
};

export const updateDomain = async (domainId: number, updates: {
  display_name?: string;
  description?: string;
  is_available?: boolean;
  is_premium?: boolean;
  max_file_size?: number;
}) => {
  return await apiService.adminRequest(`/domains/${domainId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates)
  });
};

export const deleteDomain = async (domainId: number) => {
  return await apiService.adminRequest(`/domains/${domainId}`, {
    method: 'DELETE'
  });
};

// Statistics
export const getAdminStats = async () => {
  return await apiService.adminRequest('/stats');
};

export const getUserActivityStats = async (limit?: number) => {
  const params = limit ? `?limit=${limit}` : '';
  return await apiService.adminRequest(`/stats/users${params}`);
};

export const getDomainStats = async () => {
  return await apiService.adminRequest('/stats/domains');
};

export const getRecentActivity = async (days?: number, limit?: number) => {
  const searchParams = new URLSearchParams();
  if (days) searchParams.append('days', days.toString());
  if (limit) searchParams.append('limit', limit.toString());
  
  const params = searchParams.toString() ? `?${searchParams.toString()}` : '';
  return await apiService.adminRequest(`/activity${params}`);
};

export default {
  checkAdminAccess,
  getAllUsers,
  getUserById,
  updateUser,
  deleteUser,
  getAllDomains,
  createDomain,
  updateDomain,
  deleteDomain,
  getAdminStats,
  getUserActivityStats,
  getDomainStats,
  getRecentActivity,
};