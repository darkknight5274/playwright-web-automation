import pytest
from utils.session import ensure_authenticated
from utils.session_manager import AsyncSessionManager
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
    assert "global_settings" in config
    assert "performance" in config
