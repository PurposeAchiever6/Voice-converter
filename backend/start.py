"""
Startup script for Voice Converter backend
"""
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.config import validate_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    try:
        import fastapi
        import uvicorn
        import pydub
        import httpx
        import boto3
        logger.info("All required dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is available for pydub"""
    try:
        from pydub.utils import which
        if which("ffmpeg"):
            logger.info("FFmpeg is available")
            return True
        else:
            logger.warning("FFmpeg not found - some audio formats may not work")
            return False
    except Exception as e:
        logger.warning(f"Could not check FFmpeg availability: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("Starting Voice Converter backend...")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies. Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check FFmpeg
    check_ffmpeg()
    
    # Validate configuration
    try:
        validate_settings()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.error("Please check your .env file and ensure all required variables are set")
        sys.exit(1)
    
    # Create necessary directories
    from app.utils.config import get_settings
    settings = get_settings()
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("All checks passed. Starting server...")
    
    # Start the server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
