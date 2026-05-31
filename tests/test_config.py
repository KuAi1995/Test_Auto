"""配置模块测试."""

from pathlib import Path

from test_auto.config.settings import Settings, load_settings, validate_settings


def test_default_settings():
    s = Settings()
    assert s.project_name == "Test_Auto"
    assert s.log_level == "INFO"
    assert s.opencv.similarity_threshold == 0.95


def test_load_settings_missing_file():
    s = load_settings(Path("/nonexistent/config.yaml"))
    assert s.project_name == "Test_Auto"


def test_validate_empty_repos():
    s = Settings()
    warnings = validate_settings(s)
    assert any("未配置任何目标仓库" in w for w in warnings)


def test_validate_empty_url():
    from test_auto.config.settings import RepoConfig
    s = Settings(repos={"test": RepoConfig(url="")})
    warnings = validate_settings(s)
    assert any("未配置 URL" in w for w in warnings)


def test_validate_ok():
    from test_auto.config.settings import RepoConfig
    s = Settings(repos={"fuos": RepoConfig(url="git@github.com:test/test.git")})
    warnings = validate_settings(s)
    assert len(warnings) == 0
