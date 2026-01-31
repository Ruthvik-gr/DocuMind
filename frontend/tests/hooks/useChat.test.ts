import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../../src/hooks/useChat';
import { chatService } from '../../src/services/chatService';

vi.mock('../../src/services/chatService');

describe('useChat', () => {
  const fileId = 'test-file-id';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useChat(fileId));

    expect(result.current.isLoading).toBe(false);
    expect(result.current.chatHistory).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.streamingMessage).toBe('');
    expect(result.current.lastSuggestedTimestamp).toBeUndefined();
  });

  it('should ask question with streaming successfully', async () => {
    const mockHistory = {
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [
        {
          message_id: 'msg-1',
          role: 'user' as const,
          content: 'Test question',
          timestamp: '2024-01-15T10:00:00Z',
          token_count: 0,
        },
        {
          message_id: 'msg-2',
          role: 'assistant' as const,
          content: 'Test answer from streaming',
          timestamp: '2024-01-15T10:00:01Z',
          token_count: 0,
        },
      ],
      total_messages: 2,
      total_tokens: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:01Z',
    };

    // Mock streaming to call onChunk with answer chunks
    vi.mocked(chatService.askQuestionStreaming).mockImplementation(
      async (fId, request, onChunk, onComplete) => {
        onChunk('Test ');
        onChunk('answer ');
        onChunk('from streaming');
        if (onComplete) onComplete(undefined);
        return { suggested_timestamp: undefined };
      }
    );
    vi.mocked(chatService.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.askQuestion('Test question');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.chatHistory).toEqual(mockHistory);
    expect(result.current.error).toBeNull();
  });

  it('should handle streaming with suggested timestamp', async () => {
    const mockHistory = {
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [
        {
          message_id: 'msg-1',
          role: 'user' as const,
          content: 'Test question',
          timestamp: '2024-01-15T10:00:00Z',
          token_count: 0,
        },
        {
          message_id: 'msg-2',
          role: 'assistant' as const,
          content: 'Answer about topic at 30 seconds',
          timestamp: '2024-01-15T10:00:01Z',
          token_count: 0,
        },
      ],
      total_messages: 2,
      total_tokens: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:01Z',
    };

    vi.mocked(chatService.askQuestionStreaming).mockImplementation(
      async (fId, request, onChunk, onComplete) => {
        onChunk('Answer about topic at 30 seconds');
        if (onComplete) onComplete(30);
        return { suggested_timestamp: 30 };
      }
    );
    vi.mocked(chatService.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.askQuestion('Test question');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.lastSuggestedTimestamp).toBe(30);
    // Check that the last message has suggested_timestamp
    expect(result.current.chatHistory?.messages[1].suggested_timestamp).toBe(30);
  });

  it('should handle ask question error', async () => {
    const errorMessage = 'Streaming error occurred';
    vi.mocked(chatService.askQuestionStreaming).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.askQuestion('Test question');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.streamingMessage).toBe('');
  });

  it('should load chat history successfully', async () => {
    const mockHistory = {
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [],
      total_messages: 0,
      total_tokens: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    };

    vi.mocked(chatService.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.loadHistory();
    });

    await waitFor(() => {
      expect(result.current.chatHistory).toEqual(mockHistory);
    });
  });

  it('should handle load history error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(chatService.getHistory).mockRejectedValue(new Error('Failed to load'));

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.loadHistory();
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(result.current.chatHistory).toBeNull();

    consoleErrorSpy.mockRestore();
  });

  it('should set isLoading to true during question', async () => {
    let resolveStreaming: any;
    const streamingPromise = new Promise<{ suggested_timestamp?: number }>((resolve) => {
      resolveStreaming = resolve;
    });

    vi.mocked(chatService.askQuestionStreaming).mockReturnValue(streamingPromise);
    vi.mocked(chatService.getHistory).mockResolvedValue({
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [],
      total_messages: 0,
      total_tokens: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    });

    const { result } = renderHook(() => useChat(fileId));

    act(() => {
      result.current.askQuestion('Test');
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolveStreaming({ suggested_timestamp: undefined });
      await streamingPromise;
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should add user message immediately when asking question', async () => {
    vi.mocked(chatService.askQuestionStreaming).mockImplementation(
      async (fId, request, onChunk, onComplete) => {
        onChunk('Response');
        if (onComplete) onComplete(undefined);
        return { suggested_timestamp: undefined };
      }
    );
    vi.mocked(chatService.getHistory).mockResolvedValue({
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [
        {
          message_id: 'msg-1',
          role: 'user' as const,
          content: 'Test question',
          timestamp: '2024-01-15T10:00:00Z',
          token_count: 0,
        },
        {
          message_id: 'msg-2',
          role: 'assistant' as const,
          content: 'Response',
          timestamp: '2024-01-15T10:00:01Z',
          token_count: 0,
        },
      ],
      total_messages: 2,
      total_tokens: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:01Z',
    });

    const { result } = renderHook(() => useChat(fileId));

    await act(async () => {
      await result.current.askQuestion('Test question');
    });

    expect(chatService.askQuestionStreaming).toHaveBeenCalledWith(
      fileId,
      expect.objectContaining({
        question: 'Test question',
      }),
      expect.any(Function),
      expect.any(Function)
    );
  });
});
