/**
 * Summary service for API calls
 */
import api from './api';
import { SummaryRequest, SummaryResponse, SummaryListResponse } from '../types/summary.types';

export const summaryService = {
  /**
   * Generate a summary for a file
   */
  generate: async (
    fileId: string,
    request: SummaryRequest
  ): Promise<SummaryResponse> => {
    const response = await api.post<SummaryResponse>(
      `/summaries/${fileId}/generate`,
      request
    );
    return response.data;
  },

  /**
   * Get all summaries for a file
   */
  getSummaries: async (fileId: string): Promise<SummaryListResponse> => {
    const response = await api.get<SummaryListResponse>(`/summaries/${fileId}`);
    return response.data;
  },
};
