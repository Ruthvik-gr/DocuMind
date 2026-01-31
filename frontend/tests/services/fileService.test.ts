import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fileService } from '../../src/services/fileService';
import api from '../../src/services/api';

// Mock the API module
vi.mock('../../src/services/api');

describe('fileService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('upload', () => {
    it('should upload file successfully', async () => {
      const mockResponse = {
        data: {
          file_id: 'test-file-id',
          filename: 'test.pdf',
          file_type: 'pdf',
          file_size: 1024,
          processing_status: 'pending',
          upload_date: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const result = await fileService.upload(file);

      expect(api.post).toHaveBeenCalledWith(
        '/files/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should call onProgress callback during upload', async () => {
      const mockResponse = {
        data: {
          file_id: 'test-file-id',
          filename: 'test.pdf',
        },
      };

      vi.mocked(api.post).mockImplementation((url, data, config) => {
        // Simulate upload progress
        if (config?.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: 100 } as any);
        }
        return Promise.resolve(mockResponse);
      });

      const onProgress = vi.fn();
      const file = new File(['test'], 'test.pdf');

      await fileService.upload(file, onProgress);

      expect(onProgress).toHaveBeenCalledWith(50);
    });

    it('should handle upload error', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Upload failed'));

      const file = new File(['test'], 'test.pdf');

      await expect(fileService.upload(file)).rejects.toThrow('Upload failed');
    });
  });

  describe('getFile', () => {
    it('should get file details successfully', async () => {
      const mockResponse = {
        data: {
          file_id: 'test-file-id',
          filename: 'test.pdf',
          file_type: 'pdf',
          file_size: 1024,
          processing_status: 'completed',
          upload_date: '2024-01-15T10:00:00Z',
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await fileService.getFile('test-file-id');

      expect(api.get).toHaveBeenCalledWith('/files/test-file-id');
      expect(result).toHaveProperty('file_url');
      expect(result.file_url).toContain('/files/test-file-id/stream');
    });

    it('should handle get file error', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('File not found'));

      await expect(fileService.getFile('invalid-id')).rejects.toThrow('File not found');
    });
  });

  describe('listFiles', () => {
    it('should list files successfully', async () => {
      const mockResponse = {
        data: {
          files: [
            {
              file_id: 'file-1',
              filename: 'test1.pdf',
              file_type: 'pdf',
              file_size: 1024,
              processing_status: 'completed',
              created_at: '2024-01-15T10:00:00Z',
              has_chat: true,
            },
            {
              file_id: 'file-2',
              filename: 'test2.mp4',
              file_type: 'video',
              file_size: 2048,
              processing_status: 'completed',
              created_at: '2024-01-15T11:00:00Z',
              has_chat: false,
            },
          ],
          total: 2,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await fileService.listFiles();

      expect(api.get).toHaveBeenCalledWith('/files/');
      expect(result.files).toHaveLength(2);
      expect(result.total).toBe(2);
    });

    it('should handle list files error', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Failed to list files'));

      await expect(fileService.listFiles()).rejects.toThrow('Failed to list files');
    });
  });

  describe('deleteFile', () => {
    it('should delete file successfully', async () => {
      vi.mocked(api.delete).mockResolvedValue({});

      await fileService.deleteFile('test-file-id');

      expect(api.delete).toHaveBeenCalledWith('/files/test-file-id');
    });

    it('should handle delete file error', async () => {
      vi.mocked(api.delete).mockRejectedValue(new Error('Failed to delete'));

      await expect(fileService.deleteFile('test-file-id')).rejects.toThrow('Failed to delete');
    });
  });
});
