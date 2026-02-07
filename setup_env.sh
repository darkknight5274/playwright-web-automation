#!/bin/bash

# Exit on error
set -e

echo "Installing dependencies with uv..."
uv sync

echo "Installing Playwright browsers..."
uv run playwright install

echo "Environment setup complete!"
