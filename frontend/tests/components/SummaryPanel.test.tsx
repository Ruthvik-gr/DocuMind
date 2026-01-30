import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SummaryPanel } from '../../src/components/summary/SummaryPanel';
import * as useSummaryModule from '../../src/hooks/useSummary';
import { SummaryType } from '../../src/types/summary.types';

vi.mock('../../src/hooks/useSummary');

describe('SummaryPanel Component', () => {
  const mockGenerateSummary = vi.fn();
  const mockLoadSummaries = vi.fn();
  const fileId = 'test-file-id';

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: null,
      error: null,
    });
  });

  it('renders summary generation buttons', () => {
    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText('Brief Summary')).toBeInTheDocument();
    expect(screen.getByText('Detailed Summary')).toBeInTheDocument();
    expect(screen.getByText('Key Points')).toBeInTheDocument();
  });

  it('loads summaries on mount', () => {
    render(<SummaryPanel fileId={fileId} />);

    expect(mockLoadSummaries).toHaveBeenCalled();
  });

  it('loads summaries when fileId changes', () => {
    const { rerender } = render(<SummaryPanel fileId="file-1" />);

    expect(mockLoadSummaries).toHaveBeenCalledTimes(1);

    rerender(<SummaryPanel fileId="file-2" />);

    expect(mockLoadSummaries).toHaveBeenCalledTimes(2);
  });

  it('generates brief summary when button clicked', async () => {
    const user = userEvent.setup();
    render(<SummaryPanel fileId={fileId} />);

    const briefButton = screen.getByText('Brief Summary');
    await user.click(briefButton);

    await waitFor(() => {
      expect(mockGenerateSummary).toHaveBeenCalledWith(SummaryType.BRIEF);
    });
  });

  it('generates detailed summary when button clicked', async () => {
    const user = userEvent.setup();
    render(<SummaryPanel fileId={fileId} />);

    const detailedButton = screen.getByText('Detailed Summary');
    await user.click(detailedButton);

    await waitFor(() => {
      expect(mockGenerateSummary).toHaveBeenCalledWith(SummaryType.DETAILED);
    });
  });

  it('generates key points summary when button clicked', async () => {
    const user = userEvent.setup();
    render(<SummaryPanel fileId={fileId} />);

    const keyPointsButton = screen.getByText('Key Points');
    await user.click(keyPointsButton);

    await waitFor(() => {
      expect(mockGenerateSummary).toHaveBeenCalledWith(SummaryType.KEY_POINTS);
    });
  });

  it('disables buttons when generating', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: true,
      summaries: null,
      error: null,
    });

    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText('Brief Summary')).toBeDisabled();
    expect(screen.getByText('Detailed Summary')).toBeDisabled();
    expect(screen.getByText('Key Points')).toBeDisabled();
  });

  it('displays loading indicator when generating', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: true,
      summaries: null,
      error: null,
    });

    render(<SummaryPanel fileId={fileId} />);

    // Spinner should be visible
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    expect(screen.getByText(/Generating summary/i)).toBeInTheDocument();
  });

  it('displays error message when error occurs', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: null,
      error: 'Failed to generate summary',
    });

    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText('Failed to generate summary')).toBeInTheDocument();
  });

  it('displays summaries when available', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: {
        summaries: [
          {
            summary_id: 'summary-1',
            file_id: fileId,
            summary_type: SummaryType.BRIEF,
            content: 'This is a brief summary of the document.',
            created_at: '2024-01-15T10:00:00Z',
            model_used: 'gpt-4',
            token_count: { input: 100, output: 50, total: 150 },
            parameters: { temperature: 0.3, max_tokens: 1000 },
          },
          {
            summary_id: 'summary-2',
            file_id: fileId,
            summary_type: SummaryType.DETAILED,
            content: 'This is a detailed summary with more information.',
            created_at: '2024-01-15T10:01:00Z',
            model_used: 'gpt-4',
            token_count: { input: 200, output: 100, total: 300 },
            parameters: { temperature: 0.3, max_tokens: 2000 },
          },
        ],
        count: 2,
      },
      error: null,
    });

    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText(/This is a brief summary/i)).toBeInTheDocument();
    expect(screen.getByText(/This is a detailed summary/i)).toBeInTheDocument();
  });

  it('displays summary type labels correctly', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: {
        summaries: [
          {
            summary_id: 'summary-1',
            file_id: fileId,
            summary_type: SummaryType.BRIEF,
            content: 'Test content',
            created_at: '2024-01-15T10:00:00Z',
            model_used: 'gpt-4',
            token_count: { input: 100, output: 50, total: 150 },
            parameters: { temperature: 0.3, max_tokens: 1000 },
          },
          {
            summary_id: 'summary-2',
            file_id: fileId,
            summary_type: SummaryType.KEY_POINTS,
            content: 'Test content',
            created_at: '2024-01-15T10:01:00Z',
            model_used: 'gpt-4',
            token_count: { input: 100, output: 50, total: 150 },
            parameters: { temperature: 0.3, max_tokens: 1000 },
          },
        ],
        count: 2,
      },
      error: null,
    });

    const { container } = render(<SummaryPanel fileId={fileId} />);

    // Check for labels in the summary type badges (not buttons)
    const badges = container.querySelectorAll('.bg-blue-100.text-blue-800');
    expect(badges[0]).toHaveTextContent('Brief');
    expect(badges[1]).toHaveTextContent('Key Points');
  });

  it('displays empty state when no summaries', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: {
        summaries: [],
        count: 0,
      },
      error: null,
    });

    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText(/No summaries yet/i)).toBeInTheDocument();
  });

  it('displays created date for summaries', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: {
        summaries: [
          {
            summary_id: 'summary-1',
            file_id: fileId,
            summary_type: SummaryType.BRIEF,
            content: 'Test content',
            created_at: '2024-01-15T10:00:00Z',
            model_used: 'gpt-4',
            token_count: { input: 100, output: 50, total: 150 },
            parameters: { temperature: 0.3, max_tokens: 1000 },
          },
        ],
        count: 1,
      },
      error: null,
    });

    const { container } = render(<SummaryPanel fileId={fileId} />);

    // Check that date is rendered in the component (formatted by toLocaleString)
    const dateText = container.querySelector('.text-xs.text-gray-500');
    expect(dateText).toBeInTheDocument();
  });

  it('enables buttons when not generating', () => {
    vi.mocked(useSummaryModule.useSummary).mockReturnValue({
      generateSummary: mockGenerateSummary,
      loadSummaries: mockLoadSummaries,
      isGenerating: false,
      summaries: null,
      error: null,
    });

    render(<SummaryPanel fileId={fileId} />);

    expect(screen.getByText('Brief Summary')).not.toBeDisabled();
    expect(screen.getByText('Detailed Summary')).not.toBeDisabled();
    expect(screen.getByText('Key Points')).not.toBeDisabled();
  });
});
