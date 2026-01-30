import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileUpload } from '../../src/components/file/FileUpload';
import * as useFileUploadModule from '../../src/hooks/useFileUpload';

// Mock the useFileUpload hook
vi.mock('../../src/hooks/useFileUpload');

describe('FileUpload Component', () => {
  const mockUploadFile = vi.fn();
  const mockResetUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementation
    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: false,
      uploadProgress: 0,
      uploadedFile: null,
      error: null,
    });
  });

  it('renders upload area correctly', () => {
    render(<FileUpload />);

    expect(screen.getByText(/Drag and drop your file here/i)).toBeInTheDocument();
    expect(screen.getByText('Choose File')).toBeInTheDocument();
    expect(screen.getByText(/Supported: PDF, Audio/i)).toBeInTheDocument();
  });

  it('opens file input when "Choose File" button is clicked', async () => {
    const user = userEvent.setup();
    render(<FileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const clickSpy = vi.spyOn(fileInput, 'click');

    const button = screen.getByText('Choose File');
    await user.click(button);

    expect(clickSpy).toHaveBeenCalled();
  });

  it('uploads file when selected via input', async () => {
    const mockResponse = {
      file_id: 'test-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    mockUploadFile.mockResolvedValue(mockResponse);

    render(<FileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    await waitFor(() => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(mockUploadFile).toHaveBeenCalledWith(file);
    });
  });

  it('calls onUploadSuccess callback when upload succeeds', async () => {
    const mockResponse = {
      file_id: 'test-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    mockUploadFile.mockResolvedValue(mockResponse);
    const onUploadSuccess = vi.fn();

    render(<FileUpload onUploadSuccess={onUploadSuccess} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    await waitFor(() => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(onUploadSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it('handles drag enter event', () => {
    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;

    fireEvent.dragEnter(dropZone);

    expect(dropZone).toHaveClass('border-blue-500');
    expect(dropZone).toHaveClass('bg-blue-50');
  });

  it('handles drag over event', () => {
    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;

    fireEvent.dragOver(dropZone);

    expect(dropZone).toHaveClass('border-blue-500');
    expect(dropZone).toHaveClass('bg-blue-50');
  });

  it('handles drag leave event', () => {
    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;

    // First drag enter
    fireEvent.dragEnter(dropZone);
    expect(dropZone).toHaveClass('border-blue-500');

    // Then drag leave
    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass('border-blue-500');
  });

  it('uploads file via drag and drop', async () => {
    const mockResponse = {
      file_id: 'test-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    mockUploadFile.mockResolvedValue(mockResponse);

    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const dropEvent = {
      dataTransfer: {
        files: [file],
      },
    };

    await waitFor(() => {
      fireEvent.drop(dropZone, dropEvent);
    });

    await waitFor(() => {
      expect(mockUploadFile).toHaveBeenCalledWith(file);
    });
  });

  it('displays upload progress when uploading', () => {
    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: true,
      uploadProgress: 45,
      uploadedFile: null,
      error: null,
    });

    render(<FileUpload />);

    // Check that progress text is displayed
    expect(screen.getByText('45% uploaded')).toBeInTheDocument();

    // Check that progress bar element exists
    const progressBar = document.querySelector('.bg-blue-600') as HTMLElement;
    expect(progressBar).toBeInTheDocument();
  });

  it('displays error message when upload fails', () => {
    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: false,
      uploadProgress: 0,
      uploadedFile: null,
      error: 'Upload failed: File too large',
    });

    render(<FileUpload />);

    expect(screen.getByText('Upload failed: File too large')).toBeInTheDocument();

    const errorDiv = screen.getByText('Upload failed: File too large').closest('div');
    expect(errorDiv).toHaveClass('bg-red-50');
  });

  it('displays success message when upload completes', () => {
    const uploadedFile = {
      file_id: 'test-id',
      filename: 'test.pdf',
      file_type: 'pdf' as const,
      file_size: 1024,
      processing_status: 'pending' as const,
      upload_date: '2024-01-15T10:00:00Z',
    };

    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: false,
      uploadProgress: 100,
      uploadedFile,
      error: null,
    });

    render(<FileUpload />);

    expect(screen.getByText(/test.pdf uploaded successfully!/i)).toBeInTheDocument();

    const successDiv = screen.getByText(/test.pdf uploaded successfully!/i).closest('div');
    expect(successDiv).toHaveClass('bg-green-50');
  });

  it('disables file input when uploading', () => {
    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: true,
      uploadProgress: 50,
      uploadedFile: null,
      error: null,
    });

    render(<FileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeDisabled();
  });

  it('disables "Choose File" button when uploading', () => {
    vi.mocked(useFileUploadModule.useFileUpload).mockReturnValue({
      uploadFile: mockUploadFile,
      resetUpload: mockResetUpload,
      isUploading: true,
      uploadProgress: 50,
      uploadedFile: null,
      error: null,
    });

    render(<FileUpload />);

    const button = screen.getByText('Choose File');
    expect(button).toBeDisabled();
  });

  it('handles upload failure and logs error', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const uploadError = new Error('Network error');
    mockUploadFile.mockRejectedValue(uploadError);

    render(<FileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    await waitFor(() => {
      fireEvent.change(fileInput, { target: { files: [file] } });
    });

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Upload failed:', uploadError);
    });

    consoleErrorSpy.mockRestore();
  });

  it('handles drop failure and logs error', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const uploadError = new Error('Network error');
    mockUploadFile.mockRejectedValue(uploadError);

    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const dropEvent = {
      dataTransfer: {
        files: [file],
      },
    };

    await waitFor(() => {
      fireEvent.drop(dropZone, dropEvent);
    });

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Upload failed:', uploadError);
    });

    consoleErrorSpy.mockRestore();
  });

  it('does not upload if no file is selected', async () => {
    render(<FileUpload />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    await waitFor(() => {
      fireEvent.change(fileInput, { target: { files: [] } });
    });

    expect(mockUploadFile).not.toHaveBeenCalled();
  });

  it('does not upload if no file is dropped', async () => {
    render(<FileUpload />);

    const dropZone = document.querySelector('.border-2') as HTMLElement;

    const dropEvent = {
      dataTransfer: {
        files: [],
      },
    };

    await waitFor(() => {
      fireEvent.drop(dropZone, dropEvent);
    });

    expect(mockUploadFile).not.toHaveBeenCalled();
  });
});
