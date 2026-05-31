"""SQLite 存储模块."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS test_case (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    module TEXT DEFAULT '',
    test_type TEXT DEFAULT 'manual',
    priority TEXT DEFAULT 'P1',
    precondition TEXT DEFAULT '',
    steps TEXT DEFAULT '[]',
    automated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_run (
    id TEXT PRIMARY KEY,
    test_type TEXT NOT NULL,
    device_serial TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total INTEGER DEFAULT 0,
    passed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    error INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS test_result (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    duration_ms INTEGER DEFAULT 0,
    message TEXT DEFAULT '',
    screenshot TEXT,
    executed_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES test_run(id)
);

CREATE TABLE IF NOT EXISTS baseline_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_version TEXT NOT NULL,
    screen_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(app_version, screen_name)
);

CREATE INDEX IF NOT EXISTS idx_test_result_run ON test_result(run_id);
CREATE INDEX IF NOT EXISTS idx_test_case_module ON test_case(module);
"""


class Database:
    """SQLite 数据库管理."""

    def __init__(self, db_path: str) -> None:
        """初始化数据库连接.

        Args:
            db_path: 数据库文件路径
        """
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        """获取数据库连接（懒初始化）."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def init_schema(self) -> None:
        """初始化数据库 schema."""
        self.conn.executescript(_SCHEMA_SQL)
        # 记录 schema 版本
        self.conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        self.conn.commit()
        logger.info("数据库 schema 初始化完成 (v%d): %s", SCHEMA_VERSION, self._path)

    def close(self) -> None:
        """关闭连接."""
        if self._conn:
            self._conn.close()
            self._conn = None
