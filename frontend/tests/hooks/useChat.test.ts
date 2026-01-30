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
  });

  it('should ask question successfully', async () => {
    const mockResponse = {
      answer: 'Test answer',
      sources: ['source1'],
      chat_id: 'chat-123',
      timestamp: '2024-01-15T10:00:00Z',
    };

    const mockHistory = {
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [
        {
          message_id: 'msg-1',
          role: 'user' as const,
          content: 'Test question',
          timestamp: '2024-01-15T10:00:00Z',
        },
        {
          message_id: 'msg-2',
          role: 'assistant' as const,
          content: 'Test answer',
          timestamp: '2024-01-15T10:00:01Z',
        },
      ],
      total_messages: 2,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:01Z',
    };

    vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse);
    vi.mocked(chatService.getHistory).mockResolvedValue(mockHistory);

    const { result } = renderHook(() => useChat(fileId));

    let response;
    await act(async () => {
      response = await result.current.askQuestion('Test question');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(response).toEqual(mockResponse);
    expect(result.current.chatHistory).toEqual(mockHistory);
    expect(result.current.error).toBeNull();
  });

  it('should handle ask question error', async () => {
    const errorMessage = 'Failed to get answer';
    vi.mocked(chatService.askQuestion).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useChat(fileId));

    let response;
    await act(async () => {
      response = await result.current.askQuestion('Test question');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(response).toBeNull();
    expect(result.current.error).toBe(errorMessage);
  });

  it('should load chat history successfully', async () => {
    const mockHistory = {
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [],
      total_messages: 0,
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
    let resolveQuestion: any;
    const questionPromise = new Promise((resolve) => {
      resolveQuestion = resolve;
    });

    vi.mocked(chatService.askQuestion).mockReturnValue(questionPromise as any);
    vi.mocked(chatService.getHistory).mockResolvedValue({
      chat_id: 'chat-123',
      file_id: fileId,
      messages: [],
      total_messages: 0,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    });

    const { result } = renderHook(() => useChat(fileId));

    act(() => {
      result.current.askQuestion('Test');
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolveQuestion({
        answer: 'Test',
        sources: [],
        chat_id: 'chat-123',
        timestamp: '2024-01-15T10:00:00Z',
      });
      await questionPromise;
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });
});
