from typing import List, Dict, Any


def normalize_rows(rows: List[List[str]]) -> List[List[str]]:
    if not rows:
        return []

    col_count = max(len(r) for r in rows)
    return [
        r + [""] * (col_count - len(r))
        for r in rows
    ]


def make_table_json(
    title: str,
    rows: List[List[str]],
) -> Dict[str, Any]:
    """
    rows = full table including header row at rows[0]
    Returns structured table JSON.
    """
    rows = normalize_rows(rows)

    if len(rows) < 2:
        return {}

    return {
        "type": "table",
        "title": title,
        "columns": rows[0],
        "rows": rows[1:],
    }


def table_to_row_chunks(
    table_json: Dict[str, Any],
) -> List[str]:
    """
    Convert a structured table into row-level chunks for vector search.
    Each chunk represents one row with column=value pairs.
    """
    title = table_json.get("title", "TABLE")
    columns = table_json.get("columns") or []
    rows = table_json.get("rows") or []

    chunks: list[str] = []

    for row in rows:
        parts = []
        for i, cell in enumerate(row):
            col_name = (
                columns[i]
                if i < len(columns)
                else f"col_{i}"
            )
            parts.append(f"{col_name}={cell}")

        chunks.append(
            f"TABLE: {title} | " + " | ".join(parts)
        )

    return chunks
