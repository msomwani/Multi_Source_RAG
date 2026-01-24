from typing import List, Dict, Any


def normalize_rows(rows: List[List[str]]) -> List[List[str]]:
    if not rows:
        return []

    col_count = max(len(r) for r in rows)
    return [r + [""] * (col_count - len(r)) for r in rows]


def make_table_json(title: str, rows: List[List[str]]) -> Dict[str, Any]:
    """
    rows = full table including header row as rows[0]
    Returns a structured table JSON dict.
    """
    rows = normalize_rows(rows)

    if len(rows) < 2:
        return {}

    columns = rows[0]
    body = rows[1:]

    return {
        "type": "table",
        "title": title,
        "columns": columns,
        "rows": body,
    }


def table_to_row_chunks(table_json: Dict[str, Any]) -> List[str]:
    """
    Convert a structured table into row-level chunks for vector search.
    We store each row as a text chunk while attaching full table JSON in metadata.
    """
    title = table_json.get("title", "TABLE")
    cols = table_json.get("columns", []) or []
    rows = table_json.get("rows", []) or []

    chunks = []

    for r in rows:
        parts = []
        for i, cell in enumerate(r):
            col_name = cols[i] if i < len(cols) else f"col_{i}"
            parts.append(f"{col_name}={cell}")

        chunks.append(f"TABLE: {title} | " + " | ".join(parts))

    return chunks
