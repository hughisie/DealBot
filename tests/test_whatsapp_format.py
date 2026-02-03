"""Tests for WhatsApp message formatting."""

import pytest

from adp.models import Currency, Deal, PriceInfo, ProcessedDeal, Rating, ShortLink
from adp.ui.whatsapp_format import WhatsAppFormatter


def test_format_message_basic() -> None:
    """Test basic message formatting."""
    deal = Deal(
        title="Test Product",
        url="https://amazon.es/dp/B08N5WRWNW",
        asin="B08N5WRWNW",
        stated_price=49.99,
        currency=Currency.EUR,
    )

    price_info = PriceInfo(
        asin="B08N5WRWNW",
        title="Test Product",
        current_price=49.99,
        currency=Currency.EUR,
    )

    short_link = ShortLink(
        short_url="https://amzon.fyi/abc123",
        long_url="https://amazon.es/dp/B08N5WRWNW",
        provider="bitly",
    )

    processed = ProcessedDeal(
        deal=deal,
        price_info=price_info,
        adjusted_price=49.99,
        short_link=short_link,
    )

    formatter = WhatsAppFormatter()
    message = formatter.format_message(processed)

    assert "amzon.fyi" in message
    assert "https://amzon.fyi/abc123" in message
    assert "Test Product" in message
    assert "49.99" in message
    assert "€" in message


def test_format_message_with_rating() -> None:
    """Test message formatting with rating."""
    deal = Deal(
        title="Test Product",
        url="https://amazon.es/dp/B08N5WRWNW",
        asin="B08N5WRWNW",
        stated_price=49.99,
        currency=Currency.EUR,
    )

    price_info = PriceInfo(
        asin="B08N5WRWNW",
        title="Test Product",
        current_price=49.99,
        currency=Currency.EUR,
    )

    short_link = ShortLink(
        short_url="https://amzon.fyi/abc123",
        long_url="https://amazon.es/dp/B08N5WRWNW",
        provider="bitly",
    )

    rating = Rating(value=4.5, count=1234, stars="★★★★☆")

    processed = ProcessedDeal(
        deal=deal,
        price_info=price_info,
        adjusted_price=49.99,
        short_link=short_link,
        rating=rating,
    )

    formatter = WhatsAppFormatter()
    message = formatter.format_message(processed)

    assert "★★★★☆" in message
    assert "4.5/5" in message
    assert "1,234" in message


def test_format_message_language_flags() -> None:
    """Test message formatting with language flags."""
    deal = Deal(
        title="Test Product",
        url="https://amazon.es/dp/B08N5WRWNW",
        asin="B08N5WRWNW",
        stated_price=49.99,
        currency=Currency.EUR,
        language_flag="ES",
    )

    price_info = PriceInfo(
        asin="B08N5WRWNW",
        title="Test Product",
        current_price=49.99,
        currency=Currency.EUR,
    )

    short_link = ShortLink(
        short_url="https://amzon.fyi/abc123",
        long_url="https://amazon.es/dp/B08N5WRWNW",
        provider="bitly",
    )

    processed = ProcessedDeal(
        deal=deal,
        price_info=price_info,
        adjusted_price=49.99,
        short_link=short_link,
    )

    formatter = WhatsAppFormatter()
    message = formatter.format_message(processed)

    assert "🇪🇸" in message
