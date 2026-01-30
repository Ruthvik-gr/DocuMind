import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatFileSize, formatTime, formatDate, formatRelativeTime } from '../../src/utils/formatters';

describe('formatFileSize', () => {
  it('formats 0 bytes correctly', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
  });

  it('formats bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 Bytes');
    expect(formatFileSize(1023)).toBe('1023 Bytes');
  });

  it('formats kilobytes correctly', () => {
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(2048)).toBe('2 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
  });

  it('formats megabytes correctly', () => {
    expect(formatFileSize(1048576)).toBe('1 MB');
    expect(formatFileSize(5242880)).toBe('5 MB');
    expect(formatFileSize(1572864)).toBe('1.5 MB');
  });

  it('formats gigabytes correctly', () => {
    expect(formatFileSize(1073741824)).toBe('1 GB');
    expect(formatFileSize(2147483648)).toBe('2 GB');
  });
});

describe('formatTime', () => {
  it('formats seconds only', () => {
    expect(formatTime(0)).toBe('0:00');
    expect(formatTime(30)).toBe('0:30');
    expect(formatTime(59)).toBe('0:59');
  });

  it('formats minutes and seconds', () => {
    expect(formatTime(60)).toBe('1:00');
    expect(formatTime(90)).toBe('1:30');
    expect(formatTime(125)).toBe('2:05');
    expect(formatTime(3599)).toBe('59:59');
  });

  it('formats hours, minutes, and seconds', () => {
    expect(formatTime(3600)).toBe('1:00:00');
    expect(formatTime(3661)).toBe('1:01:01');
    expect(formatTime(7325)).toBe('2:02:05');
  });

  it('pads single digit minutes and seconds with zero', () => {
    expect(formatTime(65)).toBe('1:05');
    expect(formatTime(3605)).toBe('1:00:05');
  });
});

describe('formatDate', () => {
  it('formats a valid date string', () => {
    const dateString = '2024-01-15T10:30:00.000Z';
    const result = formatDate(dateString);
    // Result will vary by locale, just check it's a string
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });

  it('formats different date formats', () => {
    const result = formatDate('2024-12-25');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });
});

describe('formatRelativeTime', () => {
  beforeEach(() => {
    // Mock Date to have a consistent "now"
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('formats "just now" for very recent times', () => {
    const now = new Date('2024-01-15T10:30:00.000Z');
    vi.setSystemTime(now);

    const recent = new Date('2024-01-15T10:29:50.000Z').toISOString();
    expect(formatRelativeTime(recent)).toBe('just now');
  });

  it('formats minutes ago', () => {
    const now = new Date('2024-01-15T10:30:00.000Z');
    vi.setSystemTime(now);

    const oneMinAgo = new Date('2024-01-15T10:29:00.000Z').toISOString();
    expect(formatRelativeTime(oneMinAgo)).toBe('1 minute ago');

    const fiveMinAgo = new Date('2024-01-15T10:25:00.000Z').toISOString();
    expect(formatRelativeTime(fiveMinAgo)).toBe('5 minutes ago');

    const fiftyNineMinAgo = new Date('2024-01-15T09:31:00.000Z').toISOString();
    expect(formatRelativeTime(fiftyNineMinAgo)).toBe('59 minutes ago');
  });

  it('formats hours ago', () => {
    const now = new Date('2024-01-15T10:30:00.000Z');
    vi.setSystemTime(now);

    const oneHourAgo = new Date('2024-01-15T09:00:00.000Z').toISOString();
    expect(formatRelativeTime(oneHourAgo)).toBe('1 hour ago');

    const fiveHoursAgo = new Date('2024-01-15T05:00:00.000Z').toISOString();
    expect(formatRelativeTime(fiveHoursAgo)).toBe('5 hours ago');

    const twentyThreeHoursAgo = new Date('2024-01-14T11:00:00.000Z').toISOString();
    expect(formatRelativeTime(twentyThreeHoursAgo)).toBe('23 hours ago');
  });

  it('formats days ago', () => {
    const now = new Date('2024-01-15T10:30:00.000Z');
    vi.setSystemTime(now);

    const oneDayAgo = new Date('2024-01-14T09:00:00.000Z').toISOString();
    expect(formatRelativeTime(oneDayAgo)).toBe('1 day ago');

    const fiveDaysAgo = new Date('2024-01-10T10:00:00.000Z').toISOString();
    expect(formatRelativeTime(fiveDaysAgo)).toBe('5 days ago');
  });
});
