# ADR 002: Security Standards for Secrets

## Context
The system manages sensitive credentials (username, password) for authenticating with game domains. Storing these in a static `config.yaml` file risks accidental exposure if committed to version control and makes it difficult to manage environment-specific secrets.

## Decision
We will use **Environment Variables** for all sensitive information.
1.  **python-dotenv**: We will use the `python-dotenv` library to load secrets from a `.env` file during local development.
2.  **Exclusion**: The `.env` file must be added to `.gitignore` to prevent it from being committed.
3.  **Access**: Secrets will be accessed via `os.getenv()` in the application logic.
4.  **Non-sensitive Config**: Non-sensitive settings like `storage_state_path` and `login_url` will remain in the `config.yaml` under `global_settings`.

## Consequences
-   **Positive**: Improved security by separating secrets from configuration.
-   **Positive**: Easier to deploy in different environments (e.g., CI/CD, Docker) by simply setting environment variables.
-   **Negative**: Requires an additional step (creating a `.env` file) for new developers.
