import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { useEffect, useRef, useCallback } from "react";

const ChatHistory = ({ messages, theme }) => {
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);
  const scrollTimeoutRef = useRef(null);

  const isMostlyArabic = (text, sampleSize = 300) => {
    if (!text) return false;
    const sample = text.slice(0, sampleSize);
    const arabicMatches = sample.match(/[\u0600-\u06FF]/g) || [];
    const totalChars = sample.replace(/\s/g, "").length;
    return arabicMatches.length / (totalChars || 1) > 0.5; // majority threshold
  };

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Debounced scroll - only scroll after typing pauses
  const debouncedScrollToBottom = useCallback(() => {
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      scrollToBottom();
    }, 100); // Wait 100ms after last update
  }, [scrollToBottom]);

  // Auto-scroll to bottom when new messages are added or updated
  useEffect(() => {
    // Check if there's a currently loading message (typing)
    const hasLoadingMessage = messages.some(
      (msg) => msg.loading === false && msg.role === "assistant"
    );

    if (hasLoadingMessage) {
      // If typing, use debounced scroll
      debouncedScrollToBottom();
    } else {
      // If not typing (new message added), scroll immediately
      scrollToBottom();
    }
  }, [messages, scrollToBottom, debouncedScrollToBottom]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // Theme background colors for assistant bubble
  const themeBg =
    theme === "light" ? "bg-white text-black" : "bg-dark text-white";

  return (
    <div
      ref={containerRef}
      className={`flex-1 overflow-y-auto py-8 px-4 md:px-8 w-full flex flex-col ${themeBg} font-global`}
    >
      {messages.map((msg, idx) => {
        const isUser = msg.role === "user";
        const isAssistant = msg.role === "assistant";
        return (
          <div
            key={msg.id || idx}
            className={`w-full flex mb-6 ${
              isUser ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`
                ${
                  isUser
                    ? "max-w-[70%] md:max-w-[60%] px-4 py-3 rounded-2xl text-base bg-blue-500 text-white"
                    : `max-w-[85%] md:max-w-[80%] pl-20 pr-20 py-0 text-base ${themeBg}`
                }
              `}
              style={{
                boxShadow: "none", // No shadow
                border: "none", // No border
              }}
            >
              {isAssistant ? (
                <div
                  className="markdown-content w-full px-4 py-2"
                  dir={
                    msg.content && isMostlyArabic(msg.content) ? "rtl" : "ltr"
                  }
                  style={{
                    textAlign:
                      msg.content && isMostlyArabic(msg.content)
                        ? "right"
                        : "left", // 👈 align text
                  }}
                >
                  {msg.loading && !msg.content ? (
                    <div
                      className={`font-semibold ${
                        theme === "light" ? "text-gray-500" : "text-gray-300"
                      }`}
                    >
                      Thinking<span className="animate-pulse">...</span>
                    </div>
                  ) : (
                    /* Show markdown content when not loading or when content exists */
                    msg.content && (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkBreaks]}
                        components={{
                          h1: ({ ...props }) => (
                            <h1
                              className="text-xl font-bold mt-2 mb-2"
                              {...props}
                            />
                          ),
                          h2: ({ ...props }) => (
                            <h2
                              className="text-lg font-bold mt-2 mb-2"
                              {...props}
                            />
                          ),
                          h3: ({ ...props }) => (
                            <h3
                              className="text-md font-bold mt-2 mb-2"
                              {...props}
                            />
                          ),
                          p: ({ ...props }) => (
                            <p className="mb-2" {...props} />
                          ),
                          ul: ({ ...props }) => (
                            <ul
                              className="list-disc list-inside mb-2"
                              {...props}
                            />
                          ),
                          ol: ({ ...props }) => (
                            <ol
                              className="list-decimal list-inside mb-2"
                              {...props}
                            />
                          ),
                          li: ({ ...props }) => (
                            <li className="mb-1" {...props} />
                          ),
                          table: ({ ...props }) => (
                            <div className="overflow-x-auto">
                              <table
                                className="min-w-full border-collapse border border-gray-300"
                                {...props}
                              />
                            </div>
                          ),
                          th: ({ ...props }) => (
                            <th
                              className="border border-gray-300 px-3 py-2 bg-gray-100 font-bold"
                              {...props}
                            />
                          ),
                          td: ({ ...props }) => (
                            <td
                              className="border border-gray-300 px-3 py-2"
                              {...props}
                            />
                          ),
                          code: ({ ...props }) => (
                            <code
                              className="bg-gray-100 px-1 rounded font-mono text-sm"
                              {...props}
                            />
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    )
                  )}
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{msg.content}</div>
              )}
            </div>
          </div>
        );
      })}
      {/* Invisible element at the bottom for scrolling */}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatHistory;
