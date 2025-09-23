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
  const typingTimeoutRef = useRef(null);
  const typingStateRef = useRef({
    answer: "",
    currentIndex: 0,
    messageId: null,
  });

  // Continue typing effect
  const continueTyping = () => {
    const { answer, currentIndex, messageId } = typingStateRef.current;

    if (currentIndex >= answer.length || !messageId) {
      setIsTyping(false);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId ? { ...message, loading: false } : message
        )
      );
      return;
    }

    const typingSpeed = 10;
    const nextChar = answer[currentIndex];
    const newContent = answer.substring(0, currentIndex + 1);

    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? { ...message, content: newContent, loading: false }
          : message
      )
    );
    

    typingStateRef.current.currentIndex++;
    typingTimeoutRef.current = setTimeout(continueTyping, typingSpeed);
  };

  // Start typing effect
  const startTypingEffect = (answer, messageId) => {
    // Store typing state
    typingStateRef.current = {
      answer,
      currentIndex: 0,
      messageId,
    };

    setIsTyping(true);
    continueTyping();
  };

  // Resume typing when component remounts
  useEffect(() => {
    if (isTyping && typingStateRef.current.messageId) {
      continueTyping();
    }
  }, []);

  // Send message function
  const sendMessage = async (input) => {
    if (!input.trim()) return;

    const conversationId = Date.now();

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: input,
        id: conversationId,
      },
    ]);

    // Add loading assistant message
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "",
        id: conversationId + 1,
        loading: true,
      },
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

      const data = await response.json();
      if (data.status === "success") {
        startTypingEffect(data.answer, conversationId + 1);
      } else {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === conversationId + 1
              ? {
                  ...message,
                  content: `Error: ${data.error}`,
                  loading: false,
                }
              : message
          )
        );
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === conversationId + 1
            ? {
                ...message,
                content: `Error: ${error.message}`,
                loading: false,
              }
            : message
        )
      );
    }
  };

  // Cleanup function
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  const value = {
    messages,
    setMessages,
    sendMessage,
    isTyping,
    startTypingEffect,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
