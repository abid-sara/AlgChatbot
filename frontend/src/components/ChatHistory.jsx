import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { useEffect, useRef } from "react";

const ChatHistory = ({ messages, theme }) => {
  const containerRef = useRef(null);

  const bottomRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom whenever messages change
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const isMostlyArabic = (text, sampleSize = 300) => {
    if (!text) return false;
    const sample = text.slice(0, sampleSize);
    const arabicMatches = sample.match(/[\u0600-\u06FF]/g) || [];
    const totalChars = sample.replace(/\s/g, "").length;
    return arabicMatches.length / (totalChars || 1) > 0.5; // majority threshold
  };

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
              className={`${
                isUser
                  ? "max-w-[70%] md:max-w-[60%] px-4 py-3 rounded-2xl text-base bg-blue-500 text-white"
                  : `max-w-[85%] md:max-w-[80%] text-base ${themeBg} mx-auto `
              }`}
              style={{
                boxShadow: "none",
                border: "none",
                marginLeft: msg.loading && !msg.content && !isUser ? 0 : undefined,
                marginRight:
                  msg.loading && !msg.content && !isUser ? 0 : undefined,
              }}
            >
              {isAssistant ? (
                msg.loading && !msg.content ? (
                  <div
                    className={`font-semibold text-left ${
                      theme === "light" ? "text-gray-500" : "text-gray-300"
                    }`}
                  >
                    Thinking<span className="animate-pulse">...</span>
                  </div>
                ) : (
                  <div
                    className="markdown-content w-full py-2"
                    dir={
                      msg.content && isMostlyArabic(msg.content) ? "rtl" : "ltr"
                    }
                    style={{
                      textAlign:
                        msg.content && isMostlyArabic(msg.content)
                          ? "right"
                          : "left",
                    }}
                  >
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
                        p: ({ ...props }) => <p className="mb-2" {...props} />,
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
                        td: ({ children, ...props }) => {
                          const text = String(children);
                          const isNumeric = /\d/.test(text); // simple check: contains a digit
                          return (
                            <td
                              className="border border-gray-300 px-3 py-2"
                              {...props}
                            >
                              {isNumeric ? (
                                <span dir="ltr">{children}</span>
                              ) : (
                                children
                              )}
                            </td>
                          );
                        },
                        th: ({ children, ...props }) => {
                          const text = String(children);
                          const isNumeric = /\d/.test(text);
                          return (
                            <th
                              className="border border-gray-300 px-3 py-2 bg-gray-100 font-bold"
                              {...props}
                            >
                              {isNumeric ? (
                                <span dir="ltr">{children}</span>
                              ) : (
                                children
                              )}
                            </th>
                          );
                        },

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
                  </div>
                )
              ) : (
                <div className="whitespace-pre-wrap">{msg.content}</div>
              )}
            </div>
          </div>
        );
      })}

      <div ref={bottomRef} />
    </div>
  );
};

export default ChatHistory;
