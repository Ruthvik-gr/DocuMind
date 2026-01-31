/**
 * TypeScript types for chat-related data structures
 */

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
}

export interface ChatRequest {
  question: string;
  chat_id?: string;
}

export interface ChatResponse {
  answer: string;
  chat_id: string;
  sources: string[];
  timestamp: string;
}

export interface MessageMetadata {
  source_chunks?: string[];
  model?: string;
  confidence?: number;
}

export interface Message {
  message_id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  token_count?: number;
  metadata?: MessageMetadata;
  suggested_timestamp?: number;
}

export interface ChatHistoryResponse {
  chat_id: string;
  file_id: string;
  messages: Message[];
  total_messages: number;
  total_tokens: number;
  created_at: string;
  updated_at: string;
}
