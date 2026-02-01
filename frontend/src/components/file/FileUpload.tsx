import React, { useRef, useState } from 'react';
import { useFileUpload } from '../../hooks/useFileUpload';
import { FileUploadResponse } from '../../types/file.types';

interface FileUploadProps {
  onUploadSuccess?: (file: FileUploadResponse) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const { uploadFile, isUploading, uploadProgress, uploadedFile, error } = useFileUpload();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        const result = await uploadFile(file);
        onUploadSuccess?.(result);
      } catch (err) {
        console.error('Upload failed:', err);
      }
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      try {
        const result = await uploadFile(file);
        onUploadSuccess?.(result);
      } catch (err) {
        console.error('Upload failed:', err);
      }
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 ${
          dragActive
            ? 'border-blue-400 bg-blue-50/50 scale-[1.02]'
            : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50/50 bg-white'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,audio/*,video/*"
          onChange={handleFileChange}
          disabled={isUploading}
        />

        <div className="space-y-5">
          {/* Icon */}
          <div className="flex justify-center">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${
              dragActive ? 'bg-blue-100' : 'bg-gradient-to-br from-blue-50 to-indigo-50'
            }`}>
              <svg
                className={`w-8 h-8 transition-colors ${dragActive ? 'text-blue-600' : 'text-blue-500'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
          </div>

          {/* Text */}
          <div>
            <p className="text-base font-medium text-gray-700">
              Drop your file here, or{' '}
              <button
                onClick={handleButtonClick}
                disabled={isUploading}
                className="text-blue-600 hover:text-blue-700 font-semibold focus:outline-none"
              >
                browse
              </button>
            </p>
            <p className="mt-1.5 text-sm text-gray-400">
              PDF, Audio, or Video up to 50MB
            </p>
          </div>

          {/* File Type Icons */}
          <div className="flex justify-center gap-3">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 rounded-lg">
              <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
              <span className="text-xs font-medium text-red-600">PDF</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 rounded-lg">
              <svg className="w-4 h-4 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217z" clipRule="evenodd" />
              </svg>
              <span className="text-xs font-medium text-purple-600">Audio</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 rounded-lg">
              <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
              </svg>
              <span className="text-xs font-medium text-blue-600">Video</span>
            </div>
          </div>
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="mt-6 px-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600 font-medium">Uploading...</span>
              <span className="text-blue-600 font-semibold">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-5 p-3 bg-red-50 border border-red-100 rounded-xl">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Success Message */}
        {uploadedFile && !isUploading && (
          <div className="mt-5 p-3 bg-green-50 border border-green-100 rounded-xl">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm text-green-600 font-medium">
                {uploadedFile.filename} uploaded successfully!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
