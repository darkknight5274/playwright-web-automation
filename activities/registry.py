from activities.home import HomeActivity
from activities.battle import BattleActivity
from typing import Dict, Type
from activities.base import BaseActivity

TASK_MAPPING: Dict[str, Type[BaseActivity]] = {
    "/home": HomeActivity,
    "/battle": BattleActivity,
}
