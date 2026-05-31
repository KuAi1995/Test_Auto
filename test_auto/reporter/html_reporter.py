"""测试报告生成器 - HTML 报告 + 截图嵌入 + 趋势图."""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>测试报告 - {title}</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 40px; background: #f5f5f5; }}
.container {{ max-width: 1100px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
h1 {{ color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; }}
h2 {{ color: #555; margin-top: 30px; }}
.summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
.stat {{ text-align: center; padding: 16px; border-radius: 8px; }}
.stat-total {{ background: #E3F2FD; }}
.stat-pass {{ background: #E8F5E9; }}
.stat-fail {{ background: #FFEBEE; }}
.stat-skip {{ background: #FFF3E0; }}
.stat .number {{ font-size: 32px; font-weight: bold; }}
.stat .label {{ color: #666; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #f8f9fa; font-weight: 600; }}
.pass {{ color: #4CAF50; }}
.fail {{ color: #F44336; }}
.error {{ color: #FF9800; }}
.skip {{ color: #9E9E9E; }}
.timestamp {{ color: #999; font-size: 14px; }}
.screenshot {{ max-width: 300px; border-radius: 4px; margin-top: 8px; cursor: pointer; }}
.screenshot:hover {{ transform: scale(1.02); }}
.trend-chart {{ width: 100%; height: 200px; margin: 20px 0; }}
.trend-bar {{ display: inline-block; vertical-align: bottom; margin: 0 2px; border-radius: 3px 3px 0 0; min-width: 20px; text-align: center; font-size: 11px; color: #fff; }}
.trend-container {{ display: flex; align-items: flex-end; height: 150px; border-bottom: 1px solid #ddd; padding: 0 10px; }}
.trend-labels {{ display: flex; padding: 4px 10px; font-size: 11px; color: #999; }}
.trend-labels span {{ flex: 1; text-align: center; }}
</style>
</head>
<body>
<div class="container">
<h1>{title}</h1>
<p class="timestamp">生成时间: {timestamp}</p>
<div class="summary">
<div class="stat stat-total"><div class="number">{total}</div><div class="label">总计</div></div>
<div class="stat stat-pass"><div class="number">{passed}</div><div class="label">通过</div></div>
<div class="stat stat-fail"><div class="number">{failed}</div><div class="label">失败</div></div>
<div class="stat stat-skip"><div class="number">{skipped}</div><div class="label">跳过</div></div>
</div>
{trend_section}
<h2>详细结果</h2>
<table>
<thead><tr><th>用例</th><th>状态</th><th>耗时</th><th>备注</th><th>截图</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
</body>
</html>"""

_TREND_TEMPLATE = """<h2>趋势</h2>
<div class="trend-container">
{bars}
</div>
<div class="trend-labels">
{labels}
</div>"""


class Reporter:
    """测试报告生成器."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self._output_dir = output_dir or Path("output/reports")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(self, title: str, results: list[dict[str, Any]],
                      history: Optional[list[dict]] = None) -> Path:
        """生成 HTML 报告.

        Args:
            title: 报告标题
            results: 测试结果列表
            history: 历史运行数据（用于趋势图）

        Returns:
            报告文件路径
        """
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        skipped = total - passed - failed

        rows = ""
        for r in results:
            status = r.get("status", "unknown")
            css_class = {"passed": "pass", "failed": "fail", "error": "error"}.get(status, "")
            duration = f"{r.get('duration_ms', 0)}ms"

            # 截图嵌入
            screenshot_html = ""
            screenshot_path = r.get("screenshot")
            if screenshot_path and Path(screenshot_path).exists():
                img_data = self._encode_image(Path(screenshot_path))
                screenshot_html = f'<img class="screenshot" src="data:image/png;base64,{img_data}" />'

            rows += (f'<tr><td>{r.get("name", "")}</td>'
                     f'<td class="{css_class}">{status}</td>'
                     f'<td>{duration}</td>'
                     f'<td>{r.get("message", "")}</td>'
                     f'<td>{screenshot_html}</td></tr>\n')

        # 趋势图
        trend_section = ""
        if history and len(history) > 1:
            trend_section = self._build_trend(history)

        html = _HTML_TEMPLATE.format(
            title=title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=total, passed=passed, failed=failed, skipped=skipped,
            trend_section=trend_section,
            rows=rows,
        )

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self._output_dir / filename
        output_path.write_text(html, encoding="utf-8")
        logger.info("报告已生成: %s", output_path)

        # JSON 报告
        json_path = output_path.with_suffix(".json")
        json_path.write_text(json.dumps({
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "summary": {"total": total, "passed": passed, "failed": failed, "skipped": skipped},
            "results": results,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        return output_path

    def generate_junit_xml(self, suite_name: str, results: list[dict[str, Any]]) -> Path:
        """生成 JUnit XML 格式报告（CI 集成用）.

        Args:
            suite_name: 测试套件名称
            results: 测试结果列表

        Returns:
            XML 文件路径
        """
        total = len(results)
        failures = sum(1 for r in results if r.get("status") == "failed")
        errors = sum(1 for r in results if r.get("status") == "error")
        total_time = sum(r.get("duration_ms", 0) for r in results) / 1000.0

        cases_xml = ""
        for r in results:
            name = r.get("name", "unknown").replace('"', '&quot;')
            time_s = r.get("duration_ms", 0) / 1000.0
            status = r.get("status", "unknown")

            if status == "passed":
                cases_xml += f'    <testcase name="{name}" time="{time_s:.3f}" />\n'
            elif status == "failed":
                msg = r.get("message", "").replace('"', '&quot;')
                cases_xml += (f'    <testcase name="{name}" time="{time_s:.3f}">\n'
                              f'      <failure message="{msg}" />\n'
                              f'    </testcase>\n')
            elif status == "error":
                msg = r.get("message", "").replace('"', '&quot;')
                cases_xml += (f'    <testcase name="{name}" time="{time_s:.3f}">\n'
                              f'      <error message="{msg}" />\n'
                              f'    </testcase>\n')
            else:
                cases_xml += (f'    <testcase name="{name}" time="{time_s:.3f}">\n'
                              f'      <skipped />\n'
                              f'    </testcase>\n')

        xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
               f'<testsuite name="{suite_name}" tests="{total}" '
               f'failures="{failures}" errors="{errors}" time="{total_time:.3f}">\n'
               f'{cases_xml}'
               f'</testsuite>\n')

        output_path = self._output_dir / f"{suite_name.replace(' ', '_')}.xml"
        output_path.write_text(xml, encoding="utf-8")
        logger.info("JUnit XML: %s", output_path)
        return output_path

    def _encode_image(self, path: Path) -> str:
        """将图片编码为 base64."""
        return base64.b64encode(path.read_bytes()).decode("ascii")

    def _build_trend(self, history: list[dict]) -> str:
        """构建趋势图 HTML."""
        # 取最近 10 次
        recent = history[:10]
        recent.reverse()  # 时间正序

        max_total = max(r.get("total", 1) for r in recent)
        bars = ""
        labels = ""

        for r in recent:
            total = r.get("total", 0)
            passed = r.get("passed", 0)
            failed = r.get("failed", 0)
            height = int((total / max_total) * 140) if max_total else 10
            color = "#4CAF50" if failed == 0 else "#FF9800" if failed < total / 2 else "#F44336"
            rate = f"{int(passed / total * 100)}%" if total else "0%"
            bars += f'<div class="trend-bar" style="height:{height}px;background:{color};">{rate}</div>\n'
            date = r.get("started_at", "")[:10]
            labels += f'<span>{date[5:]}</span>\n'

        return _TREND_TEMPLATE.format(bars=bars, labels=labels)
