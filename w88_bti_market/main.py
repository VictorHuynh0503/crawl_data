from fastapi import FastAPI, HTTPException
import sqlite3
import os

app = FastAPI(title="SQLite API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    "db": r"F:\Projects\crawl_data\w88_bti_market\w88.db"
}


def get_connection(db_name: str):
    db_path = DATABASES.get(db_name)

    if not db_path:
        raise HTTPException(
            status_code=404,
            detail=f"Database '{db_name}' not found"
        )

    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=500,
            detail=f"Database file does not exist: {db_path}"
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    return conn


@app.get("/")
def health():
    return {
        "status": "ok",
        "database_exists": os.path.exists(DATABASES["db"])
    }


@app.get("/tables/{db_name}")
def list_tables(db_name: str):
    conn = get_connection(db_name)

    try:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()

        return {
            "database": db_name,
            "tables": [row["name"] for row in rows]
        }

    finally:
        conn.close()


@app.get("/table")
def get_table(
    table: str,
    db: str = "db",
    limit: int = 1000,
    offset: int = 0
):
    conn = get_connection(db)

    try:
        exists = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (table,)
        ).fetchone()

        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table}' not found"
            )

        query = f'SELECT * FROM "{table}" LIMIT ? OFFSET ?'

        rows = conn.execute(
            query,
            (limit, offset)
        ).fetchall()

        return {
            "database": db,
            "table": table,
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "data": [dict(row) for row in rows]
        }

    finally:
        conn.close()


@app.get("/count")
def count_rows(
    table: str,
    db: str = "db"
):
    conn = get_connection(db)

    try:
        exists = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name=?
            """,
            (table,)
        ).fetchone()

        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{table}' not found"
            )

        count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        return {
            "database": db,
            "table": table,
            "count": count
        }

    finally:
        conn.close()