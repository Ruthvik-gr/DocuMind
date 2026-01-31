import React, { useEffect } from 'react';
import { useMediaPlayer } from '../../hooks/useMediaPlayer';
import { useMediaPlayerOptional } from '../../contexts/MediaPlayerContext';
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

  // Register media element with context for cross-component access
  const mediaPlayerContext = useMediaPlayerOptional();

  useEffect(() => {
    if (mediaPlayerContext && mediaRef.current) {
      mediaPlayerContext.registerMediaElement(mediaRef.current);
    }
    return () => {
      if (mediaPlayerContext) {
        mediaPlayerContext.registerMediaElement(null);
      }
    };
  }, [mediaPlayerContext, mediaRef]);

  // Update active timestamp based on current time
  useEffect(() => {
    const activeIndex = timestamps.findIndex((ts, idx) => {
      const nextTs = timestamps[idx + 1];
      return currentTime >= ts.time && (!nextTs || currentTime < nextTs.time);
    });
    setActiveTimestampIndex(activeIndex);
  }, [currentTime, timestamps, setActiveTimestampIndex]);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className={`flex flex-col ${timestamps.length > 0 ? 'lg:flex-row lg:h-[400px]' : 'h-[400px]'}`}>
        {/* Media Player */}
        <div className={`${timestamps.length > 0 ? 'lg:flex-[3]' : 'flex-1'} bg-gray-900 flex items-center justify-center p-4 min-h-0 ${timestamps.length > 0 ? 'h-auto' : 'h-full'}`}>
          {fileType === FileType.VIDEO ? (
            <video
              ref={mediaRef as React.RefObject<HTMLVideoElement>}
              src={fileUrl}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onPlay={handlePlay}
              onPause={handlePause}
              className="w-full max-h-[300px] lg:max-h-[368px] rounded-lg object-contain"
              controls
            />
          ) : (
            <div className="w-full flex flex-col items-center justify-center gap-4 py-4">
              {/* Audio Visualization Placeholder */}
              <div className="w-24 h-24 lg:w-32 lg:h-32 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg">
                <svg className="w-12 h-12 lg:w-16 lg:h-16 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
                </svg>
              </div>
              <audio
                ref={mediaRef as React.RefObject<HTMLAudioElement>}
                src={fileUrl}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onPlay={handlePlay}
                onPause={handlePause}
                className="w-full max-w-md"
                controls
              />
            </div>
          )}
        </div>

        {/* Timestamps List */}
        {timestamps.length > 0 && (
          <div className="lg:flex-[2] flex flex-col border-t lg:border-t-0 lg:border-l border-gray-200 bg-gray-50 max-h-[300px] lg:max-h-none lg:h-full min-h-0">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-white">
              <div className="w-6 h-6 rounded-md bg-indigo-100 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-gray-900">Topics</h3>
              <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">{timestamps.length}</span>
            </div>
            <div className="flex-1 overflow-y-auto p-2 min-h-0">
              <div className="space-y-1">
                {timestamps.map((ts, idx) => (
                  <div
                    key={ts.timestamp_entry_id}
                    className={`p-2.5 rounded-lg cursor-pointer transition-all duration-150 ${
                      idx === activeTimestampIndex
                        ? 'bg-indigo-50 border border-indigo-200 shadow-sm'
                        : 'bg-white border border-gray-100 hover:bg-indigo-50/50 hover:border-indigo-100'
                    }`}
                    onClick={() => seekToTime(ts.time)}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`font-mono text-xs font-semibold px-2 py-0.5 rounded ${
                        idx === activeTimestampIndex
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {formatTime(ts.time)}
                      </span>
                      {idx === activeTimestampIndex && (
                        <div className="ml-auto flex-shrink-0">
                          <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></div>
                        </div>
                      )}
                    </div>
                    <h4 className="font-medium text-gray-900 text-sm mt-1.5 leading-tight">{ts.topic}</h4>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">{ts.description}</p>
                    {ts.keywords && ts.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {ts.keywords.slice(0, 2).map((keyword, kidx) => (
                          <span
                            key={kidx}
                            className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                        {ts.keywords.length > 2 && (
                          <span className="text-xs text-gray-400">+{ts.keywords.length - 2}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
