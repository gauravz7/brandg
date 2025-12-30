import asyncio
import os
from services.gemini_computer_use_service import GeminiComputerUseService
from dotenv import load_dotenv

# Load environment variables (GOOGLE_CLOUD_PROJECT, etc.)
load_dotenv()

async def main():
    service = GeminiComputerUseService()
    
    # Prompt for Myntra
    prompt = "Go to https://www.myntra.com and find the brand's primary colors, fonts and logo. Describe them."
    
    print(f"Starting task: {prompt}")
    result = await service.execute_task(
        prompt=prompt,
        start_url="https://www.myntra.com",
        turn_limit=10
    )
    
    print("\n" + "="*50)
    print("FINAL RESULT")
    print("="*50)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
