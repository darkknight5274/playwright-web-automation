from typing import Dict, Type, List
from activities.base import BaseActivity

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
        return cls._registry.get(path)

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
