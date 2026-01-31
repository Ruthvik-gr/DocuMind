import { useState, useEffect, useCallback } from 'react';
import { FileUpload } from '../components/file/FileUpload';
import { ChatInterface } from '../components/chat/ChatInterface';
import { MediaPlayer } from '../components/media/MediaPlayer';
import { SummaryPanel } from '../components/summary/SummaryPanel';
import { Spinner } from '../components/common/Spinner';
import { Button } from '../components/common/Button';
import { MainLayout } from '../components/layout/MainLayout';
import { MediaPlayerProvider } from '../contexts/MediaPlayerContext';
import { fileService } from '../services/fileService';
import { timestampService } from '../services/timestampService';
import { FileUploadResponse, FileDetailResponse, FileType, ProcessingStatus } from '../types/file.types';
import { TimestampEntry } from '../types/timestamp.types';
import { formatFileSize, FILE_TYPE_LABELS } from '../utils/constants';

export const HomePage = () => {
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [currentFile, setCurrentFile] = useState<FileDetailResponse | null>(null);
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [timestamps, setTimestamps] = useState<TimestampEntry[]>([]);
  const [isExtractingTimestamps, setIsExtractingTimestamps] = useState(false);
  const [showUpload, setShowUpload] = useState(false);

  const loadFileDetails = useCallback(async (fileId: string) => {
    setIsLoadingFile(true);
    try {
      const fileData = await fileService.getFile(fileId);
      setCurrentFile(fileData);

      // Load timestamps for audio/video files
      if (fileData.file_type === FileType.AUDIO || fileData.file_type === FileType.VIDEO) {
        try {
          const timestampData = await timestampService.getTimestamps(fileId);
          setTimestamps(timestampData.timestamps);
        } catch {
          setTimestamps([]);
        }
      } else {
        setTimestamps([]);
      }

      // If file is still processing, poll for completion
      if (fileData.processing_status === ProcessingStatus.PENDING ||
          fileData.processing_status === ProcessingStatus.PROCESSING) {
        pollFileStatus(fileId);
      }
    } catch (err) {
      console.error('Failed to load file:', err);
      setCurrentFile(null);
    } finally {
      setIsLoadingFile(false);
    }
  }, []);

  // Load file when selectedFileId changes
  useEffect(() => {
    if (selectedFileId) {
      setShowUpload(false);
      loadFileDetails(selectedFileId);
    } else {
      setCurrentFile(null);
      setTimestamps([]);
    }
  }, [selectedFileId, loadFileDetails]);

  const handleUploadSuccess = async (file: FileUploadResponse) => {
    setShowUpload(false);
    setSelectedFileId(file.file_id);
  };

  const pollFileStatus = async (fileId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const fileData = await fileService.getFile(fileId);

        if (fileData.processing_status === ProcessingStatus.COMPLETED) {
          setCurrentFile(fileData);

          // Auto-load timestamps for audio/video files
          if (fileData.file_type === FileType.AUDIO || fileData.file_type === FileType.VIDEO) {
            try {
              const timestampData = await timestampService.getTimestamps(fileId);
              setTimestamps(timestampData.timestamps);
            } catch {
              // No timestamps yet
            }
          }
        } else if (fileData.processing_status === ProcessingStatus.FAILED) {
          alert('File processing failed: ' + fileData.processing_error);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000);
        } else {
          alert('File processing timed out');
        }
      } catch (err) {
        console.error('Failed to poll file status:', err);
      }
    };

    poll();
  };

  const handleExtractTimestamps = async () => {
    if (!currentFile) return;

    setIsExtractingTimestamps(true);
    try {
      const timestampData = await timestampService.extract(currentFile.file_id);
      setTimestamps(timestampData.timestamps);
    } catch (err) {
      console.error('Failed to extract timestamps:', err);
      alert('Failed to extract timestamps');
    } finally {
      setIsExtractingTimestamps(false);
    }
  };

  const handleNewUpload = () => {
    setShowUpload(true);
  };

  const handleSelectFile = (fileId: string | null) => {
    setSelectedFileId(fileId);
    if (!fileId) {
      setShowUpload(false);
    }
  };

  return (
    <MainLayout
      selectedFileId={selectedFileId}
      onSelectFile={handleSelectFile}
      onNewUpload={handleNewUpload}
    >
      {/* Upload Form */}
      {(showUpload || (!currentFile && !isLoadingFile && !selectedFileId)) && (
        <div className="max-w-3xl mx-auto py-12">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload a File</h2>
            <p className="text-gray-600">
              Upload a PDF, audio, or video file to start asking questions
            </p>
          </div>
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      )}

      {/* Loading State */}
      {isLoadingFile && (
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600">Loading file...</p>
        </div>
      )}

      {/* File Content */}
      {currentFile && !isLoadingFile && (
        <MediaPlayerProvider>
          <div className="space-y-6">
            {/* File Info Header */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    {currentFile.filename}
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                      <span className="font-medium">Type:</span>
                      {FILE_TYPE_LABELS[currentFile.file_type]}
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="font-medium">Size:</span>
                      {formatFileSize(currentFile.file_size)}
                    </span>
                    {currentFile.extracted_content?.word_count && (
                      <span className="flex items-center gap-1">
                        <span className="font-medium">Words:</span>
                        {currentFile.extracted_content.word_count.toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${currentFile.processing_status === ProcessingStatus.COMPLETED ? 'bg-green-100 text-green-800' : ''}
                  ${currentFile.processing_status === ProcessingStatus.PROCESSING ? 'bg-yellow-100 text-yellow-800' : ''}
                  ${currentFile.processing_status === ProcessingStatus.PENDING ? 'bg-gray-100 text-gray-800' : ''}
                  ${currentFile.processing_status === ProcessingStatus.FAILED ? 'bg-red-100 text-red-800' : ''}
                `}>
                  {currentFile.processing_status.charAt(0).toUpperCase() + currentFile.processing_status.slice(1)}
                </div>
              </div>
            </div>

            {/* Media Player (for audio/video) */}
            {(currentFile.file_type === FileType.AUDIO || currentFile.file_type === FileType.VIDEO) && (
              <div className="space-y-4">
                {timestamps.length === 0 && currentFile.processing_status === ProcessingStatus.COMPLETED && (
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <Button
                      onClick={handleExtractTimestamps}
                      isLoading={isExtractingTimestamps}
                    >
                      Extract Topics & Timestamps
                    </Button>
                  </div>
                )}
                <MediaPlayer
                  fileUrl={currentFile.file_url || ''}
                  fileType={currentFile.file_type}
                  timestamps={timestamps}
                />
              </div>
            )}

            {/* Two Column Layout for Chat and Summary */}
            {currentFile.processing_status === ProcessingStatus.COMPLETED && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <ChatInterface
                    fileId={currentFile.file_id}
                    isMediaFile={currentFile.file_type === FileType.AUDIO || currentFile.file_type === FileType.VIDEO}
                  />
                </div>
                <div>
                  <SummaryPanel fileId={currentFile.file_id} />
                </div>
              </div>
            )}

            {/* Processing Message */}
            {(currentFile.processing_status === ProcessingStatus.PENDING ||
              currentFile.processing_status === ProcessingStatus.PROCESSING) && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                <Spinner size="md" />
                <p className="mt-4 text-yellow-800">
                  Your file is being processed. This may take a few minutes for large files.
                </p>
              </div>
            )}
          </div>
        </MediaPlayerProvider>
      )}

      {/* No File Selected */}
      {!showUpload && !currentFile && !isLoadingFile && selectedFileId === null && (
        <div className="flex flex-col items-center justify-center h-[calc(100vh-200px)] text-center">
          <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mb-6">
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No file selected</h3>
          <p className="text-gray-500 mb-6">
            Select a file from the sidebar or upload a new one to get started
          </p>
          <Button onClick={handleNewUpload}>Upload a File</Button>
        </div>
      )}
    </MainLayout>
  );
};
