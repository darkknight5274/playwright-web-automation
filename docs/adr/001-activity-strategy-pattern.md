# ADR 001: Strategy Pattern and Centralized Registry for Activity Management

## Status
Accepted

## Context
We are automating an online game across multiple domains (versions/flavors) that share identical URL paths but require isolated execution logic. The system must run 24/7, support parallel domain execution, and allow ad-hoc activity triggering via an API.

### Problems to Solve:
1. **Coupling:** Hardcoding logic for each domain leads to massive `if/else` blocks and high maintenance.
2. **Git Conflicts:** Multiple developers/agents editing a single main file for different game paths cause merge hell.
3. **Dynamic Execution:** We need to trigger specific logic (e.g., `/market`) on-demand without restarting the orchestrator.

## Decision
We will implement the **Strategy Pattern** combined with a **Decorator-based Registry**.

1. **BaseActivity:** An abstract interface ensuring all activities implement `execute(page)`.
2. **ActivityRegistry:** A singleton manager that maps URL paths to Activity instances.
3. **Decentralized Logic:** Each activity (e.g., `/home`, `/battle`) will reside in its own file within `activities/impl/`.

## Consequences
- **Positive:** logic is decoupled; new activities can be added by creating a new file without touching the core engine.
- **Positive:** Enables the FastAPI control panel to look up and execute logic by path string.
- **Neutral:** Increases initial boilerplate code (abstract classes and decorators).