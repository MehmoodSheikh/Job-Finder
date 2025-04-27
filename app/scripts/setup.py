"""
Setup script for installing Job Finder dependencies
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("setup")

def install_dependencies():
    """Install all required Python dependencies"""
    logger.info("Installing required Python packages...")
    
    packages = [
        "fastapi",
        "uvicorn",
        "aiohttp",
        "beautifulsoup4",
        "python-dotenv",
        "scikit-learn",
        "nltk",
        "langchain",
        "langchain-google-genai",
        "google-generativeai"
    ]
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        logger.info("Successfully installed Python packages")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        sys.exit(1)

def setup_env_file():
    """Create .env file template if it doesn't exist"""
    if not os.path.exists(".env"):
        logger.info("Creating .env file template...")
        with open(".env", "w") as f:
            f.write("""# Environment variables for Job Finder
# Google API key for AI relevance filtering
GOOGLE_API_KEY=your_google_api_key_here

# Other API keys for job platforms (optional)
LINKEDIN_API_KEY=
INDEED_API_KEY=
GLASSDOOR_API_KEY=
ROZEE_API_KEY=
""")
        logger.info("Created .env file template. Please edit it with your API keys.")
    else:
        logger.info(".env file already exists. Please make sure it has a GOOGLE_API_KEY entry.")

if __name__ == "__main__":
    logger.info("Starting Job Finder setup...")
    install_dependencies()
    setup_env_file()
    logger.info("""
    ✅ Setup complete!
    
    Next steps:
    1. Edit the .env file and add your Google API key for AI relevance filtering
    2. Run the application with: uvicorn app.main:app --reload
    """) 