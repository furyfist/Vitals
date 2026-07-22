"""Unit tests for VerdictConfig, ConsoleConfig, StoreConfig and validation rules."""

import pytest
from vitals.config.settings import VitalsConfig, load_config


def test_config_defaults(tmp_path):
    cfg_file = tmp_path / "vitals.yaml"
    cfg_file.write_text("")
    cfg = load_config(str(cfg_file))

    assert cfg.verdict.enabled is True
    assert cfg.verdict.evaluate_interval_s == 10
    assert cfg.verdict.sigma_threshold == 3.0
    assert cfg.console.port == 8787
    assert cfg.store.path == "vitals.db"


def test_config_env_overrides(monkeypatch, tmp_path):
    cfg_file = tmp_path / "vitals.yaml"
    cfg_file.write_text("")

    monkeypatch.setenv("VITALS_CONSOLE_PORT", "9999")
    monkeypatch.setenv("VITALS_STORE_PATH", "custom.db")
    monkeypatch.setenv("VITALS_VERDICT_ENABLED", "false")

    cfg = load_config(str(cfg_file))
    assert cfg.console.port == 9999
    assert cfg.store.path == "custom.db"
    assert cfg.verdict.enabled is False


def test_config_validation():
    cfg = VitalsConfig()
    cfg.verdict.sigma_threshold = -1.0
    with pytest.raises(ValueError, match="verdict.sigma_threshold must be > 0"):
        cfg.validate()

    cfg = VitalsConfig()
    cfg.verdict.consecutive_ticks = 0
    with pytest.raises(ValueError, match="verdict.consecutive_ticks must be >= 1"):
        cfg.validate()

    cfg = VitalsConfig()
    cfg.verdict.min_samples = 2
    with pytest.raises(ValueError, match="verdict.min_samples must be >= 5"):
        cfg.validate()

    cfg = VitalsConfig()
    cfg.verdict.runaway_ratio = 0.5
    with pytest.raises(ValueError, match="verdict.runaway_ratio must be > 1"):
        cfg.validate()
