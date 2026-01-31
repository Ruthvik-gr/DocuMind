import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useSummary } from '../../hooks/useSummary';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
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
    <div className="space-y-6">
      {/* Generation Buttons */}
      <Card>
        <h3 className="text-lg font-semibold mb-4 text-gray-900">Generate Summary</h3>
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={() => handleGenerate(SummaryType.BRIEF)}
            disabled={isGenerating}
            variant="primary"
          >
            Brief Summary
          </Button>
          <Button
            onClick={() => handleGenerate(SummaryType.DETAILED)}
            disabled={isGenerating}
            variant="primary"
          >
            Detailed Summary
          </Button>
          <Button
            onClick={() => handleGenerate(SummaryType.KEY_POINTS)}
            disabled={isGenerating}
            variant="primary"
          >
            Key Points
          </Button>
        </div>

        {isGenerating && (
          <div className="mt-4 flex items-center gap-2 text-blue-600">
            <Spinner size="sm" />
            <span className="text-sm">Generating summary...</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </Card>

      {/* Summaries List */}
      {summaries && summaries.count > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Summaries</h3>
          {summaries.summaries.map((summary) => (
            <Card key={summary.summary_id}>
              <div className="mb-3">
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
                  {getSummaryTypeLabel(summary.summary_type)}
                </span>
                <span className="ml-2 text-xs text-gray-500">
                  {new Date(summary.created_at).toLocaleString()}
                </span>
              </div>
              <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-strong:font-semibold text-gray-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {summary.content}
                </ReactMarkdown>
              </div>
              <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                <span>Model: {summary.model_used}</span>
                <span className="ml-4">Tokens: {summary.token_count.total}</span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {summaries && summaries.count === 0 && !isGenerating && (
        <Card>
          <p className="text-center text-gray-500">
            No summaries yet. Generate one using the buttons above.
          </p>
        </Card>
      )}
    </div>
  );
};
