"""
Database connection module for Turso
Provides sqlite3-compatible interface for libsql
"""
import streamlit as st
from libsql_client import create_client_sync

class Row:
    """Wrapper to provide dict-like access to row data"""
    def __init__(self, columns, values):
        self._columns = columns
        self._values = values
        self._dict = dict(zip(columns, values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._dict[key]

    def keys(self):
        return self._columns

class Cursor:
    """Wrapper to provide sqlite3 cursor-like interface"""
    def __init__(self, client):
        self._client = client
        self._result = None

    def execute(self, query, params=None):
        """Execute a query"""
        if params:
            # Convert ? placeholders to positional parameters for libsql
            self._result = self._client.execute(query, params)
        else:
            self._result = self._client.execute(query)
        return self

    def fetchone(self):
        """Fetch one row"""
        if not self._result or not self._result.rows:
            return None
        row = self._result.rows[0]
        if self._result.columns:
            return Row(self._result.columns, row)
        return row

    def fetchall(self):
        """Fetch all rows"""
        if not self._result or not self._result.rows:
            return []
        if self._result.columns:
            return [Row(self._result.columns, row) for row in self._result.rows]
        return self._result.rows

class Connection:
    """Wrapper to provide sqlite3 connection-like interface"""
    def __init__(self, client):
        self._client = client
        self.row_factory = None

    def cursor(self):
        """Create a cursor"""
        return Cursor(self._client)

    def commit(self):
        """Commit transaction (auto-commit in libsql)"""
        pass

    def execute(self, query, params=None):
        """Execute a query directly on the connection"""
        cursor = self.cursor()
        return cursor.execute(query, params)

@st.cache_resource
def get_db():
    """Get database connection to Turso"""
    client = create_client_sync(
        url=st.secrets["turso"]["database_url"],
        auth_token=st.secrets["turso"]["auth_token"]
    )
    return Connection(client)
