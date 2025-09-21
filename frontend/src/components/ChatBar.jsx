const ChatBar = ({ language, theme }) => {
  return (
    <div className="flex mt-14 justify-around w-full">
      <div className="relative w-[75%] ">
        <input
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
        
          src={theme== "dark" ? "/send-dark.png":"/send.png"}
          className={`absolute ${language=="ar"?"left-3  rotate-180": "right-3"}  top-1/2 -translate-y-1/2 w-6 h-6 cursor-pointer`}
          alt="send"
        />
      </div>
    </div>
  );
};

export default ChatBar;
