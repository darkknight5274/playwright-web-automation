import pytest
from unittest.mock import MagicMock, patch
from activities.runner import run_activity
from activities.home import HomeActivity
from activities.battle import BattleActivity

@pytest.mark.asyncio
async def test_run_activity_home_enabled():
    page = MagicMock()
    page.url = "https://game-v1.com/home"

    with patch.object(HomeActivity, 'execute', new_callable=MagicMock) as mock_execute:
        mock_execute.return_value = MagicMock() # Mocking the awaitable
        # Since it's an async method, we should use AsyncMock if using Python 3.8+
        from unittest.mock import AsyncMock
        mock_execute = AsyncMock()
        with patch.object(HomeActivity, 'execute', mock_execute):
            await run_activity(page)
            mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_battle_disabled():
    page = MagicMock()
    page.url = "https://game-v1.com/battle"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(BattleActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_not_called()

@pytest.mark.asyncio
async def test_run_activity_game_v2_battle_enabled():
    page = MagicMock()
    page.url = "https://game-v2.com/battle"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(BattleActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_unmapped_path():
    page = MagicMock()
    page.url = "https://game-v1.com/unknown"

    # Should not crash, just log debug
    await run_activity(page)

@pytest.mark.asyncio
async def test_run_activity_unconfigured_domain():
    page = MagicMock()
    page.url = "https://unknown-game.com/home"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(HomeActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_not_called()
