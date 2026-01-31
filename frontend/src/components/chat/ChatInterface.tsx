import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat } from '../../hooks/useChat';
import { useMediaPlayerOptional } from '../../contexts/MediaPlayerContext';
import { Button } from '../common/Button';
import { Spinner } from '../common/Spinner';
import { Message, MessageRole } from '../../types/chat.types';
import { formatTime } from '../../utils/formatters';

interface ChatInterfaceProps {
  fileId: string;
  isMediaFile?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ fileId, isMediaFile = false }) => {
  const [question, setQuestion] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { askQuestion, loadHistory, isLoading, chatHistory, error, streamingMessage, lastSuggestedTimestamp } = useChat(fileId);
  const mediaPlayerContext = useMediaPlayerOptional();

  useEffect(() => {
    loadHistory();
  }, [fileId]);

  useEffect(() => {
    // Scroll to bottom of messages container only (not parent)
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [chatHistory, streamingMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const currentQuestion = question;
    setQuestion('');
    await askQuestion(currentQuestion);
  };

  const handlePlayFromTimestamp = (seconds: number) => {
    if (mediaPlayerContext) {
      mediaPlayerContext.seekToTime(seconds);
    }
  };

  const renderMessage = (message: Message, isLast: boolean = false) => {
    const isUser = message.role === MessageRole.USER;
    const suggestedTimestamp = message.suggested_timestamp ?? (isLast && !isUser ? lastSuggestedTimestamp : undefined);

    return (
      <div
        key={message.message_id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-[70%] rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-strong:font-semibold">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
              {isMediaFile && suggestedTimestamp !== undefined && mediaPlayerContext && (
                <button
                  onClick={() => handlePlayFromTimestamp(suggestedTimestamp)}
                  className="mt-2 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-full transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                  Play from {formatTime(suggestedTimestamp)}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">Ask Questions</h3>
        <p className="text-sm text-gray-500">Chat about the uploaded content</p>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-6 py-4">
        {chatHistory?.messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Ask a question to start the conversation</p>
          </div>
        ) : (
          <div>
            {chatHistory?.messages.map((msg, idx) =>
              renderMessage(msg, idx === (chatHistory?.messages.length || 0) - 1)
            )}
            {streamingMessage && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
                  <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0 prose-strong:font-semibold">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {streamingMessage}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
            {isLoading && !streamingMessage && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 rounded-lg px-4 py-2">
                  <Spinner size="sm" />
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-6 py-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question here..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <Button type="submit" disabled={!question.trim() || isLoading} isLoading={isLoading}>
            Send
          </Button>
        </div>
      </form>
    </div>
  );
};
