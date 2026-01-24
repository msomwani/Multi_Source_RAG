import { useRef, useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import "./App.css";

export default function App() {
  const [activeId, setActiveId] = useState("draft");
  const sidebarRef = useRef(null);

  const [dark, setDark] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });

  useEffect(() => {
    document.body.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return (
    <div className="appShell">
      <header className="topHeader">
        <div className="topHeaderLeft">
          <div className="topHeaderTitle">Multi-Source RAG</div>
          <div className="topHeaderSub">PDF • DOCX • Web • Text</div>
        </div>

        <div className="topHeaderRight">
          <span className="themeLabel">{dark ? "Dark" : "Light"}</span>

          <button
            className={dark ? "themeSwitch on" : "themeSwitch"}
            onClick={() => setDark((prev) => !prev)}
            aria-label="Toggle theme"
          >
            <span className="themeKnob" />
          </button>
        </div>
      </header>

      <div className="layoutBody">
        <Sidebar ref={sidebarRef} onSelect={setActiveId} activeId={activeId} />

        <main className="chatWrap">
          <Chat
            conversationId={activeId}
            onConversationCreated={(newId) => {
              setActiveId(newId);
              sidebarRef.current?.reload();
            }}
          />
        </main>
      </div>
    </div>
  );
}
