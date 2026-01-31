/**
 * Media Player Context for sharing media player controls across components
 */
import React, { createContext, useContext, useRef, useState, useCallback } from 'react';

interface MediaPlayerContextType {
  mediaRef: React.RefObject<HTMLVideoElement | HTMLAudioElement | null>;
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  seekToTime: (seconds: number) => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setIsPlaying: (playing: boolean) => void;
  registerMediaElement: (element: HTMLVideoElement | HTMLAudioElement | null) => void;
}

const MediaPlayerContext = createContext<MediaPlayerContextType | undefined>(undefined);

export const MediaPlayerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const registerMediaElement = useCallback((element: HTMLVideoElement | HTMLAudioElement | null) => {
    mediaRef.current = element;
  }, []);

  const seekToTime = useCallback((seconds: number) => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = seconds;
      mediaRef.current.play().catch((e) => {
        console.error('Failed to play media:', e);
      });
      setIsPlaying(true);
    }
  }, []);

  const value: MediaPlayerContextType = {
    mediaRef,
    currentTime,
    duration,
    isPlaying,
    seekToTime,
    setCurrentTime,
    setDuration,
    setIsPlaying,
    registerMediaElement,
  };

  return (
    <MediaPlayerContext.Provider value={value}>
      {children}
    </MediaPlayerContext.Provider>
  );
};

export const useMediaPlayer = (): MediaPlayerContextType => {
  const context = useContext(MediaPlayerContext);
  if (context === undefined) {
    throw new Error('useMediaPlayer must be used within a MediaPlayerProvider');
  }
  return context;
};

export const useMediaPlayerOptional = (): MediaPlayerContextType | null => {
  const context = useContext(MediaPlayerContext);
  return context ?? null;
};
