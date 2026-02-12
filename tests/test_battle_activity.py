import pytest
from unittest.mock import AsyncMock, MagicMock
from activities.impl.battle import BattleActivity

from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_get_energy_success():
    activity = BattleActivity()
    page = MagicMock()
    page.wait_for_selector = AsyncMock()
    page.reload = AsyncMock()
    page.wait_for_load_state = AsyncMock()

    # Mock locator to return a mock object that has an async inner_text method
    mock_locator = MagicMock()
    mock_locator.wait_for = AsyncMock()
    mock_inner_text = AsyncMock(return_value="1,234")
    mock_locator.inner_text = mock_inner_text
    page.locator.return_value = mock_locator

    energy = await activity.get_energy(page)
    assert energy == 1234
    page.wait_for_selector.assert_any_call('.energy_counter', state='visible', timeout=10000)
    mock_locator.wait_for.assert_called_once_with(state="visible", timeout=10000)

@pytest.mark.asyncio
async def test_get_energy_failure():
    activity = BattleActivity()
    page = AsyncMock()
    page.url = "http://manga.example.com"
    page.wait_for_selector.side_effect = Exception("Timeout")
    page.locator.side_effect = Exception("Locator Timeout")

    energy = await activity.get_energy(page)
    assert energy == 0
    page.screenshot.assert_called()

@pytest.mark.asyncio
async def test_battle_activity_path():
    activity = BattleActivity()
    assert activity.path == "/troll-pre-battle.html"
