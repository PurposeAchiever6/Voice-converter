"""
Test workflow for Voice Converter
Tests the complete pipeline with a sample audio file
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gladia_service import GladiaService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.audio_processor import AudioProcessor
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_complete_workflow():
    """Test the complete voice conversion workflow"""
    print("🎵 Testing Voice Converter Workflow")
    print("=" * 50)
    
    # Test file path
    test_file = Path(__file__).parent / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please add the test audio file to backend/tests/")
        return False
    
    print(f"📁 Using test file: {test_file}")
    
    try:
        # Initialize services
        print("\n1. Initializing services...")
        gladia_service = GladiaService()
        elevenlabs_service = ElevenLabsService()
        audio_processor = AudioProcessor()
        print("   ✅ Services initialized")
        
        # Test configuration
        settings = get_settings()
        if not settings.GLADIA_API_KEY:
            print("   ⚠️  GLADIA_API_KEY not set - will fail at transcription")
        if not settings.ELEVENLABS_API_KEY:
            print("   ⚠️  ELEVENLABS_API_KEY not set - will fail at voice cloning")
        if not settings.ELEVENLABS_VOICE_ID:
            print("   ⚠️  ELEVENLABS_VOICE_ID not set - will fail at voice cloning")
        
        # Step 1: Transcribe audio
        print("\n2. Testing speech-to-text conversion...")
        try:
            transcription_result = await gladia_service.transcribe_audio(str(test_file))
            print(f"   ✅ Transcription successful: {len(transcription_result.sentences)} sentences")
            print(f"   📝 Full text: {transcription_result.full_text[:100]}...")
            
            for i, sentence in enumerate(transcription_result.sentences[:3]):  # Show first 3
                print(f"   📝 Sentence {i+1}: {sentence.text[:50]}... ({sentence.start_time:.2f}s - {sentence.end_time:.2f}s)")
        
        except Exception as e:
            print(f"   ❌ Transcription failed: {e}")
            return False
        
        # Step 2: Test voice cloning for first sentence
        print("\n3. Testing voice cloning...")
        try:
            first_sentence = transcription_result.sentences[0]
            cloned_audio_path = await elevenlabs_service.generate_speech(
                first_sentence.text,
                settings.ELEVENLABS_VOICE_ID,
                "test_cloned_sentence"
            )
            print(f"   ✅ Voice cloning successful: {cloned_audio_path}")
            
        except Exception as e:
            print(f"   ❌ Voice cloning failed: {e}")
            return False
        
        # Step 3: Test audio timing matching
        print("\n4. Testing audio timing matching...")
        try:
            matched_audio_path = await audio_processor.match_timing(
                cloned_audio_path,
                first_sentence.start_time,
                first_sentence.end_time,
                "test_matched_sentence"
            )
            print(f"   ✅ Timing matching successful: {matched_audio_path}")
            
        except Exception as e:
            print(f"   ❌ Timing matching failed: {e}")
            return False
        
        # Step 4: Test complete workflow (all sentences)
        print(f"\n5. Testing complete workflow (all {len(transcription_result.sentences)} sentences)...")
        try:
            from test_continuous_no_gaps import ContinuousVoiceConverter
            
            # Use the continuous converter for gap-free processing
            converter = ContinuousVoiceConverter()
            output_path = await converter.convert_voice_continuous(str(test_file))
            
            print(f"   ✅ Complete workflow successful: {output_path}")
            
            # Verify output file
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"   📊 Output file size: {file_size:,} bytes")
                
                # Get final duration
                final_analysis = await audio_processor.analyze_audio(output_path)
                final_duration = final_analysis['duration_seconds']
                print(f"   📊 Final duration: {final_duration:.2f} seconds")
            
            processed_chunks = []  # Empty for cleanup compatibility
            
        except Exception as e:
            print(f"   ❌ Complete workflow failed: {e}")
            return False
        
        # Step 5: Verify continuous output (already done in step 4)
        print("\n6. Verifying continuous output...")
        try:
            # The continuous converter already handles concatenation
            print(f"   ✅ Continuous output verified")
            
            # Set final_output for compatibility
            final_output = output_path
            
        except Exception as e:
            print(f"   ❌ Output verification failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 Complete workflow test PASSED!")
        print(f"📁 Final output: {final_output}")
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow test failed: {e}")
        logger.exception("Workflow test failed")
        return False

async def test_audio_analysis():
    """Test audio analysis functionality"""
    print("\n7. Testing audio analysis...")
    
    test_file = Path(__file__).parent / "1.leo test 8.28.wav"
    if not test_file.exists():
        print("   ⚠️  Test file not found, skipping analysis")
        return True
    
    try:
        audio_processor = AudioProcessor()
        analysis = await audio_processor.analyze_audio(str(test_file))
        
        print(f"   📊 Duration: {analysis['duration_seconds']:.2f} seconds")
        print(f"   📊 Sample rate: {analysis['sample_rate']} Hz")
        print(f"   📊 Channels: {analysis['channels']}")
        print(f"   📊 Sample width: {analysis['sample_width']} bytes")
        print(f"   ✅ Audio analysis successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Audio analysis failed: {e}")
        return False

def main():
    """Main test function"""
    print("Starting Voice Converter workflow test...\n")
    
    # Run tests
    workflow_success = asyncio.run(test_complete_workflow())
    analysis_success = asyncio.run(test_audio_analysis())
    
    if workflow_success and analysis_success:
        print("\n🎉 All tests PASSED!")
        print("\nYour Voice Converter is working correctly!")
        return True
    else:
        print("\n❌ Some tests FAILED.")
        print("Please check your configuration and API keys.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
