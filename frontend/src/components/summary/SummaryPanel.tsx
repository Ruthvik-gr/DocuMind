import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSummary } from '../../hooks/useSummary';
import { Spinner } from '../common/Spinner';
import { SummaryType } from '../../types/summary.types';

interface SummaryPanelProps {
  fileId: string;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({ fileId }) => {
  const { generateSummary, loadSummaries, isGenerating, summaries, error } = useSummary(fileId);

  useEffect(() => {
    loadSummaries();
  }, [fileId]);

  const handleGenerate = (type: SummaryType) => {
    generateSummary(type);
  };

  const getSummaryTypeLabel = (type: SummaryType): string => {
    const labels = {
      [SummaryType.BRIEF]: 'Brief',
      [SummaryType.DETAILED]: 'Detailed',
      [SummaryType.KEY_POINTS]: 'Key Points',
    };
    return labels[type];
  };

  return (
    <div className="h-[500px] flex flex-col bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Header with Generation Buttons */}
      <div className="px-5 py-3.5 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Summaries</h3>
            <p className="text-xs text-gray-500">Generate AI summaries</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => handleGenerate(SummaryType.BRIEF)}
            disabled={isGenerating}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Brief
          </button>
          <button
            onClick={() => handleGenerate(SummaryType.DETAILED)}
            disabled={isGenerating}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Detailed
          </button>
          <button
            onClick={() => handleGenerate(SummaryType.KEY_POINTS)}
            disabled={isGenerating}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Key Points
          </button>
        </div>

        {isGenerating && (
          <div className="mt-3 flex items-center gap-2 text-purple-600">
            <Spinner size="sm" />
            <span className="text-xs">Generating summary...</span>
          </div>
        )}

        {error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-100 rounded-lg">
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Summaries List */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {summaries && summaries.count > 0 ? (
          <div className="space-y-3">
            {summaries.summaries.map((summary) => (
              <div key={summary.summary_id} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="inline-block px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-md">
                    {getSummaryTypeLabel(summary.summary_type)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(summary.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-sm prose-p:my-1 prose-p:text-xs prose-ul:my-1 prose-ul:text-xs prose-ol:my-1 prose-ol:text-xs prose-li:my-0 prose-strong:font-semibold text-gray-700 text-xs leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {summary.content}
                  </ReactMarkdown>
                </div>
                <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-3 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    {summary.model_used}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                    {summary.token_count.total} tokens
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : !isGenerating ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <svg className="w-12 h-12 mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm">No summaries yet</p>
            <p className="text-xs mt-1">Generate one using the buttons above</p>
          </div>
        ) : null}
      </div>
    </div>
  );
};
