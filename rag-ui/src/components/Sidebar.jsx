import { useEffect, useState, forwardRef, useImperativeHandle } from "react";
import { api } from "../api";
import IngestPanel from "./IngestPanel";

const Sidebar = forwardRef(function Sidebar({ onSelect, activeId }, ref) {
  const [conversations, setConversations] = useState([]);

  async function loadConversations() {
    try {
      const res = await api.get("/conversations");
      setConversations(res.data || []);
    } catch (e) {
      console.error("Failed to load conversations", e);
    }
  }

  useImperativeHandle(ref, () => ({
    reload: loadConversations,
  }));

  function createDraftConversation() {
    onSelect("draft");
  }

  async function deleteConversation(id) {
    try {
      await api.delete(`/conversations/${id}`);
      await loadConversations();

      if (activeId === id) {
        onSelect("draft");
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
      <IngestPanel
        conversationId={activeId}
        onConversationCreated={async (newId) => {
          await loadConversations();
          onSelect(newId);
        }}
      />

      <button className="sidebarPrimaryBtn" onClick={createDraftConversation}>
        + New Chat
      </button>

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
});

export default Sidebar;
