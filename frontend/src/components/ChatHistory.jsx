import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";

const ChatHistory = ({ messages, theme }) => {
  return (
    <div
      className={`flex-1 overflow-y-auto p-4 ${
        theme === "light" ? "bg-white text-black" : "bg-dark text-white"
      } font-global`}
    >
      {messages.map((msg, idx) => (
        <div
          key={msg.id || idx}
          className={`flex mb-4 ${
            msg.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          <div
            className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm ${
              msg.role === "user"
                ? "bg-blue-500 text-white rounded-br-none"
                : theme === "light"
                ? "bg-gray-200 text-black rounded-bl-none"
                : "bg-gray-700 text-white rounded-bl-none"
            }`}
          >
            {msg.role === "assistant" ? (
              <div className="markdown-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                  components={{
                    // Custom components for better styling
                    h1: ({ node, ...props }) => (
                      <h1 className="text-xl font-bold mt-2 mb-2" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                      <h2 className="text-lg font-bold mt-2 mb-2" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                      <h3 className="text-md font-bold mt-2 mb-2" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                      <p className="mb-2" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside mb-2" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol
                        className="list-decimal list-inside mb-2"
                        {...props}
                      />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="mb-1" {...props} />
                    ),
                    table: ({ node, ...props }) => (
                      <div className="overflow-x-auto">
                        <table
                          className="min-w-full border-collapse border border-gray-300"
                          {...props}
                        />
                      </div>
                    ),
                    th: ({ node, ...props }) => (
                      <th
                        className="border border-gray-300 px-3 py-2 bg-gray-100 font-bold"
                        {...props}
                      />
                    ),
                    td: ({ node, ...props }) => (
                      <td
                        className="border border-gray-300 px-3 py-2"
                        {...props}
                      />
                    ),
                    code: ({ node, ...props }) => (
                      <code className="bg-gray-100 px-1 rounded" {...props} />
                    ),
                  }}
                >
                  {msg.content || (msg.loading ? "Thinking..." : "")}
                </ReactMarkdown>
                {msg.loading && (
                  <div className="inline-block animate-pulse">...</div>
                )}
              </div>
            ) : (
              <div className="whitespace-pre-wrap">{msg.content}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ChatHistory;
