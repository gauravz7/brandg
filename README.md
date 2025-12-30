# Brand Analysis Agent - Setup & Usage

A "Flashy" AI Agent that analyzes brand identity from a URL using **Playwright**, **Gemini**, and **Google Grounding**.

## Prerequisites
- Python 3.9+
- Node.js 18+
- Google Cloud Project with Vertex AI / Gemini API enabled.
- `GOOGLE_API_KEY` (Get it from AI Studio or Cloud Console).

## 1. Local Development

### Backend
1. Navigate to backend:
   ```bash
   cd Brand/backend
   ```
2. Create virtual env & install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Run Server:
   **Important**: You must set your `GOOGLE_API_KEY` (from Google AI Studio).
   ```bash
   export GOOGLE_API_KEY="your_api_key_here"
   python main.py
   ```
   The backend will start at `http://localhost:8000`.

### Frontend
1. Navigate to frontend:
   ```bash
   cd Brand/frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run Dev Server:
   ```bash
   npm run dev
   ```
   The application dashboard will be available at `http://localhost:3000`.

## 2. Cloud Run Deployment

A `deploy.sh` script is provided in the `Brand` directory.

1. Configure Google Cloud CLI:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Run Deploy Script:
   ```bash
   cd Brand
   ./deploy.sh
   # Note: You might need to update the REPO_NAME or PROJECT_ID in deploy.sh if auto-detection fails.
   ```
   
   **Important**: You need to set `GOOGLE_API_KEY` environment variable in Cloud Run service for the Backend after deployment (or update `deploy.sh` to include it via `--set-env-vars`).

## Features
- **URL Analysis**: Screenshots, Colors, Fonts, Assets (Logos, Favicons).
- **CSS Capture**: Extracts both external stylesheets and significant inline styles for technical brand analysis.
- **Brand Grounding**: Uses Gemini with Google Search grounding to find official brand guidelines and strategic info.
- **Visual Assets**: Supported formats include PNG, JPG, GIF, and **SVG** for high-quality logo rendering.
- **PDF Report**: Generates a comprehensive, formatted PDF report with title pages, snapshots, color swatches, and asset galleries.
- **Technical Specs**: Includes a dedicated section in the PDF for technical identity (CSS).
- **Intelligent Reuse**: Caches results by hostname and task ID for faster retrieval of previous analyses.
- **Anti-Bot Resilience**: Integrated stealth measures and browser refinement (though some sites like Myntra still show high resistance).

## Tech Stack
- **Backend**: FastAPI, Playwright (Stealth), Google GenAI SDK (Gemini), ReportLab, Svglib.
- **Frontend**: Next.js 15 (App Router), Tailwind CSS v4, Framer Motion, Lucide React.
