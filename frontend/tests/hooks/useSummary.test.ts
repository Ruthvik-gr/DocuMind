import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSummary } from '../../src/hooks/useSummary';
import { summaryService } from '../../src/services/summaryService';

vi.mock('../../src/services/summaryService');

describe('useSummary', () => {
  const fileId = 'test-file-id';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useSummary(fileId));

    expect(result.current.isGenerating).toBe(false);
    expect(result.current.summaries).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should generate summary successfully', async () => {
    const mockSummaryResponse = {
      summary_id: 'summary-123',
      file_id: fileId,
      summary_type: 'brief' as const,
      content: 'Test summary',
      created_at: '2024-01-15T10:00:00Z',
    };

    const mockSummariesList = {
      file_id: fileId,
      summaries: [mockSummaryResponse],
      total: 1,
    };

    vi.mocked(summaryService.generate).mockResolvedValue(mockSummaryResponse);
    vi.mocked(summaryService.getSummaries).mockResolvedValue(mockSummariesList);

    const { result } = renderHook(() => useSummary(fileId));

    await act(async () => {
      await result.current.generateSummary('brief');
    });

    await waitFor(() => {
      expect(result.current.isGenerating).toBe(false);
    });

    expect(result.current.summaries).toEqual(mockSummariesList);
    expect(result.current.error).toBeNull();
  });

  it('should handle generate summary error', async () => {
    const errorMessage = 'Failed to generate summary';
    vi.mocked(summaryService.generate).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useSummary(fileId));

    await act(async () => {
      await result.current.generateSummary('brief');
    });

    await waitFor(() => {
      expect(result.current.isGenerating).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
  });

  it('should load summaries successfully', async () => {
    const mockSummariesList = {
      file_id: fileId,
      summaries: [
        {
          summary_id: 'summary-1',
          file_id: fileId,
          summary_type: 'brief' as const,
          content: 'Brief summary',
          created_at: '2024-01-15T10:00:00Z',
        },
        {
          summary_id: 'summary-2',
          file_id: fileId,
          summary_type: 'detailed' as const,
          content: 'Detailed summary',
          created_at: '2024-01-15T10:01:00Z',
        },
      ],
      total: 2,
    };

    vi.mocked(summaryService.getSummaries).mockResolvedValue(mockSummariesList);

    const { result } = renderHook(() => useSummary(fileId));

    await act(async () => {
      await result.current.loadSummaries();
    });

    await waitFor(() => {
      expect(result.current.summaries).toEqual(mockSummariesList);
    });
  });

  it('should handle load summaries error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(summaryService.getSummaries).mockRejectedValue(new Error('Failed to load'));

    const { result } = renderHook(() => useSummary(fileId));

    await act(async () => {
      await result.current.loadSummaries();
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(result.current.summaries).toBeNull();

    consoleErrorSpy.mockRestore();
  });

  it('should set isGenerating to true during generation', async () => {
    let resolveGenerate: any;
    const generatePromise = new Promise((resolve) => {
      resolveGenerate = resolve;
    });

    vi.mocked(summaryService.generate).mockReturnValue(generatePromise as any);
    vi.mocked(summaryService.getSummaries).mockResolvedValue({
      file_id: fileId,
      summaries: [],
      total: 0,
    });

    const { result } = renderHook(() => useSummary(fileId));

    act(() => {
      result.current.generateSummary('brief');
    });

    expect(result.current.isGenerating).toBe(true);

    await act(async () => {
      resolveGenerate({
        summary_id: 'summary-123',
        file_id: fileId,
        summary_type: 'brief',
        content: 'Test',
        created_at: '2024-01-15T10:00:00Z',
      });
      await generatePromise;
    });

    await waitFor(() => {
      expect(result.current.isGenerating).toBe(false);
    });
  });

  it('should generate different summary types', async () => {
    const generateMock = vi.mocked(summaryService.generate);
    generateMock.mockResolvedValue({
      summary_id: 'summary-123',
      file_id: fileId,
      summary_type: 'detailed',
      content: 'Test',
      created_at: '2024-01-15T10:00:00Z',
    });

    vi.mocked(summaryService.getSummaries).mockResolvedValue({
      file_id: fileId,
      summaries: [],
      total: 0,
    });

    const { result } = renderHook(() => useSummary(fileId));

    await act(async () => {
      await result.current.generateSummary('detailed');
    });

    expect(generateMock).toHaveBeenCalledWith(fileId, { summary_type: 'detailed' });

    await act(async () => {
      await result.current.generateSummary('key_points');
    });

    expect(generateMock).toHaveBeenCalledWith(fileId, { summary_type: 'key_points' });
  });
});
