import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MediaPlayer } from '../../src/components/media/MediaPlayer';
import * as useMediaPlayerModule from '../../src/hooks/useMediaPlayer';
import { FileType } from '../../src/types/file.types';

vi.mock('../../src/hooks/useMediaPlayer');

describe('MediaPlayer Component', () => {
  const mockSeekToTime = vi.fn();
  const mockHandleTimeUpdate = vi.fn();
  const mockHandleLoadedMetadata = vi.fn();
  const mockHandlePlay = vi.fn();
  const mockHandlePause = vi.fn();
  const mockSetActiveTimestampIndex = vi.fn();

  const mockTimestamps = [
    {
      timestamp_entry_id: 'ts-1',
      time: 0,
      topic: 'Introduction',
      description: 'Overview of content',
      keywords: ['intro'],
      confidence: 0.9,
    },
    {
      timestamp_entry_id: 'ts-2',
      time: 120,
      topic: 'Main Topic',
      description: 'Detailed discussion',
      keywords: ['main'],
      confidence: 0.85,
    },
    {
      timestamp_entry_id: 'ts-3',
      time: 300,
      topic: 'Conclusion',
      description: 'Summary and wrap up',
      keywords: ['conclusion'],
      confidence: 0.8,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(useMediaPlayerModule.useMediaPlayer).mockReturnValue({
      mediaRef: { current: null },
      currentTime: 0,
      duration: 600,
      isPlaying: false,
      activeTimestampIndex: -1,
      setActiveTimestampIndex: mockSetActiveTimestampIndex,
      seekToTime: mockSeekToTime,
      togglePlayPause: vi.fn(),
      handleTimeUpdate: mockHandleTimeUpdate,
      handleLoadedMetadata: mockHandleLoadedMetadata,
      handlePlay: mockHandlePlay,
      handlePause: mockHandlePause,
    });
  });

  it('renders video player for video file type', () => {
    const { container } = render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    const video = container.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute('src', '/test-video.mp4');
  });

  it('renders audio player for audio file type', () => {
    const { container } = render(
      <MediaPlayer fileUrl="/test-audio.mp3" fileType={FileType.AUDIO} timestamps={mockTimestamps} />
    );

    const audio = container.querySelector('audio');
    expect(audio).toBeInTheDocument();
    expect(audio).toHaveAttribute('src', '/test-audio.mp3');
  });

  it('renders all timestamp entries', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    expect(screen.getByText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Main Topic')).toBeInTheDocument();
    expect(screen.getByText('Conclusion')).toBeInTheDocument();
  });

  it('displays timestamp topics and descriptions', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    expect(screen.getByText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Overview of content')).toBeInTheDocument();
    expect(screen.getByText('Main Topic')).toBeInTheDocument();
    expect(screen.getByText('Detailed discussion')).toBeInTheDocument();
  });

  it('displays formatted timestamps', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    expect(screen.getByText('0:00')).toBeInTheDocument();
    expect(screen.getByText('2:00')).toBeInTheDocument();
    expect(screen.getByText('5:00')).toBeInTheDocument();
  });

  it('displays keywords for timestamps', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    expect(screen.getByText('intro')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('conclusion')).toBeInTheDocument();
  });

  it('calls seekToTime when timestamp is clicked', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    const mainTopicButton = screen.getByText('Main Topic').closest('div');
    fireEvent.click(mainTopicButton!);

    expect(mockSeekToTime).toHaveBeenCalledWith(120);
  });

  it('highlights active timestamp', () => {
    vi.mocked(useMediaPlayerModule.useMediaPlayer).mockReturnValue({
      mediaRef: { current: null },
      currentTime: 150,
      duration: 600,
      isPlaying: true,
      activeTimestampIndex: 1, // Main Topic is active
      setActiveTimestampIndex: mockSetActiveTimestampIndex,
      seekToTime: mockSeekToTime,
      togglePlayPause: vi.fn(),
      handleTimeUpdate: mockHandleTimeUpdate,
      handleLoadedMetadata: mockHandleLoadedMetadata,
      handlePlay: mockHandlePlay,
      handlePause: mockHandlePause,
    });

    const { container } = render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    // Check that the active timestamp has highlighting class (now using indigo)
    const timestampItems = container.querySelectorAll('.cursor-pointer');
    expect(timestampItems[1]).toHaveClass('bg-indigo-50');
  });

  it('attaches event handlers to video element', () => {
    const { container } = render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    const video = container.querySelector('video');
    expect(video).toHaveAttribute('controls');

    // Simulate events
    fireEvent.timeUpdate(video!);
    expect(mockHandleTimeUpdate).toHaveBeenCalled();

    fireEvent.loadedMetadata(video!);
    expect(mockHandleLoadedMetadata).toHaveBeenCalled();

    fireEvent.play(video!);
    expect(mockHandlePlay).toHaveBeenCalled();

    fireEvent.pause(video!);
    expect(mockHandlePause).toHaveBeenCalled();
  });

  it('attaches event handlers to audio element', () => {
    const { container } = render(
      <MediaPlayer fileUrl="/test-audio.mp3" fileType={FileType.AUDIO} timestamps={mockTimestamps} />
    );

    const audio = container.querySelector('audio');
    expect(audio).toHaveAttribute('controls');

    // Simulate events
    fireEvent.timeUpdate(audio!);
    expect(mockHandleTimeUpdate).toHaveBeenCalled();

    fireEvent.loadedMetadata(audio!);
    expect(mockHandleLoadedMetadata).toHaveBeenCalled();

    fireEvent.play(audio!);
    expect(mockHandlePlay).toHaveBeenCalled();

    fireEvent.pause(audio!);
    expect(mockHandlePause).toHaveBeenCalled();
  });

  it('does not render timestamps section when no timestamps', () => {
    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={[]} />
    );

    expect(screen.queryByText(/Topics & Timestamps/i)).not.toBeInTheDocument();
  });

  it('handles timestamps without keywords', () => {
    const timestampsWithoutKeywords = [
      {
        timestamp_entry_id: 'ts-1',
        time: 0,
        topic: 'Test Topic',
        description: 'Test Description',
        keywords: [],
        confidence: 0.9,
      },
    ];

    render(
      <MediaPlayer
        fileUrl="/test-video.mp4"
        fileType={FileType.VIDEO}
        timestamps={timestampsWithoutKeywords}
      />
    );

    expect(screen.getByText('Test Topic')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('formats hours correctly in timestamps', () => {
    const longTimestamps = [
      {
        timestamp_entry_id: 'ts-1',
        time: 3665, // 1:01:05
        topic: 'Long Video Section',
        description: 'After an hour',
        keywords: [],
        confidence: 0.9,
      },
    ];

    render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={longTimestamps} />
    );

    expect(screen.getByText('1:01:05')).toBeInTheDocument();
  });

  it('applies correct styling to non-active timestamps', () => {
    vi.mocked(useMediaPlayerModule.useMediaPlayer).mockReturnValue({
      mediaRef: { current: null },
      currentTime: 0,
      duration: 600,
      isPlaying: false,
      activeTimestampIndex: -1, // No active timestamp
      setActiveTimestampIndex: mockSetActiveTimestampIndex,
      seekToTime: mockSeekToTime,
      togglePlayPause: vi.fn(),
      handleTimeUpdate: mockHandleTimeUpdate,
      handleLoadedMetadata: mockHandleLoadedMetadata,
      handlePlay: mockHandlePlay,
      handlePause: mockHandlePause,
    });

    const { container } = render(
      <MediaPlayer fileUrl="/test-video.mp4" fileType={FileType.VIDEO} timestamps={mockTimestamps} />
    );

    const timestampItems = container.querySelectorAll('.cursor-pointer');
    timestampItems.forEach((item) => {
      // Non-active timestamps now have bg-white styling
      expect(item).toHaveClass('bg-white');
    });
  });
});
