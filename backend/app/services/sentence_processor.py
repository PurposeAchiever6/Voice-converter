"""
Sentence-by-sentence audio processing service with timestamp-based segmentation
"""
import asyncio
import os
import tempfile
from typing import List, Tuple
from pathlib import Path
import uuid

from pydub import AudioSegment

from .elevenlabs_service import ElevenLabsService
from .audio_processor import AudioProcessor
from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class SentenceProcessor:
    """Service for processing audio sentence by sentence with timestamp handling"""
    
    def __init__(self):
        self.elevenlabs_service = ElevenLabsService()
        self.audio_processor = AudioProcessor()
        self.temp_dir = Path(settings.OUTPUT_DIR) / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_sentences_with_timestamps(
        self,
        original_audio_path: str,
        sentences: List[dict],
        voice_id: str,
        output_filename: str
    ) -> str:
        """
        Process sentences with timestamp-based segmentation to avoid empty spaces
        
        Args:
            original_audio_path: Path to original audio file
            sentences: List of sentence dictionaries with text, start_time, end_time
            voice_id: ElevenLabs voice ID
            output_filename: Base filename for output
            
        Returns:
            Path to final processed audio file
        """
        try:
            logger.info(f"Processing {len(sentences)} sentences with timestamp handling")
            
            # Load original audio for reference
            original_audio = AudioSegment.from_file(original_audio_path)
            
            # Filter out empty spaces and create continuous timeline
            filtered_sentences = self._filter_empty_spaces(sentences)
            continuous_timeline = self._create_continuous_timeline(filtered_sentences)
            
            # Generate temp files for each sentence
            temp_files = []
            for i, (sentence_data, target_duration) in enumerate(continuous_timeline):
                logger.info(f"Processing sentence {i+1}/{len(continuous_timeline)}: '{sentence_data['text'][:50]}...'")
                
                # Generate voice clone for this sentence
                temp_filename = f"temp_sentence_{uuid.uuid4().hex[:8]}_{i}"
                cloned_audio_path = await self.elevenlabs_service.generate_speech(
                    sentence_data['text'],
                    voice_id,
                    temp_filename
                )
                
                # Adjust length to match target duration
                adjusted_audio_path = await self._adjust_audio_length(
                    cloned_audio_path,
                    target_duration,
                    f"adjusted_{temp_filename}"
                )
                
                temp_files.append(adjusted_audio_path)
                
                # Clean up intermediate file
                if os.path.exists(cloned_audio_path):
                    os.remove(cloned_audio_path)
            
            # Combine all temp files into final output
            final_output_path = await self.audio_processor.concatenate_audio(
                temp_files,
                output_filename
            )
            
            # Clean up temp files
            await self._cleanup_temp_files(temp_files)
            
            logger.info(f"Sentence processing completed: {final_output_path}")
            return final_output_path
            
        except Exception as e:
            logger.error(f"Sentence processing failed: {str(e)}")
            raise Exception(f"Sentence processing failed: {str(e)}")
    
    def _filter_empty_spaces(self, sentences: List[dict]) -> List[dict]:
        """
        Filter out sentences that fall in empty spaces and adjust timestamps
        
        Args:
            sentences: List of sentence dictionaries
            
        Returns:
            Filtered list of sentences with valid content
        """
        filtered = []
        
        for sentence in sentences:
            # Skip very short sentences (likely empty spaces or artifacts)
            duration = sentence['end_time'] - sentence['start_time']
            if duration < 0.1:  # Skip sentences shorter than 100ms
                logger.debug(f"Skipping short sentence: {sentence['text'][:30]}... ({duration:.3f}s)")
                continue
            
            # Skip sentences with minimal text content
            text = sentence['text'].strip()
            if len(text) < 2:  # Skip sentences with less than 2 characters
                logger.debug(f"Skipping minimal text: '{text}' ({duration:.3f}s)")
                continue
            
            filtered.append(sentence)
        
        logger.info(f"Filtered {len(sentences)} sentences to {len(filtered)} valid sentences")
        return filtered
    
    def _create_continuous_timeline(self, sentences: List[dict]) -> List[Tuple[dict, float]]:
        """
        Create a continuous timeline without gaps between sentences
        
        Args:
            sentences: List of filtered sentence dictionaries
            
        Returns:
            List of tuples (sentence_data, target_duration)
        """
        timeline = []
        
        for sentence in sentences:
            original_duration = sentence['end_time'] - sentence['start_time']
            timeline.append((sentence, original_duration))
        
        logger.info(f"Created continuous timeline with {len(timeline)} segments")
        
        # Log timeline for debugging
        total_duration = 0
        for i, (sentence, duration) in enumerate(timeline):
            logger.debug(f"Segment {i+1}: {duration:.3f}s - '{sentence['text'][:50]}...'")
            total_duration += duration
        
        logger.info(f"Total continuous duration: {total_duration:.3f}s")
        return timeline
    
    async def _adjust_audio_length(
        self,
        audio_path: str,
        target_duration: float,
        output_filename: str
    ) -> str:
        """
        Adjust audio length to match target duration using pydub
        
        Args:
            audio_path: Path to input audio file
            target_duration: Target duration in seconds
            output_filename: Output filename
            
        Returns:
            Path to length-adjusted audio file
        """
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            current_duration = len(audio) / 1000.0  # Convert to seconds
            
            logger.debug(f"Adjusting audio: {current_duration:.3f}s -> {target_duration:.3f}s")
            
            # Calculate adjustment ratio
            ratio = target_duration / current_duration
            
            # Prepare output path
            output_path = self.temp_dir / f"{output_filename}.wav"
            
            if abs(ratio - 1.0) < 0.05:  # Within 5% - no adjustment needed
                adjusted_audio = audio
                logger.debug("Duration close enough, no adjustment needed")
            elif ratio > 1.0:  # Need to stretch (slow down)
                # Use speed adjustment to stretch audio
                adjusted_audio = audio.speedup(playback_speed=1.0/ratio)
                logger.debug(f"Stretched audio by factor {ratio:.3f}")
            else:  # Need to compress (speed up)
                # Use speed adjustment to compress audio
                adjusted_audio = audio.speedup(playback_speed=1.0/ratio)
                logger.debug(f"Compressed audio by factor {ratio:.3f}")
            
            # Ensure exact duration by padding or trimming
            target_duration_ms = int(target_duration * 1000)
            current_duration_ms = len(adjusted_audio)
            
            if current_duration_ms < target_duration_ms:
                # Add silence padding
                padding_ms = target_duration_ms - current_duration_ms
                silence = AudioSegment.silent(duration=padding_ms)
                adjusted_audio = adjusted_audio + silence
                logger.debug(f"Added {padding_ms}ms silence padding")
            elif current_duration_ms > target_duration_ms:
                # Trim excess
                adjusted_audio = adjusted_audio[:target_duration_ms]
                logger.debug(f"Trimmed {current_duration_ms - target_duration_ms}ms excess")
            
            # Export adjusted audio
            adjusted_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(settings.AUDIO_SAMPLE_RATE),
                    "-ac", str(settings.AUDIO_CHANNELS)
                ]
            )
            
            final_duration = len(adjusted_audio) / 1000.0
            logger.debug(f"Audio length adjusted: {output_path} ({final_duration:.3f}s)")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Audio length adjustment failed: {str(e)}")
            raise Exception(f"Audio length adjustment failed: {str(e)}")
    
    async def _cleanup_temp_files(self, temp_files: List[str]):
        """Clean up temporary files"""
        try:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            
            logger.info(f"Cleaned up {len(temp_files)} temporary files")
            
        except Exception as e:
            logger.warning(f"Temp file cleanup failed: {str(e)}")
    
    async def analyze_sentence_gaps(self, sentences: List[dict]) -> dict:
        """
        Analyze gaps between sentences to identify empty spaces
        
        Args:
            sentences: List of sentence dictionaries
            
        Returns:
            Analysis results with gap information
        """
        try:
            gaps = []
            total_speech_time = 0
            
            # Sort sentences by start time
            sorted_sentences = sorted(sentences, key=lambda x: x['start_time'])
            
            for i, sentence in enumerate(sorted_sentences):
                speech_duration = sentence['end_time'] - sentence['start_time']
                total_speech_time += speech_duration
                
                if i > 0:
                    # Calculate gap from previous sentence
                    prev_sentence = sorted_sentences[i-1]
                    gap_start = prev_sentence['end_time']
                    gap_end = sentence['start_time']
                    gap_duration = gap_end - gap_start
                    
                    if gap_duration > 0.1:  # Gaps longer than 100ms
                        gaps.append({
                            'start': gap_start,
                            'end': gap_end,
                            'duration': gap_duration
                        })
            
            # Check for gap at the beginning
            if sorted_sentences and sorted_sentences[0]['start_time'] > 0.1:
                gaps.insert(0, {
                    'start': 0,
                    'end': sorted_sentences[0]['start_time'],
                    'duration': sorted_sentences[0]['start_time']
                })
            
            total_gap_time = sum(gap['duration'] for gap in gaps)
            total_duration = sorted_sentences[-1]['end_time'] if sorted_sentences else 0
            
            analysis = {
                'total_sentences': len(sentences),
                'total_duration': total_duration,
                'total_speech_time': total_speech_time,
                'total_gap_time': total_gap_time,
                'speech_ratio': total_speech_time / total_duration if total_duration > 0 else 0,
                'gaps': gaps,
                'filtered_sentences': len([s for s in sentences if s['end_time'] - s['start_time'] >= 0.1])
            }
            
            logger.info(f"Gap analysis: {analysis['total_sentences']} sentences, "
                       f"{analysis['total_gap_time']:.2f}s gaps, "
                       f"{analysis['speech_ratio']:.1%} speech ratio")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Gap analysis failed: {str(e)}")
            return {}
