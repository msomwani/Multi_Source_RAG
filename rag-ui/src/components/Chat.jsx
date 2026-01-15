import { useState, useEffect } from "react";
import { api } from "../api";

export default function Chat({ conversationId, onMessageSent }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Load messages
  useEffect(() => {
    if (typeof conversationId !== "number") {
      setMessages([]);
      return;
    }

    async function loadConversation() {
      const res = await api.get(`/conversations/${conversationId}`);
      setMessages(res.data.messages || []);
    }

    loadConversation();
  }, [conversationId]);

  async function sendMessage() {
    if (!input.trim() || typeof conversationId !== "number") return;

    setLoading(true);

    try {
      const res = await api.post("/query", {
        query: input,
        conversation_id: conversationId,
      });

      const newId = res.data.conversation_id;
      onMessageSent(newId);

      const convo = await api.get(`/conversations/${newId}`);
      setMessages(convo.data.messages || []);

      setInput("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === "assistant" ? "msg bot" : "msg user"}
          >
            <div>{m.content}</div>

            {/* ✅ SOURCES */}
            {m.role === "assistant" &&
              m.meta?.sources?.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  <ul>
                    {m.meta.sources.map((src, i) => (
                      <li key={i}>{src}</li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        ))}
      </div>

      <div className="inputRow">
        <input
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message…"
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
