"""Shared pytest fixtures and configuration."""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_db():
    """Mock database for testing."""
    return MagicMock()


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        'email': 'test@example.com',
        'password': '$2b$12$hashedpassword',
        'name': 'Test User',
        'role': 'Customer',
        'failed_attempts': 0
    }


@pytest.fixture
def sample_inventory():
    """Sample inventory data for testing."""
    return [
        {'name': 'Tomatoes', 'price': '5 RON', 'stock': '10 kg', 'status': 'In Stock'},
        {'name': 'Carrots', 'price': '3 RON', 'stock': '20 kg', 'status': 'In Stock'}
    ]


@pytest.fixture
def sample_order():
    """Sample order data for testing."""
    return {
        'customer_email': 'customer@example.com',
        'items': [{'name': 'Tomatoes', 'quantity': 5}],
        'total': 25.0,
        'status': 'Created'
    }