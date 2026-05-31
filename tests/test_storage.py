"""存储模块测试."""

import tempfile
from pathlib import Path

from test_auto.storage.database import Database


def test_init_schema():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(f"{tmp}/test.db")
        db.init_schema()
        # 验证表存在
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in tables}
        assert "test_case" in names
        assert "test_run" in names
        assert "test_result" in names
        assert "analysis_cache" in names
        db.close()


def test_save_and_get_run():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(f"{tmp}/test.db")
        db.init_schema()
        db.save_run("run-1", "unit", repo_name="fuos", total=10, passed=8, failed=2)
        history = db.get_run_history()
        assert len(history) == 1
        assert history[0]["id"] == "run-1"
        assert history[0]["passed"] == 8
        db.close()


def test_save_test_cases():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(f"{tmp}/test.db")
        db.init_schema()
        cases = [
            {"id": "TC-001", "title": "Test A", "module": "M1", "priority": "P0"},
            {"id": "TC-002", "title": "Test B", "module": "M1", "priority": "P1"},
        ]
        db.save_test_cases(cases)
        rows = db.conn.execute("SELECT COUNT(*) FROM test_case").fetchone()[0]
        assert rows == 2
        db.close()
