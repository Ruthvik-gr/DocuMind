/**
 * File service for API calls
 */
import api from './api';
import { FileUploadResponse, FileDetailResponse } from '../types/file.types';
import { API_BASE_URL } from '../utils/constants';

export const fileService = {
  /**
   * Upload a file
   */
  upload: async (
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<FileUploadResponse>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  /**
   * Get file details
   */
  getFile: async (fileId: string): Promise<FileDetailResponse> => {
    const response = await api.get<FileDetailResponse>(`/files/${fileId}`);
    const data = response.data;
    // Construct file URL for streaming
    data.file_url = `${API_BASE_URL}/files/${fileId}/stream`;
    return data;
  },
};
