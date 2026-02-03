"""Tests for TXT parsing."""

import pytest

from adp.parsers.txt_parser import TxtParser


def test_parse_basic_deal() -> None:
    """Test parsing a basic deal."""
    parser = TxtParser()
    content = """
    Amazing Product ES
    https://amazon.es/dp/B08N5WRWNW
    €49.99
    """

    deals = parser.parse_content(content)

    assert len(deals) == 1
    deal = deals[0]
    assert "Amazing Product" in deal.title
    assert deal.asin == "B08N5WRWNW"
    assert deal.stated_price == 49.99
    assert deal.url == "https://amazon.es/dp/B08N5WRWNW"


def test_parse_multiple_deals() -> None:
    """Test parsing multiple deals."""
    parser = TxtParser()
    content = """
    Product One
    https://amazon.es/dp/B08N5WRWN1
    €29.99

    Product Two EN
    https://amazon.co.uk/dp/B08N5WRWN2
    £39.99
    """

    deals = parser.parse_content(content)

    assert len(deals) == 2
    assert deals[0].asin == "B08N5WRWN1"
    assert deals[1].asin == "B08N5WRWN2"
    assert deals[0].stated_price == 29.99
    assert deals[1].stated_price == 39.99


def test_parse_language_flags() -> None:
    """Test language flag extraction."""
    parser = TxtParser()
    content = """
    Product ES
    https://amazon.es/dp/B08N5WRWN1
    €29.99
    """

    deals = parser.parse_content(content)

    assert len(deals) == 1
    assert deals[0].language_flag == "ES"


def test_parse_no_price() -> None:
    """Test parsing deal without stated price."""
    parser = TxtParser()
    content = """
    Product Without Price
    https://amazon.es/dp/B08N5WRWN1
    """

    deals = parser.parse_content(content)

    assert len(deals) == 1
    assert deals[0].stated_price is None
    assert deals[0].asin == "B08N5WRWN1"
