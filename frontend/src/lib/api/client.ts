import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'sonner';
import { getAuthToken, removeAuthToken } from '@/lib/auth';

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  details?: any;
  status: number;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    this.client = axios.create({
      baseURL: `${this.baseURL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        const { response } = error;
        
        if (response?.status === 401) {
          // Unauthorized - redirect to login
          removeAuthToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        } else if (response?.status >= 500) {
          // Server error
          toast.error('Server error occurred. Please try again later.');
        } else if (response?.status === 403) {
          // Forbidden
          toast.error('You do not have permission to perform this action.');
        } else if (response?.status === 404) {
          // Not found
          toast.error('Resource not found.');
        } else if (response?.data?.error?.message) {
          // Custom error message from API
          toast.error(response.data.error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  // Generic HTTP methods
  async get<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(endpoint, config);
    return response.data;
  }

  async post<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(endpoint, data, config);
    return response.data;
  }

  async put<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(endpoint, data, config);
    return response.data;
  }

  async patch<T>(endpoint: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(endpoint, data, config);
    return response.data;
  }

  async delete<T>(endpoint: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(endpoint, config);
    return response.data;
  }

  // File upload method
  async uploadFile<T>(endpoint: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response = await this.client.post<T>(endpoint, formData, config);
    return response.data;
  }

  // WebSocket connection (for real-time features)
  createWebSocket(endpoint: string): WebSocket {
    const wsUrl = this.baseURL.replace('http', 'ws') + endpoint;
    const token = getAuthToken();
    
    const ws = new WebSocket(`${wsUrl}?token=${token}`);
    
    ws.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
      toast.error('Real-time connection failed');
    });

    return ws;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.get('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export default for easy importing
export default apiClient;
