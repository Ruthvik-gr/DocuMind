import { useState } from 'react';
import { FileUpload } from '../components/file/FileUpload';
import { ChatInterface } from '../components/chat/ChatInterface';
import { MediaPlayer } from '../components/media/MediaPlayer';
import { SummaryPanel } from '../components/summary/SummaryPanel';
import { Spinner } from '../components/common/Spinner';
import { Button } from '../components/common/Button';
import { fileService } from '../services/fileService';
import { timestampService } from '../services/timestampService';
import { FileUploadResponse, FileDetailResponse, FileType, ProcessingStatus } from '../types/file.types';
import { TimestampEntry } from '../types/timestamp.types';
import { formatFileSize, FILE_TYPE_LABELS } from '../utils/constants';

export const HomePage = () => {
  const [currentFile, setCurrentFile] = useState<FileDetailResponse | null>(null);
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [timestamps, setTimestamps] = useState<TimestampEntry[]>([]);
  const [isExtractingTimestamps, setIsExtractingTimestamps] = useState(false);

  const handleUploadSuccess = async (file: FileUploadResponse) => {
    // Start polling for file processing completion
    pollFileStatus(file.file_id);
  };

  const pollFileStatus = async (fileId: string) => {
    setIsLoadingFile(true);
    const maxAttempts = 60; // Poll for up to 5 minutes
    let attempts = 0;

    const poll = async () => {
      try {
        const fileData = await fileService.getFile(fileId);

        if (fileData.processing_status === ProcessingStatus.COMPLETED) {
          setCurrentFile(fileData);
          setIsLoadingFile(false);

          // Auto-load timestamps for audio/video files
          if (fileData.file_type === FileType.AUDIO || fileData.file_type === FileType.VIDEO) {
            loadTimestamps(fileId);
          }
        } else if (fileData.processing_status === ProcessingStatus.FAILED) {
          setIsLoadingFile(false);
          alert('File processing failed: ' + fileData.processing_error);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setIsLoadingFile(false);
          alert('File processing timed out');
        }
      } catch (err) {
        console.error('Failed to load file:', err);
        setIsLoadingFile(false);
      }
    };

    poll();
  };

  const loadTimestamps = async (fileId: string) => {
    try {
      // Try to get existing timestamps
      const timestampData = await timestampService.getTimestamps(fileId);
      setTimestamps(timestampData.timestamps);
    } catch (err) {
      // If no timestamps exist, that's okay
      console.log('No timestamps found yet');
    }
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
    setCurrentFile(null);
    setTimestamps([]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">DocuMind</h1>
              <p className="text-gray-600 mt-1">AI-Powered Document & Multimedia Question Answering</p>
            </div>
            {currentFile && (
              <Button onClick={handleNewUpload} variant="secondary">
                Upload New File
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {!currentFile && !isLoadingFile && (
          <div className="py-12">
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {isLoadingFile && (
          <div className="flex flex-col items-center justify-center py-20">
            <Spinner size="lg" />
            <p className="mt-4 text-gray-600">Processing your file...</p>
          </div>
        )}

        {currentFile && (
          <div className="space-y-8">
            {/* File Info */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">File Information</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Filename:</span>
                  <span className="ml-2 font-medium">{currentFile.filename}</span>
                </div>
                <div>
                  <span className="text-gray-600">Type:</span>
                  <span className="ml-2 font-medium">{FILE_TYPE_LABELS[currentFile.file_type]}</span>
                </div>
                <div>
                  <span className="text-gray-600">Size:</span>
                  <span className="ml-2 font-medium">{formatFileSize(currentFile.file_size)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Words:</span>
                  <span className="ml-2 font-medium">
                    {currentFile.extracted_content?.word_count?.toLocaleString() || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Media Player (for audio/video) */}
            {(currentFile.file_type === FileType.AUDIO || currentFile.file_type === FileType.VIDEO) && (
              <div className="space-y-4">
                {timestamps.length === 0 && (
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

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Chat Interface */}
              <div>
                <ChatInterface fileId={currentFile.file_id} />
              </div>

              {/* Summary Panel */}
              <div>
                <SummaryPanel fileId={currentFile.file_id} />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
