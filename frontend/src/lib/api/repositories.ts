import apiClient from './client';
import { Repository, RepositoryCreate, ConnectRepositoryRequest, PaginationParams } from '@/lib/types/api';

export const repositoriesApi = {
  // Get user's repositories
  async getRepositories(params?: PaginationParams & {
    provider?: string;
    is_active?: boolean;
  }) {
    const searchParams = new URLSearchParams();
    
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.search) searchParams.append('search', params.search);
    if (params?.provider) searchParams.append('provider', params.provider);
    if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());

    return apiClient.get<Repository[]>(`/repositories?${searchParams.toString()}`);
  },

  // Get single repository with stats
  async getRepository(id: number) {
    return apiClient.get<any>(`/repositories/${id}`);
  },

  // Connect new repository
  async connectRepository(data: ConnectRepositoryRequest) {
    return apiClient.post<Repository>('/repositories/connect', data);
  },

  // Update repository settings
  async updateRepository(id: number, data: Partial<Repository>) {
    return apiClient.put<Repository>(`/repositories/${id}`, data);
  },

  // Delete repository connection
  async deleteRepository(id: number) {
    return apiClient.delete(`/repositories/${id}`);
  },

  // Get repository branches
  async getRepositoryBranches(id: number) {
    return apiClient.get<{ branches: string[] }>(`/repositories/${id}/branches`);
  },

  // Trigger manual analysis
  async triggerAnalysis(id: number, branch?: string) {
    return apiClient.post(`/repositories/${id}/analyze`, { branch });
  },
};

export const dashboardApi = {
  // Get dashboard statistics
  async getDashboardStats() {
    return apiClient.get<any>('/dashboard/stats');
  },

  // Get recent activity
  async getRecentActivity(limit = 10) {
    return apiClient.get<any>(`/dashboard/activity?limit=${limit}`);
  },
};
