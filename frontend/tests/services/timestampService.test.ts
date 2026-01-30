import { describe, it, expect, vi, beforeEach } from 'vitest';
import { timestampService } from '../../src/services/timestampService';
import api from '../../src/services/api';

vi.mock('../../src/services/api');

describe('timestampService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('extract', () => {
    it('should extract timestamps successfully', async () => {
      const mockResponse = {
        data: {
          timestamp_id: 'test-timestamp-id',
          file_id: 'test-file-id',
          timestamps: [
            {
              timestamp_entry_id: 'entry-1',
              time: 0,
              topic: 'Introduction',
              description: 'Overview of the content',
              keywords: ['intro', 'overview'],
            },
            {
              timestamp_entry_id: 'entry-2',
              time: 120,
              topic: 'Main Topic',
              description: 'Detailed discussion',
              keywords: ['main', 'discussion'],
            },
          ],
          extraction_metadata: {
            total_topics: 2,
            extraction_method: 'groq-llama',
          },
          created_at: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await timestampService.extract('test-file-id');

      expect(api.post).toHaveBeenCalledWith('/timestamps/test-file-id/extract');
      expect(result).toEqual(mockResponse.data);
      expect(result.timestamps).toHaveLength(2);
    });

    it('should handle extract error', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Failed to extract timestamps'));

      await expect(timestampService.extract('test-file-id')).rejects.toThrow(
        'Failed to extract timestamps'
      );
    });
  });

  describe('getTimestamps', () => {
    it('should get timestamps successfully', async () => {
      const mockResponse = {
        data: {
          timestamp_id: 'test-timestamp-id',
          file_id: 'test-file-id',
          timestamps: [
            {
              timestamp_entry_id: 'entry-1',
              time: 0,
              topic: 'Intro',
              description: 'Introduction',
              keywords: [],
            },
          ],
          extraction_metadata: {
            total_topics: 1,
          },
          created_at: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await timestampService.getTimestamps('test-file-id');

      expect(api.get).toHaveBeenCalledWith('/timestamps/test-file-id');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle get timestamps error', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Timestamps not found'));

      await expect(timestampService.getTimestamps('test-file-id')).rejects.toThrow(
        'Timestamps not found'
      );
    });
  });
});
