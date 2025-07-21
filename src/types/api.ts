// Core evaluation models
export interface Metric {
  name: string;
  description: string;
  category: string;
  weight: number;
}

export interface MetricResult {
  metric: Metric;
  score: number;
  reasoning: string;
  improvement_advice: string;
  positive_examples: string[];
  improvement_examples: string[];
  confidence: number;
}

export interface CategoryScores {
  [category: string]: number;
}

export interface EvaluationResult {
  overall_score: number;
  category_scores: CategoryScores;
  metric_results: MetricResult[];
  content_hash: string;
  timestamp: string;
  metadata: {
    metrics_evaluated: number;
    evaluation_time: number;
    model_used: string;
  };
}

// Configuration models
export interface LLMConfig {
  provider: "openai" | "ollama" | "lmstudio";
  model_name: string;
  api_key?: string;
  base_url?: string;
}

export interface AppConfig {
  llm: LLMConfig;
  guidelines_path: string;
  reports_dir: string;
}

// API response models
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Request models
export interface EvaluateContentRequest {
  content: string;
  llm?: LLMConfig;  // Optional LLM configuration for this evaluation
  options?: {
    guidelines?: string;
    metrics?: string[];
  };
}

export interface UpdateSettingsRequest {
  llm?: LLMConfig;
  guidelines_path?: string;
  reports_dir?: string;
}

export interface TestConnectionRequest {
  provider: "openai" | "ollama" | "lmstudio";
  model_name: string;
  api_key?: string;
  base_url?: string;
}

// Sample content
export interface Sample {
  id: string;
  name: string;
  description: string;
  content: string;
  type: string;
  tags: string[];
}