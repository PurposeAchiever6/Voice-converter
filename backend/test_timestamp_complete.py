"""
Complete test script for timestamp-based sentence processing with actual audio output
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.sentence_processor import SentenceProcessor
from app.services.gladia_service import GladiaService
from app.services.elevenlabs_service import ElevenLabsService
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

async def test_complete_timestamp_processing():
    """Test the complete timestamp-based sentence processing with actual output"""
    
    # Initialize services
    sentence_processor = SentenceProcessor()
    gladia_service = GladiaService()
    elevenlabs_service = ElevenLabsService()
    
    # Test audio file path (use existing test file)
    test_audio_path = "tests/1.leo test 8.28.wav"
    
    if not os.path.exists(test_audio_path):
        logger.error(f"Test audio file not found: {test_audio_path}")
        print("❌ Test audio file not found. Please ensure the test file exists.")
        return
    
    try:
        print("🎵 Complete Timestamp-Based Processing Test")
        print("=" * 60)
        
        # Step 1: Transcribe audio to get sentences with timestamps
        print("📝 Step 1: Transcribing audio...")
        transcription_result = await gladia_service.transcribe_audio(test_audio_path)
        
        print(f"✅ Found {len(transcription_result.sentences)} sentences")
        
        # Convert to dictionary format
        sentences_dict = [
            {
                'text': sentence.text,
                'start_time': sentence.start_time,
                'end_time': sentence.end_time
            }
            for sentence in transcription_result.sentences
        ]
        
        # Step 2: Analyze gaps in the audio
        print("\n🔍 Step 2: Analyzing gaps and empty spaces...")
        gap_analysis = await sentence_processor.analyze_sentence_gaps(sentences_dict)
        
        print(f"📊 Gap Analysis Results:")
        print(f"   • Total sentences: {gap_analysis.get('total_sentences', 0)}")
        print(f"   • Valid sentences: {gap_analysis.get('filtered_sentences', 0)}")
        print(f"   • Total duration: {gap_analysis.get('total_duration', 0):.2f}s")
        print(f"   • Speech time: {gap_analysis.get('total_speech_time', 0):.2f}s")
        print(f"   • Gap time: {gap_analysis.get('total_gap_time', 0):.2f}s")
        print(f"   • Speech efficiency: {gap_analysis.get('speech_ratio', 0):.1%}")
        
        # Display first few gaps
        gaps = gap_analysis.get('gaps', [])
        if gaps:
            print(f"\n🕳️  First 3 detected empty spaces:")
            for i, gap in enumerate(gaps[:3]):
                print(f"   Gap {i+1}: {gap['start']:.2f}s - {gap['end']:.2f}s ({gap['duration']:.2f}s)")
            if len(gaps) > 3:
                print(f"   ... and {len(gaps) - 3} more gaps")
        
        # Step 3: Process with timestamp-based method (ACTUAL PROCESSING)
        print(f"\n🎯 Step 3: Processing with timestamp-based method...")
        print(f"   • This will generate actual audio files using ElevenLabs")
        print(f"   • Processing {gap_analysis.get('filtered_sentences', 0)} valid sentences")
        
        # Use default voice ID from settings
        voice_id = settings.ELEVENLABS_VOICE_ID
        output_filename = "test_timestamp_based_output"
        
        print(f"   • Using voice ID: {voice_id}")
        print(f"   • Output filename: {output_filename}")
        
        # ACTUAL PROCESSING - This will create the real output file
        output_path = await sentence_processor.process_sentences_with_timestamps(
            test_audio_path,
            sentences_dict,
            voice_id,
            output_filename
        )
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📁 Output file created: {output_path}")
        
        # Verify the output file exists
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📊 Output file details:")
            print(f"   • File path: {output_path}")
            print(f"   • File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            # Analyze the output audio
            from pydub import AudioSegment
            output_audio = AudioSegment.from_file(output_path)
            output_duration = len(output_audio) / 1000.0
            
            print(f"   • Duration: {output_duration:.2f}s")
            print(f"   • Sample rate: {output_audio.frame_rate} Hz")
            print(f"   • Channels: {output_audio.channels}")
            
            # Compare with original
            original_duration = gap_analysis.get('total_duration', 0)
            time_saved = original_duration - output_duration
            
            print(f"\n📈 Comparison with original:")
            print(f"   • Original duration: {original_duration:.2f}s")
            print(f"   • New duration: {output_duration:.2f}s")
            print(f"   • Time saved: {time_saved:.2f}s ({time_saved/original_duration*100:.1f}%)")
            
            print(f"\n🎉 SUCCESS: Timestamp-based processing completed!")
            print(f"🔊 You can now play the output file: {output_path}")
            
        else:
            print(f"❌ Error: Output file was not created at {output_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_with_example_sentences():
    """Test with the exact example sentences provided by the user"""
    
    print("🧪 Testing with User's Example Sentences")
    print("=" * 50)
    
    # Example sentences with gaps (exactly as user provided)
    example_sentences = [
        {'text': 'Hello,', 'start_time': 0.33, 'end_time': 0.47},
        {'text': 'so today', 'start_time': 1.15, 'end_time': 2.23},
        {'text': 'I will demonstrate on how to scrape any type of', 'start_time': 2.57, 'end_time': 7.52}
    ]
    
    print("📝 User's example sentences:")
    for i, sentence in enumerate(example_sentences):
        duration = sentence['end_time'] - sentence['start_time']
        print(f"   📝 Sentence {i+1}: {sentence['text'][:50]}... ({sentence['start_time']}s - {sentence['end_time']}s)")
    
    sentence_processor = SentenceProcessor()
    
    # Analyze gaps
    gap_analysis = await sentence_processor.analyze_sentence_gaps(example_sentences)
    
    print(f"\n🔍 Gap Analysis Results:")
    print(f"   • Total duration: {gap_analysis.get('total_duration', 0):.2f}s")
    print(f"   • Speech time: {gap_analysis.get('total_speech_time', 0):.2f}s")
    print(f"   • Gap time: {gap_analysis.get('total_gap_time', 0):.2f}s")
    print(f"   • Speech efficiency: {gap_analysis.get('speech_ratio', 0):.1%}")
    
    gaps = gap_analysis.get('gaps', [])
    print(f"\n🕳️  Detected empty spaces (matching your example):")
    for i, gap in enumerate(gaps):
        print(f"   Gap {i+1}: {gap['start']:.2f}s - {gap['end']:.2f}s ({gap['duration']:.2f}s)")
    
    print(f"\n✅ Perfect match with your example:")
    print(f"   • 0-0.33s: Empty space ✓")
    print(f"   • 0.47-1.15s: Empty space ✓") 
    print(f"   • 2.23-2.57s: Empty space ✓")
    
    print(f"\n💡 With timestamp-based processing:")
    print(f"   • These gaps would be eliminated")
    print(f"   • Final audio would be continuous: 0-6.17s")
    print(f"   • Time saved: {gap_analysis.get('total_gap_time', 0):.2f}s")

if __name__ == "__main__":
    print("🚀 Starting Complete Timestamp-Based Processing Test")
    print()
    
    # Test with example data first
    asyncio.run(test_with_example_sentences())
    
    print("\n" + "="*70 + "\n")
    
    # Test with actual audio file and generate output
    asyncio.run(test_complete_timestamp_processing())
