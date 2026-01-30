/**
 * Timestamp service for API calls
 */
import api from './api';
import { TimestampResponse } from '../types/timestamp.types';

export const timestampService = {
  /**
   * Extract timestamps from a file
   */
  extract: async (fileId: string): Promise<TimestampResponse> => {
    const response = await api.post<TimestampResponse>(`/timestamps/${fileId}/extract`);
    return response.data;
  },

  /**
   * Get timestamps for a file
   */
  getTimestamps: async (fileId: string): Promise<TimestampResponse> => {
    const response = await api.get<TimestampResponse>(`/timestamps/${fileId}`);
    return response.data;
  },
};
