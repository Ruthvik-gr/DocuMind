/**
 * Hook for managing file list
 */
import { useState, useEffect, useCallback } from 'react';
import { fileService } from '../services/fileService';
import { FileListItem } from '../types/file.types';

interface UseFilesReturn {
  files: FileListItem[];
  isLoading: boolean;
  error: string | null;
  selectedFileId: string | null;
  selectFile: (fileId: string) => void;
  refreshFiles: () => Promise<void>;
  deleteFile: (fileId: string) => Promise<void>;
}

export const useFiles = (): UseFilesReturn => {
  const [files, setFiles] = useState<FileListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);

  const fetchFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fileService.listFiles();
      setFiles(response.files);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load files';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const selectFile = useCallback((fileId: string) => {
    setSelectedFileId(fileId);
  }, []);

  const deleteFile = useCallback(async (fileId: string) => {
    try {
      await fileService.deleteFile(fileId);
      setFiles((prevFiles) => prevFiles.filter((f) => f.file_id !== fileId));
      if (selectedFileId === fileId) {
        setSelectedFileId(null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete file';
      throw new Error(errorMessage);
    }
  }, [selectedFileId]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  return {
    files,
    isLoading,
    error,
    selectedFileId,
    selectFile,
    refreshFiles: fetchFiles,
    deleteFile,
  };
};
