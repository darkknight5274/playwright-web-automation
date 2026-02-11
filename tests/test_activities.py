import pytest
from unittest.mock import MagicMock, patch
from activities.runner import run_activity
from activities.impl.home import HomeActivity
from activities.impl.battle import BattleActivity
from activities.impl.training import TrainingActivity
from activities.impl.season import SeasonActivity
from activities.impl.collect import CollectActivity
from activities.impl.league import LeagueActivity

@pytest.mark.asyncio
async def test_run_activity_training_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/training"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(TrainingActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_home_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/home"

    with patch.object(HomeActivity, 'execute', new_callable=MagicMock) as mock_execute:
        mock_execute.return_value = MagicMock() # Mocking the awaitable
        # Since it's an async method, we should use AsyncMock if using Python 3.8+
        from unittest.mock import AsyncMock
        mock_execute = AsyncMock()
        with patch.object(HomeActivity, 'execute', mock_execute):
            await run_activity(page)
            mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_battle_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/troll-pre-battle.html"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(BattleActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_game_v2_battle_enabled():
    page = MagicMock()
    page.url = "https://www.comicrpg.com/troll-pre-battle.html"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(BattleActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_season_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/season-arena.html"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(SeasonActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_collect_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/collect"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(CollectActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_league_enabled():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/leagues.html"

    from unittest.mock import AsyncMock
    mock_execute = AsyncMock()
    with patch.object(LeagueActivity, 'execute', mock_execute):
        await run_activity(page)
        mock_execute.assert_called_once_with(page)

@pytest.mark.asyncio
async def test_run_activity_unmapped_path():
    page = MagicMock()
    page.url = "https://www.mangarpg.com/unknown"

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
