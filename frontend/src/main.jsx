import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./pages/Landing.jsx";
import {ChatProvider} from "./utils/ChatContext.jsx";

createRoot(document.getElementById("root")).render(
  <ChatProvider>
    <StrictMode>
      <App />
    </StrictMode>
  </ChatProvider>
);
