"""
Server script for running the Job Finder API
"""
import uvicorn
import os

# Fall back to default settings if import fails
try:
    from app.core.config import settings
    host = settings.HOST
    port = settings.PORT 
    reload = settings.RELOAD
except ImportError:
    print("Warning: Could not import app.core.config, using default settings")
    host = "0.0.0.0"
    port = 8000
    reload = True

if __name__ == "__main__":
    print(f"Starting server on {host}:{port} (reload: {reload})")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )
