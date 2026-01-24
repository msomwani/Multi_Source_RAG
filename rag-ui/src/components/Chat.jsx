import { useState, useEffect, useRef } from "react";
import { api } from "../api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ✅ NEW: structured table renderer
import TableBlock from "./TableBlock";

export default function Chat({ conversationId, onConversationCreated }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const abortRef = useRef(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  const isDraft = conversationId === "draft";
  const isRealConversation = typeof conversationId === "number";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  useEffect(() => {
    if (!isRealConversation) {
      setMessages([]);
      return;
    }

    async function loadConversation() {
      const res = await api.get(`/conversations/${conversationId}`);
      setMessages(res.data.messages || []);
    }

    loadConversation();
  }, [conversationId, isRealConversation]);

  function stopStreaming() {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
    setLoading(false);
  }

  async function ensureConversationExists() {
    if (isRealConversation) return conversationId;

    const res = await api.post("/conversations");
    const newId = res.data.id;

    onConversationCreated?.(newId);
    return newId;
  }

  async function sendMessage() {
    if (!input.trim()) return;

    const userText = input.trim();
    setInput("");

    setLoading(true);
    setIsStreaming(true);

    const realConversationId = await ensureConversationExists();

    const userMsgId = Date.now();
    const assistantMsgId = userMsgId + 1;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: userText },
      { id: assistantMsgId, role: "assistant", content: "" },
    ]);

    abortRef.current = new AbortController();

    try {
      const res = await fetch(`${api.defaults.baseURL}/query/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortRef.current.signal,
        body: JSON.stringify({
          query: userText,
          conversation_id: realConversationId,
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
            m.id === assistantMsgId ? { ...m, content: m.content + chunk } : m
          )
        );
      }

      // ✅ After stream completes, reload conversation to get meta (sources + tables)
      const convo = await api.get(`/conversations/${realConversationId}`);
      setMessages(convo.data.messages || []);
    } catch (err) {
      if (err?.name !== "AbortError") {
        console.error("Streaming failed", err);
      }
    } finally {
      setLoading(false);
      setIsStreaming(false);
      abortRef.current = null;
    }
  }

  // ✅ Enter = Send, Shift+Enter = New line
  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.length === 0 && (
          <div className="emptyState">
            <h2>{isDraft ? "New Chat ✍️" : "No messages yet"}</h2>
            <p>
              {isDraft
                ? "Type a message or ingest a document to start."
                : "Start by sending your first message."}
            </p>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === "assistant" ? "msg bot" : "msg user"}
          >
            <div className="msgContent">
              {m.role === "assistant" ? (
                <>
                  {/* ✅ normal markdown answer */}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}
                    components={{
                      table: () => null,
                      thead: () => null,
                      tbody: () => null,
                      tr: () => null,
                      th: () => null,
                      td: () => null,
                    }}
                    >
                    {m.content}
                  </ReactMarkdown>

                  {/* ✅ structured tables (from m.meta.tables) */}
                  {m.meta?.tables?.length > 0 && (
                    <div className="tablesWrap">
                      {m.meta.tables.map((t, i) => (
                        <TableBlock key={i} table={t} />
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div>{m.content}</div>
              )}

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
        <textarea
          ref={textareaRef}
          className="chatInput"
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message… (Enter to send, Shift+Enter for new line)"
          rows={1}
        />

        {isStreaming ? (
          <button onClick={stopStreaming} className="stop">
            Stop
          </button>
        ) : (
          <button onClick={sendMessage} disabled={loading}>
            Send
          </button>
        )}
      </div>
    </div>
  );
}
