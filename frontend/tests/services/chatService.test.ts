import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chatService } from '../../src/services/chatService';
import api from '../../src/services/api';

vi.mock('../../src/services/api');

describe('chatService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
