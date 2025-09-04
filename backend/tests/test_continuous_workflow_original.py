"""
Continuous Voice Converter workflow test
Processes all sentences without gaps for continuous audio output
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

class ContinuousVoiceConverter:
    """Continuous voice conversion workflow without gaps"""
    
    def __init__(self):
        self.gladia_service = GladiaService()
        self.elevenlabs_service = ElevenLabsService()
        self.audio_processor = AudioProcessor()
        self.settings = get_settings()
        self.temp_files = []  # Track temporary files for cleanup
    
    async def convert_voice_continuous(self, input_audio_path: str) -> str:
        """
        Convert voice in audio file with continuous workflow (no gaps)
        
        Args:
            input_audio_path: Path to input audio file
            
        Returns:
            Path to final converted audio file
        """
        try:
            input_path = Path(input_audio_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
            
            print(f"🎵 Starting Continuous Voice Conversion")
            print(f"📁 Input file: {input_path}")
            print("=" * 60)
            
            # Step 1: Transcribe audio
            print("1. Transcribing audio...")
            transcription_result = await self.gladia_service.transcribe_audio(str(input_path))
            sentence_count = len(transcription_result.sentences)
            print(f"   ✅ Found {sentence_count} sentences")
            
            if sentence_count == 0:
                raise Exception("No sentences found in transcription")
            
            # Step 2: Process each sentence (generate voice clones only)
            print(f"\n2. Processing {sentence_count} sentences...")
            temp_audio_files = []
            
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
                
                print(f"      ✅ Sentence {i+1} voice cloned")
            
            # Step 3: Create continuous final audio (no gaps)
            print(f"\n3. Creating continuous final audio...")
            final_audio_path = await self._create_continuous_audio(
                temp_audio_files,
                input_path
            )
            
            # Step 4: Cleanup temporary files
            print(f"\n4. Cleaning up temporary files...")
            deleted_count = self._cleanup_temp_files()
            print(f"   ✅ Cleaned up {deleted_count} temporary files")
            
            print("\n" + "=" * 60)
            print("🎉 Continuous voice conversion completed successfully!")
            print(f"📁 Final output: {final_audio_path}")
            
            return final_audio_path
            
        except Exception as e:
            logger.error(f"Continuous voice conversion failed: {str(e)}")
            # Cleanup on error
            self._cleanup_temp_files()
            raise Exception(f"Continuous voice conversion failed: {str(e)}")
    
    async def _create_continuous_audio(
        self, 
        temp_audio_files: List[str], 
        input_path: Path
    ) -> str:
        """Create final audio by concatenating all sentences without gaps"""
        try:
            # Create output filename (same as input but with _continuous suffix)
            output_filename = input_path.stem + "_continuous"
            output_path = Path(self.settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Start with empty audio
            final_audio = AudioSegment.empty()
            
            print(f"   Building continuous audio timeline...")
            
            for i, audio_file in enumerate(temp_audio_files):
                # Load and add each sentence audio directly (no gaps)
                sentence_audio = AudioSegment.from_file(audio_file)
                final_audio += sentence_audio
                
                duration = len(sentence_audio) / 1000.0
                print(f"      Added sentence {i+1} audio ({duration:.2f}s)")
            
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
            print(f"   ✅ Continuous audio created: {final_duration:.2f}s duration")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Continuous audio creation failed: {str(e)}")
            raise Exception(f"Continuous audio creation failed: {str(e)}")
    
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

async def test_continuous_workflow():
    """Test the continuous voice conversion workflow"""
    print("Starting Continuous Voice Converter workflow test...\n")
    
    # Test file path
    test_file = Path(__file__).parent / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please add the test audio file to backend/tests/")
        return False
    
    try:
        # Initialize converter
        converter = ContinuousVoiceConverter()
        
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
        
        # Run continuous conversion
        final_output = await converter.convert_voice_continuous(str(test_file))
        
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
        print(f"❌ Continuous workflow test failed: {e}")
        logger.exception("Continuous workflow test failed")
        return False

def main():
    """Main test function"""
    success = asyncio.run(test_continuous_workflow())
    
    if success:
        print("\n🎉 Continuous workflow test PASSED!")
        print("Your Voice Converter is working correctly with continuous audio!")
    else:
        print("\n❌ Continuous workflow test FAILED.")
        print("Please check your configuration and API keys.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
