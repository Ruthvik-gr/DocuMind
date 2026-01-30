/**
 * Chat service for API calls
 */
import api from './api';
import { ChatRequest, ChatResponse, ChatHistoryResponse } from '../types/chat.types';

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
   * Get chat history for a file
   */
  getHistory: async (fileId: string): Promise<ChatHistoryResponse> => {
    const response = await api.get<ChatHistoryResponse>(`/chat/${fileId}/history`);
    return response.data;
  },
};
