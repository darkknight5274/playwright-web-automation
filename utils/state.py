from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import asyncio
from utils.config_loader import load_config

@dataclass
class DomainStatus:
    current_activity: Optional[str] = None
    last_run_time: Optional[datetime] = None
    status: str = "Idle"  # Idle, Busy, Error
    is_adhoc_pending: bool = False
    is_authenticated: bool = False

class SharedState:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.domains: Dict[str, DomainStatus] = {}
        self.adhoc_event = asyncio.Event()
        self._initialize_from_config()
        self._initialized = True

    def _initialize_from_config(self):
        config = load_config()
        domains_config = config.get("domains", [])
        for domain in domains_config:
            name = domain.get("name")
            if name:
                self.domains[name] = DomainStatus()

    async def update_status(self, domain_name: str, **kwargs):
        """
        Thread-safe (async-safe) method to update the status of a domain.
        """
        async with self._lock:
            if domain_name in self.domains:
                status_obj = self.domains[domain_name]
                for key, value in kwargs.items():
                    if hasattr(status_obj, key):
                        setattr(status_obj, key, value)

                # If we are setting an adhoc as pending, trigger the event
                if kwargs.get("is_adhoc_pending"):
                    self.adhoc_event.set()

    async def get_domain_status(self, domain_name: str) -> Optional[DomainStatus]:
        async with self._lock:
            return self.domains.get(domain_name)

    async def get_all_statuses(self) -> Dict[str, DomainStatus]:
        async with self._lock:
            # Return a copy to prevent external mutation
            return {k: v for k, v in self.domains.items()}

    def check_adhoc_requested(self) -> bool:
        """
        Non-blocking check if any ad-hoc activity is pending.
        """
        return self.adhoc_event.is_set()

    async def clear_adhoc_signal(self):
        """
        Clears the ad-hoc signal after workers have acknowledged it.
        """
        async with self._lock:
            # Check if any domain still has is_adhoc_pending=True
            still_pending = any(d.is_adhoc_pending for d in self.domains.values())
            if not still_pending:
                self.adhoc_event.clear()

# Singleton instance
state_manager = SharedState()
