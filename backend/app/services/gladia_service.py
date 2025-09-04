"""
Gladia Speech-to-Text service integration
"""
import asyncio
import httpx
from typing import Optional
from pathlib import Path

from ..models.audio import TranscriptionResult, AudioSentence
from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class GladiaService:
    """Service for Gladia STT API integration"""
    
    def __init__(self):
        self.api_key = settings.GLADIA_API_KEY
        self.base_url = settings.GLADIA_API_URL
        self.headers = {
            "x-gladia-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def health_check(self) -> dict:
        """Check if Gladia service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Use the transcription endpoint which supports GET and validates API key
                response = await client.get(
                    f"{self.base_url}/v2/transcription",
                    headers={"x-gladia-key": self.api_key}
                )
                if response.status_code == 200:
                    return {"status": "healthy", "message": "Gladia service is available"}
                elif response.status_code == 401:
                    return {"status": "error", "message": "Invalid API key"}
                elif response.status_code == 403:
                    return {"status": "warning", "message": "API key valid but insufficient permissions"}
                else:
                    return {"status": "warning", "message": f"Unexpected status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Gladia health check failed: {str(e)}")
            return {"status": "error", "message": f"Service unavailable: {str(e)}"}
    
    async def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe audio file using Gladia API with sentence-level timestamps
        """
        try:
            logger.info(f"Starting transcription for {audio_path}")
            
            # Step 1: Upload audio file
            upload_response = await self._upload_audio(audio_path)
            audio_url = upload_response["audio_url"]
            
            # Step 2: Start transcription with sentence-level timestamps
            transcription_id = await self._start_transcription(audio_url)
            
            # Step 3: Poll for results
            result = await self._poll_transcription_result(transcription_id)
            
            # Step 4: Parse results into our model
            transcription_result = self._parse_transcription_result(result)
            
            logger.info(f"Transcription completed: {len(transcription_result.sentences)} sentences")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise Exception(f"Gladia transcription failed: {str(e)}")
    
    async def _upload_audio(self, audio_path: str) -> dict:
        """Upload audio file to Gladia"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(audio_path, "rb") as audio_file:
                    files = {"audio": audio_file}
                    headers = {"x-gladia-key": self.api_key}
                    
                    response = await client.post(
                        f"{self.base_url}/v2/upload",
                        headers=headers,
                        files=files
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Upload failed: {response.text}")
                    
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Audio upload failed: {str(e)}")
            raise
    
    async def _start_transcription(self, audio_url: str) -> str:
        """Start transcription job with sentence-level timestamps"""
        try:
            payload = {
                "audio_url": audio_url,
                "diarization": False,
                "sentences": True  # Enable sentence-level timestamps
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/v2/transcription",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    raise Exception(f"Transcription start failed: {response.text}")
                
                result = response.json()
                # The response should contain an ID
                if "id" in result:
                    logger.info(f"Transcription started with ID: {result['id']}")
                    return result["id"]
                else:
                    raise Exception(f"No transcription ID in response: {result}")
                
        except Exception as e:
            logger.error(f"Transcription start failed: {str(e)}")
            raise
    
    async def _poll_transcription_result(self, transcription_id: str, max_wait_time: int = 600) -> dict:
        """Poll for transcription results"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                start_time = asyncio.get_event_loop().time()
                
                while True:
                    response = await client.get(
                        f"{self.base_url}/v2/transcription/{transcription_id}",
                        headers=self.headers
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Status check failed: {response.text}")
                    
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "done":
                        return result
                    elif status == "error":
                        error_msg = result.get("error", "Unknown error")
                        raise Exception(f"Transcription failed: {error_msg}")
                    
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > max_wait_time:
                        raise Exception("Transcription timeout")
                    
                    # Wait before next poll
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Transcription polling failed: {str(e)}")
            raise
    
    def _parse_transcription_result(self, result: dict) -> TranscriptionResult:
        """Parse Gladia API response into our model"""
        try:
            # Extract full text
            full_text = result.get("result", {}).get("transcription", {}).get("full_transcript", "")
            
            # Extract sentences with timestamps
            sentences = []
            utterances = result.get("result", {}).get("transcription", {}).get("utterances", [])
            
            for utterance in utterances:
                # Each utterance may contain multiple sentences
                utterance_sentences = utterance.get("sentences", [])
                
                for sentence_data in utterance_sentences:
                    sentence = AudioSentence(
                        text=sentence_data.get("sentence", "").strip(),
                        start_time=sentence_data.get("start", 0.0),
                        end_time=sentence_data.get("end", 0.0),
                        confidence=sentence_data.get("confidence")
                    )
                    
                    if sentence.text:  # Only add non-empty sentences
                        sentences.append(sentence)
            
            # If no sentences found, try to extract from words
            if not sentences and utterances:
                sentences = self._extract_sentences_from_words(utterances)
            
            # Get language and duration
            metadata = result.get("result", {}).get("metadata", {})
            language = metadata.get("language")
            duration = metadata.get("duration")
            
            return TranscriptionResult(
                full_text=full_text,
                sentences=sentences,
                language=language,
                duration=duration
            )
            
        except Exception as e:
            logger.error(f"Result parsing failed: {str(e)}")
            raise Exception(f"Failed to parse transcription result: {str(e)}")
    
    def _extract_sentences_from_words(self, utterances: list) -> list:
        """Fallback: extract sentences from word-level data"""
        sentences = []
        
        try:
            for utterance in utterances:
                words = utterance.get("words", [])
                if not words:
                    continue
                
                # Group words into sentences (simple approach)
                current_sentence = []
                sentence_start = None
                
                for word_data in words:
                    word = word_data.get("word", "").strip()
                    start_time = word_data.get("start", 0.0)
                    end_time = word_data.get("end", 0.0)
                    
                    if sentence_start is None:
                        sentence_start = start_time
                    
                    current_sentence.append(word)
                    
                    # End sentence on punctuation or after ~10 words
                    if (word.endswith(('.', '!', '?')) or 
                        len(current_sentence) >= 10):
                        
                        sentence_text = ' '.join(current_sentence).strip()
                        if sentence_text:
                            sentences.append(AudioSentence(
                                text=sentence_text,
                                start_time=sentence_start,
                                end_time=end_time
                            ))
                        
                        current_sentence = []
                        sentence_start = None
                
                # Add remaining words as final sentence
                if current_sentence:
                    sentence_text = ' '.join(current_sentence).strip()
                    if sentence_text:
                        sentences.append(AudioSentence(
                            text=sentence_text,
                            start_time=sentence_start,
                            end_time=words[-1].get("end", 0.0)
                        ))
            
        except Exception as e:
            logger.warning(f"Fallback sentence extraction failed: {str(e)}")
        
        return sentences
