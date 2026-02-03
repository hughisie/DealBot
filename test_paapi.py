from amazon_paapi import AmazonApi

# Your credentials
ACCESS_KEY = "AKPA0DQU0S1763063154"
SECRET_KEY = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
ASSOCIATE_TAG = "retroshell00-20"

# Use the region where your PA-API account actually exists:
COUNTRY = "US"    # Spain is not supported — US works

def test_paapi():
    try:
        print("\n🔍 Testing PA-API (US region)...\n")

        amazon = AmazonApi(
            ACCESS_KEY,
            SECRET_KEY,
            ASSOCIATE_TAG,
            COUNTRY
        )

        response = amazon.search_items(
            keywords="Nintendo",
            search_index="VideoGames",
            item_count=1
        )

        # Show raw response
        print("\n🔹 PA-API Response (US region):\n")
        print(response)

        # Extract ASIN
        asin = response['SearchResult']['Items'][0]['ASIN']
        print("\n🔹 Extracted ASIN:", asin)

        # Build Amazon Spain affiliate link
        spain_url = f"https://www.amazon.es/dp/{asin}?tag={ASSOCIATE_TAG}"
        print("\n🇪🇸 Spain Affiliate URL:\n", spain_url)

        print("\n✅ SUCCESS — US region working. Spain link generated.\n")

    except Exception as e:
        print("\n❌ ERROR — PA-API request failed.\n")
        print(str(e))

if __name__ == "__main__":
    test_paapi()