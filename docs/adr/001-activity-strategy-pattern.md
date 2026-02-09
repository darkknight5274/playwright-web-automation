# ADR 001: Activity Strategy Pattern and Automated Registry

## Context
The system needs to manage multiple concurrent activities across different domains. Many domains share identical URL paths (e.g., `/home`, `/battle`) but require domain-specific handling or at least a standardized way to be triggered and executed.

## Decision
We will implement a **Strategy Pattern** for all game activities to ensure a consistent interface and allow for parallel execution and ad-hoc triggering.

### Components:
1.  **BaseActivity**: An abstract base class that defines the required interface:
    -   `path`: An abstract property defining the URL path this activity handles.
    -   `execute(page)`: An abstract async method that performs the actual game logic on a Playwright Page.
2.  **ActivityRegistry**: A centralized registry that:
    -   Uses a class decorator `@register` to automatically instantiate and map activity classes to their paths.
    -   Provides methods to retrieve activity instances by path.
3.  **Discovery**: Implementation modules in `activities/impl/` will be explicitly imported in the registry to trigger automatic registration.

## Consequences
-   **Positive**: New activities can be added by simply creating a new class in `activities/impl/` and adding the decorator.
-   **Positive**: Parallel execution and ad-hoc triggering become trivial as the Orchestrator can simply query the Registry for the appropriate activity by path.
-   **Negative**: Requires explicit imports of implementations to trigger registration (handled in `activities/registry.py`).
