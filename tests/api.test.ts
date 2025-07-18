import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import apiClient from '../src/api/client';
import mockApiClient from '../src/api/mockClient';
import { EvaluationResult, AppConfig } from '../src/types/api';

// Mock axios for testing
const mockAxios = new MockAdapter(axios);

describe('API Client', () => {
  beforeEach(() => {
    mockAxios.reset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('evaluateContent', () => {
    it('should successfully evaluate content', async () => {
      const mockResponse = {
        success: true,
        data: {
          overall_score: 4.2,
          category_scores: { clarity: 4.5 },
          metric_results: [],
          content_hash: 'abc123',
          timestamp: '2025-07-18T12:00:00Z',
          metadata: {
            metrics_evaluated: 10,
            evaluation_time: 2.5,
            model_used: 'gpt-4'
          }
        }
      };

      mockAxios.onPost('/api/evaluate').reply(200, mockResponse);

      const result = await apiClient.evaluateContent('Test content');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle errors during content evaluation', async () => {
      mockAxios.onPost('/api/evaluate').reply(500, {
        success: false,
        error: 'Server error'
      });

      await expect(apiClient.evaluateContent('Test content')).rejects.toThrow();
    });
  });

  describe('getSettings', () => {
    it('should fetch settings successfully', async () => {
      const mockSettings = {
        success: true,
        data: {
          llm: {
            provider: 'openai',
            model_name: 'gpt-4'
          },
          guidelines_path: '/path/to/guidelines',
          reports_dir: '/path/to/reports'
        }
      };

      mockAxios.onGet('/api/settings').reply(200, mockSettings);

      const result = await apiClient.getSettings();
      expect(result).toEqual(mockSettings.data);
    });
  });

  describe('testConnection', () => {
    it('should test connection successfully', async () => {
      const mockResponse = {
        success: true,
        data: {
          success: true,
          latency: 450,
          message: 'Successfully connected to OpenAI API'
        }
      };

      mockAxios.onPost('/api/settings/test').reply(200, mockResponse);

      const result = await apiClient.testConnection({
        provider: 'openai',
        model_name: 'gpt-4',
        api_key: 'test-key'
      });
      
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('retry logic', () => {
    it('should retry failed requests', async () => {
      const mockResponse = {
        success: true,
        data: { message: 'Success after retry' }
      };

      // Fail twice, then succeed
      let attempts = 0;
      mockAxios.onGet('/api/settings').reply(() => {
        attempts++;
        if (attempts <= 2) {
          return [503, { success: false, error: 'Service unavailable' }];
        }
        return [200, mockResponse];
      });

      // Reduce retry delay for testing
      vi.spyOn(global, 'setTimeout').mockImplementation((cb: any) => {
        cb();
        return 0 as any;
      });

      const result = await apiClient.getSettings();
      expect(attempts).toBe(3);
      expect(result).toEqual(mockResponse.data);
    });
  });
});

describe('Mock API Client', () => {
  it('should return mock evaluation results', async () => {
    const result = await mockApiClient.evaluateContent('Test content');
    expect(result).toBeDefined();
    expect(result.overall_score).toBeDefined();
    expect(result.category_scores).toBeDefined();
    expect(result.metric_results.length).toBeGreaterThan(0);
  });

  it('should return mock settings', async () => {
    const settings = await mockApiClient.getSettings();
    expect(settings).toBeDefined();
    expect(settings.llm).toBeDefined();
    expect(settings.llm.provider).toBeDefined();
  });

  it('should update mock settings', async () => {
    const newSettings = {
      llm: {
        provider: 'ollama' as const,
        model_name: 'llama2',
        base_url: 'http://localhost:11434'
      }
    };
    
    const result = await mockApiClient.updateSettings(newSettings);
    expect(result.llm.provider).toBe('ollama');
    expect(result.llm.model_name).toBe('llama2');
    expect(result.llm.base_url).toBe('http://localhost:11434');
  });

  it('should return mock samples', async () => {
    const samples = await mockApiClient.getSamples();
    expect(samples).toBeDefined();
    expect(samples.length).toBeGreaterThan(0);
    expect(samples[0].id).toBeDefined();
    expect(samples[0].content).toBeDefined();
  });
});