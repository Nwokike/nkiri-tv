import json
import time
import aiosqlite
import os


class Cache:
    def __init__(self, db_path: str = "storage/data/seriestv.db"):
        self.db_path = os.path.abspath(db_path)
        self._db: aiosqlite.Connection | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            await self._db.execute("PRAGMA journal_mode=WAL;")
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires INTEGER
                )
            """)
            await self._db.commit()
        return self._db

    async def get(self, key: str) -> str | None:
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT value, expires FROM cache WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        if row:
            value, expires = row
            if expires > time.time():
                return value
            await db.execute("DELETE FROM cache WHERE key = ?", (key,))
            await db.commit()
        return None

    async def set(self, key: str, value: str, ttl: int = 3600):
        db = await self._get_db()
        expires = int(time.time()) + ttl
        await db.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
            (key, value, expires),
        )
        await db.commit()

    async def set_json(self, key: str, value, ttl: int = 3600):
        await self.set(key, json.dumps(value, default=str), ttl)

    async def get_json(self, key: str):
        raw = await self.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def invalidate(self, key: str):
        db = await self._get_db()
        await db.execute("DELETE FROM cache WHERE key = ?", (key,))
        await db.commit()

    async def clear(self):
        db = await self._get_db()
        await db.execute("DELETE FROM cache")
        await db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None
