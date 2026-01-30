import React, { useEffect } from 'react';
import { useMediaPlayer } from '../../hooks/useMediaPlayer';
import { FileType } from '../../types/file.types';
import { TimestampEntry } from '../../types/timestamp.types';
import { formatTime } from '../../utils/formatters';

interface MediaPlayerProps {
  fileUrl: string;
  fileType: FileType;
  timestamps: TimestampEntry[];
}

export const MediaPlayer: React.FC<MediaPlayerProps> = ({ fileUrl, fileType, timestamps }) => {
  const {
    mediaRef,
    currentTime,
    seekToTime,
    handleTimeUpdate,
    handleLoadedMetadata,
    handlePlay,
    handlePause,
    activeTimestampIndex,
    setActiveTimestampIndex,
  } = useMediaPlayer();

  // Update active timestamp based on current time
  useEffect(() => {
    const activeIndex = timestamps.findIndex((ts, idx) => {
      const nextTs = timestamps[idx + 1];
      return currentTime >= ts.time && (!nextTs || currentTime < nextTs.time);
    });
    setActiveTimestampIndex(activeIndex);
  }, [currentTime, timestamps, setActiveTimestampIndex]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Media Player */}
      <div className="mb-6">
        {fileType === FileType.VIDEO ? (
          <video
            ref={mediaRef as React.RefObject<HTMLVideoElement>}
            src={fileUrl}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={handlePlay}
            onPause={handlePause}
            className="w-full rounded-lg shadow-lg"
            controls
          />
        ) : (
          <audio
            ref={mediaRef as React.RefObject<HTMLAudioElement>}
            src={fileUrl}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onPlay={handlePlay}
            onPause={handlePause}
            className="w-full"
            controls
          />
        )}
      </div>

      {/* Timestamps List */}
      {timestamps.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Topics & Timestamps</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {timestamps.map((ts, idx) => (
              <div
                key={ts.timestamp_entry_id}
                className={`p-4 rounded-lg cursor-pointer transition-all duration-200 ${
                  idx === activeTimestampIndex
                    ? 'bg-blue-100 border-2 border-blue-500 shadow-md'
                    : 'bg-gray-50 border border-gray-200 hover:bg-blue-50'
                }`}
                onClick={() => seekToTime(ts.time)}
              >
                <div className="flex items-start gap-4">
                  <span className="text-blue-600 font-mono text-sm font-semibold min-w-[60px]">
                    {formatTime(ts.time)}
                  </span>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{ts.topic}</h4>
                    <p className="text-sm text-gray-600 mt-1">{ts.description}</p>
                    {ts.keywords && ts.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {ts.keywords.map((keyword, kidx) => (
                          <span
                            key={kidx}
                            className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
