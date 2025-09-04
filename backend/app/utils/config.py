"""
Configuration management for Voice Converter
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    GLADIA_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    
    
    # Application Settings
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    MAX_FILE_SIZE: int = 100000000  # 100MB
    ALLOWED_EXTENSIONS: str = "wav,mp3,m4a,flac,ogg"
    
    # ElevenLabs Settings
    ELEVENLABS_VOICE_ID: str = ""
    ELEVENLABS_MODEL_ID: str = "eleven_multilingual_v2"
    
    # API URLs
    GLADIA_API_URL: str = "https://api.gladia.io"
    ELEVENLABS_API_URL: str = "https://api.elevenlabs.io"
    FILEIO_API_URL: str = "https://file.io"
    
    # Processing Settings
    AUDIO_SAMPLE_RATE: int = 22050
    AUDIO_CHANNELS: int = 1
    CHUNK_SILENCE_THRESHOLD: float = 0.1  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def validate_settings():
    """Validate required settings"""
    settings = get_settings()
    
    required_fields = [
        "GLADIA_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    return True
