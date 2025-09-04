"""
Complete Voice Converter workflow test
Processes all sentences with proper timing and silence gaps
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

class CompleteVoiceConverter:
    """Complete voice conversion workflow"""
    
    def __init__(self):
        self.gladia_service = GladiaService()
        self.elevenlabs_service = ElevenLabsService()
        self.audio_processor = AudioProcessor()
        self.settings = get_settings()
        self.temp_files = []  # Track temporary files for cleanup
    
    async def convert_voice(self, input_audio_path: str) -> str:
        """
        Convert voice in audio file with complete workflow
        
        Args:
            input_audio_path: Path to input audio file
            
        Returns:
            Path to final converted audio file (same name as original)
        """
        try:
            input_path = Path(input_audio_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
            
            print(f"🎵 Starting Voice Conversion")
            print(f"📁 Input file: {input_path}")
            print("=" * 60)
            
            # Step 1: Transcribe audio
            print("1. Transcribing audio...")
            transcription_result = await self.gladia_service.transcribe_audio(str(input_path))
            sentence_count = len(transcription_result.sentences)
            print(f"   ✅ Found {sentence_count} sentences")
            
            if sentence_count == 0:
                raise Exception("No sentences found in transcription")
            
            # Show all sentences with timing
            for i, sentence in enumerate(transcription_result.sentences):
                duration = sentence.end_time - sentence.start_time
                print(f"   📝 Sentence {i+1}: {sentence.text[:50]}... ({sentence.start_time:.2f}s - {sentence.end_time:.2f}s, {duration:.2f}s)")
            
            # Step 2: Process each sentence
            print(f"\n2. Processing all {sentence_count} sentences...")
            processed_segments = []
            
            for i, sentence in enumerate(transcription_result.sentences):
                print(f"   Processing sentence {i+1}/{sentence_count}: {sentence.text[:50]}...")
                
                # Generate voice clone for this sentence
                temp_cloned_path = await self.elevenlabs_service.generate_speech(
                    sentence.text,
                    self.settings.ELEVENLABS_VOICE_ID,
                    f"temp_sentence_{i}"
                )
                self.temp_files.append(temp_cloned_path)
                
                # Match timing to original sentence duration
                sentence_duration = sentence.end_time - sentence.start_time
                temp_matched_path = await self.audio_processor.match_timing(
                    temp_cloned_path,
                    sentence.start_time,
                    sentence.end_time,
                    f"temp_matched_{i}"
                )
                self.temp_files.append(temp_matched_path)
                
                processed_segments.append({
                    'audio_path': temp_matched_path,
                    'start_time': sentence.start_time,
                    'end_time': sentence.end_time,
                    'duration': sentence_duration
                })
                
                print(f"      ✅ Sentence {i+1} processed ({sentence_duration:.2f}s)")
            
            # Step 3: Create final audio with proper timing and silence gaps
            print(f"\n3. Creating final audio with timing gaps...")
            final_audio_path = await self._create_final_audio_with_gaps(
                processed_segments,
                transcription_result.sentences,
                input_path
            )
            
            # Step 4: Cleanup temporary files
            print(f"\n4. Cleaning up temporary files...")
            deleted_count = self._cleanup_temp_files()
            print(f"   ✅ Cleaned up {deleted_count} temporary files")
            
            print("\n" + "=" * 60)
            print("🎉 Voice conversion completed successfully!")
            print(f"📁 Final output: {final_audio_path}")
            
            return final_audio_path
            
        except Exception as e:
            logger.error(f"Voice conversion failed: {str(e)}")
            # Cleanup on error
            self._cleanup_temp_files()
            raise Exception(f"Voice conversion failed: {str(e)}")
    
    async def _create_final_audio_with_gaps(
        self, 
        processed_segments: List[dict], 
        sentences: List,
        input_path: Path
    ) -> str:
        """Create final audio with proper timing and silence gaps"""
        try:
            # Create output filename (same as input file name)
            output_path = Path(self.settings.OUTPUT_DIR) / input_path.name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get original audio to determine total duration
            original_audio = AudioSegment.from_file(str(input_path))
            original_duration = len(original_audio) / 1000.0
            
            # Start with empty audio
            final_audio = AudioSegment.empty()
            current_time = 0.0
            
            print(f"   Building final audio timeline (target: {original_duration:.2f}s)...")
            
            for i, (segment, sentence) in enumerate(zip(processed_segments, sentences)):
                # Add silence gap before this sentence (if needed)
                gap_duration = sentence.start_time - current_time
                if gap_duration > 0.01:  # Only add gap if > 10ms
                    silence_ms = int(gap_duration * 1000)
                    silence = AudioSegment.silent(duration=silence_ms)
                    final_audio += silence
                    print(f"      Added {gap_duration:.2f}s silence gap before sentence {i+1}")
                
                # Add the processed sentence audio
                sentence_audio = AudioSegment.from_file(segment['audio_path'])
                final_audio += sentence_audio
                print(f"      Added sentence {i+1} audio ({segment['duration']:.2f}s)")
                
                # Update current time
                current_time = sentence.end_time
            
            # Add final silence gap if original audio is longer
            final_gap = original_duration - current_time
            if final_gap > 0.01:
                silence_ms = int(final_gap * 1000)
                silence = AudioSegment.silent(duration=silence_ms)
                final_audio += silence
                print(f"      Added final {final_gap:.2f}s silence gap")
            
            # Export final audio with same properties as original
            final_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(original_audio.frame_rate),
                    "-ac", str(original_audio.channels)
                ]
            )
            
            final_duration = len(final_audio) / 1000.0
            print(f"   ✅ Final audio created: {final_duration:.2f}s duration")
            print(f"   📊 Original: {original_duration:.2f}s, Final: {final_duration:.2f}s")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Final audio creation failed: {str(e)}")
            raise Exception(f"Final audio creation failed: {str(e)}")
    
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

async def test_complete_workflow():
    """Test the complete voice conversion workflow"""
    print("Starting Complete Voice Converter workflow test...\n")
    
    # Test file path
    test_file = Path(__file__).parent / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please add the test audio file to backend/tests/")
        return False
    
    try:
        # Initialize converter
        converter = CompleteVoiceConverter()
        
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
        
        # Run complete conversion
        final_output = await converter.convert_voice(str(test_file))
        
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
            
            return True
        else:
            print(f"❌ Output file not found: {final_output}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        logger.exception("Complete workflow test failed")
        return False

def main():
    """Main test function"""
    success = asyncio.run(test_complete_workflow())
    
    if success:
        print("\n🎉 Complete workflow test PASSED!")
        print("Your Voice Converter is working correctly with all sentences!")
    else:
        print("\n❌ Complete workflow test FAILED.")
        print("Please check your configuration and API keys.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
