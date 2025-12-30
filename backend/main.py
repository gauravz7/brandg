import os
import uuid
import asyncio
import aiofiles
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

from services.scraper_service import ScraperService
from services.asset_manager import AssetManager
from services.gemini_service import GeminiService
from services.pdf_generator import PDFGenerator

# Load env
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Brand Analysis Agent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
os.makedirs("results", exist_ok=True)
app.mount("/results", StaticFiles(directory="results"), name="results")

# In-memory store
tasks: Dict[str, Dict[str, Any]] = {}

class AnalysisRequest(BaseModel):
    url: str

# ... imports ...
from urllib.parse import urlparse
import json

# ... (previous code) ...

def get_brand_id(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.netloc or parsed.path
    # Remove www. and active ports
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname.split(':')[0].replace('.', '_')

async def analyze_brand_task(task_id: str, url: str): # task_id is now brand_id
    tasks[task_id] = tasks.get(task_id, {})
    tasks[task_id].update({"status": "processing", "progress": 0, "logs": []})
    
    def log(msg):
        print(f"[{task_id}] {msg}")
        if "logs" in tasks[task_id]:
            tasks[task_id]["logs"].append(msg)

    try:
        brand_id = task_id # Use brand_id as task_id
        
        # Check if already done (simple check: data.json exists)
        if os.path.exists(f"results/{brand_id}/data.json"):
            log("Found existing data. Reusing...")
            async with aiofiles.open(f"results/{brand_id}/data.json", "r") as f:
                data = json.loads(await f.read())
                tasks[task_id]["data"] = data
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["progress"] = 100
                return

        scraper = ScraperService()
        assets = AssetManager("results")
        gemini = GeminiService()
        pdf_gen = PDFGenerator()
        
        # Step 0: Setup
        log("Setting up directories...")
        assets.create_task_dirs(brand_id)
        
        # Step 1: Scrape
        tasks[task_id]["progress"] = 10
        log(f"Scraping {url}...")
        brand_data = await scraper.analyze_url(url)
        tasks[task_id]["progress"] = 40
        log("Scraping complete.")
        
        # Step 2: Save Assets
        log("Saving assets...")
        await assets.save_screenshot(brand_id, brand_data["screenshot"])
        brand_asset_paths = await assets.save_assets(brand_id, brand_data["assets"])
        await assets.save_fonts(brand_id, brand_data["fonts"])
        
        log("Generating color swatches...")
        color_asset_paths = await assets.save_color_images(brand_id, brand_data["colors"])
        
        log("Saving CSS assets...")
        css_asset_paths = await assets.save_css(brand_id, brand_data["css"])
        
        tasks[task_id]["progress"] = 60
        
        # Step 3: Gemini Search & Grounding
        log("Searching Brand Guidelines with Gemini...")
        guidelines_text = await gemini.search_brand_guidelines(brand_data["title"], url)
        async with aiofiles.open(f"results/{brand_id}/Google Search/guidelines.txt", "w") as f:
            await f.write(guidelines_text)
        tasks[task_id]["progress"] = 80
        
        # Step 4: Generate Report
        log("Compiling final report...")
        report_text = await gemini.compile_final_report(brand_data, guidelines_text)
        
        # Step 5: PDF
        log("Generating PDF...")
        pdf_path = pdf_gen.generate_pdf(brand_id, "results", brand_data["title"], report_text, color_assets=color_asset_paths, brand_assets=brand_asset_paths, css_assets=css_asset_paths)
        
        # Finalize
        if "screenshot" in brand_data:
            del brand_data["screenshot"]
            
        final_data = {
            "brand_data": brand_data,
            "guidelines": guidelines_text,
            "report": report_text,
            "pdf_url": f"/results/{brand_id}/{os.path.basename(pdf_path)}" if pdf_path else None,
            "screenshot_url": f"/results/{brand_id}/Snapshot/homepage.png",
            "assets_urls": [
                f"/results/{brand_id}/Brand Assets/{f}" 
                for f in os.listdir(f"results/{brand_id}/Brand Assets") 
                if not f.startswith('.')
            ],
            "css_urls": [
                f"/results/{brand_id}/CSS/{f}"
                for f in os.listdir(f"results/{brand_id}/CSS")
                if not f.startswith('.')
            ]
        }
        
        # Save data.json for reuse
        async with aiofiles.open(f"results/{brand_id}/data.json", "w") as f:
            await f.write(json.dumps(final_data, default=str)) # handle non-serializable if any

        tasks[task_id]["data"] = final_data
        
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        log("Analysis complete!")

    except Exception as e:
        log(f"Error: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.post("/analyze")
async def analyze_brand(request: AnalysisRequest, background_tasks: BackgroundTasks):
    brand_id = get_brand_id(request.url)
    
    # If task allows concurrent same-brand processing, we might want to check if it's already running?
    # For now, we'll just overwrite/join.
    if brand_id not in tasks:
        tasks[brand_id] = {"status": "pending", "created_at": str(asyncio.get_event_loop().time())}
        background_tasks.add_task(analyze_brand_task, brand_id, request.url)
    elif tasks[brand_id]["status"] == "completed":
        # It's done, ensure data is loaded?
        # The background task logic checks persistence, but tasks dict might be empty on restart.
        # We should probably trigger the task to load from disk if needed.
        # Let's just trigger the task again; the task logic handles "Found existing data".
        if "data" not in tasks[brand_id]:
             background_tasks.add_task(analyze_brand_task, brand_id, request.url)
    else:
        # It's running/failed -> let it run or restart if failed?
        if tasks[brand_id].get("status") == "failed":
             background_tasks.add_task(analyze_brand_task, brand_id, request.url)

    return {"status": tasks[brand_id].get("status", "started"), "task_id": brand_id, "url": request.url}


@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
