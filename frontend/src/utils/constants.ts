/**
 * Application constants
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const ALLOWED_FILE_TYPES = {
  PDF: ['application/pdf'],
  AUDIO: ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-m4a'],
  VIDEO: ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'],
};

export const MAX_FILE_SIZE_MB = 200;

export const FILE_TYPE_LABELS = {
  pdf: 'PDF Document',
  audio: 'Audio File',
  video: 'Video File',
};

export const PROCESSING_STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
};

/**
 * Format file size in bytes to human readable string
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};
