import { React, useState } from "react";
import UpperBar from "../components/UpperBar";
import WelcomeSection from "../components/WelcomeSection";
import ChatBar from "../components/ChatBar";

function App() {
  const [themeColor, setThemeColor] = useState("light");
  const [lang, setLang] = useState("fr"); //default is french

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
      <WelcomeSection language={lang} theme={themeColor}></WelcomeSection>

      {/* Chat bar */}
      <ChatBar language={lang} theme={themeColor}></ChatBar>
    </div>
  );
}

export default App;
