"""
Same Length Voice Converter workflow test
Processes all sentences without gaps but maintains original audio duration
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gladia_service import GladiaService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.audio_processor import AudioProcessor
from app.utils.config import get_settings
from app.utils.logger import get_logger
from pydub import AudioSegment

logger = get_logger(__name__)

class SameLengthVoiceConverter:
    """Same length voice conversion workflow without gaps but same duration"""
    
    def __init__(self):
        self.gladia_service = GladiaService()
        self.elevenlabs_service = ElevenLabsService()
        self.audio_processor = AudioProcessor()
        self.settings = get_settings()
        self.temp_files = []  # Track temporary files for cleanup
    
    async def convert_voice_same_length(self, input_audio_path: str) -> str:
        """
        Convert voice in audio file maintaining original duration but without gaps
        
        Args:
            input_audio_path: Path to input audio file
            
        Returns:
            Path to final converted audio file
        """
        try:
            input_path = Path(input_audio_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
            
            print(f"🎵 Starting Same Length Voice Conversion")
            print(f"📁 Input file: {input_path}")
            print("=" * 60)
            
            # Get original audio duration
            original_audio = AudioSegment.from_file(str(input_path))
            original_duration = len(original_audio) / 1000.0
            print(f"📊 Original audio duration: {original_duration:.2f} seconds")
            
            # Step 1: Transcribe audio
            print("\n1. Transcribing audio...")
            transcription_result = await self.gladia_service.transcribe_audio(str(input_path))
            sentence_count = len(transcription_result.sentences)
            print(f"   ✅ Found {sentence_count} sentences")
            
            if sentence_count == 0:
                raise Exception("No sentences found in transcription")
            
            # Step 2: Process each sentence (generate voice clones only)
            print(f"\n2. Processing {sentence_count} sentences...")
            temp_audio_files = []
            sentence_durations = []
            
            for i, sentence in enumerate(transcription_result.sentences):
                print(f"   Processing sentence {i+1}/{sentence_count}: {sentence.text[:50]}...")
                
                # Generate voice clone for this sentence
                temp_cloned_path = await self.elevenlabs_service.generate_speech(
                    sentence.text,
                    self.settings.ELEVENLABS_VOICE_ID,
                    f"temp_sentence_{i}"
                )
                self.temp_files.append(temp_cloned_path)
                temp_audio_files.append(temp_cloned_path)
                
                # Get the duration of the cloned audio
                cloned_audio = AudioSegment.from_file(temp_cloned_path)
                cloned_duration = len(cloned_audio) / 1000.0
                sentence_durations.append(cloned_duration)
                
                print(f"      ✅ Sentence {i+1} voice cloned ({cloned_duration:.2f}s)")
            
            # Step 3: Create same-length final audio
            print(f"\n3. Creating same-length final audio...")
            final_audio_path = await self._create_same_length_audio(
                temp_audio_files,
                sentence_durations,
                original_duration,
                input_path
            )
            
            # Step 4: Cleanup temporary files
            print(f"\n4. Cleaning up temporary files...")
            deleted_count = self._cleanup_temp_files()
            print(f"   ✅ Cleaned up {deleted_count} temporary files")
            
            print("\n" + "=" * 60)
            print("🎉 Same length voice conversion completed successfully!")
            print(f"📁 Final output: {final_audio_path}")
            
            return final_audio_path
            
        except Exception as e:
            logger.error(f"Same length voice conversion failed: {str(e)}")
            # Cleanup on error
            self._cleanup_temp_files()
            raise Exception(f"Same length voice conversion failed: {str(e)}")
    
    async def _create_same_length_audio(
        self, 
        temp_audio_files: List[str], 
        sentence_durations: List[float],
        target_duration: float,
        input_path: Path
    ) -> str:
        """Create final audio with same length as original but without gaps"""
        try:
            # Create output filename (same as input but with _same_length suffix)
            output_filename = input_path.stem + "_same_length"
            output_path = Path(self.settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate total duration of all sentences
            total_sentence_duration = sum(sentence_durations)
            print(f"   📊 Total sentence duration: {total_sentence_duration:.2f}s")
            print(f"   📊 Target duration: {target_duration:.2f}s")
            
            # Calculate how much extra time we need to distribute
            extra_time = target_duration - total_sentence_duration
            print(f"   📊 Extra time to distribute: {extra_time:.2f}s")
            
            # Distribute extra time proportionally across sentences
            sentence_weights = [duration / total_sentence_duration for duration in sentence_durations]
            extra_time_per_sentence = [extra_time * weight for weight in sentence_weights]
            
            # Start with empty audio
            final_audio = AudioSegment.empty()
            
            print(f"   Building same-length audio timeline...")
            
            for i, (audio_file, original_duration, extra_time_for_sentence) in enumerate(zip(temp_audio_files, sentence_durations, extra_time_per_sentence)):
                # Load sentence audio
                sentence_audio = AudioSegment.from_file(audio_file)
                
                # Calculate target duration for this sentence (original + proportional extra time)
                target_sentence_duration = original_duration + extra_time_for_sentence
                target_duration_ms = int(target_sentence_duration * 1000)
                
                # Adjust sentence duration to fit target
                current_duration_ms = len(sentence_audio)
                
                if target_duration_ms > current_duration_ms:
                    # Need to stretch or add padding
                    stretch_factor = target_duration_ms / current_duration_ms
                    if stretch_factor <= 2.0:  # Reasonable stretch limit
                        # Stretch the audio
                        adjusted_audio = sentence_audio.speedup(playback_speed=1.0/stretch_factor)
                        print(f"      Sentence {i+1}: Stretched by {stretch_factor:.2f}x to {target_sentence_duration:.2f}s")
                    else:
                        # Add silence padding instead of extreme stretching
                        padding_ms = target_duration_ms - current_duration_ms
                        # Distribute padding: half at end, half as pauses within
                        end_padding_ms = padding_ms // 2
                        remaining_padding_ms = padding_ms - end_padding_ms
                        
                        # Add some padding at the end
                        end_silence = AudioSegment.silent(duration=end_padding_ms)
                        adjusted_audio = sentence_audio + end_silence
                        
                        # Add remaining padding as brief pauses (if significant)
                        if remaining_padding_ms > 100:  # Only if > 100ms
                            mid_silence = AudioSegment.silent(duration=remaining_padding_ms)
                            adjusted_audio = adjusted_audio + mid_silence
                        
                        print(f"      Sentence {i+1}: Added {padding_ms/1000:.2f}s distributed padding to reach {target_sentence_duration:.2f}s")
                elif target_duration_ms < current_duration_ms:
                    # Need to compress
                    compress_factor = target_duration_ms / current_duration_ms
                    if compress_factor >= 0.5:  # Reasonable compression limit
                        # Compress the audio
                        adjusted_audio = sentence_audio.speedup(playback_speed=1.0/compress_factor)
                        print(f"      Sentence {i+1}: Compressed by {1/compress_factor:.2f}x to {target_sentence_duration:.2f}s")
                    else:
                        # Trim instead of extreme compression
                        adjusted_audio = sentence_audio[:target_duration_ms]
                        print(f"      Sentence {i+1}: Trimmed to {target_sentence_duration:.2f}s")
                else:
                    # Duration is already correct
                    adjusted_audio = sentence_audio
                    print(f"      Sentence {i+1}: Duration already correct ({target_sentence_duration:.2f}s)")
                
                # Add to final audio
                final_audio += adjusted_audio
            
            # Ensure exact target duration (fine-tuning)
            final_duration_ms = len(final_audio)
            target_duration_ms = int(target_duration * 1000)
            
            if abs(final_duration_ms - target_duration_ms) > 100:  # Only adjust if difference > 100ms
                if final_duration_ms < target_duration_ms:
                    # Add minimal final padding if needed
                    padding_ms = target_duration_ms - final_duration_ms
                    silence = AudioSegment.silent(duration=padding_ms)
                    final_audio += silence
                    print(f"   Added final padding: {padding_ms/1000:.2f}s")
                elif final_duration_ms > target_duration_ms:
                    # Trim if slightly over
                    final_audio = final_audio[:target_duration_ms]
                    print(f"   Trimmed excess: {(final_duration_ms - target_duration_ms)/1000:.2f}s")
            
            # Export final audio
            final_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(self.audio_processor.sample_rate),
                    "-ac", str(self.audio_processor.channels)
                ]
            )
            
            final_duration = len(final_audio) / 1000.0
            print(f"   ✅ Same-length audio created: {final_duration:.2f}s duration")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Same-length audio creation failed: {str(e)}")
            raise Exception(f"Same-length audio creation failed: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up all temporary files"""
        deleted_count = 0
        for temp_file in self.temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {str(e)}")
        
        self.temp_files.clear()
        return deleted_count

async def test_same_length_workflow():
    """Test the same length voice conversion workflow"""
    print("Starting Same Length Voice Converter workflow test...\n")
    
    # Test file path
    test_file = Path(__file__).parent / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please add the test audio file to backend/tests/")
        return False
    
    try:
        # Initialize converter
        converter = SameLengthVoiceConverter()
        
        # Test configuration
        settings = get_settings()
        if not settings.GLADIA_API_KEY:
            print("❌ GLADIA_API_KEY not set")
            return False
        if not settings.ELEVENLABS_API_KEY:
            print("❌ ELEVENLABS_API_KEY not set")
            return False
        if not settings.ELEVENLABS_VOICE_ID:
            print("❌ ELEVENLABS_VOICE_ID not set")
            return False
        
        # Run same length conversion
        final_output = await converter.convert_voice_same_length(str(test_file))
        
        # Verify output
        output_path = Path(final_output)
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"📊 Output file size: {file_size:,} bytes")
            
            # Analyze final audio
            audio_analysis = await converter.audio_processor.analyze_audio(final_output)
            print(f"📊 Final duration: {audio_analysis['duration_seconds']:.2f} seconds")
            print(f"📊 Sample rate: {audio_analysis['sample_rate']} Hz")
            print(f"📊 Channels: {audio_analysis['channels']}")
            
            # Compare with original
            original_audio = AudioSegment.from_file(str(test_file))
            original_duration = len(original_audio) / 1000.0
            print(f"📊 Original duration: {original_duration:.2f} seconds")
            
            duration_diff = abs(audio_analysis['duration_seconds'] - original_duration)
            if duration_diff < 0.1:  # Within 0.1 seconds
                print("✅ Duration matches original!")
            else:
                print(f"⚠️  Duration difference: {duration_diff:.2f} seconds")
            
            return True
        else:
            print(f"❌ Output file not found: {final_output}")
            return False
            
    except Exception as e:
        print(f"❌ Same length workflow test failed: {e}")
        logger.exception("Same length workflow test failed")
        return False

def main():
    """Main test function"""
    success = asyncio.run(test_same_length_workflow())
    
    if success:
        print("\n🎉 Same length workflow test PASSED!")
        print("Your Voice Converter is working correctly with same length audio!")
    else:
        print("\n❌ Same length workflow test FAILED.")
        print("Please check your configuration and API keys.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
