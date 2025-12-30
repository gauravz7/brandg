import os
import asyncio
import base64
from typing import List, Dict, Any, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth
from google import genai
from google.genai import types
from google.genai.types import Content, Part
import time

class GeminiComputerUseService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        # Use gemini-2.5-flash as default as requested
        self.model_id = 'gemini-2.5-flash'
        # Original preview model from docs: 'gemini-2.5-computer-use-preview-10-2025'
        self.screen_width = 1440
        self.screen_height = 900

    def _denormalize_x(self, x: int) -> int:
        return int(x / 1000 * self.screen_width)

    def _denormalize_y(self, y: int) -> int:
        return int(y / 1000 * self.screen_height)

    async def _execute_function_calls(self, candidate, page: Page) -> List[Tuple[str, Dict[str, Any]]]:
        results = []
        function_calls = []
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append(part.function_call)

        for function_call in function_calls:
            fname = function_call.name
            args = function_call.args
            print(f"  -> Executing: {fname} with args: {args}")
            action_result = {}

            try:
                if fname == "open_web_browser":
                    pass # Handled by the loop if needed, but usually already open
                elif fname == "navigate":
                    await page.goto(args["url"], wait_until="networkidle")
                elif fname == "click_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    await page.mouse.click(actual_x, actual_y)
                elif fname == "type_text_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    text = args["text"]
                    press_enter = args.get("press_enter", True)
                    clear_before = args.get("clear_before_typing", True)

                    await page.mouse.click(actual_x, actual_y)
                    if clear_before:
                        # Simple clear (Command+A, Backspace)
                        await page.keyboard.press("Meta+A")
                        await page.keyboard.press("Backspace")
                    
                    await page.keyboard.type(text)
                    if press_enter:
                        await page.keyboard.press("Enter")
                elif fname == "key_combination":
                    await page.keyboard.press(args["keys"])
                elif fname == "wait_5_seconds":
                    await asyncio.sleep(5)
                elif fname == "scroll_document":
                    direction = args.get("direction", "down")
                    if direction == "down":
                        await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    elif direction == "up":
                        await page.evaluate("window.scrollBy(0, -window.innerHeight)")
                else:
                    print(f"Warning: Unimplemented function {fname}")
                    action_result = {"error": f"Function {fname} is not implemented"}

                await page.wait_for_load_state("load", timeout=10000)
                await asyncio.sleep(1) # Small buffer

            except Exception as e:
                print(f"Error executing {fname}: {e}")
                action_result = {"error": str(e)}

            results.append((fname, action_result))
        
        return results

    async def _get_function_responses(self, page: Page, results: List[Tuple[str, Dict[str, Any]]]) -> List[types.FunctionResponse]:
        screenshot_bytes = await page.screenshot(type="png")
        current_url = page.url
        function_responses = []
        for name, result in results:
            response_data = {"url": current_url}
            response_data.update(result)
            function_responses.append(
                types.FunctionResponse(
                    name=name,
                    response=response_data,
                    parts=[types.FunctionResponsePart(
                            inline_data=types.FunctionResponseBlob(
                                mime_type="image/png",
                                data=screenshot_bytes))
                    ]
                )
            )
        return function_responses

    async def execute_task(self, prompt: str, start_url: str = None, turn_limit: int = 10):
        async with async_playwright() as p:
            print("Initializing browser...")
            browser = await p.chromium.launch(headless=False) # Headless=False for debugging
            context = await browser.new_context(viewport={"width": self.screen_width, "height": self.screen_height})
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)

            try:
                if start_url:
                    try:
                        await page.goto(start_url, wait_until="commit", timeout=45000)
                    except Exception as e:
                        print(f"Initial navigation timeout/warning: {e}")
                    await asyncio.sleep(15) # Wait for content to render on heavy sites like Myntra
                
                initial_screenshot = await page.screenshot(type="png")
                
                contents = [
                    Content(role="user", parts=[
                        Part(text=prompt),
                        Part.from_bytes(data=initial_screenshot, mime_type='image/png')
                    ])
                ]

                config = types.GenerateContentConfig(
                    tools=[types.Tool(computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    ))],
                    thinking_config=types.ThinkingConfig(include_thoughts=True),
                )

                for i in range(turn_limit):
                    print(f"\n--- Turn {i+1} ---")
                    print("Thinking...")
                    
                    response = await self.client.aio.models.generate_content(
                        model=self.model_id,
                        contents=contents,
                        config=config,
                    )

                    candidate = response.candidates[0]
                    contents.append(candidate.content)

                    # Print thoughts if available
                    if candidate.content.parts[0].thought:
                        print(f"Agent Thoughts: {candidate.content.parts[0].text}")

                    has_function_calls = any(part.function_call for part in candidate.content.parts)
                    if not has_function_calls:
                        text_response = " ".join([part.text for part in candidate.content.parts if part.text])
                        print(f"Agent finished: {text_response}")
                        return text_response

                    print("Executing actions...")
                    results = await self._execute_function_calls(candidate, page)

                    print("Capturing state...")
                    function_responses = await self._get_function_responses(page, results)

                    contents.append(
                        Content(role="user", parts=[Part(function_response=fr) for fr in function_responses])
                    )

                print("Reached turn limit.")
                return "Reached turn limit without completion."

            finally:
                print("\nClosing browser...")
                await browser.close()
