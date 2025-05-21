"""Test package initialization.

Sets required environment variables so modules that depend on them can be
imported without errors during test collection.
"""

import os

# Provide a dummy API key for the Anthropic client during tests
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")

