#!/usr/bin/env python3
"""Test parsing of real Scrapula API response."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.services.scrapula import ScrapulaService

def test_real_response():
    """Test with the actual Scrapula response format."""
    
    # Real Scrapula API response for Lacoste watch
    real_response = {
        "short_url": "https://www.amazon.com/Lacoste-Womens-Stainless-Leather-Calfskin/dp/B00G3XWLR8",
        "asin": "B00G3XWLR8",
        "name": "Lacoste Women's 12.12 Stainless Steel Quartz Watch with Leather Calfskin Strap, Taupe, 16 (Model: 2001150)",
        "rating": None,
        "reviews": None,
        "answered_questions": None,
        "fast_track_message": None,
        "about": "ON TIME, IN STYLE: Once upon a time there was a polo shirt...",
        "description": "The Lacoste legend was born in 1933...",
        "categories": [
            "Clothing, Shoes & Jewelry",
            "Women",
            "Watches",
            "Wrist Watches"
        ],
        "store_title": "Lacoste Store",
        "store_url": "https://www.amazon.com/stores/Lacoste/page/C85490CB-0E64-4F8B-89A8-217111AFF6FE",
        "price": "$175.00",
        "availability": "In stock soon. Order it now.",
        "strike_price": None,
        "price_saving": None,
        "shipping": "",
        "merchant_info": "",
        "bage": "",
        "currency": None,
        "image_1": "https://m.media-amazon.com/images/I/314jzz9RfsL.jpg",
        "image_2": "https://m.media-amazon.com/images/I/31he4kecs0L.jpg",
        "image_3": "https://m.media-amazon.com/images/I/31FgebhbXEL.jpg",
        "image_4": "https://m.media-amazon.com/images/I/41IYiTJyLIL.jpg",
        "image_5": "https://m.media-amazon.com/images/I/41gZMv+FwoL.jpg",
    }
    
    print("=" * 70)
    print("Testing Real Scrapula API Response Parsing")
    print("=" * 70)
    
    service = ScrapulaService(api_key="test_key")
    
    asin = real_response["asin"]
    product = service._parse_response(asin, real_response)
    
    print(f"\n✅ Parsed Product Info:")
    print(f"  ASIN: {product.asin}")
    print(f"  Title: {product.title[:60]}...")
    print(f"  Current Price: {product.currency} {product.current_price}")
    print(f"  List Price: {product.list_price if product.list_price else 'N/A'}")
    print(f"  Availability: {product.availability}")
    print(f"  Rating: {product.rating if product.rating else 'N/A'}")
    print(f"  Reviews: {product.review_count if product.review_count else 'N/A'}")
    print(f"  Image URL: {product.image_url[:60]}...")
    print(f"  Success: {product.success}")
    
    # Verify parsing
    assert product.asin == "B00G3XWLR8"
    assert product.title is not None
    assert product.current_price == 175.00
    assert product.currency == "USD"
    assert product.image_url is not None
    assert product.availability == "In stock soon. Order it now."
    assert product.success == True
    
    print(f"\n✅ All assertions passed!")
    
    print(f"\n{'=' * 70}")
    print("Field Mapping Verified:")
    print('=' * 70)
    print(f"  ✅ ASIN: 'asin' field")
    print(f"  ✅ Title: 'name' field")
    print(f"  ✅ Price: Parsed from '$175.00' string")
    print(f"  ✅ Currency: Extracted from price string ($→USD)")
    print(f"  ✅ Image: 'image_1' field")
    print(f"  ✅ Availability: 'availability' field")
    print(f"  ✅ Rating: Handled null value")
    print(f"  ✅ Reviews: Handled null value")
    
    print(f"\n{'=' * 70}")
    print("✅ READY FOR INTEGRATION!")
    print('=' * 70)
    print(f"\nScrapula service correctly parses real API responses!")
    print(f"Next: Find the Amazon service_name to create tasks")
    
    return True

if __name__ == "__main__":
    success = test_real_response()
    
    if success:
        print(f"\n🎉 Parser is ready for Scrapula integration!")

