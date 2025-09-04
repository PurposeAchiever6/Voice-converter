"""
Test workflow for Voice Converter - Continuous mode without gaps
Creates a seamless audio file by concatenating sentences without empty spaces
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.gladia_service import GladiaService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.audio_processor import AudioProcessor
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ContinuousVoiceConverter:
    """Voice converter that creates continuous audio without gaps"""
    
    def __init__(self):
        self.gladia_service = GladiaService()
        self.elevenlabs_service = ElevenLabsService()
        self.audio_processor = AudioProcessor()
        self.settings = get_settings()
    
    async def convert_voice_continuous(self, input_path: str) -> str:
        """
        Convert voice to continuous audio without gaps
        
        Args:
            input_path: Path to input audio file
            
        Returns:
            Path to output continuous audio file
        """
        try:
            print("🎵 Starting Continuous Voice Conversion (No Gaps)")
            print(f"📁 Input file: {input_path}")
            print("=" * 60)
            
            # Step 1: Transcribe audio
            print("1. Transcribing audio...")
            transcription_result = await self.gladia_service.transcribe_audio(input_path)
            print(f"   ✅ Found {len(transcription_result.sentences)} sentences")
            
            # Step 2: Filter valid sentences (remove empty spaces)
            print("\n2. Filtering valid sentences...")
            valid_sentences = self._filter_valid_sentences(transcription_result.sentences)
            print(f"   ✅ Filtered to {len(valid_sentences)} valid sentences")
            
            # Show sentence details
            for i, sentence in enumerate(valid_sentences[:5]):  # Show first 5
                duration = sentence.end_time - sentence.start_time
                print(f"   📝 Sentence {i+1}: {sentence.text[:50]}... ({duration:.2f}s)")
            
            if len(valid_sentences) > 5:
                print(f"   📝 ... and {len(valid_sentences) - 5} more sentences")
            
            # Step 3: Generate continuous audio
            print(f"\n3. Processing {len(valid_sentences)} sentences continuously...")
            temp_files = []
            
            for i, sentence in enumerate(valid_sentences):
                print(f"   Processing sentence {i+1}/{len(valid_sentences)}: {sentence.text[:50]}...")
                
                # Generate voice clone for this sentence
                cloned_audio_path = await self.elevenlabs_service.generate_speech(
                    sentence.text,
                    self.settings.ELEVENLABS_VOICE_ID,
                    f"temp_continuous_{i}"
                )
                
                temp_files.append(cloned_audio_path)
                
                # Calculate original duration for comparison
                original_duration = sentence.end_time - sentence.start_time
                
                # Get actual duration of generated audio
                analysis = await self.audio_processor.analyze_audio(cloned_audio_path)
                generated_duration = analysis['duration_seconds']
                
                print(f"      ✅ Sentence {i+1} processed ({generated_duration:.2f}s vs {original_duration:.2f}s original)")
            
            # Step 4: Concatenate all audio files continuously
            print(f"\n4. Creating continuous audio from {len(temp_files)} segments...")
            
            # Get base filename for output
            input_filename = Path(input_path).stem
            output_filename = f"{input_filename}_continuous_no_gaps"
            
            final_output_path = await self.audio_processor.concatenate_audio(
                temp_files,
                output_filename
            )
            
            # Step 5: Analyze final output
            print("\n5. Analyzing final output...")
            final_analysis = await self.audio_processor.analyze_audio(final_output_path)
            final_duration = final_analysis['duration_seconds']
            
            # Calculate original speech time (without gaps)
            original_speech_time = sum(s.end_time - s.start_time for s in valid_sentences)
            original_total_time = transcription_result.sentences[-1].end_time if transcription_result.sentences else 0
            
            print(f"   📊 Final duration: {final_duration:.2f} seconds")
            print(f"   📊 Original speech time: {original_speech_time:.2f} seconds")
            print(f"   📊 Original total time: {original_total_time:.2f} seconds")
            print(f"   📊 Time saved: {original_total_time - final_duration:.2f} seconds")
            print(f"   📊 Compression ratio: {final_duration/original_total_time:.1%}")
            
            # Step 6: Cleanup temporary files
            print(f"\n6. Cleaning up {len(temp_files)} temporary files...")
            await self._cleanup_temp_files(temp_files)
            print("   ✅ Cleanup completed")
            
            print("\n" + "=" * 60)
            print("🎉 Continuous voice conversion completed successfully!")
            print(f"📁 Final output: {final_output_path}")
            
            return final_output_path
            
        except Exception as e:
            logger.error(f"Continuous voice conversion failed: {str(e)}")
            raise Exception(f"Continuous voice conversion failed: {str(e)}")
    
    def _filter_valid_sentences(self, sentences) -> list:
        """
        Filter out sentences that are too short or have minimal content
        
        Args:
            sentences: List of sentence objects from transcription
            
        Returns:
            List of valid sentences
        """
        valid_sentences = []
        
        for sentence in sentences:
            # Calculate duration
            duration = sentence.end_time - sentence.start_time
            
            # Skip very short sentences (likely artifacts)
            if duration < 0.1:  # Less than 100ms
                logger.debug(f"Skipping short sentence: {sentence.text[:30]}... ({duration:.3f}s)")
                continue
            
            # Skip sentences with minimal text content
            text = sentence.text.strip()
            if len(text) < 2:  # Less than 2 characters
                logger.debug(f"Skipping minimal text: '{text}' ({duration:.3f}s)")
                continue
            
            # Skip sentences that are just punctuation or whitespace
            if not any(c.isalnum() for c in text):
                logger.debug(f"Skipping non-alphanumeric: '{text}' ({duration:.3f}s)")
                continue
            
            valid_sentences.append(sentence)
        
        logger.info(f"Filtered {len(sentences)} sentences to {len(valid_sentences)} valid sentences")
        return valid_sentences
    
    async def _cleanup_temp_files(self, temp_files: list):
        """Clean up temporary files"""
        try:
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up: {temp_file}")
            
            logger.info(f"Cleaned up {len(temp_files)} temporary files")
            
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")

async def test_continuous_no_gaps():
    """Test the continuous voice conversion without gaps"""
    print("Starting Continuous Voice Converter test (No Gaps)...\n")
    
    # Test file path
    test_file = Path(__file__).parent / "tests" / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure the test audio file exists at backend/tests/1.leo test 8.28.wav")
        return False
    
    try:
        # Initialize converter
        converter = ContinuousVoiceConverter()
        
        # Convert voice
        output_path = await converter.convert_voice_continuous(str(test_file))
        
        # Verify output
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"\n📊 Output file size: {file_size:,} bytes")
            
            # Analyze output audio
            audio_processor = AudioProcessor()
            analysis = await audio_processor.analyze_audio(output_path)
            print(f"📊 Sample rate: {analysis['sample_rate']} Hz")
            print(f"📊 Channels: {analysis['channels']}")
            print(f"📊 Sample width: {analysis['sample_width']} bytes")
            
            print(f"\n🎉 Test PASSED! Continuous audio created successfully.")
            print(f"📁 Output: {output_path}")
            return True
        else:
            print(f"\n❌ Test FAILED! Output file not found: {output_path}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test FAILED! Error: {str(e)}")
        logger.exception("Continuous conversion test failed")
        return False

def main():
    """Main test function"""
    success = asyncio.run(test_continuous_no_gaps())
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
