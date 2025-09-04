"""
ElevenLabs voice cloning service integration
"""
import asyncio
import httpx
from typing import Optional
from pathlib import Path

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class ElevenLabsService:
    """Service for ElevenLabs voice cloning API integration"""
    
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = settings.ELEVENLABS_API_URL
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.default_voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    async def health_check(self) -> dict:
        """Check if ElevenLabs service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/voices",
                    headers={"xi-api-key": self.api_key}
                )
                if response.status_code == 200:
                    return {"status": "healthy", "message": "ElevenLabs service is available"}
                else:
                    return {"status": "warning", "message": f"Unexpected status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"ElevenLabs health check failed: {str(e)}")
            return {"status": "error", "message": f"Service unavailable: {str(e)}"}
    
    async def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        output_filename: str,
        voice_settings: Optional[dict] = None
    ) -> str:
        """
        Generate speech from text using ElevenLabs voice cloning
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            output_filename: Base filename for output (without extension)
            voice_settings: Optional voice settings override
            
        Returns:
            Path to generated audio file
        """
        try:
            logger.info(f"Generating speech for text: '{text[:50]}...' with voice {voice_id}")
            
            # Prepare output path
            output_path = Path(settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare request payload
            payload = {
                "text": text,
                "model_id": settings.ELEVENLABS_MODEL_ID,
                "voice_settings": voice_settings or self.default_voice_settings
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/text-to-speech/{voice_id}",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # Save audio content
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Speech generated successfully: {output_path}")
                return str(output_path)
                
        except Exception as e:
            logger.error(f"Speech generation failed: {str(e)}")
            raise Exception(f"ElevenLabs speech generation failed: {str(e)}")
    
    async def get_available_voices(self) -> list:
        """Get list of available voices"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get voices: {response.text}")
                
                data = response.json()
                return data.get("voices", [])
                
        except Exception as e:
            logger.error(f"Failed to get voices: {str(e)}")
            raise
    
    async def get_voice_info(self, voice_id: str) -> dict:
        """Get information about a specific voice"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get voice info: {response.text}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get voice info: {str(e)}")
            raise
    
    async def clone_voice_from_sample(
        self, 
        name: str, 
        description: str, 
        audio_files: list,
        labels: Optional[dict] = None
    ) -> str:
        """
        Clone a voice from audio samples
        
        Args:
            name: Name for the cloned voice
            description: Description of the voice
            audio_files: List of audio file paths for voice cloning
            labels: Optional labels for the voice
            
        Returns:
            Voice ID of the cloned voice
        """
        try:
            logger.info(f"Cloning voice '{name}' from {len(audio_files)} samples")
            
            # Prepare files for upload
            files = []
            for i, audio_file in enumerate(audio_files):
                with open(audio_file, "rb") as f:
                    files.append(("files", (f"sample_{i}.wav", f.read(), "audio/wav")))
            
            # Prepare form data
            data = {
                "name": name,
                "description": description,
                "labels": labels or {}
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/voices/add",
                    headers={"xi-api-key": self.api_key},
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"Voice cloning failed: {response.text}")
                
                result = response.json()
                voice_id = result.get("voice_id")
                
                logger.info(f"Voice cloned successfully: {voice_id}")
                return voice_id
                
        except Exception as e:
            logger.error(f"Voice cloning failed: {str(e)}")
            raise Exception(f"ElevenLabs voice cloning failed: {str(e)}")
    
    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a cloned voice"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/v1/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to delete voice {voice_id}: {response.text}")
                    return False
                
                logger.info(f"Voice {voice_id} deleted successfully")
                return True
                
        except Exception as e:
            logger.error(f"Voice deletion failed: {str(e)}")
            return False
    
    async def get_user_info(self) -> dict:
        """Get user account information and usage"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/user",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get user info: {response.text}")
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            raise
    
    def validate_voice_settings(self, voice_settings: dict) -> dict:
        """Validate and normalize voice settings"""
        validated = self.default_voice_settings.copy()
        
        if voice_settings:
            # Validate stability (0.0 - 1.0)
            if "stability" in voice_settings:
                validated["stability"] = max(0.0, min(1.0, float(voice_settings["stability"])))
            
            # Validate similarity_boost (0.0 - 1.0)
            if "similarity_boost" in voice_settings:
                validated["similarity_boost"] = max(0.0, min(1.0, float(voice_settings["similarity_boost"])))
            
            # Validate style (0.0 - 1.0)
            if "style" in voice_settings:
                validated["style"] = max(0.0, min(1.0, float(voice_settings["style"])))
            
            # Validate use_speaker_boost (boolean)
            if "use_speaker_boost" in voice_settings:
                validated["use_speaker_boost"] = bool(voice_settings["use_speaker_boost"])
        
        return validated
