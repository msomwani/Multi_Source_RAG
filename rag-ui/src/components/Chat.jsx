import { useState, useEffect, useRef } from "react";
import { api } from "../api";

export default function Chat({ conversationId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  // ✅ Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  // ✅ Load conversation messages
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

  // ✅ Stop streaming
  function stopStreaming() {
    abortRef.current?.abort();
    setIsStreaming(false);
    setLoading(false);
  }

  // ✅ Send message (stream)
  async function sendMessage() {
    if (!input.trim()) return;
    if (typeof conversationId !== "number") return;

    setLoading(true);
    setIsStreaming(true);

    const tempId = Date.now();

    setMessages((prev) => [
      ...prev,
      { id: tempId, role: "assistant", content: "" },
    ]);

    abortRef.current = new AbortController();

    try {
      const res = await fetch(`${api.defaults.baseURL}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortRef.current.signal,
        body: JSON.stringify({
          query: input,
          conversation_id: conversationId,
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempId ? { ...m, content: m.content + chunk } : m
          )
        );
      }

      // Reload final messages (for sources)
      const convo = await api.get(`/conversations/${conversationId}`);
      setMessages(convo.data.messages || []);
      setInput("");
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Streaming failed", err);
      }
    } finally {
      setLoading(false);
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  // ✅ IMPORTANT: If no chat selected, render nothing (App.jsx shows emptyState)
  if (typeof conversationId !== "number") return null;

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === "assistant" ? "msg bot" : "msg user"}
          >
            <div>
              {m.content}
              {isStreaming && m === messages[messages.length - 1] && (
                <span className="cursor">▍</span>
              )}
            </div>

            {m.role === "assistant" && m.meta?.sources?.length > 0 && (
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

        {isStreaming && <div className="typing">Assistant is typing…</div>}

        <div ref={bottomRef} />
      </div>

      <div className="inputRow">
        <input
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type your message…"
        />

        {isStreaming ? (
          <button onClick={stopStreaming} className="stop">
            Stop
          </button>
        ) : (
          <button onClick={sendMessage}>Send</button>
        )}
      </div>
    </div>
  );
}
