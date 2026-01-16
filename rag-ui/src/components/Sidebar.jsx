import { useEffect, useState } from "react";
import { api } from "../api";
import IngestPanel from "./IngestPanel";

export default function Sidebar({ onSelect, activeId }) {
  const [conversations, setConversations] = useState([]);

  async function loadConversations() {
    try {
      const res = await api.get("/conversations");
      setConversations(res.data || []);
    } catch (e) {
      console.error("Failed to load conversations", e);
    }
  }

  async function createConversation() {
    try {
      const res = await api.post("/conversations");
      await loadConversations();
      onSelect(res.data.id);
    } catch (e) {
      console.error("Failed to create conversation", e);
    }
  }

  async function deleteConversation(id) {
    try {
      await api.delete(`/conversations/${id}`);
      await loadConversations();

      if (activeId === id) {
        onSelect(null);
      }
    } catch (e) {
      console.error("Failed to delete conversation", e);
    }
  }

  useEffect(() => {
    loadConversations();
  }, []);

  return (
    <div className="sidebar">
      {/* ✅ Ingest Panel FIRST */}
      <IngestPanel conversationId={activeId} />

      {/* ✅ New Chat button BELOW ingest (less cluttered) */}
      <button className="sidebarPrimaryBtn" onClick={createConversation}>
        + New Chat
      </button>

      {/* ✅ Conversations List */}
      <div className="sidebarSectionTitle">Chats</div>

      <ul className="sidebarList">
        {conversations.map((c) => (
          <li
            key={c.id}
            className={c.id === activeId ? "sidebarItem active" : "sidebarItem"}
            onClick={() => onSelect(c.id)}
          >
            <span className="sidebarItemText">Chat #{c.id}</span>

            <button
              className="sidebarDeleteBtn"
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(c.id);
              }}
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
