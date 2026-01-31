import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HomePage } from '../../src/pages/HomePage';
import { FileType, ProcessingStatus } from '../../src/types/file.types';
import type { FileDetailResponse } from '../../src/types/file.types';
import type { TimestampResponse } from '../../src/types/timestamp.types';
import React from 'react';

// Mock services without factory to avoid hoisting issues
vi.mock('../../src/services/fileService');
vi.mock('../../src/services/timestampService');

// Mock the AuthContext
vi.mock('../../src/contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: { id: 'test-user-id', email: 'test@example.com', name: 'Test User' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    googleLogin: vi.fn(),
  }),
}));

// Mock the useFiles hook
vi.mock('../../src/hooks/useFiles', () => ({
  useFiles: () => ({
    files: [],
    isLoading: false,
    error: null,
    refreshFiles: vi.fn(),
    deleteFile: vi.fn(),
  }),
}));

// Mock child components with simple implementations
vi.mock('../../src/components/file/FileUpload', () => ({
  FileUpload: ({ onUploadSuccess }: any) => (
    <div data-testid="file-upload">
      <button
        onClick={() =>
          onUploadSuccess({ file_id: 'test-file-id' } as FileDetailResponse)
        }
      >
        Trigger Upload
      </button>
    </div>
  ),
}));

vi.mock('../../src/components/chat/ChatInterface', () => ({
  ChatInterface: ({ fileId }: { fileId: string }) => (
    <div data-testid="chat-interface">Chat for {fileId}</div>
  ),
}));

vi.mock('../../src/components/media/MediaPlayer', () => ({
  MediaPlayer: ({ fileUrl, timestamps }: any) => (
    <div data-testid="media-player">
      Player: {fileUrl} with {timestamps.length} timestamps
    </div>
  ),
}));

vi.mock('../../src/components/summary/SummaryPanel', () => ({
  SummaryPanel: ({ fileId }: { fileId: string }) => (
    <div data-testid="summary-panel">Summary for {fileId}</div>
  ),
}));

// Import mocked services after mocking
import { fileService } from '../../src/services/fileService';
import { timestampService } from '../../src/services/timestampService';

describe('HomePage', () => {
  const mockPDFFile: FileDetailResponse = {
    file_id: 'test-file-id',
    filename: 'test.pdf',
    file_type: FileType.PDF,
    file_size: 1024000,
    mime_type: 'application/pdf',
    processing_status: ProcessingStatus.COMPLETED,
    file_url: 'http://localhost:8000/storage/test.pdf',
    extracted_content: {
      text: 'Sample content',
      word_count: 100,
      language: 'en',
      extraction_method: 'PyPDF2',
    },
    upload_date: '2024-01-15T10:00:00Z',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  };

  const mockVideoFile: FileDetailResponse = {
    ...mockPDFFile,
    file_id: 'video-file-id',
    filename: 'test.mp4',
    file_type: FileType.VIDEO,
    mime_type: 'video/mp4',
    file_url: 'http://localhost:8000/storage/test.mp4',
  };

  const mockTimestamps: TimestampResponse = {
    timestamp_id: 'ts-id',
    file_id: 'video-file-id',
    timestamps: [
      {
        timestamp_entry_id: 'entry-1',
        time: 0,
        topic: 'Intro',
        description: 'Introduction',
        keywords: ['intro'],
        confidence: 0.9,
      },
    ],
    created_at: '2024-01-15T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fileService.getFile).mockResolvedValue(mockPDFFile);
    vi.mocked(timestampService.getTimestamps).mockRejectedValue(new Error('Not found'));
    vi.mocked(timestampService.extract).mockResolvedValue(mockTimestamps);
  });

  describe('Initial State', () => {
    it('renders header with title', () => {
      render(<HomePage />);
      // The title is in MainLayout header
      expect(screen.getByText('DocuMind')).toBeInTheDocument();
    });

    it('shows file upload component initially', () => {
      render(<HomePage />);
      expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    });

    it('shows upload section initially', () => {
      render(<HomePage />);
      // "Upload a File" appears both as a heading and button, use heading role
      expect(screen.getByRole('heading', { name: 'Upload a File' })).toBeInTheDocument();
    });
  });

  describe('PDF File Upload', () => {
    it('loads and displays PDF file information', async () => {
      render(<HomePage />);

      const uploadButton = screen.getByText('Trigger Upload');
      await userEvent.click(uploadButton);

      await waitFor(() => {
        expect(fileService.getFile).toHaveBeenCalledWith('test-file-id');
      });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText('PDF Document')).toBeInTheDocument();
        expect(screen.getByText('1000 KB')).toBeInTheDocument();
      });
    });

    it('displays word count for PDF', async () => {
      render(<HomePage />);

      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText(/100 words/)).toBeInTheDocument();
      });
    });

    it('does not show word count when content is missing', async () => {
      vi.mocked(fileService.getFile).mockResolvedValue({
        ...mockPDFFile,
        extracted_content: null,
      });

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      // Word count section should not be rendered when no content
      expect(screen.queryByText('Words:')).not.toBeInTheDocument();
    });

    it('renders ChatInterface and SummaryPanel for PDF', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
        expect(screen.getByTestId('summary-panel')).toBeInTheDocument();
        expect(screen.getByText('Chat for test-file-id')).toBeInTheDocument();
        expect(screen.getByText('Summary for test-file-id')).toBeInTheDocument();
      });
    });

    it('does not render MediaPlayer for PDF', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('media-player')).not.toBeInTheDocument();
    });

    it('shows "Upload New File" button after upload', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('Upload New File')).toBeInTheDocument();
      });
    });
  });

  describe('Video File Upload', () => {
    beforeEach(() => {
      fileService.getFile.mockResolvedValue(mockVideoFile);
    });

    it('renders MediaPlayer for video files', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByTestId('media-player')).toBeInTheDocument();
        expect(
          screen.getByText(/Player:.*test.mp4.*with 0 timestamps/)
        ).toBeInTheDocument();
      });
    });

    it('attempts to load existing timestamps for video', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      // Wait for the media player to be rendered
      await waitFor(() => {
        expect(screen.getByTestId('media-player')).toBeInTheDocument();
        // When timestamps don't exist, extract button is shown
        expect(screen.getByText('Extract Timestamps')).toBeInTheDocument();
      });

      // Verify timestamps service was attempted (mock should have been called)
      // The console log "No timestamps found yet" confirms the call was made
      expect(vi.mocked(timestampService.getTimestamps).mock.calls.length).toBeGreaterThan(0);
    });

    it('shows extract button when no timestamps exist', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText('Extract Timestamps')
        ).toBeInTheDocument();
      });
    });

    it('loads existing timestamps if available', async () => {
      timestampService.getTimestamps.mockResolvedValue(mockTimestamps);

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText(/Player:.*with 1 timestamps/)
        ).toBeInTheDocument();
      });

      expect(
        screen.queryByText('Extract Timestamps')
      ).not.toBeInTheDocument();
    });
  });

  describe('Timestamp Extraction', () => {
    beforeEach(() => {
      fileService.getFile.mockResolvedValue(mockVideoFile);
    });

    it('extracts timestamps when button clicked', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText('Extract Timestamps')
        ).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Extract Timestamps'));

      await waitFor(() => {
        expect(timestampService.extract).toHaveBeenCalledWith('video-file-id');
      });

      await waitFor(() => {
        expect(
          screen.getByText(/Player:.*with 1 timestamps/)
        ).toBeInTheDocument();
      });
    });

    it('handles extraction errors gracefully', async () => {
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      timestampService.extract.mockRejectedValue(new Error('Extraction failed'));

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText('Extract Timestamps')
        ).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Extract Timestamps'));

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
        expect(alertSpy).toHaveBeenCalledWith('Failed to extract timestamps');
      });

      alertSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });
  });

  describe('New Upload Flow', () => {
    it('resets state when "Upload New File" clicked', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Upload New File'));

      expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
      expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    });

    it('clears timestamps when starting new upload', async () => {
      fileService.getFile.mockResolvedValue(mockVideoFile);
      timestampService.getTimestamps.mockResolvedValue(mockTimestamps);

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText(/Player:.*with 1 timestamps/)
        ).toBeInTheDocument();
      });

      await userEvent.click(screen.getByText('Upload New File'));

      expect(screen.queryByTestId('media-player')).not.toBeInTheDocument();
      expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    });
  });

  describe('Processing States', () => {
    it('shows processing message while file is being processed', async () => {
      // Clear default mock and set processing status
      vi.mocked(fileService.getFile).mockReset();
      vi.mocked(fileService.getFile).mockResolvedValue({
        ...mockPDFFile,
        processing_status: ProcessingStatus.PROCESSING,
      });

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText(/Your file is being processed/)).toBeInTheDocument();
      });
    });

    it('displays file after processing completes', async () => {
      // This test verifies that when processing completes, the completed status shows
      vi.mocked(fileService.getFile).mockReset();
      vi.mocked(fileService.getFile).mockResolvedValue(mockPDFFile);

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      // After upload, file should show with Completed status
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText(/Completed/)).toBeInTheDocument();
      });
    });

    it('handles failed processing', async () => {
      vi.mocked(fileService.getFile).mockResolvedValue({
        ...mockPDFFile,
        processing_status: ProcessingStatus.FAILED,
        processing_error: 'Extraction error',
      });

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      // Failed status shows a badge in the UI (alert only occurs during polling)
      await waitFor(() => {
        expect(screen.getByText(/Failed/)).toBeInTheDocument();
      });
    });
  });

  describe('Audio Files', () => {
    const mockAudioFile: FileDetailResponse = {
      ...mockPDFFile,
      file_id: 'audio-file-id',
      filename: 'test.mp3',
      file_type: FileType.AUDIO,
      mime_type: 'audio/mpeg',
      file_url: 'http://localhost:8000/storage/test.mp3',
    };

    it('renders MediaPlayer for audio files', async () => {
      fileService.getFile.mockResolvedValue(mockAudioFile);

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByTestId('media-player')).toBeInTheDocument();
        expect(
          screen.getByText(/Player:.*test.mp3/)
        ).toBeInTheDocument();
      });
    });

    it('shows extract button for audio files', async () => {
      fileService.getFile.mockResolvedValue(mockAudioFile);

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(
          screen.getByText('Extract Timestamps')
        ).toBeInTheDocument();
      });
    });
  });

  describe('File Information Display', () => {
    it('formats large word counts with commas', async () => {
      fileService.getFile.mockResolvedValue({
        ...mockPDFFile,
        extracted_content: {
          text: 'Content',
          word_count: 1500000,
          language: 'en',
          extraction_method: 'PyPDF2',
        },
      });

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        // Check for formatted number (locale-agnostic: accepts both 1,500,000 and 15,00,000)
        const element = screen.getByText(/1[,\s]*[0-9]{1,2}[,\s]*[0-9]{2}[,\s]*[0-9]{3}/);
        expect(element).toBeInTheDocument();
      });
    });

    it('displays file type labels correctly', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('PDF Document')).toBeInTheDocument();
      });
    });

    it('formats file size correctly', async () => {
      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(screen.getByText('1000 KB')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles file loading errors', async () => {
      const consoleErrorSpy = vi
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      fileService.getFile.mockRejectedValue(new Error('Network error'));

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Failed to load file:',
          expect.any(Error)
        );
      });

      consoleErrorSpy.mockRestore();
    });

    it('handles missing timestamps gracefully', async () => {
      vi.mocked(fileService.getFile).mockResolvedValue(mockVideoFile);
      vi.mocked(timestampService.getTimestamps).mockRejectedValue(new Error('Not found'));

      render(<HomePage />);
      await userEvent.click(screen.getByText('Trigger Upload'));

      // When timestamps fail to load, we should show the extract button
      await waitFor(() => {
        expect(screen.getByText('Extract Timestamps')).toBeInTheDocument();
      });
    });
  });
});
