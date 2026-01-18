import { useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import "./App.css";

export default function App() {
  const [activeId, setActiveId] = useState("draft");

  const sidebarRef = useRef(null);

  return (
    <div className="appShell">
      <header className="topHeader">
        <div className="topHeaderTitle">Multi-Source RAG</div>
        <div className="topHeaderSub">PDF • DOCX • Web • Text • Streaming</div>
      </header>

      <div className="layoutBody">
        <Sidebar ref={sidebarRef} onSelect={setActiveId} activeId={activeId} />

        <main className="chatWrap">
          <Chat
            conversationId={activeId}
            onConversationCreated={(newId) => {
              setActiveId(newId);

              // ✅ THIS is your "ChatGPT refresh effect"
              sidebarRef.current?.reload();
            }}
          />
        </main>
      </div>
    </div>
  );
}
