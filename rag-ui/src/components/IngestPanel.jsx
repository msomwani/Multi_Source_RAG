import { useState } from "react";
import { api } from "../api";

export default function IngestPanel() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");

  async function uploadFile() {
    if (!file) return;

    try {
      const form = new FormData();
      form.append("file", file);

      await api.post("/ingest", form, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setStatus("📄 File ingested successfully ✔");
      setFile(null);
    } catch (e) {
      setStatus("❌ Failed to ingest file");
    }
  }

  async function uploadUrl() {
    if (!url.trim()) return;

    try {
      await api.post("/ingest/url", null, {
        params: { url }
      });

      setStatus("🌐 URL ingested successfully ✔");
      setUrl("");
    } catch (e) {
      setStatus("❌ Failed to ingest URL");
    }
  }

  return (
    <div style={{ padding: 10, borderBottom: "1px solid #333" }}>
      <h3 style={{ color: "white" }}>📥 Ingest Data</h3>

      {/* FILE UPLOAD */}
      <div style={{ marginBottom: 10 }}>
        <input
          type="file"
          onChange={e => setFile(e.target.files[0])}
        />
        <button onClick={uploadFile}>Upload File</button>
      </div>

      {/* URL UPLOAD */}
      <div>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Enter website URL"
          style={{ width: "70%" }}
        />
        <button onClick={uploadUrl}>Add URL</button>
      </div>

      {status && (
        <p style={{ color: "lightgreen" }}>{status}</p>
      )}
    </div>
  );
}
