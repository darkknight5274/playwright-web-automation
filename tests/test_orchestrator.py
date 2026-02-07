import pytest
import asyncio
from main import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_init():
    orchestrator = Orchestrator()
    assert orchestrator.config is not None
    assert orchestrator.ad_hoc_active is False
    assert orchestrator.ad_hoc_path is None

@pytest.mark.asyncio
async def test_orchestrator_toggle_ad_hoc():
    orchestrator = Orchestrator()
    orchestrator.toggle_ad_hoc(True, "/test-path")
    assert orchestrator.ad_hoc_active is True
    assert orchestrator.ad_hoc_path == "/test-path"

    orchestrator.toggle_ad_hoc(False)
    assert orchestrator.ad_hoc_active is False
