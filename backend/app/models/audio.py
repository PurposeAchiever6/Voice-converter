"""
Audio processing data models
"""
from typing import List, Optional
from pydantic import BaseModel

class AudioSentence(BaseModel):
    """Model for a sentence with timing information"""
    text: str
    start_time: float  # in seconds
    end_time: float    # in seconds
    confidence: Optional[float] = None

class TranscriptionResult(BaseModel):
    """Model for transcription results from Gladia"""
    full_text: str
    sentences: List[AudioSentence]
    language: Optional[str] = None
    duration: Optional[float] = None

class VoiceCloneRequest(BaseModel):
    """Model for voice cloning request"""
    text: str
    voice_id: str
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    voice_settings: Optional[dict] = None
    
    model_config = {"protected_namespaces": ()}

class AudioProcessingResult(BaseModel):
    """Model for audio processing results"""
    original_duration: float
    processed_duration: float
    chunks_count: int
    output_path: str
    success: bool
    error_message: Optional[str] = None
