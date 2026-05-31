"""报告模块测试."""

import tempfile
from pathlib import Path

from test_auto.reporter.html_reporter import Reporter


def test_generate_html():
    with tempfile.TemporaryDirectory() as tmp:
        r = Reporter(output_dir=Path(tmp))
        results = [
            {"name": "test_a", "status": "passed", "duration_ms": 100, "message": ""},
            {"name": "test_b", "status": "failed", "duration_ms": 200, "message": "断言失败"},
        ]
        path = r.generate_html("Test Report", results)
        assert path.exists()
        content = path.read_text()
        assert "test_a" in content
        assert "test_b" in content
        assert "断言失败" in content


def test_generate_junit_xml():
    with tempfile.TemporaryDirectory() as tmp:
        r = Reporter(output_dir=Path(tmp))
        results = [
            {"name": "test_pass", "status": "passed", "duration_ms": 50},
            {"name": "test_fail", "status": "failed", "duration_ms": 100, "message": "error msg"},
        ]
        path = r.generate_junit_xml("my_suite", results)
        assert path.exists()
        content = path.read_text()
        assert 'tests="2"' in content
        assert 'failures="1"' in content
        assert "test_pass" in content
        assert "error msg" in content
