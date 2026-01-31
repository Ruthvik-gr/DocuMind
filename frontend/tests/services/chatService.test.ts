import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { chatService } from '../../src/services/chatService';
import api from '../../src/services/api';

vi.mock('../../src/services/api');

// Helper to create a mock ReadableStream
function createMockStream(chunks: string[]) {
  let index = 0;
  return {
    getReader: () => ({
      read: async () => {
        if (index < chunks.length) {
          const value = new TextEncoder().encode(chunks[index++]);
          return { done: false, value };
        }
        return { done: true, value: undefined };
      },
      releaseLock: vi.fn(),
    }),
  };
}

describe('chatService', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(() => 'test-token'),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('askQuestion', () => {
    it('should ask question successfully', async () => {
      const mockResponse = {
        data: {
          answer: 'This is the answer',
          sources: ['source1', 'source2'],
          chat_id: 'test-chat-id',
          timestamp: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const request = {
        question: 'What is this about?',
        chat_history: [],
      };

      const result = await chatService.askQuestion('test-file-id', request);

      expect(api.post).toHaveBeenCalledWith('/chat/test-file-id/ask', request);
      expect(result).toEqual(mockResponse.data);
      expect(result.answer).toBe('This is the answer');
    });

    it('should handle ask question error', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Failed to get answer'));

      const request = {
        question: 'What is this?',
        chat_history: [],
      };

      await expect(chatService.askQuestion('test-file-id', request)).rejects.toThrow(
        'Failed to get answer'
      );
    });
  });

  describe('getHistory', () => {
    it('should get chat history successfully', async () => {
      const mockResponse = {
        data: {
          chat_id: 'test-chat-id',
          file_id: 'test-file-id',
          messages: [
            {
              message_id: 'msg-1',
              role: 'user',
              content: 'Hello',
              timestamp: '2024-01-15T10:00:00Z',
            },
            {
              message_id: 'msg-2',
              role: 'assistant',
              content: 'Hi there',
              timestamp: '2024-01-15T10:00:01Z',
            },
          ],
          total_messages: 2,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await chatService.getHistory('test-file-id');

      expect(api.get).toHaveBeenCalledWith('/chat/test-file-id/history');
      expect(result).toEqual(mockResponse.data);
      expect(result.messages).toHaveLength(2);
    });

    it('should handle get history error', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('History not found'));

      await expect(chatService.getHistory('test-file-id')).rejects.toThrow('History not found');
    });
  });

  describe('askQuestionStreaming', () => {
    it('should handle streaming response with content chunks', async () => {
      const mockStream = createMockStream([
        'data: {"type":"content","content":"Hello "}\n\n',
        'data: {"type":"content","content":"world"}\n\n',
        'data: {"type":"done"}\n\n',
      ]);

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      const onChunk = vi.fn();
      const onComplete = vi.fn();

      await chatService.askQuestionStreaming(
        'test-file-id',
        { question: 'Test question' },
        onChunk,
        onComplete
      );

      expect(onChunk).toHaveBeenCalledWith('Hello ');
      expect(onChunk).toHaveBeenCalledWith('world');
      expect(onComplete).toHaveBeenCalled();
    });

    it('should handle streaming response with suggested timestamp', async () => {
      const mockStream = createMockStream([
        'data: {"type":"content","content":"Answer"}\n\n',
        'data: {"type":"done","suggested_timestamp":30}\n\n',
      ]);

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      const onChunk = vi.fn();
      const onComplete = vi.fn();

      const result = await chatService.askQuestionStreaming(
        'test-file-id',
        { question: 'Test question' },
        onChunk,
        onComplete
      );

      expect(result.suggested_timestamp).toBe(30);
      expect(onComplete).toHaveBeenCalledWith(30);
    });

    it('should handle HTTP error response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
      });

      const onChunk = vi.fn();

      await expect(
        chatService.askQuestionStreaming(
          'test-file-id',
          { question: 'Test question' },
          onChunk
        )
      ).rejects.toThrow('HTTP error! status: 500');
    });

    it('should log streaming error event', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      const mockStream = createMockStream([
        'data: {"type":"error","error":"Something went wrong"}\n\n',
      ]);

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      const onChunk = vi.fn();

      // The error is caught and logged, not thrown
      await chatService.askQuestionStreaming(
        'test-file-id',
        { question: 'Test question' },
        onChunk
      );

      expect(consoleErrorSpy).toHaveBeenCalled();
      consoleErrorSpy.mockRestore();
    });

    it('should include authorization header', async () => {
      const mockStream = createMockStream([
        'data: {"type":"done"}\n\n',
      ]);

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        body: mockStream,
      });

      await chatService.askQuestionStreaming(
        'test-file-id',
        { question: 'Test question' },
        vi.fn()
      );

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });
  });
});
