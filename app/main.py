"""
Main application module for Job Finder API
"""
import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Job Finder API",
    description="API for searching jobs across multiple platforms",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path("app/static")
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
    logger.warning(f"Created missing static directory: {static_dir}")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Import and include API routes
try:
    from app.api.routes import router as api_router
    app.include_router(api_router, prefix="/api")
    logger.info("✅ API routes loaded successfully")
except Exception as e:
    logger.error(f"Failed to load API routes: {e}")
    raise

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the index.html file"""
    try:
        html_path = Path("app/static/index.html")
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<html><body><h1>Error: index.html not found</h1></body></html>")
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Verify Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        logger.info("✅ Google API key found")
    else:
        logger.warning("⚠️ Google API key not found - AI relevance filtering will not be available")
    
    logger.info("Job Finder API started successfully")
