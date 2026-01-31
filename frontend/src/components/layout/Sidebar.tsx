/**
 * Sidebar component for file navigation
 */
import React, { useState } from 'react';
import { FileListItem, FileType, ProcessingStatus } from '../../types/file.types';

interface SidebarProps {
  files: FileListItem[];
  selectedFileId: string | null;
  isLoading: boolean;
  onSelectFile: (fileId: string) => void;
  onDeleteFile: (fileId: string) => Promise<void>;
  onNewUpload: () => void;
  onRefresh: () => void;
}

const getFileIcon = (fileType: FileType): string => {
  switch (fileType) {
    case FileType.PDF:
      return 'pdf';
    case FileType.AUDIO:
      return 'audio';
    case FileType.VIDEO:
      return 'video';
    default:
      return 'file';
  }
};

const getStatusColor = (status: ProcessingStatus): string => {
  switch (status) {
    case ProcessingStatus.COMPLETED:
      return 'bg-green-500';
    case ProcessingStatus.PROCESSING:
      return 'bg-yellow-500';
    case ProcessingStatus.PENDING:
      return 'bg-gray-400';
    case ProcessingStatus.FAILED:
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

export const Sidebar: React.FC<SidebarProps> = ({
  files,
  selectedFileId,
  isLoading,
  onSelectFile,
  onDeleteFile,
  onNewUpload,
  onRefresh,
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation();
    if (deletingId) return;

    if (window.confirm('Are you sure you want to delete this file?')) {
      setDeletingId(fileId);
      try {
        await onDeleteFile(fileId);
      } catch (error) {
        console.error('Failed to delete file:', error);
      } finally {
        setDeletingId(null);
      }
    }
  };

  // Group files by type
  const groupedFiles = files.reduce((acc, file) => {
    const type = file.file_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(file);
    return acc;
  }, {} as Record<FileType, FileListItem[]>);

  const typeLabels: Record<FileType, string> = {
    [FileType.PDF]: 'Documents',
    [FileType.AUDIO]: 'Audio Files',
    [FileType.VIDEO]: 'Video Files',
  };

  return (
    <div className="w-72 bg-gray-900 text-white h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Your Files</h2>
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg hover:bg-gray-700 transition-colors"
            title="Refresh files"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <button
          onClick={onNewUpload}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Upload New File
        </button>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto p-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : files.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <p>No files uploaded yet</p>
            <p className="text-sm mt-1">Click "Upload New File" to get started</p>
          </div>
        ) : (
          Object.entries(groupedFiles).map(([type, typeFiles]) => (
            <div key={type} className="mb-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-2">
                {typeLabels[type as FileType]} ({typeFiles.length})
              </h3>
              <div className="space-y-1">
                {typeFiles.map((file) => (
                  <div
                    key={file.file_id}
                    onClick={() => onSelectFile(file.file_id)}
                    className={`
                      group p-3 rounded-lg cursor-pointer transition-all
                      ${selectedFileId === file.file_id
                        ? 'bg-blue-600'
                        : 'hover:bg-gray-800'
                      }
                    `}
                  >
                    <div className="flex items-start gap-3">
                      {/* File Type Icon */}
                      <div className={`
                        w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                        ${selectedFileId === file.file_id ? 'bg-blue-500' : 'bg-gray-700'}
                      `}>
                        {getFileIcon(file.file_type) === 'pdf' && (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                          </svg>
                        )}
                        {getFileIcon(file.file_type) === 'audio' && (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                          </svg>
                        )}
                        {getFileIcon(file.file_type) === 'video' && (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
                          </svg>
                        )}
                      </div>

                      {/* File Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate text-sm">{file.filename}</p>
                          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusColor(file.processing_status)}`} />
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                          <span>{formatFileSize(file.file_size)}</span>
                          <span>•</span>
                          <span>{formatDate(file.created_at)}</span>
                        </div>
                        {file.has_chat && (
                          <div className="flex items-center gap-1 text-xs text-blue-400 mt-1">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                            </svg>
                            <span>Has chat history</span>
                          </div>
                        )}
                      </div>

                      {/* Delete Button */}
                      <button
                        onClick={(e) => handleDelete(e, file.file_id)}
                        disabled={deletingId === file.file_id}
                        className={`
                          p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity
                          ${selectedFileId === file.file_id ? 'hover:bg-blue-500' : 'hover:bg-gray-700'}
                          ${deletingId === file.file_id ? 'opacity-100' : ''}
                        `}
                      >
                        {deletingId === file.file_id ? (
                          <div className="w-4 h-4 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
                        ) : (
                          <svg className="w-4 h-4 text-gray-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
