import pytest
from utils.auth import ensure_authenticated
from utils.session import AsyncSessionManager
import os

@pytest.mark.asyncio
async def test_auth_import():
    assert ensure_authenticated is not None

@pytest.mark.asyncio
async def test_async_session_manager():
    manager = AsyncSessionManager()
    assert manager is not None
    assert manager.config is not None

def test_config_loader():
    from utils.config_loader import load_config
    config = load_config()
    assert "auth" in config
    assert "performance" in config
