import pytest

from src.core.config import Settings


def test_prod_rejects_default_jwt_secret() -> None:
    cfg = Settings(environment="prod", jwt_secret="change-this-secret", dev_bootstrap_key="safe-key")
    with pytest.raises(ValueError, match="JWT_SECRET"):
        cfg.validate_runtime_security()


def test_prod_rejects_short_jwt_secret() -> None:
    cfg = Settings(environment="prod", jwt_secret="short-secret", dev_bootstrap_key="safe-key")
    with pytest.raises(ValueError, match="JWT_SECRET"):
        cfg.validate_runtime_security()


def test_prod_rejects_default_bootstrap_key() -> None:
    cfg = Settings(
        environment="production",
        jwt_secret="a" * 32,
        dev_bootstrap_key="dev-bootstrap-key",
    )
    with pytest.raises(ValueError, match="DEV_BOOTSTRAP_KEY"):
        cfg.validate_runtime_security()


def test_prod_accepts_strong_config() -> None:
    cfg = Settings(
        environment="prod",
        jwt_secret="a" * 48,
        dev_bootstrap_key="internal-disabled-key",
        portal_access_key="portal-access-key-2026",
    )
    cfg.validate_runtime_security()
