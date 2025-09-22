import { React, useState } from "react";
import UpperBar from "../components/UpperBar";
import WelcomeSection from "../components/WelcomeSection";
import ChatBar from "../components/ChatBar";
import ChatHistory from "../components/ChatHistory";

function App() {
  const [themeColor, setThemeColor] = useState("light");
  const [lang, setLang] = useState("fr");
  const [messages, setMessages] = useState([]);

  const handleSending = (msg) => {
    console.log("Landing.jsx received:", msg);

    setMessages((prev) => {
      switch (msg.type) {
        case "user":
          console.log("Adding user message");
          return [
            ...prev,
            {
              role: "user",
              content: msg.content,
              id: msg.id || Date.now(),
            },
          ];

        case "assistant_start":
          console.log("Adding empty assistant message");
          return [
            ...prev,
            {
              role: "assistant",
              content: "",
              id: msg.id,
              loading: true,
            },
          ];

        case "assistant_update":
          console.log("Updating assistant message:", msg.content);
          // Check if assistant message already exists
          const existingMessageIndex = prev.findIndex((m) => m.id === msg.id);
          if (existingMessageIndex !== -1) {
            const newMessages = [...prev];
            newMessages[existingMessageIndex] = {
              ...newMessages[existingMessageIndex],
              content: msg.content,
            };
            return newMessages;
          } else {
            // If message doesn't exist, create it
            return [
              ...prev,
              {
                role: "assistant",
                content: msg.content,
                id: msg.id,
                loading: true,
              },
            ];
          }

        case "assistant_complete":
          console.log("Marking assistant message as complete");
          return prev.map((message) =>
            message.id === msg.id ? { ...message, loading: false } : message
          );

        case "assistant_error":
          console.log("Assistant error:", msg.error);
          return prev.map((message) =>
            message.id === msg.id
              ? {
                  ...message,
                  content: `Error: ${msg.error}`,
                  loading: false,
                }
              : message
          );

        default:
          console.log("Unknown message type, returning previous");
          return prev;
      }
    });
  };

  return (
    <div
      className={`h-screen w-screen flex flex-col ${
        themeColor === "light" ? "bg-white text-black" : "bg-dark text-white"
      } font-global`}
    >
      {/* Upper bar */}
      <UpperBar
        theme={themeColor}
        setTheme={setThemeColor}
        language={lang}
        setLanguage={setLang}
      />

      {/* Welcome section */}
      {messages.length === 0 && (
        <WelcomeSection language={lang} theme={themeColor} />
      )}

      {/* chat history */}
      <ChatHistory messages={messages} theme={themeColor} />

      {/* Chat bar */}
      <ChatBar language={lang} theme={themeColor} onSend={handleSending} />
    </div>
  );
}

export default App;
