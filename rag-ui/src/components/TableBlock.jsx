export default function TableBlock({ table }) {
  if (!table) return null;

  const title = table.title || "Table";
  const columns = table.columns || [];
  const rows = table.rows || [];

  if (columns.length === 0) return null;

  // ✅ Filter example: remove "Handwriting OCR" row
  const filteredRows = rows.filter((r) => {
    const firstCol = (r?.[0] || "").toLowerCase().trim();
    return firstCol !== "handwriting ocr";
  });

  return (
    <div className="tableBlock">
      <div className="tableTitle">{title}</div>

      <div className="tableScroll">
        <table className="structuredTable">
          <thead>
            <tr>
              {columns.map((c, i) => (
                <th key={i}>{c}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {filteredRows.map((r, ri) => (
              <tr key={ri}>
                {r.map((cell, ci) => (
                  <td key={ci}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
