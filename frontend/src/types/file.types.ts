/**
 * TypeScript types for file-related data structures
 */

export enum FileType {
  PDF = 'pdf',
  AUDIO = 'audio',
  VIDEO = 'video',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface ExtractedContent {
  text: string;
  word_count: number;
  language: string;
  extraction_method: string;
}

export interface FileMetadata {
  duration?: number;
  format?: string;
  resolution?: string;
  sample_rate?: number;
  channels?: number;
}

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: FileType;
  file_size: number;
  processing_status: ProcessingStatus;
  upload_date: string;
}

export interface FileDetailResponse {
  file_id: string;
  filename: string;
  file_type: FileType;
  file_size: number;
  mime_type: string;
  processing_status: ProcessingStatus;
  processing_error?: string;
  extracted_content?: ExtractedContent;
  metadata?: FileMetadata;
  upload_date: string;
  created_at: string;
  updated_at: string;
  file_url?: string;
}

export interface FileListItem {
  file_id: string;
  filename: string;
  file_type: FileType;
  file_size: number;
  processing_status: ProcessingStatus;
  created_at: string;
  has_chat: boolean;
}

export interface FileListResponse {
  files: FileListItem[];
  total: number;
}
