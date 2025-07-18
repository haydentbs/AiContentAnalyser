import realApiClient from './client';
import mockApiClient from './mockClient';

// Determine which API client to use based on environment
const USE_MOCK_API = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_API === 'true';

// Export the appropriate client
const api = USE_MOCK_API ? mockApiClient : realApiClient;

export default api;

// Re-export types
export * from '../types/api';