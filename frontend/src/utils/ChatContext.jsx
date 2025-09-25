import React, {
  createContext,
  useContext,
  useState,
  useRef,
  useEffect,
} from "react";

const ChatContext = createContext();

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  // --- STREAMING SEND MESSAGE ---
  const sendMessage = async (input) => {
    if (!input.trim()) return;

    const userMsgId = Date.now();
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: input },
    ]);

    const assistantId = userMsgId + 1;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", loading: true },
    ]);

    try {
      const response = await fetch("http://127.0.0.1:5000/api/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          user_id: "frontend_user",
          use_context: true,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let partial = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        chunk.split("\n").forEach((line) => {
          if (line.startsWith("data:")) {
            try {
              const data = JSON.parse(line.replace("data:", "").trim());
              if (data.token) {
                partial += data.token;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: partial } : m
                  )
                );
              }
            } catch (_) {}
          }
        });
      }
    } catch (err) {
      console.error("Streaming error:", err);
    } finally {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, loading: false } : m
        )
      );
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        sendMessage,
        isTyping,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
