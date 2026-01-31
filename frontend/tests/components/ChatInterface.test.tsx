import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '../../src/components/chat/ChatInterface';
import * as useChatModule from '../../src/hooks/useChat';
import { MessageRole } from '../../src/types/chat.types';

vi.mock('../../src/hooks/useChat');

describe('ChatInterface Component', () => {
  const mockAskQuestion = vi.fn();
  const mockLoadHistory = vi.fn();
  const fileId = 'test-file-id';

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock with all required properties
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: null,
      error: null,
      streamingMessage: '',
      lastSuggestedTimestamp: undefined,
    });
  });

  it('renders chat interface correctly', () => {
    render(<ChatInterface fileId={fileId} />);

    expect(screen.getByPlaceholderText(/Type your question here/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('loads chat history on mount', () => {
    render(<ChatInterface fileId={fileId} />);

    expect(mockLoadHistory).toHaveBeenCalled();
  });

  it('loads chat history when fileId changes', () => {
    const { rerender } = render(<ChatInterface fileId="file-1" />);

    expect(mockLoadHistory).toHaveBeenCalledTimes(1);

    rerender(<ChatInterface fileId="file-2" />);

    expect(mockLoadHistory).toHaveBeenCalledTimes(2);
  });

  it('submits question when form is submitted', async () => {
    const user = userEvent.setup();
    mockAskQuestion.mockResolvedValue({
      answer: 'Test answer',
      sources: [],
      chat_id: 'chat-123',
      timestamp: '2024-01-15T10:00:00Z',
    });

    render(<ChatInterface fileId={fileId} />);

    const input = screen.getByPlaceholderText(/Type your question here/i);
    await user.type(input, 'What is this?');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockAskQuestion).toHaveBeenCalledWith('What is this?');
    });
  });

  it('clears input after question is submitted', async () => {
    const user = userEvent.setup();
    mockAskQuestion.mockResolvedValue({
      answer: 'Test answer',
      sources: [],
      chat_id: 'chat-123',
      timestamp: '2024-01-15T10:00:00Z',
    });

    render(<ChatInterface fileId={fileId} />);

    const input = screen.getByPlaceholderText(/Type your question here/i) as HTMLInputElement;
    await user.type(input, 'Test question');
    expect(input.value).toBe('Test question');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('does not submit empty question', async () => {
    const user = userEvent.setup();
    render(<ChatInterface fileId={fileId} />);

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    expect(mockAskQuestion).not.toHaveBeenCalled();
  });

  it('does not submit whitespace-only question', async () => {
    const user = userEvent.setup();
    render(<ChatInterface fileId={fileId} />);

    const input = screen.getByPlaceholderText(/Type your question here/i);
    await user.type(input, '   ');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    expect(mockAskQuestion).not.toHaveBeenCalled();
  });

  it('displays chat messages when chat history exists', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: {
        chat_id: 'chat-123',
        file_id: fileId,
        messages: [
          {
            message_id: 'msg-1',
            role: MessageRole.USER,
            content: 'Hello',
            timestamp: '2024-01-15T10:00:00Z',
            token_count: 10,
          },
          {
            message_id: 'msg-2',
            role: MessageRole.ASSISTANT,
            content: 'Hi there!',
            timestamp: '2024-01-15T10:00:01Z',
            token_count: 15,
          },
        ],
        total_messages: 2,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:01Z',
      },
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('displays user messages with correct styling', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: {
        chat_id: 'chat-123',
        file_id: fileId,
        messages: [
          {
            message_id: 'msg-1',
            role: MessageRole.USER,
            content: 'User message',
            timestamp: '2024-01-15T10:00:00Z',
            token_count: 10,
          },
        ],
        total_messages: 1,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    const messageElement = screen.getByText('User message').closest('div');
    expect(messageElement).toHaveClass('bg-blue-600');
    expect(messageElement).toHaveClass('text-white');
  });

  it('displays assistant messages with correct styling', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: {
        chat_id: 'chat-123',
        file_id: fileId,
        messages: [
          {
            message_id: 'msg-1',
            role: MessageRole.ASSISTANT,
            content: 'Assistant message',
            timestamp: '2024-01-15T10:00:00Z',
            token_count: 10,
          },
        ],
        total_messages: 1,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    // Assistant messages have markdown wrapper, need to go up 2 levels
    const textElement = screen.getByText('Assistant message');
    const proseDiv = textElement.closest('.prose');
    const messageElement = proseDiv?.parentElement;
    expect(messageElement).toHaveClass('bg-gray-100');
    expect(messageElement).toHaveClass('text-gray-900');
  });

  it('disables send button when loading', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: true,
      chatHistory: null,
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    // When isLoading is true, the send button should be disabled
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('displays loading indicator when loading', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: true,
      chatHistory: null,
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    // Bouncing dots loading indicator should be visible
    expect(document.querySelector('.animate-bounce')).toBeInTheDocument();
  });

  it('displays error message when error occurs', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: null,
      error: 'Failed to get answer',
    });

    render(<ChatInterface fileId={fileId} />);

    expect(screen.getByText('Failed to get answer')).toBeInTheDocument();
  });

  it('displays empty state when no messages', () => {
    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: false,
      chatHistory: {
        chat_id: 'chat-123',
        file_id: fileId,
        messages: [],
        total_messages: 0,
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    expect(screen.getByText(/Ask a question to start the conversation/i)).toBeInTheDocument();
  });

  it('prevents submission when already loading', async () => {
    const user = userEvent.setup();

    vi.mocked(useChatModule.useChat).mockReturnValue({
      askQuestion: mockAskQuestion,
      loadHistory: mockLoadHistory,
      isLoading: true,
      chatHistory: null,
      error: null,
    });

    render(<ChatInterface fileId={fileId} />);

    const input = screen.getByPlaceholderText(/Type your question here/i);
    await user.type(input, 'Test question');

    const form = input.closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    expect(mockAskQuestion).not.toHaveBeenCalled();
  });
});
