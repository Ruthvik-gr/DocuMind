import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMediaPlayer } from '../../src/hooks/useMediaPlayer';

describe('useMediaPlayer', () => {
  beforeEach(() => {
    // Mock HTML media element methods
    HTMLMediaElement.prototype.play = () => Promise.resolve();
    HTMLMediaElement.prototype.pause = () => {};
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useMediaPlayer());

    expect(result.current.currentTime).toBe(0);
    expect(result.current.duration).toBe(0);
    expect(result.current.isPlaying).toBe(false);
    expect(result.current.activeTimestampIndex).toBe(-1);
    expect(result.current.mediaRef.current).toBeNull();
  });

  it('should seek to time and play', () => {
    const { result } = renderHook(() => useMediaPlayer());

    // Create a mock media element
    const mockMediaElement = document.createElement('video') as HTMLVideoElement;
    Object.defineProperty(result.current.mediaRef, 'current', {
      value: mockMediaElement,
      writable: true,
    });

    act(() => {
      result.current.seekToTime(120);
    });

    expect(mockMediaElement.currentTime).toBe(120);
    expect(result.current.isPlaying).toBe(true);
  });

  it('should handle time update', () => {
    const { result } = renderHook(() => useMediaPlayer());

    const mockMediaElement = document.createElement('video') as HTMLVideoElement;
    Object.defineProperty(mockMediaElement, 'currentTime', {
      value: 45,
      writable: true,
    });
    Object.defineProperty(result.current.mediaRef, 'current', {
      value: mockMediaElement,
      writable: true,
    });

    act(() => {
      result.current.handleTimeUpdate();
    });

    expect(result.current.currentTime).toBe(45);
  });

  it('should handle loaded metadata', () => {
    const { result } = renderHook(() => useMediaPlayer());

    const mockMediaElement = document.createElement('video') as HTMLVideoElement;
    Object.defineProperty(mockMediaElement, 'duration', {
      value: 300,
      writable: true,
    });
    Object.defineProperty(result.current.mediaRef, 'current', {
      value: mockMediaElement,
      writable: true,
    });

    act(() => {
      result.current.handleLoadedMetadata();
    });

    expect(result.current.duration).toBe(300);
  });

  it('should toggle play/pause', () => {
    const { result } = renderHook(() => useMediaPlayer());

    const mockMediaElement = document.createElement('video') as HTMLVideoElement;
    let paused = true;

    mockMediaElement.play = () => {
      paused = false;
      return Promise.resolve();
    };
    mockMediaElement.pause = () => {
      paused = true;
    };

    Object.defineProperty(result.current.mediaRef, 'current', {
      value: mockMediaElement,
      writable: true,
    });

    // Initially not playing
    expect(result.current.isPlaying).toBe(false);

    // Toggle to play
    act(() => {
      result.current.togglePlayPause();
    });

    expect(result.current.isPlaying).toBe(true);

    // Toggle to pause
    act(() => {
      result.current.togglePlayPause();
    });

    expect(result.current.isPlaying).toBe(false);
  });

  it('should handle play event', () => {
    const { result } = renderHook(() => useMediaPlayer());

    expect(result.current.isPlaying).toBe(false);

    act(() => {
      result.current.handlePlay();
    });

    expect(result.current.isPlaying).toBe(true);
  });

  it('should handle pause event', () => {
    const { result } = renderHook(() => useMediaPlayer());

    // Set initial playing state
    act(() => {
      result.current.handlePlay();
    });

    expect(result.current.isPlaying).toBe(true);

    act(() => {
      result.current.handlePause();
    });

    expect(result.current.isPlaying).toBe(false);
  });

  it('should set active timestamp index', () => {
    const { result } = renderHook(() => useMediaPlayer());

    expect(result.current.activeTimestampIndex).toBe(-1);

    act(() => {
      result.current.setActiveTimestampIndex(2);
    });

    expect(result.current.activeTimestampIndex).toBe(2);
  });

  it('should not error when calling methods without media element', () => {
    const { result } = renderHook(() => useMediaPlayer());

    // mediaRef.current is null, should not throw
    expect(() => {
      act(() => {
        result.current.seekToTime(100);
        result.current.handleTimeUpdate();
        result.current.handleLoadedMetadata();
        result.current.togglePlayPause();
      });
    }).not.toThrow();
  });
});
