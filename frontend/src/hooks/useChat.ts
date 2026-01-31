/**
 * Custom hook for chat functionality with streaming support
 */
import { useState } from 'react';
import { chatService } from '../services/chatService';
import { ChatResponse, ChatHistoryResponse, Message, MessageRole } from '../types/chat.types';

export const useChat = (fileId: string) => {
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [lastSuggestedTimestamp, setLastSuggestedTimestamp] = useState<number | undefined>();

  const askQuestion = async (question: string): Promise<ChatResponse | null> => {
    setIsLoading(true);
    setError(null);
    setStreamingMessage('');
    setLastSuggestedTimestamp(undefined);

    try {
      // Add user message immediately to chat history
      const tempUserMessage: Message = {
        message_id: `temp-${Date.now()}`,
        role: MessageRole.USER,
        content: question,
        timestamp: new Date().toISOString(),
        token_count: 0,
      };

      setChatHistory((prev) => ({
        ...prev!,
        messages: [...(prev?.messages || []), tempUserMessage],
        total_messages: (prev?.total_messages || 0) + 1,
        total_tokens: prev?.total_tokens || 0,
        chat_id: prev?.chat_id || '',
        file_id: fileId,
        created_at: prev?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

      // Use streaming service
      let fullAnswer = '';
      let suggestedTs: number | undefined;

      const result = await chatService.askQuestionStreaming(
        fileId,
        {
          question,
          chat_id: chatHistory?.chat_id,
        },
        (chunk) => {
          fullAnswer += chunk;
          setStreamingMessage(fullAnswer);
        },
        (timestamp) => {
          suggestedTs = timestamp;
          setLastSuggestedTimestamp(timestamp);
        }
      );

      // If we got a suggested timestamp from the result
      if (result.suggested_timestamp !== undefined) {
        suggestedTs = result.suggested_timestamp;
        setLastSuggestedTimestamp(result.suggested_timestamp);
      }

      // Refresh chat history after streaming completes
      // and add the suggested timestamp to the last assistant message
      const history = await chatService.getHistory(fileId);

      // Add suggested_timestamp to the last assistant message
      if (suggestedTs !== undefined && history.messages.length > 0) {
        const lastMessage = history.messages[history.messages.length - 1];
        if (lastMessage.role === MessageRole.ASSISTANT) {
          lastMessage.suggested_timestamp = suggestedTs;
        }
      }

      setChatHistory(history);
      setStreamingMessage('');

      return null;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get answer';
      setError(errorMessage);
      setStreamingMessage('');
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
    streamingMessage,
    lastSuggestedTimestamp,
  };
};
