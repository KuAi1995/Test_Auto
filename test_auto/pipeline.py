"""Pipeline - 编排完整测试流程."""

import logging
import time
from pathlib import Path
from typing import Optional

from test_auto.analyzer.scanner import Analyzer
from test_auto.config.settings import Settings
from test_auto.generator.manual.generator import ManualTestGenerator
from test_auto.generator.unit.generator import UnitTestGenerator
from test_auto.repo.manager import RepoManager
from test_auto.reporter.html_reporter import Reporter

logger = logging.getLogger(__name__)


class Pipeline:
    """测试流程编排器.

    完整流程: clone/pull → 分析 → 生成测试 → 报告
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._repo_mgr = RepoManager(settings)
        self._reporter = Reporter()

    def run(self, repo_name: Optional[str] = None, skip_clone: bool = False) -> None:
        """执行完整测试流程.

        Args:
            repo_name: 仓库名称（默认第一个）
            skip_clone: 跳过 clone/pull 步骤
        """
        start = time.time()
        name = repo_name or next(iter(self._settings.repos), None)
        if not name:
            logger.error("未配置仓库")
            return

        logger.info("=" * 60)
        logger.info("开始测试流程: %s", name)
        logger.info("=" * 60)

        # Step 1: 仓库同步
        if not skip_clone:
            logger.info("[1/4] 同步仓库...")
            repo_path = self._repo_mgr.clone(name)
        else:
            repo_path = Path(self._settings.workspace_dir) / name
            logger.info("[1/4] 跳过仓库同步，使用: %s", repo_path)

        # Step 2: 代码分析
        logger.info("[2/4] 代码分析...")
        analyzer = Analyzer(repo_path)
        analysis = analyzer.analyze()

        # Step 3: 生成测试
        logger.info("[3/4] 生成测试...")
        output_base = Path("output") / name

        # 单元测试
        unit_gen = UnitTestGenerator(output_base / "unit_tests")
        unit_files = unit_gen.generate_for_project(analysis.classes, analysis.methods)

        # 人工用例
        manual_gen = ManualTestGenerator(output_base / "manual_cases")
        manual_gen.generate_for_project(analysis.classes, analysis.methods)

        # Step 4: 生成报告
        logger.info("[4/4] 生成报告...")
        results = []
        for cls in analysis.classes:
            results.append({
                "name": f"{cls.package}.{cls.name}",
                "status": "passed",
                "duration_ms": 0,
                "message": f"分析完成: {len(cls.methods)} methods",
            })

        report_path = self._reporter.generate_html(
            f"{name} 代码分析与测试生成报告",
            results,
        )

        duration = time.time() - start
        logger.info("=" * 60)
        logger.info("流程完成 (%.1fs)", duration)
        logger.info("  分析: %s", analysis.summary())
        logger.info("  单元测试: %d 文件", len(unit_files))
        logger.info("  报告: %s", report_path)
        logger.info("=" * 60)
