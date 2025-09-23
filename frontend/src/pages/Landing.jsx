import { React, useState } from "react";
import { useChatContext } from "../utils/ChatContext";
import UpperBar from "../components/UpperBar";
import WelcomeSection from "../components/WelcomeSection";
import ChatBar from "../components/ChatBar";
import ChatHistory from "../components/ChatHistory";

function App() {
  const [themeColor, setThemeColor] = useState("light");
  const [lang, setLang] = useState("fr");
  const { messages, sendMessage } = useChatContext();

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
      <ChatBar language={lang} theme={themeColor} onSend={sendMessage} />
    </div>
  );
}

export default App;
