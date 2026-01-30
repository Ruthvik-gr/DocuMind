/**
 * Custom hook for summary functionality
 */
import { useState } from 'react';
import { summaryService } from '../services/summaryService';
import { SummaryType, SummaryListResponse } from '../types/summary.types';

export const useSummary = (fileId: string) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [summaries, setSummaries] = useState<SummaryListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generateSummary = async (summaryType: SummaryType) => {
    setIsGenerating(true);
    setError(null);

    try {
      await summaryService.generate(fileId, { summary_type: summaryType });

      // Refresh summaries list
      await loadSummaries();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate summary';
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const loadSummaries = async () => {
    try {
      const response = await summaryService.getSummaries(fileId);
      setSummaries(response);
    } catch (err) {
      console.error('Failed to load summaries:', err);
    }
  };

  return {
    generateSummary,
    loadSummaries,
    isGenerating,
    summaries,
    error,
  };
};
