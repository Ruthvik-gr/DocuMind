import { describe, it, expect, vi, beforeEach } from 'vitest';
import { summaryService } from '../../src/services/summaryService';
import api from '../../src/services/api';

vi.mock('../../src/services/api');

describe('summaryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('generate', () => {
    it('should generate summary successfully', async () => {
      const mockResponse = {
        data: {
          summary_id: 'test-summary-id',
          file_id: 'test-file-id',
          summary_type: 'brief',
          content: 'This is a brief summary',
          created_at: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const request = {
        summary_type: 'brief' as const,
      };

      const result = await summaryService.generate('test-file-id', request);

      expect(api.post).toHaveBeenCalledWith('/summaries/test-file-id/generate', request);
      expect(result).toEqual(mockResponse.data);
      expect(result.summary_type).toBe('brief');
    });

    it('should generate detailed summary', async () => {
      const mockResponse = {
        data: {
          summary_id: 'test-summary-id',
          file_id: 'test-file-id',
          summary_type: 'detailed',
          content: 'This is a detailed summary with more information',
          created_at: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const request = {
        summary_type: 'detailed' as const,
      };

      const result = await summaryService.generate('test-file-id', request);

      expect(result.summary_type).toBe('detailed');
    });

    it('should handle generate error', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Failed to generate summary'));

      const request = {
        summary_type: 'brief' as const,
      };

      await expect(summaryService.generate('test-file-id', request)).rejects.toThrow(
        'Failed to generate summary'
      );
    });
  });

  describe('getSummaries', () => {
    it('should get summaries successfully', async () => {
      const mockResponse = {
        data: {
          file_id: 'test-file-id',
          summaries: [
            {
              summary_id: 'summary-1',
              summary_type: 'brief',
              content: 'Brief summary',
              created_at: '2024-01-15T10:00:00Z',
            },
            {
              summary_id: 'summary-2',
              summary_type: 'detailed',
              content: 'Detailed summary',
              created_at: '2024-01-15T10:01:00Z',
            },
          ],
          total: 2,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await summaryService.getSummaries('test-file-id');

      expect(api.get).toHaveBeenCalledWith('/summaries/test-file-id');
      expect(result).toEqual(mockResponse.data);
      expect(result.summaries).toHaveLength(2);
    });

    it('should handle get summaries error', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Summaries not found'));

      await expect(summaryService.getSummaries('test-file-id')).rejects.toThrow(
        'Summaries not found'
      );
    });
  });
});
