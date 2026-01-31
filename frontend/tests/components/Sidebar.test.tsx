import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Sidebar } from '../../src/components/layout/Sidebar';
import { FileType, ProcessingStatus } from '../../src/types/file.types';

describe('Sidebar Component', () => {
  const mockOnSelectFile = vi.fn();
  const mockOnDeleteFile = vi.fn();
  const mockOnNewUpload = vi.fn();
  const mockOnRefresh = vi.fn();

  const mockFiles = [
    {
      file_id: 'file-1',
      filename: 'document.pdf',
      file_type: FileType.PDF,
      file_size: 1024,
      processing_status: ProcessingStatus.COMPLETED,
      created_at: '2024-01-15T10:00:00Z',
      has_chat: true,
    },
    {
      file_id: 'file-2',
      filename: 'audio.mp3',
      file_type: FileType.AUDIO,
      file_size: 2048000,
      processing_status: ProcessingStatus.PROCESSING,
      created_at: '2024-01-14T10:00:00Z',
      has_chat: false,
    },
    {
      file_id: 'file-3',
      filename: 'video.mp4',
      file_type: FileType.VIDEO,
      file_size: 10485760,
      processing_status: ProcessingStatus.PENDING,
      created_at: '2024-01-13T10:00:00Z',
      has_chat: false,
    },
    {
      file_id: 'file-4',
      filename: 'failed.pdf',
      file_type: FileType.PDF,
      file_size: 500,
      processing_status: ProcessingStatus.FAILED,
      created_at: '2024-01-12T10:00:00Z',
      has_chat: false,
    },
  ];

  const defaultProps = {
    files: mockFiles,
    selectedFileId: null,
    isLoading: false,
    onSelectFile: mockOnSelectFile,
    onDeleteFile: mockOnDeleteFile,
    onNewUpload: mockOnNewUpload,
    onRefresh: mockOnRefresh,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sidebar header with title', () => {
    render(<Sidebar {...defaultProps} />);

    expect(screen.getByText('Your Files')).toBeInTheDocument();
    expect(screen.getByText('Upload New File')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(<Sidebar {...defaultProps} isLoading={true} />);

    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('renders empty state when no files', () => {
    render(<Sidebar {...defaultProps} files={[]} />);

    expect(screen.getByText('No files uploaded yet')).toBeInTheDocument();
    expect(screen.getByText('Click "Upload New File" to get started')).toBeInTheDocument();
  });

  it('renders files grouped by type', () => {
    render(<Sidebar {...defaultProps} />);

    expect(screen.getByText(/Documents \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Audio Files \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Video Files \(1\)/)).toBeInTheDocument();
  });

  it('renders file information correctly', () => {
    render(<Sidebar {...defaultProps} />);

    expect(screen.getByText('document.pdf')).toBeInTheDocument();
    expect(screen.getByText('audio.mp3')).toBeInTheDocument();
    expect(screen.getByText('video.mp4')).toBeInTheDocument();
  });

  it('formats file sizes correctly', () => {
    render(<Sidebar {...defaultProps} />);

    expect(screen.getByText('1.0 KB')).toBeInTheDocument(); // 1024 bytes
    expect(screen.getByText('2.0 MB')).toBeInTheDocument(); // 2048000 bytes
    expect(screen.getByText('10.0 MB')).toBeInTheDocument(); // 10485760 bytes
  });

  it('shows chat indicator for files with chat history', () => {
    render(<Sidebar {...defaultProps} />);

    expect(screen.getByText('Has chat history')).toBeInTheDocument();
  });

  it('calls onSelectFile when file is clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} />);

    await user.click(screen.getByText('document.pdf'));

    expect(mockOnSelectFile).toHaveBeenCalledWith('file-1');
  });

  it('highlights selected file', () => {
    render(<Sidebar {...defaultProps} selectedFileId="file-1" />);

    const selectedFile = screen.getByText('document.pdf').closest('.group');
    expect(selectedFile).toHaveClass('bg-blue-600');
  });

  it('calls onNewUpload when upload button is clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} />);

    await user.click(screen.getByText('Upload New File'));

    expect(mockOnNewUpload).toHaveBeenCalled();
  });

  it('calls onRefresh when refresh button is clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar {...defaultProps} />);

    const refreshButton = screen.getByTitle('Refresh files');
    await user.click(refreshButton);

    expect(mockOnRefresh).toHaveBeenCalled();
  });

  it('deletes file when delete button is clicked and confirmed', async () => {
    const user = userEvent.setup();
    mockOnDeleteFile.mockResolvedValue(undefined);
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<Sidebar {...defaultProps} />);

    // Hover over file to show delete button
    const fileItem = screen.getByText('document.pdf').closest('.group');
    fireEvent.mouseOver(fileItem!);

    // Find delete buttons and click the first one
    const deleteButtons = document.querySelectorAll('button');
    const deleteButton = Array.from(deleteButtons).find(btn =>
      btn.querySelector('svg path[d*="M19 7"]')
    );

    if (deleteButton) {
      await user.click(deleteButton);
    }

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this file?');
    expect(mockOnDeleteFile).toHaveBeenCalledWith('file-1');

    confirmSpy.mockRestore();
  });

  it('does not delete file when confirmation is cancelled', async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    render(<Sidebar {...defaultProps} />);

    const fileItem = screen.getByText('document.pdf').closest('.group');
    fireEvent.mouseOver(fileItem!);

    const deleteButtons = document.querySelectorAll('button');
    const deleteButton = Array.from(deleteButtons).find(btn =>
      btn.querySelector('svg path[d*="M19 7"]')
    );

    if (deleteButton) {
      await user.click(deleteButton);
    }

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockOnDeleteFile).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('handles delete error gracefully', async () => {
    const user = userEvent.setup();
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockOnDeleteFile.mockRejectedValue(new Error('Delete failed'));
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<Sidebar {...defaultProps} />);

    const fileItem = screen.getByText('document.pdf').closest('.group');
    fireEvent.mouseOver(fileItem!);

    const deleteButtons = document.querySelectorAll('button');
    const deleteButton = Array.from(deleteButtons).find(btn =>
      btn.querySelector('svg path[d*="M19 7"]')
    );

    if (deleteButton) {
      await user.click(deleteButton);
    }

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to delete file:', expect.any(Error));
    });

    confirmSpy.mockRestore();
    consoleErrorSpy.mockRestore();
  });

  it('shows different status colors for different processing states', () => {
    render(<Sidebar {...defaultProps} />);

    // Check status indicators exist
    const statusIndicators = document.querySelectorAll('.rounded-full.w-2.h-2');
    expect(statusIndicators.length).toBeGreaterThan(0);
  });

  it('prevents multiple simultaneous deletions', async () => {
    const user = userEvent.setup();
    let resolveDelete: () => void;
    const deletePromise = new Promise<void>(resolve => {
      resolveDelete = resolve;
    });
    mockOnDeleteFile.mockReturnValue(deletePromise);
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<Sidebar {...defaultProps} />);

    const fileItem = screen.getByText('document.pdf').closest('.group');
    fireEvent.mouseOver(fileItem!);

    const deleteButtons = document.querySelectorAll('button');
    const deleteButton = Array.from(deleteButtons).find(btn =>
      btn.querySelector('svg path[d*="M19 7"]')
    );

    if (deleteButton) {
      // First click starts deletion
      await user.click(deleteButton);

      // Second click should be ignored (deletingId is set)
      await user.click(deleteButton);
    }

    // Should only be called once
    expect(mockOnDeleteFile).toHaveBeenCalledTimes(1);

    // Clean up
    resolveDelete!();
    confirmSpy.mockRestore();
  });
});
