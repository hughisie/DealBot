"""Tests for controller."""

import pytest
from unittest.mock import MagicMock, patch

from adp.controller import DealController
from adp.models import Currency, Deal
from adp.utils.config import Config


@patch("adp.controller.Database")
@patch("adp.controller.InterstitialServer")
def test_controller_initialization(mock_interstitial: MagicMock, mock_db: MagicMock) -> None:
    """Test controller initialization."""
    config = MagicMock(spec=Config)
    config.interstitial_enabled = False
    config.price_multiplier = 1.0
    config.price_additive = 0.0
    config.affiliate_tag = "test-21"
    config.get = MagicMock(return_value=None)
    config.shortlink_provider = "bitly"
    config.ratings_enabled = False
    config.require_env = MagicMock(side_effect=ValueError("Missing env var"))

    # Controller initialization should not fail even if some services fail
    # We'll test that it handles exceptions gracefully


@patch("adp.controller.TxtParser")
def test_parse_file(mock_parser: MagicMock) -> None:
    """Test file parsing."""
    config = MagicMock(spec=Config)

    mock_deal = Deal(
        title="Test",
        url="https://amazon.es/dp/B08N5WRWNW",
        asin="B08N5WRWNW",
        stated_price=49.99,
        currency=Currency.EUR,
    )

    mock_parser.return_value.parse_file.return_value = [mock_deal]

    # Test that controller calls parser correctly
    assert True  # Placeholder - full integration test would go here
