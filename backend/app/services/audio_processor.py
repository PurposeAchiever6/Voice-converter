"""
Audio processing service using pydub for duration matching and concatenation
"""
import asyncio
from typing import List
from pathlib import Path
import math

from pydub import AudioSegment
from pydub.silence import split_on_silence

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class AudioProcessor:
    """Service for audio processing operations"""
    
    def __init__(self):
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
        self.channels = settings.AUDIO_CHANNELS
        self.silence_threshold = settings.CHUNK_SILENCE_THRESHOLD
    
    async def match_timing(
        self, 
        cloned_audio_path: str, 
        target_start_time: float, 
        target_end_time: float,
        output_filename: str
    ) -> str:
        """
        Match the timing of cloned audio to original chunk duration
        
        Args:
            cloned_audio_path: Path to the cloned audio file
            target_start_time: Start time of original chunk (seconds)
            target_end_time: End time of original chunk (seconds)
            output_filename: Base filename for output (without extension)
            
        Returns:
            Path to timing-matched audio file
        """
        try:
            target_duration = target_end_time - target_start_time
            logger.info(f"Matching timing: target duration {target_duration:.2f}s")
            
            # Load cloned audio
            cloned_audio = AudioSegment.from_file(cloned_audio_path)
            cloned_duration = len(cloned_audio) / 1000.0  # Convert to seconds
            
            logger.info(f"Cloned audio duration: {cloned_duration:.2f}s")
            
            # Calculate timing adjustment needed
            duration_ratio = target_duration / cloned_duration
            
            # Prepare output path
            output_path = Path(settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if abs(duration_ratio - 1.0) < 0.05:  # Within 5% - no adjustment needed
                logger.info("Duration match is close enough, no adjustment needed")
                matched_audio = cloned_audio
            elif duration_ratio > 1.0:  # Need to stretch/slow down
                matched_audio = await self._stretch_audio(cloned_audio, duration_ratio)
            else:  # Need to compress/speed up
                matched_audio = await self._compress_audio(cloned_audio, duration_ratio)
            
            # Ensure exact duration by padding or trimming
            matched_audio = await self._ensure_exact_duration(matched_audio, target_duration)
            
            # Export with consistent format
            matched_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(self.sample_rate),
                    "-ac", str(self.channels)
                ]
            )
            
            logger.info(f"Timing matched audio saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Timing matching failed: {str(e)}")
            raise Exception(f"Audio timing matching failed: {str(e)}")
    
    async def _stretch_audio(self, audio: AudioSegment, ratio: float) -> AudioSegment:
        """Stretch audio to make it longer (slower)"""
        try:
            # Use pydub's speedup with inverse ratio to slow down
            # Note: speedup with ratio < 1.0 actually slows down the audio
            stretched = audio.speedup(playback_speed=1.0/ratio)
            logger.info(f"Audio stretched by factor {ratio:.2f}")
            return stretched
        except Exception as e:
            logger.warning(f"Stretch failed, using padding fallback: {str(e)}")
            # Fallback: add silence padding
            target_duration_ms = int(len(audio) * ratio)
            padding_ms = target_duration_ms - len(audio)
            silence = AudioSegment.silent(duration=padding_ms)
            return audio + silence
    
    async def _compress_audio(self, audio: AudioSegment, ratio: float) -> AudioSegment:
        """Compress audio to make it shorter (faster)"""
        try:
            # Use pydub's speedup to make audio faster
            compressed = audio.speedup(playback_speed=1.0/ratio)
            logger.info(f"Audio compressed by factor {ratio:.2f}")
            return compressed
        except Exception as e:
            logger.warning(f"Compression failed, using trimming fallback: {str(e)}")
            # Fallback: trim audio
            target_duration_ms = int(len(audio) * ratio)
            return audio[:target_duration_ms]
    
    async def _ensure_exact_duration(self, audio: AudioSegment, target_duration: float) -> AudioSegment:
        """Ensure audio has exact target duration by padding or trimming"""
        target_duration_ms = int(target_duration * 1000)
        current_duration_ms = len(audio)
        
        if current_duration_ms < target_duration_ms:
            # Add silence padding
            padding_ms = target_duration_ms - current_duration_ms
            silence = AudioSegment.silent(duration=padding_ms)
            audio = audio + silence
            logger.info(f"Added {padding_ms}ms silence padding")
        elif current_duration_ms > target_duration_ms:
            # Trim excess
            audio = audio[:target_duration_ms]
            logger.info(f"Trimmed {current_duration_ms - target_duration_ms}ms excess")
        
        return audio
    
    async def concatenate_audio(self, audio_paths: List[str], output_filename: str) -> str:
        """
        Concatenate multiple audio files into one
        
        Args:
            audio_paths: List of audio file paths to concatenate
            output_filename: Base filename for output (without extension)
            
        Returns:
            Path to concatenated audio file
        """
        try:
            logger.info(f"Concatenating {len(audio_paths)} audio files")
            
            if not audio_paths:
                raise ValueError("No audio files to concatenate")
            
            # Prepare output path
            output_path = Path(settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load and concatenate audio files
            combined_audio = AudioSegment.empty()
            
            for i, audio_path in enumerate(audio_paths):
                try:
                    audio_segment = AudioSegment.from_file(audio_path)
                    
                    # Normalize audio properties
                    audio_segment = audio_segment.set_frame_rate(self.sample_rate)
                    audio_segment = audio_segment.set_channels(self.channels)
                    
                    combined_audio += audio_segment
                    logger.info(f"Added segment {i+1}/{len(audio_paths)}: {len(audio_segment)}ms")
                    
                except Exception as e:
                    logger.warning(f"Failed to load audio segment {audio_path}: {str(e)}")
                    # Add silence for failed segments to maintain timing
                    silence_duration = 1000  # 1 second default
                    combined_audio += AudioSegment.silent(duration=silence_duration)
            
            if len(combined_audio) == 0:
                raise Exception("No valid audio segments found")
            
            # Export final audio
            combined_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(self.sample_rate),
                    "-ac", str(self.channels)
                ]
            )
            
            total_duration = len(combined_audio) / 1000.0
            logger.info(f"Concatenated audio saved: {output_path} (duration: {total_duration:.2f}s)")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Audio concatenation failed: {str(e)}")
            raise Exception(f"Audio concatenation failed: {str(e)}")
    
    async def analyze_audio(self, audio_path: str) -> dict:
        """
        Analyze audio file properties
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio properties
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            return {
                "duration_seconds": len(audio) / 1000.0,
                "duration_ms": len(audio),
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "frame_count": audio.frame_count(),
                "max_possible_amplitude": audio.max_possible_amplitude,
                "rms": audio.rms,
                "dBFS": audio.dBFS
            }
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {str(e)}")
            raise Exception(f"Audio analysis failed: {str(e)}")
    
    async def split_on_silence(self, audio_path: str, min_silence_len: int = 500) -> List[AudioSegment]:
        """
        Split audio on silence periods
        
        Args:
            audio_path: Path to audio file
            min_silence_len: Minimum silence length in milliseconds
            
        Returns:
            List of audio segments
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Split on silence
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=audio.dBFS - 14,  # Adjust based on audio
                keep_silence=100  # Keep some silence at edges
            )
            
            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Audio splitting failed: {str(e)}")
            raise Exception(f"Audio splitting failed: {str(e)}")
    
    async def normalize_audio(self, audio_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume
        
        Args:
            audio_path: Path to input audio file
            target_dBFS: Target volume in dBFS
            
        Returns:
            Path to normalized audio file
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Calculate normalization
            change_in_dBFS = target_dBFS - audio.dBFS
            normalized_audio = audio.apply_gain(change_in_dBFS)
            
            # Save normalized audio
            output_path = audio_path.replace('.wav', '_normalized.wav')
            normalized_audio.export(output_path, format="wav")
            
            logger.info(f"Audio normalized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio normalization failed: {str(e)}")
            raise Exception(f"Audio normalization failed: {str(e)}")
