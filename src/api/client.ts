import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { 
  ApiResponse, 
  AppConfig, 
  EvaluateContentRequest, 
  EvaluationResult, 
  Sample, 
  TestConnectionRequest, 
  UpdateSettingsRequest 
} from '../types/api';

// Maximum number of retries for failed requests
const MAX_RETRIES = 2; // Reduced retries but with better timing
// Base delay for exponential backoff (in ms)
const BASE_RETRY_DELAY = 2000; // Increased base delay

/**
 * API Client for backend communication
 */
class ApiClient {
  private client: AxiosInstance;
  private isProduction: boolean;

  constructor() {
    this.isProduction = !import.meta.env.DEV;
    
    this.client = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000, // 60 seconds - increased for content evaluation
    });

    this.setupInterceptors();
  }

  /**
   * Configure request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor for handling auth
    this.client.interceptors.request.use(
      (config) => {
        // You could add auth tokens here if needed
        // const token = localStorage.getItem('auth_token');
        // if (token) {
        //   config.headers.Authorization = `Bearer ${token}`;
        // }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        // Log errors in development
        if (!this.isProduction) {
          this.logError(error);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Log API errors with useful information
   */
  private logError(error: AxiosError): void {
    if (error.response) {
      // Server responded with a status code outside of 2xx
      console.error(
        `API Error (${error.response.status}):`, 
        error.response.data
      );
    } else if (error.request) {
      // Request was made but no response received
      console.error('API No Response:', error.request);
    } else {
      // Something else happened while setting up the request
      console.error('API Request Error:', error.message);
    }
  }

  /**
   * Make an API request with retry logic
   */
  private async requestWithRetry<T>(
    config: AxiosRequestConfig,
    retries = MAX_RETRIES
  ): Promise<AxiosResponse<ApiResponse<T>>> {
    try {
      return await this.client.request<ApiResponse<T>>(config);
    } catch (error) {
      if (
        retries > 0 && 
        axios.isAxiosError(error) && 
        this.isRetryableError(error)
      ) {
        const delay = this.getRetryDelay(MAX_RETRIES - retries + 1);
        console.log(`Retrying request (${MAX_RETRIES - retries + 1}/${MAX_RETRIES}) after ${delay}ms`);
        
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.requestWithRetry<T>(config, retries - 1);
      }
      throw error;
    }
  }

  /**
   * Determine if an error should trigger a retry
   */
  private isRetryableError(error: AxiosError): boolean {
    // Retry on network errors or specific HTTP status codes
    // Also retry on connection refused (status 0) which typically happens during startup
    return (
      !error.response || // Network error (including connection refused)
      error.code === 'ECONNABORTED' || // Timeout
      error.code === 'ECONNREFUSED' || // Connection refused (backend starting)
      (error.response && [408, 429, 500, 502, 503, 504].includes(error.response.status))
    );
  }

  /**
   * Calculate exponential backoff delay optimized for backend startup
   */
  private getRetryDelay(retryCount: number): number {
    // Optimized delays for backend startup (which typically takes 7-8 seconds)
    if (retryCount === 1) {
      return 3000 + Math.random() * 1000; // 3-4 seconds (backend likely starting)
    }
    if (retryCount === 2) {
      return 4000 + Math.random() * 1000; // 4-5 seconds (backend should be ready)
    }
    
    // Fallback to exponential backoff for other scenarios
    return Math.min(
      BASE_RETRY_DELAY * Math.pow(2, retryCount - 1) + Math.random() * 1000,
      10000 // Max 10 seconds
    );
  }

  /**
   * Process API response to extract data or handle errors
   */
  private processResponse<T>(response: AxiosResponse<ApiResponse<T>>): T {
    const { data } = response;
    
    if (!data.success) {
      throw new Error(data.error || 'Unknown API error');
    }
    
    return data.data as T;
  }

  // Content evaluation
  /**
   * Submit content for evaluation
   */
  async evaluateContent(content: string | EvaluateContentRequest | FormData): Promise<EvaluationResult> {
    const isFormData = content instanceof FormData;
    
    // Convert string content to proper request format
    let requestData;
    if (typeof content === 'string') {
      requestData = { content };
    } else if (isFormData) {
      requestData = content;
    } else {
      requestData = content;
    }
    
    const config: AxiosRequestConfig = {
      method: 'POST',
      url: '/evaluate',
      data: requestData,
      headers: isFormData ? {
        'Content-Type': 'multipart/form-data'
      } : undefined
    };
    
    const response = await this.requestWithRetry<EvaluationResult>(config);
    return this.processResponse(response);
  }
  
  // Report management
  /**
   * Get a specific report by ID
   */
  async getReport(reportId: string): Promise<EvaluationResult> {
    const response = await this.requestWithRetry<EvaluationResult>({
      method: 'GET',
      url: `/reports/${reportId}`
    });
    return this.processResponse(response);
  }
  
  /**
   * Export a report in the specified format
   */
  async exportReport(reportId: string, format: 'json' | 'markdown'): Promise<Blob> {
    const response = await this.client.get(`/reports/${reportId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }
  
  // Settings management
  /**
   * Get current application settings
   */
  async getSettings(): Promise<AppConfig> {
    const response = await this.requestWithRetry<AppConfig>({
      method: 'GET',
      url: '/settings'
    });
    return this.processResponse(response);
  }
  
  /**
   * Update application settings
   */
  async updateSettings(settings: UpdateSettingsRequest): Promise<AppConfig> {
    const response = await this.requestWithRetry<AppConfig>({
      method: 'PUT',
      url: '/settings',
      data: settings
    });
    return this.processResponse(response);
  }
  
  /**
   * Test connection to LLM provider
   */
  async testConnection(config: TestConnectionRequest): Promise<{ success: boolean; latency: number; message: string }> {
    const response = await this.requestWithRetry<{ success: boolean; latency: number; message: string }>({
      method: 'POST',
      url: '/settings/test',
      data: config
    });
    return this.processResponse(response);
  }

  /**
   * Check if the backend is healthy and ready
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.requestWithRetry<any>({
        method: 'GET',
        url: '/',
        timeout: 5000, // Short timeout for health checks
      });
      return this.processResponse(response) !== null;
    } catch (error) {
      return false;
    }
  }
  
  // Sample content
  /**
   * Get list of available sample content
   */
  async getSamples(): Promise<Sample[]> {
    const response = await this.requestWithRetry<Sample[]>({
      method: 'GET',
      url: '/samples'
    });
    return this.processResponse(response);
  }
  
  /**
   * Get specific sample content by ID
   */
  async getSample(sampleId: string): Promise<Sample> {
    const response = await this.requestWithRetry<Sample>({
      method: 'GET',
      url: `/samples/${sampleId}`
    });
    return this.processResponse(response);
  }
}

// Create and export a singleton instance
const apiClient = new ApiClient();
export default apiClient;