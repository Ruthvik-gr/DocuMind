/**
 * TypeScript types for timestamp-related data structures
 */

export interface TimestampEntry {
  timestamp_entry_id: string;
  time: number;
  topic: string;
  description: string;
  keywords: string[];
  confidence?: number;
}

export interface ExtractionMetadata {
  total_topics: number;
  extraction_method: string;
  model_used: string;
}

export interface TimestampResponse {
  timestamp_id: string;
  file_id: string;
  timestamps: TimestampEntry[];
  extraction_metadata: ExtractionMetadata;
  created_at: string;
  updated_at: string;
}
