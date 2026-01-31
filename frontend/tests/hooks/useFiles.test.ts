import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFiles } from '../../src/hooks/useFiles';
import { fileService } from '../../src/services/fileService';
import { FileType, ProcessingStatus } from '../../src/types/file.types';

vi.mock('../../src/services/fileService');

describe('useFiles Hook', () => {
  const mockFiles = [
    {
      file_id: 'file-1',
      filename: 'test.pdf',
      file_type: FileType.PDF,
      file_size: 1024,
      processing_status: ProcessingStatus.COMPLETED,
      created_at: '2024-01-15T10:00:00Z',
      has_chat: true,
    },
    {
      file_id: 'file-2',
      filename: 'audio.mp3',
      file_type: FileType.AUDIO,
      file_size: 2048,
      processing_status: ProcessingStatus.PROCESSING,
      created_at: '2024-01-14T10:00:00Z',
      has_chat: false,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fileService.listFiles).mockResolvedValue({
      files: mockFiles,
      total: 2,
    });
  });

  it('fetches files on mount', async () => {
    const { result } = renderHook(() => useFiles());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(fileService.listFiles).toHaveBeenCalled();
    expect(result.current.files).toEqual(mockFiles);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch error', async () => {
    vi.mocked(fileService.listFiles).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.files).toEqual([]);
  });

  it('handles non-Error fetch failure', async () => {
    vi.mocked(fileService.listFiles).mockRejectedValue('Unknown error');

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load files');
  });

  it('selects a file', async () => {
    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.selectFile('file-1');
    });

    expect(result.current.selectedFileId).toBe('file-1');
  });

  it('refreshes files', async () => {
    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(fileService.listFiles).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refreshFiles();
    });

    expect(fileService.listFiles).toHaveBeenCalledTimes(2);
  });

  it('deletes a file', async () => {
    vi.mocked(fileService.deleteFile).mockResolvedValue(undefined);

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.files).toHaveLength(2);

    await act(async () => {
      await result.current.deleteFile('file-1');
    });

    expect(fileService.deleteFile).toHaveBeenCalledWith('file-1');
    expect(result.current.files).toHaveLength(1);
    expect(result.current.files[0].file_id).toBe('file-2');
  });

  it('clears selected file when it is deleted', async () => {
    vi.mocked(fileService.deleteFile).mockResolvedValue(undefined);

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.selectFile('file-1');
    });

    expect(result.current.selectedFileId).toBe('file-1');

    await act(async () => {
      await result.current.deleteFile('file-1');
    });

    expect(result.current.selectedFileId).toBeNull();
  });

  it('keeps selected file when different file is deleted', async () => {
    vi.mocked(fileService.deleteFile).mockResolvedValue(undefined);

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.selectFile('file-1');
    });

    await act(async () => {
      await result.current.deleteFile('file-2');
    });

    expect(result.current.selectedFileId).toBe('file-1');
  });

  it('throws error when delete fails', async () => {
    vi.mocked(fileService.deleteFile).mockRejectedValue(new Error('Delete failed'));

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      act(async () => {
        await result.current.deleteFile('file-1');
      })
    ).rejects.toThrow('Delete failed');
  });

  it('throws generic error when delete fails with non-Error', async () => {
    vi.mocked(fileService.deleteFile).mockRejectedValue('Unknown error');

    const { result } = renderHook(() => useFiles());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      act(async () => {
        await result.current.deleteFile('file-1');
      })
    ).rejects.toThrow('Failed to delete file');
  });
});
