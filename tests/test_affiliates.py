"""Tests for affiliate service."""

import pytest
from unittest.mock import MagicMock

from adp.services.affiliates import AffiliateService
from adp.utils.config import Config


def test_ensure_affiliate_tag_missing() -> None:
    """Test adding affiliate tag when missing."""
    config = MagicMock(spec=Config)
    config.affiliate_tag = "mytag-21"
    config.get = MagicMock(side_effect=lambda key, default=None: {
        "affiliates.tag_param": "tag",
        "affiliates.ensure_tag": True,
    }.get(key, default))

    service = AffiliateService(config)
    url = "https://amazon.es/dp/B08N5WRWNW"
    result = service.ensure_affiliate_tag(url)

    assert "tag=mytag-21" in result
    assert "B08N5WRWNW" in result


def test_ensure_affiliate_tag_existing() -> None:
    """Test that existing tag is preserved."""
    config = MagicMock(spec=Config)
    config.affiliate_tag = "mytag-21"
    config.get = MagicMock(side_effect=lambda key, default=None: {
        "affiliates.tag_param": "tag",
        "affiliates.ensure_tag": True,
    }.get(key, default))

    service = AffiliateService(config)
    url = "https://amazon.es/dp/B08N5WRWNW?tag=mytag-21"
    result = service.ensure_affiliate_tag(url)

    assert result == url
    assert result.count("tag=") == 1


def test_clean_url() -> None:
    """Test URL cleaning keeps only specified params."""
    config = MagicMock(spec=Config)
    config.affiliate_tag = "mytag-21"
    config.get = MagicMock(side_effect=lambda key, default=None: {
        "affiliates.tag_param": "tag",
        "affiliates.ensure_tag": True,
    }.get(key, default))

    service = AffiliateService(config)
    url = "https://amazon.es/dp/B08N5WRWNW?tag=mytag-21&ref=tracking&foo=bar"
    result = service.clean_url(url, keep_params=["tag"])

    assert "tag=mytag-21" in result
    assert "ref=" not in result
    assert "foo=" not in result
