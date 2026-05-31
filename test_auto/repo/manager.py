"""仓库管理模块 - clone/pull/分支切换."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from test_auto.config.settings import Settings

logger = logging.getLogger(__name__)

_GIT_TIMEOUT = 300  # 5 minutes


class RepoError(Exception):
    """仓库操作异常."""


class RepoManager:
    """远程仓库管理."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._workspace = Path(settings.workspace_dir)
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _repo_path(self, name: str) -> Path:
        """获取仓库本地路径."""
        return self._workspace / name

    def _get_repo_config(self, name: Optional[str] = None):
        """获取仓库配置."""
        if name is None:
            # 默认取第一个
            if not self._settings.repos:
                raise RepoError("配置中未定义任何仓库")
            name = next(iter(self._settings.repos))
        if name not in self._settings.repos:
            raise RepoError(f"仓库 '{name}' 未在配置中定义")
        return name, self._settings.repos[name]

    def clone(self, name: Optional[str] = None) -> Path:
        """Clone 仓库.

        Args:
            name: 仓库名称（配置中的 key）

        Returns:
            本地仓库路径
        """
        name, config = self._get_repo_config(name)
        local_path = self._repo_path(name)

        if local_path.exists() and (local_path / ".git").exists():
            logger.info("仓库已存在，执行 pull: %s", local_path)
            return self.pull(name)

        cmd = ["git", "clone"]
        if config.depth > 0:
            cmd.extend(["--depth", str(config.depth)])
        cmd.extend(["--branch", config.branch, config.url, str(local_path)])

        logger.info("Cloning %s (%s) → %s", config.url, config.branch, local_path)
        self._run_git(cmd)
        logger.info("Clone 完成: %s", local_path)
        return local_path

    def pull(self, name: Optional[str] = None) -> Path:
        """Pull 最新代码.

        Args:
            name: 仓库名称

        Returns:
            本地仓库路径
        """
        name, config = self._get_repo_config(name)
        local_path = self._repo_path(name)

        if not local_path.exists():
            raise RepoError(f"仓库不存在: {local_path}，请先 clone")

        logger.info("Pulling %s...", name)
        self._run_git(["git", "pull", "--ff-only"], cwd=local_path)
        return local_path

    def status(self, name: Optional[str] = None) -> None:
        """显示仓库状态."""
        name, config = self._get_repo_config(name)
        local_path = self._repo_path(name)

        if not local_path.exists():
            logger.info("[%s] 未 clone (url: %s)", name, config.url)
            return

        branch = self._run_git(["git", "branch", "--show-current"], cwd=local_path)
        commit = self._run_git(["git", "log", "-1", "--format=%h %s"], cwd=local_path)
        logger.info("[%s] branch=%s, latest=%s", name, branch, commit)

    def _run_git(self, cmd: list[str], cwd: Optional[Path] = None) -> str:
        """执行 git 命令."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_GIT_TIMEOUT,
                cwd=cwd,
            )
            if result.returncode != 0:
                raise RepoError(f"git 命令失败: {' '.join(cmd)}\n{result.stderr.strip()}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired as e:
            raise RepoError(f"git 命令超时 ({_GIT_TIMEOUT}s): {' '.join(cmd)}") from e
