/**
 * TypeScript types for summary-related data structures
 */

export enum SummaryType {
  BRIEF = 'brief',
  DETAILED = 'detailed',
  KEY_POINTS = 'key_points',
}

export interface SummaryRequest {
  summary_type: SummaryType;
}

export interface TokenCount {
  input: number;
  output: number;
  total: number;
}

export interface SummaryParameters {
  temperature: number;
  max_tokens: number;
}

export interface SummaryResponse {
  summary_id: string;
  file_id: string;
  summary_type: SummaryType;
  content: string;
  model_used: string;
  token_count: TokenCount;
  parameters: SummaryParameters;
  created_at: string;
}

export interface SummaryListResponse {
  summaries: SummaryResponse[];
  count: number;
}
