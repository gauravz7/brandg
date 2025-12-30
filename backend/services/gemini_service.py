import os
from google import genai
from google.genai import types
from typing import Dict, Any

class GeminiService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        try:
            # Using google-genai SDK
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            self.model_id = "gemini-2.5-flash"
        except Exception as e:
            print(f"GenAI Client Init failed: {e}")
            self.client = None

    async def search_brand_guidelines(self, brand_name: str, url: str) -> str:
        if not self.client:
            return "GenAI Client not initialized."

        prompt = f"""
        Find the official brand guidelines for {brand_name} ({url}).
        Look for:
        1. Primary and Secondary Colors (Hex codes if available)
        2. Typography fonts
        3. Logo usage rules
        4. Brand Voice and Tone
        
        Provide a detailed summary.
        """
        
        try:
            # google-genai uses a sync client by default or we can use async?
            # Actually google-genai has an async client too: client.aio.models...
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text
        except Exception as e:
            return f"Error searching brand guidelines: {str(e)}"

    async def compile_final_report(self, brand_data: Dict[str, Any], guidelines_text: str) -> str:
        if not self.client:
            return "GenAI Client not initialized."

        prompt = f"""
        Create a comprehensive Brand Identity Report for {brand_data.get('title', 'the brand')}.
        
        Website Data:
        - URL: {brand_data.get('url')}
        - Description: {brand_data.get('description')}
        - Extracted Colors: {brand_data.get('colors')}
        - Extracted Fonts: {brand_data.get('fonts')}
        
        Brand Guidelines Research:
        {guidelines_text}
        
        Format the report as a professional Markdown document suitable for a PDF. 
        Include sections for:
        1. Executive Summary
        2. Visual Identity (Colors, Fonts, Logos)
        3. Brand Voice & Guidelines
        4. Recommendations
        """
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating report: {str(e)}"

