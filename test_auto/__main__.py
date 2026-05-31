"""CLI 入口."""

import argparse
import logging
import sys

from test_auto import __version__
from test_auto.config.settings import load_settings


def setup_logging(level: str) -> None:
    """配置日志."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    """主入口.

    Returns:
        退出码
    """
    parser = argparse.ArgumentParser(
        prog="test_auto",
        description="Android App 自动化测试平台",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-c", "--config", help="配置文件路径", default=None)

    subparsers = parser.add_subparsers(dest="command")

    # repo 子命令
    repo_parser = subparsers.add_parser("repo", help="仓库管理")
    repo_parser.add_argument("action", choices=["clone", "pull", "status"], help="操作")
    repo_parser.add_argument("--name", help="仓库名称（对应配置中的 key）")

    # analyze 子命令
    subparsers.add_parser("analyze", help="代码分析")

    # generate 子命令
    gen_parser = subparsers.add_parser("generate", help="生成测试")
    gen_parser.add_argument("type", choices=["unit", "manual"], help="测试类型")
    gen_parser.add_argument("--name", help="仓库名称")
    gen_parser.add_argument("--output", help="输出目录", default=None)

    # devices 子命令
    subparsers.add_parser("devices", help="列出已连接设备")

    # init 子命令
    subparsers.add_parser("init", help="初始化工作目录和数据库")

    args = parser.parse_args()

    from pathlib import Path

    config_path = Path(args.config) if args.config else None
    settings = load_settings(config_path)
    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)

    if args.command == "init":
        from test_auto.storage.database import Database

        db = Database(settings.storage.db_path)
        db.init_schema()
        db.close()
        # 创建工作目录
        Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.storage.screenshots_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.storage.baselines_dir).mkdir(parents=True, exist_ok=True)
        logger.info("初始化完成")
        return 0

    if args.command == "devices":
        from test_auto.utils.adb import ADBError, list_devices

        try:
            devices = list_devices()
            if not devices:
                print("未发现已连接设备")
            else:
                for d in devices:
                    print(f"  {d.serial}  {d.state}  {d.model}")
        except ADBError as e:
            logger.error("ADB 错误: %s", e)
            return 1
        return 0

    if args.command == "repo":
        from test_auto.repo.manager import RepoManager

        mgr = RepoManager(settings)
        if args.action == "clone":
            mgr.clone(args.name)
        elif args.action == "pull":
            mgr.pull(args.name)
        elif args.action == "status":
            mgr.status(args.name)
        return 0

    if args.command == "analyze":
        from pathlib import Path as P

        from test_auto.analyzer.scanner import Analyzer

        # 分析所有已 clone 的仓库
        workspace = P(settings.workspace_dir)
        for name in settings.repos:
            repo_path = workspace / name
            if not repo_path.exists():
                logger.warning("仓库未 clone: %s，跳过", name)
                continue
            logger.info("分析仓库: %s", name)
            analyzer = Analyzer(repo_path)
            result = analyzer.analyze()
            print(f"\n[{name}] {result.summary()}")
            for cls in result.classes:
                print(f"  {cls.package}.{cls.name} ({cls.superclass or 'Object'}) - {len(cls.methods)} methods")
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "generate":
        from pathlib import Path as P

        from test_auto.analyzer.scanner import Analyzer
        from test_auto.generator.unit.generator import UnitTestGenerator

        workspace = P(settings.workspace_dir)
        name = args.name or next(iter(settings.repos), None)
        if not name:
            logger.error("未配置仓库")
            return 1
        repo_path = workspace / name
        if not repo_path.exists():
            logger.error("仓库未 clone: %s", name)
            return 1

        analyzer = Analyzer(repo_path)
        result = analyzer.analyze()

        if args.type == "unit":
            output_dir = P(args.output) if args.output else P("output/tests") / name
            gen = UnitTestGenerator(output_dir)
            files = gen.generate_for_project(result.classes, result.methods)
            print(f"\n生成 {len(files)} 个单元测试文件 → {output_dir}")
            for f in files:
                print(f"  {f.relative_to(output_dir)}")
        else:
            from test_auto.generator.manual.generator import ManualTestGenerator

            output_dir = P(args.output) if args.output else P("output/cases") / name
            gen = ManualTestGenerator(output_dir)
            output_file = gen.generate_for_project(result.classes, result.methods)
            print(f"\n测试用例已生成 → {output_file}")
        return 0

    logger.warning("未实现的命令: %s", args.command)
    return 1


if __name__ == "__main__":
    sys.exit(main())
