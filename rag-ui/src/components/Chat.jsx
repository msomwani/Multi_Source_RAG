import { useState, useEffect } from "react";
import { api } from "../api";

export default function Chat({ conversationId, onMessageSent }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  // Load conversation messages when ID changes
  useEffect(() => {
    async function load() {
      if (!conversationId) return;

      const res = await api.get(`/conversations/${conversationId}`);
      setMessages(res.data.messages);
    }
    load();
  }, [conversationId]);

  async function sendMessage() {
    if (!input.trim()) return;

    const res = await api.post("/query", {
      query: input,
      conversation_id: conversationId ?? null,
    });

    const newId = res.data.conversation_id;
    onMessageSent(newId);

    // reload messages
    const convo = await api.get(`/conversations/${newId}`);
    setMessages(convo.data.messages);

    setInput("");
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.map(m => (
          <div
            key={m.id}
            className={m.role === "assistant" ? "msg bot" : "msg user"}
          >
            {m.content}
          </div>
        ))}
      </div>

      <div className="inputRow">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message…"
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
