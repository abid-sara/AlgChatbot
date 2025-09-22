import { useState } from "react";

const ChatBar = ({ language, theme, onSend }) => {
  const [input, setInput] = useState("");

  const handleSending = async () => {
    if (!input.trim()) return;

    // Generate a unique ID for this conversation pair
    const conversationId = Date.now();

    // Send user message
    onSend({ type: "user", content: input, id: conversationId });

    // Send assistant start message
    onSend({ type: "assistant_start", id: conversationId + 1 });

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

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantText = "";
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || "";

        for (let line of lines) {
          if (line.startsWith("data: ")) {
            const text = line.replace("data: ", "").trim();

            if (text === "[DONE]") {
              onSend({ type: "assistant_complete", id: conversationId + 1 });
              break;
            }

            if (text && !text.includes("Error:")) {
              // IMPORTANT: Preserve the spaces by simply appending
              assistantText += text;

              // Update the assistant message with accumulated text
              onSend({
                type: "assistant_update",
                id: conversationId + 1,
                content: assistantText,
              });
            } else if (text.includes("Error:")) {
              onSend({
                type: "assistant_error",
                id: conversationId + 1,
                error: text.replace("Error: ", ""),
              });
              break;
            }
          }
        }
      }

      // Handle any remaining data in buffer
      if (buffer.trim()) {
        const text = buffer.replace("data: ", "").trim();
        if (text && text !== "[DONE]" && !text.includes("Error:")) {
          assistantText += text;
          onSend({
            type: "assistant_update",
            id: conversationId + 1,
            content: assistantText,
          });
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      onSend({
        type: "assistant_error",
        id: conversationId + 1,
        error: error.message,
      });
    }

    setInput("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSending();
    }
  };

  return (
    <div className="flex mt-14 justify-around w-full mb-7">
      <div className="relative w-[75%] ">
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
