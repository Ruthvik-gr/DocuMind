/**
 * Custom hook for media player functionality
 */
import { useState, useRef, useCallback } from 'react';

export const useMediaPlayer = () => {
  const mediaRef = useRef<HTMLVideoElement | HTMLAudioElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTimestampIndex, setActiveTimestampIndex] = useState<number>(-1);

  const seekToTime = useCallback((time: number) => {
    if (mediaRef.current) {
      mediaRef.current.currentTime = time;
      mediaRef.current.play();
      setIsPlaying(true);
    }
  }, []);

  const handleTimeUpdate = useCallback(() => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (mediaRef.current) {
      setDuration(mediaRef.current.duration);
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    if (mediaRef.current) {
      if (isPlaying) {
        mediaRef.current.pause();
      } else {
        mediaRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying]);

  const handlePlay = useCallback(() => {
    setIsPlaying(true);
  }, []);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  return {
    mediaRef,
    currentTime,
    duration,
    isPlaying,
    activeTimestampIndex,
    setActiveTimestampIndex,
    seekToTime,
    togglePlayPause,
    handleTimeUpdate,
    handleLoadedMetadata,
    handlePlay,
    handlePause,
  };
};
