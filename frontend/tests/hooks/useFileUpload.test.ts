import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFileUpload } from '../../src/hooks/useFileUpload';
import { fileService } from '../../src/services/fileService';

vi.mock('../../src/services/fileService');

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useFileUpload());

    expect(result.current.isUploading).toBe(false);
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.uploadedFile).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should upload file successfully', async () => {
    const mockResponse = {
      file_id: 'test-file-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    vi.mocked(fileService.upload).mockImplementation(async (file, onProgress) => {
      if (onProgress) {
        onProgress(50);
        onProgress(100);
      }
      return mockResponse;
    });

    const { result } = renderHook(() => useFileUpload());
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    let uploadResult;
    await act(async () => {
      uploadResult = await result.current.uploadFile(file);
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    expect(uploadResult).toEqual(mockResponse);
    expect(result.current.uploadedFile).toEqual(mockResponse);
    expect(result.current.uploadProgress).toBe(100);
    expect(result.current.error).toBeNull();
  });

  it('should handle upload error', async () => {
    const errorMessage = 'Upload failed';
    vi.mocked(fileService.upload).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useFileUpload());
    const file = new File(['test'], 'test.pdf');

    await act(async () => {
      try {
        await result.current.uploadFile(file);
      } catch (error) {
        // Expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.isUploading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.uploadedFile).toBeNull();
  });

  it('should update upload progress during upload', async () => {
    vi.mocked(fileService.upload).mockImplementation(async (file, onProgress) => {
      if (onProgress) {
        onProgress(25);
        onProgress(50);
        onProgress(75);
      }
      return {
        file_id: 'test',
        filename: 'test.pdf',
        file_type: 'pdf' as const,
        file_size: 1024,
        processing_status: 'pending' as const,
        upload_date: '2024-01-15T10:00:00Z',
      };
    });

    const { result } = renderHook(() => useFileUpload());
    const file = new File(['test'], 'test.pdf');

    await act(async () => {
      await result.current.uploadFile(file);
    });

    // Progress should be 100 after successful upload
    expect(result.current.uploadProgress).toBe(100);
  });

  it('should reset upload state', async () => {
    const mockResponse = {
      file_id: 'test-file-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    vi.mocked(fileService.upload).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useFileUpload());
    const file = new File(['test'], 'test.pdf');

    await act(async () => {
      await result.current.uploadFile(file);
    });

    expect(result.current.uploadedFile).not.toBeNull();

    act(() => {
      result.current.resetUpload();
    });

    expect(result.current.uploadedFile).toBeNull();
    expect(result.current.uploadProgress).toBe(0);
    expect(result.current.error).toBeNull();
  });

  it('should set isUploading to true during upload', async () => {
    let resolveUpload: any;
    const uploadPromise = new Promise((resolve) => {
      resolveUpload = resolve;
    });

    vi.mocked(fileService.upload).mockReturnValue(uploadPromise as any);

    const { result } = renderHook(() => useFileUpload());
    const file = new File(['test'], 'test.pdf');

    act(() => {
      result.current.uploadFile(file);
    });

    // Should be uploading
    expect(result.current.isUploading).toBe(true);

    // Resolve upload
    await act(async () => {
      resolveUpload({
        file_id: 'test',
        filename: 'test.pdf',
        file_type: 'pdf',
        file_size: 1024,
        processing_status: 'pending',
        upload_date: '2024-01-15T10:00:00Z',
      });
      await uploadPromise;
    });

    expect(result.current.isUploading).toBe(false);
  });
});
