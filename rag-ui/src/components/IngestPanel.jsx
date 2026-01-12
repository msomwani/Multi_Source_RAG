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
        params: { conversation_id: conversationId } // ✅ QUERY PARAM
      });

      setStatus("📄 File ingested successfully ✔");
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
          conversation_id: conversationId
        }
      });

      setStatus("🌐 URL ingested successfully ✔");
      setUrl("");
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed to ingest URL");
    }
  }

  return (
    <div style={{ padding: 10, borderBottom: "1px solid #333" }}>
      <h3 style={{ color: "white" }}>📥 Ingest Data</h3>

      <div style={{ marginBottom: 10 }}>
        <input type="file" onChange={e => setFile(e.target.files[0])} />
        <button onClick={uploadFile}>Upload File</button>
      </div>

      <div>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Enter website URL"
          style={{ width: "70%" }}
        />
        <button onClick={uploadUrl}>Add URL</button>
      </div>

      {status && <p style={{ color: "lightgreen" }}>{status}</p>}
    </div>
  );
}
