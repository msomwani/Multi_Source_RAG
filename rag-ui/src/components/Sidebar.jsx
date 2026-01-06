import IngestPanel from "./IngestPanel";
import { useEffect, useState } from "react";
import { api } from "../api";

export default function Sidebar({ onSelect, activeId }) {
  const [convos, setConvos] = useState([]);

  async function load() {
    const res = await api.get("/conversations");
    setConvos(res.data);
  }

  async function createConversation() {
    const res = await api.post("/conversations");
    load();
    onSelect(res.data.id);
  }

  async function deleteConversation(id) {
    await api.delete(`/conversations/${id}`);
    load();
    if (id === activeId) onSelect(null);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="sidebar">
      <IngestPanel />
      <button onClick={createConversation}>+ New Chat</button>

      <ul>
        {convos.map(c => (
          <li
            key={c.id}
            className={c.id === activeId ? "active" : ""}
            onClick={() => onSelect(c.id)}
          >
            Chat #{c.id}
            <span onClick={(e) => { e.stopPropagation(); deleteConversation(c.id); }}>
              ❌
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
