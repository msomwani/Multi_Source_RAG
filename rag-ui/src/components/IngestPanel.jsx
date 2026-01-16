import { useState } from "react";
import { api } from "../api";

export default function IngestPanel({ conversationId }) {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");

  async function uploadFile() {
    if (!file || !conversationId) {
      setStatus("❌ Select a chat before ingesting");
      return;
    }

    try {
      const form = new FormData();
      form.append("file", file);

      await api.post("/ingest", form, {
        params: { conversation_id: conversationId },
      });

      setStatus("✅ File ingested successfully");
      setFile(null);
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed to ingest file");
    }
  }

  async function uploadUrl() {
    if (!url.trim() || !conversationId) {
      setStatus("❌ Select a chat before ingesting");
      return;
    }

    try {
      await api.post("/ingest/url", null, {
        params: {
          url,
          conversation_id: conversationId,
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
          {conversationId ? `Chat #${conversationId}` : "Select a chat first"}
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
