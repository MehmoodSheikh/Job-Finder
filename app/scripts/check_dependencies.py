import sys
import subprocess
import importlib
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dependency_checker")

# List of required packages and their import modules
REQUIRED_PACKAGES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "aiohttp": "aiohttp",
    "beautifulsoup4": "bs4",
    "python-dotenv": "dotenv",
    "numpy": "numpy",
    "bs4": "bs4",
    "langchain": "langchain",
    "langchain-google-genai": "langchain_google_genai",
    "google-generativeai": "google.generativeai"
}

# List of optional packages with descriptions
OPTIONAL_PACKAGES = {
    "scikit-learn": "sklearn",
    "nltk": "nltk"
}

def check_and_install_dependencies():
    """Check if required dependencies are installed, and install them if missing"""
    missing_packages = []
    
    for package, module_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ {package} ({module_name}) is installed")
        except ImportError:
            logger.warning(f"❌ {package} ({module_name}) is not installed")
            missing_packages.append(package)
    
    for package, module_name in OPTIONAL_PACKAGES.items():
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ {package} ({module_name}) is installed (optional)")
        except ImportError:
            logger.warning(f"⚠️ {package} ({module_name}) is not installed (optional)")
    
    if missing_packages:
        logger.info(f"Installing {len(missing_packages)} missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("All required packages have been installed successfully")
        except subprocess.CalledProcessError:
            logger.error("Failed to install some packages. Please install them manually.")
            return False
    else:
        logger.info("All required packages are already installed")
    
    return True

def check_environment_variables():
    """Check if required environment variables are set"""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.warning("⚠️ GOOGLE_API_KEY environment variable is not set")
        logger.warning("AI-powered relevance filtering will not be available")
        return False
    else:
        logger.info("✅ GOOGLE_API_KEY is set")
        return True

if __name__ == "__main__":
    logger.info("Checking dependencies...")
    check_and_install_dependencies()
    check_environment_variables()
    logger.info("Dependency check completed")
