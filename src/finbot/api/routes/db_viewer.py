"""Read-only database browser endpoints."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import inspect, text

from finbot.api.deps import CurrentUser, DbSession
from finbot.db.database import get_engine

router = APIRouter(prefix="/api/db", tags=["db-viewer"])


@router.get("/tables")
def list_tables(_user: CurrentUser):
    """Return all table names with row counts."""
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    result = []
    with engine.connect() as conn:
        for name in sorted(tables):
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar()  # noqa: S608
            columns = [col["name"] for col in inspector.get_columns(name)]
            result.append({"name": name, "row_count": count, "column_count": len(columns)})
    return result


@router.get("/tables/{table_name}")
def get_table_rows(
    table_name: str,
    db: DbSession,
    _user: CurrentUser,
    limit: int = Query(25, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc"),
    search: str | None = Query(None),
):
    """Return paginated rows with column metadata."""
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if table_name not in tables:
        return {"error": f"Table '{table_name}' not found"}

    columns_meta = inspector.get_columns(table_name)
    col_names = [c["name"] for c in columns_meta]
    col_types = [str(c["type"]) for c in columns_meta]

    with engine.connect() as conn:
        total = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()  # noqa: S608

        query = f'SELECT * FROM "{table_name}"'  # noqa: S608

        if search:
            text_cols = [c["name"] for c in columns_meta if "CHAR" in str(c["type"]).upper() or "TEXT" in str(c["type"]).upper()]
            if text_cols:
                conditions = " OR ".join(f'"{col}" LIKE :search' for col in text_cols)
                query += f" WHERE ({conditions})"

        if sort_by and sort_by in col_names:
            direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
            query += f' ORDER BY "{sort_by}" {direction}'

        query += f" LIMIT {limit} OFFSET {offset}"

        params = {}
        if search:
            params["search"] = f"%{search}%"

        rows = conn.execute(text(query), params).fetchall()

    return {
        "table": table_name,
        "columns": [{"name": n, "type": t} for n, t in zip(col_names, col_types)],
        "rows": [dict(zip(col_names, row)) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/tables/{table_name}/export")
def export_table(table_name: str, _user: CurrentUser):
    """Export full table as CSV."""
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if table_name not in tables:
        return {"error": f"Table '{table_name}' not found"}

    col_names = [c["name"] for c in inspector.get_columns(table_name)]

    with engine.connect() as conn:
        rows = conn.execute(text(f'SELECT * FROM "{table_name}"')).fetchall()  # noqa: S608

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(col_names)
    for row in rows:
        writer.writerow(list(row))

    return PlainTextResponse(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"},
    )
