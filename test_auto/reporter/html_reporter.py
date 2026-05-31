"""测试报告生成器 - HTML 报告."""

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
.container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
h1 {{ color: #333; border-bottom: 2px solid #007AFF; padding-bottom: 10px; }}
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
<table>
<thead><tr><th>用例</th><th>状态</th><th>耗时</th><th>备注</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
</body>
</html>"""


class Reporter:
    """测试报告生成器."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self._output_dir = output_dir or Path("output/reports")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(self, title: str, results: list[dict[str, Any]]) -> Path:
        """生成 HTML 报告.

        Args:
            title: 报告标题
            results: 测试结果列表，每项包含 name/status/duration_ms/message

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
            css_class = status if status in ("pass", "fail", "error", "skip") else ""
            if status == "passed":
                css_class = "pass"
            elif status == "failed":
                css_class = "fail"
            duration = f"{r.get('duration_ms', 0)}ms"
            rows += f'<tr><td>{r.get("name", "")}</td><td class="{css_class}">{status}</td><td>{duration}</td><td>{r.get("message", "")}</td></tr>\n'

        html = _HTML_TEMPLATE.format(
            title=title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            rows=rows,
        )

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self._output_dir / filename
        output_path.write_text(html, encoding="utf-8")
        logger.info("报告已生成: %s", output_path)

        # 同时输出 JSON
        json_path = output_path.with_suffix(".json")
        json_path.write_text(json.dumps({
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "summary": {"total": total, "passed": passed, "failed": failed, "skipped": skipped},
            "results": results,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        return output_path
