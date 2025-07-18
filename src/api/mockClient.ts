import { 
  ApiResponse, 
  AppConfig, 
  EvaluationResult, 
  Sample, 
  TestConnectionRequest, 
  UpdateSettingsRequest 
} from '../types/api';

// Import sample data
import sampleReport from '../data/report.json';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Random delay between 300-1200ms to simulate network latency
const randomDelay = () => delay(300 + Math.random() * 900);

// Simulate occasional errors (10% chance)
const simulateRandomError = () => {
  if (Math.random() < 0.1) {
    throw new Error('Simulated random API error');
  }
};

/**
 * Mock API Client for development and testing
 */
class MockApiClient {
  private settings: AppConfig = {
    llm: {
      provider: 'openai',
      model_name: 'gpt-4',
      api_key: 'sk-mock-key',
    },
    guidelines_path: '/path/to/guidelines',
    reports_dir: '/path/to/reports'
  };

  private samples: Sample[] = [
    {
      id: 'sample1',
      name: 'Product Description',
      description: 'A sample product description for an AI-powered content analysis tool',
      content: 'Our AI-powered content analysis tool helps content creators improve their writing by providing detailed feedback on clarity, engagement, and SEO optimization. The tool uses advanced natural language processing to evaluate your content against industry best practices and provides actionable recommendations for improvement.',
      type: 'text',
      tags: ['product', 'marketing']
    },
    {
      id: 'sample2',
      name: 'Technical Blog Post',
      description: 'A technical blog post about implementing machine learning models',
      content: 'Implementing machine learning models in production requires careful consideration of scalability, monitoring, and maintenance. This post explores best practices for deploying ML models, including containerization with Docker, orchestration with Kubernetes, and continuous monitoring with Prometheus.',
      type: 'text',
      tags: ['technical', 'blog']
    },
    {
      id: 'sample3',
      name: 'Marketing Email',
      description: 'A sample marketing email promoting a new feature',
      content: 'Subject: Introducing Our New AI Content Analyzer\n\nDear Valued Customer,\n\nWe\'re excited to announce the launch of our new AI Content Analyzer feature! This powerful tool will help you optimize your content for better engagement and conversion. Try it today and see the difference it can make for your content strategy.',
      type: 'text',
      tags: ['email', 'marketing']
    }
  ];

  private reports: Record<string, EvaluationResult> = {
    'default': sampleReport as unknown as EvaluationResult,
  };

  /**
   * Submit content for evaluation
   */
  async evaluateContent(content: string | FormData): Promise<EvaluationResult> {
    await randomDelay();
    simulateRandomError();
    
    // Generate a unique report ID
    const reportId = `report_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;
    
    // Clone the sample report and modify it slightly
    const report = JSON.parse(JSON.stringify(sampleReport)) as EvaluationResult;
    report.content_hash = reportId;
    report.timestamp = new Date().toISOString();
    report.metadata.evaluation_time = 2 + Math.random() * 3;
    
    // Store the report for later retrieval
    this.reports[reportId] = report;
    
    return report;
  }
  
  /**
   * Get a specific report by ID
   */
  async getReport(reportId: string): Promise<EvaluationResult> {
    await randomDelay();
    simulateRandomError();
    
    const report = this.reports[reportId] || this.reports['default'];
    if (!report) {
      throw new Error(`Report not found: ${reportId}`);
    }
    
    return report;
  }
  
  /**
   * Export a report in the specified format
   */
  async exportReport(reportId: string, format: 'json' | 'markdown'): Promise<Blob> {
    await randomDelay();
    simulateRandomError();
    
    const report = this.reports[reportId] || this.reports['default'];
    if (!report) {
      throw new Error(`Report not found: ${reportId}`);
    }
    
    if (format === 'json') {
      return new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    } else {
      // Generate a simple markdown report
      const markdown = `# Content Evaluation Report\n\n` +
        `## Overall Score: ${report.overall_score}/5\n\n` +
        `Generated on: ${report.timestamp}\n\n` +
        `## Category Scores\n\n` +
        Object.entries(report.category_scores)
          .map(([category, score]) => `- ${category}: ${score}/5`)
          .join('\n') +
        `\n\n## Detailed Metrics\n\n` +
        report.metric_results
          .map(result => (
            `### ${result.metric.name} (${result.score}/5)\n\n` +
            `**Category:** ${result.metric.category}\n\n` +
            `**Reasoning:** ${result.reasoning}\n\n` +
            `**Improvement Advice:** ${result.improvement_advice}\n\n`
          ))
          .join('\n');
      
      return new Blob([markdown], { type: 'text/markdown' });
    }
  }
  
  /**
   * Get current application settings
   */
  async getSettings(): Promise<AppConfig> {
    await randomDelay();
    simulateRandomError();
    
    return { ...this.settings };
  }
  
  /**
   * Update application settings
   */
  async updateSettings(settings: UpdateSettingsRequest): Promise<AppConfig> {
    await randomDelay();
    simulateRandomError();
    
    this.settings = {
      ...this.settings,
      ...settings,
      llm: {
        ...this.settings.llm,
        ...(settings.llm || {})
      }
    };
    
    return { ...this.settings };
  }
  
  /**
   * Test connection to LLM provider
   */
  async testConnection(config: TestConnectionRequest): Promise<{ success: boolean; latency: number; message: string }> {
    await randomDelay();
    simulateRandomError();
    
    // Simulate different responses based on provider
    switch (config.provider) {
      case 'openai':
        return {
          success: true,
          latency: 450 + Math.random() * 200,
          message: 'Successfully connected to OpenAI API'
        };
      case 'ollama':
        if (!config.base_url) {
          return {
            success: false,
            latency: 0,
            message: 'Base URL is required for Ollama'
          };
        }
        return {
          success: true,
          latency: 150 + Math.random() * 100,
          message: 'Successfully connected to Ollama API'
        };
      case 'lmstudio':
        if (!config.base_url) {
          return {
            success: false,
            latency: 0,
            message: 'Base URL is required for LM Studio'
          };
        }
        return {
          success: true,
          latency: 200 + Math.random() * 150,
          message: 'Successfully connected to LM Studio API'
        };
      default:
        return {
          success: false,
          latency: 0,
          message: `Unknown provider: ${config.provider}`
        };
    }
  }
  
  /**
   * Get list of available sample content
   */
  async getSamples(): Promise<Sample[]> {
    await randomDelay();
    simulateRandomError();
    
    return [...this.samples];
  }
  
  /**
   * Get specific sample content by ID
   */
  async getSample(sampleId: string): Promise<Sample> {
    await randomDelay();
    simulateRandomError();
    
    const sample = this.samples.find(s => s.id === sampleId);
    if (!sample) {
      throw new Error(`Sample not found: ${sampleId}`);
    }
    
    return { ...sample };
  }
}

// Create and export a singleton instance
const mockApiClient = new MockApiClient();
export default mockApiClient;