import os
import asyncio
from services.scraper_service import ScraperService
from services.gemini_service import GeminiService
from dotenv import load_dotenv

load_dotenv()

async def verify():
    print("Checking environment variables...")
    print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    print(f"GOOGLE_CLOUD_LOCATION: {os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')}")
    print(f"GOOGLE_API_KEY: {'Set' if os.getenv('GOOGLE_API_KEY') else 'Not Set'}")
    
    print("\nTesting ScraperService (playwright)...")
    try:
        scraper = ScraperService()
        # Just test navigation to a simple page
        result = await scraper.analyze_url("https://example.com")
        print(f"Scraper Success: {result['title']}")
    except Exception as e:
        print(f"Scraper Failed: {e}")

    print("\nTesting GeminiService...")
    try:
        gemini = GeminiService()
        if gemini.client:
            print("Gemini initialized.")
            # Simple test
            print("Sending test request to Gemini...")
            res = await gemini.search_brand_guidelines("Stripe", "https://stripe.com")
            print(f"Gemini Success: {res[:100]}...")
        else:
            print("Gemini NOT initialized.")
    except Exception as e:
        print(f"Gemini Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
