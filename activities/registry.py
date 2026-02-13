from typing import Dict, Type, List
from activities.base import BaseActivity

TASK_MAPPING = {
    "/home": None,  # To be populated at the end of the module
    "/battle": None,
}

class ActivityRegistry:
    _registry: Dict[str, BaseActivity] = {}

    @classmethod
    def register(cls, activity_class: Type[BaseActivity]):
        """
        Class decorator to automatically instantiate and register an activity class by its path.
        """
        instance = activity_class()
        cls._registry[instance.path] = instance
        return activity_class

    @classmethod
    def get_activity(cls, path: str) -> BaseActivity:
        """
        Retrieves an activity instance by its path.
        """
        instance = cls._registry.get(path)
        if not instance and path in TASK_MAPPING:
            activity_class = TASK_MAPPING[path]
            if activity_class:
                instance = activity_class()
                cls._registry[path] = instance
        return instance

    @classmethod
    def get_all_paths(cls) -> List[str]:
        """
        Returns all registered activity paths.
        """
        return list(cls._registry.keys())

# Import implementations to trigger registration
# Note: These are imported here to ensure the decorators are executed.
import activities.impl.home
import activities.impl.battle
import activities.impl.training
import activities.impl.season
import activities.impl.collect
import activities.impl.league

TASK_MAPPING.update({
    "/home": activities.impl.home.HomeActivity,
    "/battle": activities.impl.battle.BattleActivity,
    "/troll-pre-battle.html": activities.impl.battle.BattleActivity,
})
