import { useState } from "react";
import { api } from "../api";

export default function IngestPanel({ conversationId, onConversationCreated }) {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");

  const isDraft = conversationId === "draft";
  const isRealConversation = typeof conversationId === "number";

  async function ensureConversationExists() {
    if (isRealConversation) return conversationId;

    const res = await api.post("/conversations");
    const newId = res.data.id;
    onConversationCreated?.(newId);
    return newId;
  }

  async function uploadFile() {
    if (!file) {
      setStatus("❌ Select a file first");
      return;
    }

    try {
      const realConversationId = await ensureConversationExists();

      const form = new FormData();
      form.append("file", file);

      await api.post("/ingest", form, {
        params: { conversation_id: realConversationId },
      });

      setStatus("✅ File ingested successfully");
      setFile(null);
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed to ingest file");
    }
  }

  async function uploadUrl() {
    if (!url.trim()) {
      setStatus("❌ Enter a URL first");
      return;
    }

    try {
      const realConversationId = await ensureConversationExists();

      await api.post("/ingest/url", null, {
        params: {
          url,
          conversation_id: realConversationId,
        },
      });

      setStatus("✅ URL ingested successfully");
      setUrl("");
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed to ingest URL");
    }
  }

  return (
    <div className="ingestCard">
      <div className="ingestCardHeader">
        <div className="ingestTitle">📥 Ingest Data</div>
        <div className="ingestHint">
          {isRealConversation
            ? `Chat #${conversationId}`
            : "New chat (not saved yet)"}
        </div>
      </div>

      {/* ✅ File */}
      <div className="ingestBlock">
        <label className="ingestLabel">Upload File</label>

        <input
          className="ingestInput"
          type="file"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button className="ingestActionBtn" onClick={uploadFile}>
          Upload
        </button>
      </div>

      {/* ✅ URL */}
      <div className="ingestBlock">
        <label className="ingestLabel">Ingest URL</label>

        <input
          className="ingestInput"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
        />

        <button className="ingestActionBtn" onClick={uploadUrl}>
          Add URL
        </button>
      </div>

      {status && <div className="ingestStatus">{status}</div>}
    </div>
  );
}
