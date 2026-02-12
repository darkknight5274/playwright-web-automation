import pytest
from unittest.mock import AsyncMock, MagicMock
from activities.impl.battle import BattleActivity

from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_get_energy_success():
    activity = BattleActivity()
    page = MagicMock()
    page.wait_for_selector = AsyncMock()

    # Mock locator to return a mock object that has an async inner_text method
    mock_locator = MagicMock()
    mock_inner_text = AsyncMock(return_value="1,234")
    mock_locator.inner_text = mock_inner_text
    page.locator.return_value = mock_locator

    energy = await activity.get_energy(page)
    assert energy == 1234
    page.wait_for_selector.assert_called_once_with('#fight_energy_bar span[energy=""]', timeout=5000)

@pytest.mark.asyncio
async def test_get_energy_failure():
    activity = BattleActivity()
    page = AsyncMock()
    page.wait_for_selector.side_effect = Exception("Timeout")

    energy = await activity.get_energy(page)
    assert energy == 0

@pytest.mark.asyncio
async def test_battle_activity_path():
    activity = BattleActivity()
    assert activity.path == "/troll-pre-battle.html"
