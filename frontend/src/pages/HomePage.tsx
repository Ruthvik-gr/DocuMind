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
        <div className="max-w-2xl mx-auto py-8">
          <div className="text-center mb-6">
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
        <div className="flex flex-col items-center justify-center py-16">
          <Spinner size="lg" />
          <p className="mt-3 text-gray-600">Loading file...</p>
        </div>
      )}

      {/* File Content */}
      {currentFile && !isLoadingFile && (
        <MediaPlayerProvider>
          <div className="space-y-4">
            {/* Compact File Info Header */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-5 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 min-w-0">
                  {/* File Type Icon */}
                  <div className={`
                    w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                    ${currentFile.file_type === FileType.PDF ? 'bg-red-100 text-red-600' : ''}
                    ${currentFile.file_type === FileType.AUDIO ? 'bg-purple-100 text-purple-600' : ''}
                    ${currentFile.file_type === FileType.VIDEO ? 'bg-blue-100 text-blue-600' : ''}
                  `}>
                    {currentFile.file_type === FileType.PDF && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                    )}
                    {currentFile.file_type === FileType.AUDIO && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                    {currentFile.file_type === FileType.VIDEO && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                      </svg>
                    )}
                  </div>
                  {/* File Details */}
                  <div className="min-w-0 flex-1">
                    <h2 className="text-base font-semibold text-gray-900 truncate">
                      {currentFile.filename}
                    </h2>
                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                      <span>{FILE_TYPE_LABELS[currentFile.file_type]}</span>
                      <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                      <span>{formatFileSize(currentFile.file_size)}</span>
                      {currentFile.extracted_content?.word_count && (
                        <>
                          <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                          <span>{currentFile.extracted_content.word_count.toLocaleString()} words</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                {/* Status Badge */}
                <div className={`
                  px-2.5 py-1 rounded-full text-xs font-medium flex-shrink-0
                  ${currentFile.processing_status === ProcessingStatus.COMPLETED ? 'bg-green-100 text-green-700' : ''}
                  ${currentFile.processing_status === ProcessingStatus.PROCESSING ? 'bg-amber-100 text-amber-700' : ''}
                  ${currentFile.processing_status === ProcessingStatus.PENDING ? 'bg-gray-100 text-gray-600' : ''}
                  ${currentFile.processing_status === ProcessingStatus.FAILED ? 'bg-red-100 text-red-700' : ''}
                `}>
                  {currentFile.processing_status === ProcessingStatus.COMPLETED && '● '}
                  {currentFile.processing_status === ProcessingStatus.PROCESSING && '○ '}
                  {currentFile.processing_status.charAt(0).toUpperCase() + currentFile.processing_status.slice(1)}
                </div>
              </div>
            </div>

            {/* Media Player (for audio/video) */}
            {(currentFile.file_type === FileType.AUDIO || currentFile.file_type === FileType.VIDEO) && (
              <div className="space-y-3">
                {timestamps.length === 0 && currentFile.processing_status === ProcessingStatus.COMPLETED && (
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 px-5 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Extract Topics</p>
                        <p className="text-xs text-gray-500 mt-0.5">Identify key topics and timestamps in your media</p>
                      </div>
                      <Button
                        onClick={handleExtractTimestamps}
                        isLoading={isExtractingTimestamps}
                        variant="primary"
                      >
                        Extract Timestamps
                      </Button>
                    </div>
                  </div>
                )}
                <MediaPlayer
                  fileUrl={currentFile.file_url || ''}
                  fileType={currentFile.file_type}
                  timestamps={timestamps}
                />
              </div>
            )}

            {/* Chat and Summary Layout */}
            {currentFile.processing_status === ProcessingStatus.COMPLETED && (
              <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
                {/* Chat - Takes more space */}
                <div className="xl:col-span-3">
                  <ChatInterface
                    fileId={currentFile.file_id}
                    isMediaFile={currentFile.file_type === FileType.AUDIO || currentFile.file_type === FileType.VIDEO}
                  />
                </div>
                {/* Summary - Smaller column */}
                <div className="xl:col-span-2">
                  <SummaryPanel fileId={currentFile.file_id} />
                </div>
              </div>
            )}

            {/* Processing Message */}
            {(currentFile.processing_status === ProcessingStatus.PENDING ||
              currentFile.processing_status === ProcessingStatus.PROCESSING) && (
                <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl px-6 py-5 text-center">
                  <Spinner size="md" />
                  <p className="mt-3 text-amber-800 text-sm">
                    Your file is being processed. This may take a few minutes for large files.
                  </p>
                </div>
              )}
          </div>
        </MediaPlayerProvider>
      )}
    </MainLayout>
  );
};
