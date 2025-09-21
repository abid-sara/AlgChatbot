import React, { useState } from "react";

const UpperBar = ({ theme, setTheme, setLanguage, language }) => {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex items-center justify-between px-6 py-6 relative">
      <div className="flex items-center gap-4">
        {/*theme button*/}
        <div
          className={`cursor-pointer p-2 border rounded-md ${
            theme == "dark" ? "hover:bg-gray-700" : "hover:bg-gray-200"
          }   transition`}
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
        >
          <img
            src={theme === "light" ? "/theme-light.png" : "/theme-dark.png"}
            alt="toggle theme"
            className="h-5 w-5"
          />
        </div>

        {/*language */}
        <div className="relative">
          <button
            onClick={() => setOpen(!open)}
            className={`flex items-center gap-1 px-3 py-2 border rounded-md ${
              theme === "dark"
                ? "hover:bg-gray-700 text-white"
                : "bg-white hover:bg-gray-100 text-gray-900"
            } transition cursor-pointer`}
          >
            {language === "en"
              ? "English"
              : language === "fr"
              ? "Français"
              : "العربية"}
          </button>

          {open && (
            <div
              className={`absolute left-0 mt-2 w-32 border rounded-md shadow-lg ${
                theme === "dark" ? "bg-gray-700" : "bg-white"
              }`}
            >
              <ul className="flex flex-col">
                {["en", "fr", "ar"]
                  .filter((lang) => lang !== language) // exclude current language
                  .map((lang) => (
                    <li
                      key={lang}
                      className={`px-4 py-2 ${
                        theme === "dark"
                          ? "hover:bg-gray-600"
                          : "hover:bg-gray-100"
                      } cursor-pointer`}
                      onClick={() => {
                        setLanguage(lang);
                        setOpen(false);
                      }}
                    >
                      {lang === "en"
                        ? "English"
                        : lang === "fr"
                        ? "Français"
                        : "العربية"}
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/*centered logo */}
      <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center mt-7">
        <img
          src="/Logo_Algerie_telecom.svg"
          alt="algerie telecom logo"
          className="h-14 md:h-16 lg:h-20"
        />
      </div>

      {/*login button */}
      <div className="cursor-pointer h-6 w-7">
        {theme === "light" ? (
          <img src="/user-dark.png" alt="account credentials" />
        ) : (
          <img src="/user-light.png" alt="account credentials" />
        )}
      </div>
    </div>
  );
};

export default UpperBar;
