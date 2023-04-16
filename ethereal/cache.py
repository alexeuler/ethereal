from typing import TypedDict, Any, Callable
import os
import json
from sqlite3 import Connection, connect
from functools import cached_property
from .base import Base


class CacheConfig(TypedDict):
    """
    Cache configuration
    """

    root: str | None


class MemoryCache(Base):
    """
    In-memory cache
    """

    _cache: dict[str, bytes]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}

    def read(self, key: Any) -> Any:
        """
        Read a value from the cache

        Args:
            key: The key to read

        Returns:
            The value or None if not found
        """
        key_str = json.dumps(canonical_arguments(key))
        return self._cache.get(key_str)

    def upsert(self, key: Any, data: Any):
        """
        Upsert a value into the cache

        Args:
            key: The key to upsert
            data: The data to upsert
        """
        key_str = json.dumps(canonical_arguments(key))
        self._cache[key_str] = data

    def delete(self, key: Any):
        """
        Delete a value from the cache

        Args:
            key: The key to delete
        """
        key_str = json.dumps(canonical_arguments(key))
        del self._cache[key_str]


class DbCache(Base):
    """
    Database cache
    """

    _config: CacheConfig
    _root: str

    def __init__(self, config: CacheConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config
        if "root" in config:
            self._root = os.path.realpath(config["root"])
        else:
            current_folder = os.path.realpath(os.path.dirname(__file__))
            self._root = f"{current_folder}/cache"
        os.makedirs(self._root, exist_ok=True)

    def upsert(self, key: Any, data: Any):
        """
        Upsert a value into the cache

        Args:
            key: The key to upsert
            data: The data to upsert
        """
        key_str = json.dumps(canonical_arguments(key))
        self._upsert_str(key_str, data)

    def delete(self, key: Any):
        """
        Delete a value from the cache

        Args:
            key: The key to delete
        """
        key_str = json.dumps(canonical_arguments(key))
        self._delete_str(key_str)

    def read(self, key: Any) -> bytes | None:
        """
        Read a value from the cache

        Args:
            key: The key to read

        Returns:
            The value or None if not found
        """
        key_str = json.dumps(canonical_arguments(key))
        res = self._read_str(key_str)
        if res is None:
            return None
        return json.loads(res)

    def commit(self):
        """
        Commit the cache to disk
        """
        self._conn.commit()

    def _read_str(self, key: str) -> bytes | None:
        cursor = self._conn.cursor()
        statement = "SELECT data FROM cache WHERE key = ?"
        cursor.execute(
            statement,
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def _upsert_str(self, key: str, data: Any):
        cursor = self._conn.cursor()
        statement = (
            "INSERT INTO cache (key, data) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET data = excluded.data"
        )
        cursor.execute(statement, (key, json.dumps(data)))

    def _delete_str(self, key: str):
        cursor = self._conn.cursor()
        statement = (
            "DELETE FROM cache WHERE key = ?",
            (key,),
        )
        cursor.execute(statement)

    @cached_property
    def _conn(self) -> Connection:
        """
        :class:`sqlite3.Connection` to a database cache
        """
        return connection_from_path(f"{self._root}/cache.sqlite3")


class Cache(Base):
    """
    Cache that uses both memory and database
    """

    _memory_cache: MemoryCache
    _db_cache: DbCache

    def __init__(self, memory_cache: MemoryCache, db_cache: DbCache, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._memory_cache = memory_cache
        self._db_cache = db_cache

    def read_or_fetch(self, key: Any, fetcher: Callable) -> Any:
        """
        Read a value from the cache or fetch it if not found

        Args:
            key: The key to read
            fetcher: A function to fetch the value

        Returns:
            The value as int / str / list / dict
        """
        value = self.read(key)
        if value is None:
            value = fetcher()
            self.upsert(key, value)
        return value

    def read(self, key: Any) -> bytes | None:
        """
        Read a value from the cache

        Args:
            key: The key to read

        Returns:
            The value or None if not found
        """
        value = self._memory_cache.read(key)
        if value is None:
            value = self._db_cache.read(key)

        if value is not None:
            self._memory_cache.upsert(key, value)

        return value

    def upsert(self, key: Any, data: bytes):
        """
        Upsert a value into the cache

        Args:
            key: The key to upsert
            data: The data to upsert
        """
        self._memory_cache.upsert(key, data)
        self._db_cache.upsert(key, data)
        self._db_cache.commit()

    def delete(self, key: Any):
        """
        Delete a value from the cache

        Args:
            key: The key to delete
        """
        self._memory_cache.delete(key)
        self._db_cache.delete(key)


def canonical_arguments(args: Any) -> Any:
    """
    Sort all dictionaries by key

    Args:
        args: args to sort
    """
    if isinstance(args, dict):
        args = {k: canonical_arguments(v) for k, v in args.items()}
        return {k: args[k] for k in sorted(args.keys())}
    if not isinstance(args, (list, tuple)):
        return args
    args = [canonical_arguments(v) for v in args]
    return args


def connection_from_path(path: str) -> Connection:
    """
    Creates a connection to a database at ``path``.
    If the file at ``path`` doesn't exist, creates a new one and
    initializes a database schema.

    Args:
        path: The absolute path to the database

    Returns:
        An instance of sqlite3 Connection

    Note:
        The schema migrations are currently not supported.
    """

    is_fresh = not os.path.exists(path)
    conn = connect(path)
    if is_fresh:
        _init_db(conn)
    return conn


def _init_db(conn: Connection):
    """
    Initialize db schema

    Args:
        conn: Connection to the database
    """
    cursor = conn.cursor()

    # Cache table

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS cache
            (key TEXT, data BLOB)"""
    )
    cursor.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_cache_id \
        ON cache(key)
    """
    )
    conn.commit()
