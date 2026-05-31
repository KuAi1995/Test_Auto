"""配置加载模块 - 基于 Pydantic v2 + YAML."""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path("configs/config.yaml")


class RepoConfig(BaseModel):
    """目标仓库配置."""

    url: str = ""
    branch: str = "main"
    depth: int = 0  # 0 表示完整 clone


class DeviceConfig(BaseModel):
    """设备配置."""

    serial: str = ""
    name: str = ""
    platform_version: str = ""


class OpenCVConfig(BaseModel):
    """OpenCV UI 对比配置."""

    similarity_threshold: float = 0.95
    mask_regions: list[dict] = Field(default_factory=list)


class StorageConfig(BaseModel):
    """存储配置."""

    db_path: str = "data/db/test_auto.db"
    screenshots_dir: str = "data/screenshots"
    baselines_dir: str = "data/baselines"


class Settings(BaseModel):
    """全局配置."""

    project_name: str = "Test_Auto"
    repos: dict[str, RepoConfig] = Field(default_factory=dict)
    devices: list[DeviceConfig] = Field(default_factory=list)
    opencv: OpenCVConfig = Field(default_factory=OpenCVConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    log_level: str = "INFO"
    workspace_dir: str = "workspace"


def load_settings(config_path: Optional[Path] = None) -> Settings:
    """从 YAML 文件加载配置.

    Args:
        config_path: 配置文件路径，默认 configs/config.yaml

    Returns:
        Settings 实例
    """
    path = config_path or _DEFAULT_CONFIG_PATH
    if not path.exists():
        logger.warning("配置文件不存在: %s，使用默认配置", path)
        return Settings()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return Settings(**data)


def validate_settings(settings: Settings) -> list[str]:
    """校验配置完整性.

    Args:
        settings: 配置实例

    Returns:
        警告信息列表（空列表表示配置完整）
    """
    warnings = []

    if not settings.repos:
        warnings.append("未配置任何目标仓库 (repos)")
    else:
        for name, repo in settings.repos.items():
            if not repo.url:
                warnings.append(f"仓库 '{name}' 未配置 URL")

    if not Path(settings.workspace_dir).parent.exists():
        warnings.append(f"工作目录父路径不存在: {settings.workspace_dir}")

    return warnings
