/**
 * Chat service for API calls
 */
import api from './api';
import { ChatRequest, ChatResponse, ChatHistoryResponse } from '../types/chat.types';
import { API_BASE_URL } from '../utils/constants';

export const chatService = {
  /**
   * Ask a question about a file
   */
  askQuestion: async (
    fileId: string,
    request: ChatRequest
  ): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>(`/chat/${fileId}/ask`, request);
    return response.data;
  },

  /**
   * Ask a question with streaming response
   */
  askQuestionStreaming: async (
    fileId: string,
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete?: (suggestedTimestamp?: number) => void
  ): Promise<{ suggested_timestamp?: number }> => {
    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/chat/${fileId}/ask`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let suggestedTimestamp: number | undefined;

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6); // Remove 'data: ' prefix

            if (jsonStr.trim()) {
              try {
                const data = JSON.parse(jsonStr);

                if (data.type === 'content') {
                  onChunk(data.content);
                } else if (data.type === 'error') {
                  throw new Error(data.error || 'Streaming error occurred');
                } else if (data.type === 'done') {
                  // Capture suggested_timestamp from done event
                  if (data.suggested_timestamp !== undefined) {
                    suggestedTimestamp = data.suggested_timestamp;
                  }
                  if (onComplete) {
                    onComplete(suggestedTimestamp);
                  }
                }
              } catch (parseError) {
                console.error('Error parsing SSE data:', parseError);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }

    return { suggested_timestamp: suggestedTimestamp };
  },

  /**
   * Get chat history for a file
   */
  getHistory: async (fileId: string): Promise<ChatHistoryResponse> => {
    const response = await api.get<ChatHistoryResponse>(`/chat/${fileId}/history`);
    return response.data;
  },
};
