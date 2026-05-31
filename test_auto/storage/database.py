"""SQLite 存储模块."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2

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
    repo_name TEXT DEFAULT '',
    device_serial TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total INTEGER DEFAULT 0,
    passed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    error INTEGER DEFAULT 0,
    report_path TEXT DEFAULT ''
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

CREATE TABLE IF NOT EXISTS analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_name TEXT NOT NULL,
    commit_hash TEXT DEFAULT '',
    total_classes INTEGER DEFAULT 0,
    total_methods INTEGER DEFAULT 0,
    total_packages INTEGER DEFAULT 0,
    total_activities INTEGER DEFAULT 0,
    data_json TEXT DEFAULT '{}',
    analyzed_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_test_result_run ON test_result(run_id);
CREATE INDEX IF NOT EXISTS idx_test_case_module ON test_case(module);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_repo ON analysis_cache(repo_name);
CREATE INDEX IF NOT EXISTS idx_test_run_repo ON test_run(repo_name);
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

    def save_run(self, run_id: str, test_type: str, repo_name: str = "",
                 total: int = 0, passed: int = 0, failed: int = 0,
                 report_path: str = "") -> None:
        """保存测试运行记录."""
        from datetime import datetime
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT OR REPLACE INTO test_run
               (id, test_type, repo_name, started_at, finished_at, total, passed, failed, report_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, test_type, repo_name, now, now, total, passed, failed, report_path),
        )
        self.conn.commit()

    def save_results(self, run_id: str, results: list[dict]) -> None:
        """批量保存测试结果."""
        import uuid
        from datetime import datetime
        now = datetime.now().isoformat()
        rows = [
            (str(uuid.uuid4()), run_id, r.get("case_id", ""), r.get("status", "pending"),
             r.get("duration_ms", 0), r.get("message", ""), r.get("screenshot"), now)
            for r in results
        ]
        self.conn.executemany(
            """INSERT INTO test_result (id, run_id, case_id, status, duration_ms, message, screenshot, executed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        self.conn.commit()

    def save_analysis(self, repo_name: str, commit_hash: str,
                      total_classes: int, total_methods: int,
                      total_packages: int, total_activities: int,
                      data_json: str = "{}") -> None:
        """保存分析结果缓存."""
        from datetime import datetime
        self.conn.execute(
            """INSERT INTO analysis_cache
               (repo_name, commit_hash, total_classes, total_methods, total_packages, total_activities, data_json, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (repo_name, commit_hash, total_classes, total_methods, total_packages, total_activities,
             data_json, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_run_history(self, repo_name: str = "", limit: int = 10) -> list[dict]:
        """获取测试运行历史."""
        if repo_name:
            rows = self.conn.execute(
                "SELECT * FROM test_run WHERE repo_name=? ORDER BY started_at DESC LIMIT ?",
                (repo_name, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM test_run ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def save_test_cases(self, cases: list[dict]) -> None:
        """批量保存测试用例."""
        import json
        from datetime import datetime
        now = datetime.now().isoformat()
        rows = [
            (c["id"], c["title"], c.get("module", ""), c.get("test_type", "manual"),
             c.get("priority", "P1"), c.get("precondition", ""),
             json.dumps(c.get("steps", []), ensure_ascii=False),
             1 if c.get("automated") else 0, now, now)
            for c in cases
        ]
        self.conn.executemany(
            """INSERT OR REPLACE INTO test_case
               (id, title, module, test_type, priority, precondition, steps, automated, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        self.conn.commit()
        logger.info("保存 %d 条测试用例", len(cases))
