import sqlite3
import pandas as pd
from pathlib import Path

class SQLiteDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def write_df(
        self,
        df: pd.DataFrame,
        table_name: str,
        index: bool = False
    ):
        """
        Replace table with dataframe.
        """
        with self._connect() as conn:
            df.to_sql(
                table_name,
                conn,
                if_exists="replace",
                index=index
            )

    def append_df(
        self,
        df: pd.DataFrame,
        table_name: str,
        index: bool = False
    ):
        """
        Append dataframe rows to table.
        """
        with self._connect() as conn:
            df.to_sql(
                table_name,
                conn,
                if_exists="append",
                index=index
            )

    def read_df(
        self,
        query: str,
        params=None
    ) -> pd.DataFrame:
        """
        Read SQL query result into DataFrame.
        """
        with self._connect() as conn:
            return pd.read_sql_query(
                query,
                conn,
                params=params
            )

    def execute(
        self,
        sql: str,
        params=None
    ):
        """
        Execute INSERT/UPDATE/DELETE/DDL.
        """
        with self._connect() as conn:
            conn.execute(sql, params or [])
            conn.commit()
            
    def table_exists(self, table_name: str) -> bool:
        with self._connect() as conn:
            result = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                  AND name=?
                """,
                (table_name,)
            ).fetchone()

        return result is not None

    def save_df(
        self,
        df: pd.DataFrame,
        table_name: str,
        index: bool = False
    ):
        """
        Create table if it doesn't exist.
        Append otherwise.
        """

        db_exists = Path(self.db_path).exists()

        if not db_exists:
            mode = "replace"
        elif not self.table_exists(table_name):
            mode = "replace"
        else:
            mode = "append"

        with self._connect() as conn:
            df.to_sql(
                table_name,
                conn,
                if_exists=mode,
                index=index
            )

        print(f"{mode.upper()} -> {table_name}")