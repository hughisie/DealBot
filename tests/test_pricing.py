"""Tests for pricing service."""

import pytest
from unittest.mock import MagicMock

from adp.services.pricing import PricingService
from adp.utils.config import Config


def test_price_adjustment_no_change() -> None:
    """Test price adjustment with no change."""
    config = MagicMock(spec=Config)
    config.price_multiplier = 1.0
    config.price_additive = 0.0

    pricing = PricingService(config)
    result = pricing.adjust_price(50.00)

    assert result == 50.00


def test_price_adjustment_multiplier() -> None:
    """Test price adjustment with multiplier."""
    config = MagicMock(spec=Config)
    config.price_multiplier = 1.1
    config.price_additive = 0.0

    pricing = PricingService(config)
    result = pricing.adjust_price(50.00)

    assert result == 55.00


def test_price_adjustment_additive() -> None:
    """Test price adjustment with additive."""
    config = MagicMock(spec=Config)
    config.price_multiplier = 1.0
    config.price_additive = 5.0

    pricing = PricingService(config)
    result = pricing.adjust_price(50.00)

    assert result == 55.00


def test_price_adjustment_combined() -> None:
    """Test price adjustment with both multiplier and additive."""
    config = MagicMock(spec=Config)
    config.price_multiplier = 1.1
    config.price_additive = 2.0

    pricing = PricingService(config)
    result = pricing.adjust_price(50.00)

    # (50 * 1.1) + 2 = 57.0
    assert result == 57.00
