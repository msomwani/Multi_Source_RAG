import { useState } from "react";
import { api } from "../api";

export default function IngestPanel({ conversationId, onConversationCreated }) {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");

  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [isUploadingUrl, setIsUploadingUrl] = useState(false);

  const isRealConversation = typeof conversationId === "number";

  async function ensureConversationExists() {
    if (isRealConversation) return conversationId;

    const res = await api.post("/conversations");
    const newId = res.data.id;
    onConversationCreated?.(newId);
    return newId;
  }

  // -----------------------------
  // FILE INGESTION
  // -----------------------------
  async function uploadFile() {
    if (!file || isUploadingFile) return;

    try {
      setIsUploadingFile(true);
      setStatus("⏱️ Ingesting file...");

      const realConversationId = await ensureConversationExists();

      const form = new FormData();
      form.append("file", file);

      await api.post("/ingest", form, {
        params: { conversation_id: realConversationId },
      });

      setStatus("✅ File ingested successfully");
      setFile(null); // reset file
    } catch (e) {
      console.error(e);
      setStatus("❌ Failed to ingest file");
    } finally {
      setIsUploadingFile(false);
    }
  }

  // -----------------------------
  // URL INGESTION
  // -----------------------------
  async function uploadUrl() {
    if (!url.trim() || isUploadingUrl) return;

    try {
      setIsUploadingUrl(true);
      setStatus("⏱️ Ingesting URL...");

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
    } finally {
      setIsUploadingUrl(false);
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

      {/* ---------------- FILE ---------------- */}
      <div className="ingestBlock">
        <label className="ingestLabel">Upload File</label>

        <input
          key={file ? file.name : "empty"} // force reset after upload
          className="ingestInput"
          type="file"
          onChange={(e) => {
            setFile(e.target.files[0] || null);
            setStatus("");
          }}
        />

        <button
          className="ingestActionBtn"
          onClick={uploadFile}
          disabled={!file || isUploadingFile}
        >
          {isUploadingFile ? "Uploading..." : "Upload"}
        </button>
      </div>

      {/* ---------------- URL ---------------- */}
      <div className="ingestBlock">
        <label className="ingestLabel">Ingest URL</label>

        <input
          className="ingestInput"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setStatus("");
          }}
          placeholder="https://example.com"
        />

        <button
          className="ingestActionBtn"
          onClick={uploadUrl}
          disabled={!url.trim() || isUploadingUrl}
        >
          {isUploadingUrl ? "Adding..." : "Add URL"}
        </button>
      </div>

      {status && <div className="ingestStatus">{status}</div>}
    </div>
  );
}
