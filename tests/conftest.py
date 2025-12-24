"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def mock_api_key() -> str:
    """Provide a mock API key for testing."""
    return "sk-test-mock-api-key-for-testing"
