/**
 * Custom hook for file upload functionality
 */
import { useState } from 'react';
import { fileService } from '../services/fileService';
import { FileUploadResponse } from '../types/file.types';

export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<FileUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response = await fileService.upload(file, (progress) => {
        setUploadProgress(progress);
      });

      setUploadedFile(response);
      setUploadProgress(100);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setUploadProgress(0);
    setError(null);
  };

  return {
    uploadFile,
    resetUpload,
    isUploading,
    uploadProgress,
    uploadedFile,
    error,
  };
};
