/**
 * Custom hook for chat functionality
 */
import { useState } from 'react';
import { chatService } from '../services/chatService';
import { ChatResponse, ChatHistoryResponse } from '../types/chat.types';

export const useChat = (fileId: string) => {
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const askQuestion = async (question: string): Promise<ChatResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.askQuestion(fileId, {
        question,
        chat_id: chatHistory?.chat_id,
      });

      // Refresh chat history
      await loadHistory();

      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get answer';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const history = await chatService.getHistory(fileId);
      setChatHistory(history);
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  return {
    askQuestion,
    loadHistory,
    isLoading,
    chatHistory,
    error,
  };
};
