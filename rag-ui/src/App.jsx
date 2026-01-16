import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";
import "./App.css";

export default function App() {
  const [activeId, setActiveId] = useState(null);

  return (
    <div className="appShell">
      {/* ✅ Top Header */}
      <header className="topHeader">
        <div className="topHeaderTitle">Multi-Source RAG</div>
        <div className="topHeaderSub">PDF • DOCX • Web • Text • Streaming</div>
      </header>

      {/* ✅ Body */}
      <div className="layoutBody">
        <Sidebar onSelect={setActiveId} activeId={activeId} />

        <main className="chatWrap">
          {typeof activeId === "number" ? (
            <Chat conversationId={activeId} />
          ) : (
            <div className="emptyState">
              <h2>👋 Select or create a chat</h2>
              <p>Start by clicking <b>+ New Chat</b> from the sidebar.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
