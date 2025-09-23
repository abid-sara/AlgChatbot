import { useState } from "react";

const ChatBar = ({ language, theme, onSend }) => {
  const [input, setInput] = useState("");

  const handleSending = async () => {
    if (!input.trim()) return;

    const currentInput = input.trim();
    // Clear input immediately when sending
    setInput("");

    // Send to parent component to handle API call and typing
    await onSend(currentInput);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSending();
    }
  };

  return (
    <div className="flex  justify-around w-full mb-7">
      <div className="relative w-[60%] ">
        <input
          value={input}
          onChange={(element) => setInput(element.target.value)}
          onKeyPress={handleKeyPress}
          className={`${
            theme === "dark"
              ? "border-gray-300 focus:outline-none focus:border-gray-300 bg-gray text-white"
              : "border-gray-400 focus:outline-none focus:border-gray-400 bg-white text-black"
          } border rounded-lg w-full p-4 text-md `}
          type="text"
          placeholder={
            language === "fr"
              ? "Entrez votre text ici"
              : language === "en"
              ? "Enter your text here "
              : "قم بإدخال نصك هنا"
          }
          dir={language === "ar" ? "rtl" : "ltr"}
        />
        <img
          src={theme == "dark" ? "/send-dark.png" : "/send.png"}
          className={`absolute ${
            language == "ar" ? "left-3  rotate-180" : "right-3"
          }  top-1/2 -translate-y-1/2 w-6 h-6 cursor-pointer`}
          alt="send"
          onClick={handleSending}
        />
      </div>
    </div>
  );
};

export default ChatBar;
