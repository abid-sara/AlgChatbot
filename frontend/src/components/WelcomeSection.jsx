import React, { useState, useEffect } from "react";
import welcomeTranslation from "../assets/welcomeTranslation.json";

const WelcomeSection = ({ language, theme }) => {
  const [displayText, setDisplayText] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const typingText = welcomeTranslation[language].introduction;

  //typing effect
  useEffect(() => {
    let index = 0;
    setDisplayText(typingText[0]);

    const interval = setInterval(() => {
      setDisplayText((previous) => previous + typingText[index]);
      index++;
      if (index === typingText.length - 1) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 50);

    return () => {
      clearInterval(interval);
      setIsTyping(true);
    };
  }, [language, typingText]);

  return (
    <div className="px-6 mt-12 max-w-2xl mx-auto text-center">
      <h2 className="text-xl font-bold mb-4">
        {welcomeTranslation[language].welcome}
      </h2>

      <p
        className={`mb-2 min-h-[60px]`}
        dir={language === "ar" ? "rtl" : "ltr"}
      >
        {displayText}
        {isTyping && <span className="animate-pulse">|</span>}
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-xl mx-auto items-center">
        {welcomeTranslation[language].services.map((service, i) => (
          <div
            key={i}
            className={`p-2 rounded-lg ${
              theme == "light"
                ? "bg-blue-100 text-gray-800"
                : "bg-[#575859] text-gray-200"
            }
                 
                 text-center text-base`}
          >
            {service}
          </div>
        ))}
      </div>
    </div>
  );
};

export default WelcomeSection;
