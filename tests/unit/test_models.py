"""Unit tests for InfdbConfig and InfdbLogger — no database required."""
import logging
import os

import pytest
import yaml
from infdb.config import InfdbConfig
from infdb.logger import InfdbLogger


# ── InfdbConfig: no config file ───────────────────────────────────────────────


class TestInfdbConfigNoFile:
    def test_empty_config_when_no_path(self):
        cfg = InfdbConfig(tool_name="tool", config_path=None)
        assert cfg.get_config() == {}

    def test_str_contains_tool_name(self):
        cfg = InfdbConfig(tool_name="mytool", config_path=None)
        assert "mytool" in str(cfg)

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            InfdbConfig(tool_name="tool", config_path=str(tmp_path / "missing.yml"))

    def test_get_value_raises_on_empty_keys(self):
        cfg = InfdbConfig(tool_name="tool", config_path=None)
        with pytest.raises(ValueError):
            cfg.get_value([])

    def test_get_value_returns_none_on_missing_key(self):
        cfg = InfdbConfig(tool_name="tool", config_path=None)
        assert cfg.get_value(["missing"]) is None


# ── InfdbConfig: with YAML file ───────────────────────────────────────────────


class TestInfdbConfigWithFile:
    @pytest.fixture
    def config_file(self, tmp_path):
        data = {
            "mytool": {
                "logging": {"path": "mytool.log", "level": "DEBUG"},
                "base": "mybase",
                "derived": "{mytool/base}-extra",
                "hosts": {
                    "postgres": {
                        "user": "testuser",
                        "db": "testdb",
                        "host": "localhost",
                        "exposed_port": "5432",
                    }
                },
            }
        }
        path = tmp_path / "config-mytool.yml"
        path.write_text(yaml.dump(data), encoding="utf-8")
        return str(path)

    def test_loads_nested_value(self, config_file):
        cfg = InfdbConfig(tool_name="mytool", config_path=config_file)
        assert cfg.get_value(["mytool", "logging", "level"]) == "DEBUG"

    def test_get_value_returns_none_for_absent_key(self, config_file):
        cfg = InfdbConfig(tool_name="mytool", config_path=config_file)
        assert cfg.get_value(["mytool", "nonexistent"]) is None

    def test_placeholder_resolution(self, config_file):
        cfg = InfdbConfig(tool_name="mytool", config_path=config_file)
        assert cfg.get_value(["mytool", "derived"]) == "mybase-extra"

    def test_host_override_stored(self, config_file):
        cfg = InfdbConfig(tool_name="mytool", config_path=config_file, host="override-host")
        assert cfg.host == "override-host"

    def test_get_config_returns_dict_with_tool_key(self, config_file):
        cfg = InfdbConfig(tool_name="mytool", config_path=config_file)
        result = cfg.get_config()
        assert isinstance(result, dict)
        assert "mytool" in result


# ── InfdbConfig: environment variable access ──────────────────────────────────


class TestInfdbConfigEnvParams:
    def test_returns_env_variable(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_VAR_INFDB", "hello")
        cfg = InfdbConfig(tool_name="tool", config_path=None)
        assert cfg.get_env_parameters("MY_TEST_VAR_INFDB") == "hello"

    def test_raises_on_missing_env_variable(self, monkeypatch):
        monkeypatch.delenv("MY_ABSENT_VAR_XYZZY_INFDB", raising=False)
        cfg = InfdbConfig(tool_name="tool", config_path=None)
        with pytest.raises(ValueError, match="MY_ABSENT_VAR_XYZZY_INFDB"):
            cfg.get_env_parameters("MY_ABSENT_VAR_XYZZY_INFDB")


# ── InfdbLogger ───────────────────────────────────────────────────────────────


class TestInfdbLogger:
    def test_creates_log_file(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = InfdbLogger(log_path=log_file)
        logger.stop()
        assert os.path.exists(log_file)

    def test_root_logger_is_standard_logger(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = InfdbLogger(log_path=log_file)
        logger.stop()
        assert isinstance(logger.root_logger, logging.Logger)

    def test_writes_message_to_log_file(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = InfdbLogger(log_path=log_file, level="DEBUG")
        logger.root_logger.info("sentinel-message-abc123")
        logger.stop()
        content = open(log_file, encoding="utf-8").read()
        assert "sentinel-message-abc123" in content

    def test_worker_logger_returns_logger_instance(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = InfdbLogger(log_path=log_file)
        worker = logger.setup_worker_logger()
        logger.stop()
        assert isinstance(worker, logging.Logger)

    def test_stop_does_not_raise(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        logger = InfdbLogger(log_path=log_file)
        logger.stop()

    def test_cleanup_removes_previous_content(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("old content\n")
        logger = InfdbLogger(log_path=log_file, cleanup=True)
        logger.root_logger.info("new content")
        logger.stop()
        content = open(log_file, encoding="utf-8").read()
        assert "old content" not in content
