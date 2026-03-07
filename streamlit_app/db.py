"""
Database connection module for Turso
Uses libsql_experimental SDK (libsql-client is deprecated and hangs
on regional Turso URLs).
"""
import time

import streamlit as st
import libsql_experimental as libsql


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
    """Wrapper that adds dict-like Row access to libsql cursors."""
    def __init__(self, raw_cursor):
        self._cursor = raw_cursor

    def execute(self, query, params=None):
        if params:
            # libsql_experimental requires tuples, not lists
            self._cursor.execute(query, tuple(params))
        else:
            self._cursor.execute(query)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in self._cursor.description]
        return Row(columns, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        columns = [desc[0] for desc in self._cursor.description]
        return [Row(columns, row) for row in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid


class Connection:
    """Wrapper that returns dict-like Row cursors."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return Cursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()
        self._conn.sync()

    def rollback(self):
        self._conn.rollback()

    def execute(self, query, params=None):
        cursor = self.cursor()
        return cursor.execute(query, params)


@st.cache_resource
def get_db():
    """Get database connection to Turso (embedded replica for fast reads)"""
    conn = libsql.connect(
        "shows-attended",
        sync_url=st.secrets["turso"]["database_url"],
        auth_token=st.secrets["turso"]["auth_token"],
    )
    conn.sync()
    return Connection(conn)
