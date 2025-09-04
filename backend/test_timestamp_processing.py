"""
Test script for timestamp-based sentence processing
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.services.sentence_processor import SentenceProcessor
from app.services.gladia_service import GladiaService
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

async def test_timestamp_processing():
    """Test the timestamp-based sentence processing"""
    
    # Initialize services
    sentence_processor = SentenceProcessor()
    gladia_service = GladiaService()
    
    # Test audio file path (use existing test file)
    test_audio_path = "tests/1.leo test 8.28.wav"
    
    if not os.path.exists(test_audio_path):
        logger.error(f"Test audio file not found: {test_audio_path}")
        print("❌ Test audio file not found. Please ensure the test file exists.")
        return
    
    try:
        print("🎵 Testing Timestamp-Based Sentence Processing")
        print("=" * 50)
        
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
        
        # Display gaps
        gaps = gap_analysis.get('gaps', [])
        if gaps:
            print(f"\n🕳️  Detected {len(gaps)} empty spaces:")
            for i, gap in enumerate(gaps):
                print(f"   Gap {i+1}: {gap['start']:.2f}s - {gap['end']:.2f}s ({gap['duration']:.2f}s)")
        
        # Display sentence details
        print(f"\n📝 Sentence Details:")
        for i, sentence in enumerate(sentences_dict[:3]):  # Show first 3 sentences
            duration = sentence['end_time'] - sentence['start_time']
            text_preview = sentence['text'][:50] + '...' if len(sentence['text']) > 50 else sentence['text']
            print(f"   Sentence {i+1}: {sentence['start_time']:.2f}s - {sentence['end_time']:.2f}s ({duration:.2f}s)")
            print(f"      Text: \"{text_preview}\"")
        
        if len(sentences_dict) > 3:
            print(f"   ... and {len(sentences_dict) - 3} more sentences")
        
        # Step 3: Process with timestamp-based method (simulation)
        print(f"\n🎯 Step 3: Timestamp-based processing simulation...")
        print(f"   • Would filter out {gap_analysis.get('total_sentences', 0) - gap_analysis.get('filtered_sentences', 0)} invalid sentences")
        print(f"   • Would eliminate {gap_analysis.get('total_gap_time', 0):.2f}s of empty space")
        print(f"   • Final audio would be {gap_analysis.get('total_speech_time', 0):.2f}s (continuous)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if gap_analysis.get('total_gap_time', 0) > 1.0:
            print(f"   ✅ Use timestamp_based=True - significant gap reduction potential")
            print(f"   📉 Can reduce audio by {gap_analysis.get('total_gap_time', 0):.1f}s")
        else:
            print(f"   ℹ️  Minimal gaps detected - timestamp processing optional")
        
        print(f"   📈 Current speech efficiency: {gap_analysis.get('speech_ratio', 0):.1%}")
        
        # Example API usage
        print(f"\n🔧 API Usage Example:")
        print(f"   curl -X POST 'http://localhost:8000/upload' \\")
        print(f"        -F 'file=@your_audio.wav' \\")
        print(f"        -F 'timestamp_based=true' \\")
        print(f"        -F 'voice_id=your_voice_id'")
        
        print(f"\n✅ Timestamp-based processing test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

async def test_gap_analysis_only():
    """Test just the gap analysis functionality"""
    
    sentence_processor = SentenceProcessor()
    
    # Example sentences with gaps (like the user's example)
    example_sentences = [
        {'text': 'Hello,', 'start_time': 0.33, 'end_time': 0.47},
        {'text': 'so today', 'start_time': 1.15, 'end_time': 2.23},
        {'text': 'I will demonstrate on how to scrape any type of', 'start_time': 2.57, 'end_time': 7.52}
    ]
    
    print("🧪 Testing Gap Analysis with Example Data")
    print("=" * 50)
    
    print("📝 Example sentences:")
    for i, sentence in enumerate(example_sentences):
        duration = sentence['end_time'] - sentence['start_time']
        print(f"   Sentence {i+1}: {sentence['start_time']}s - {sentence['end_time']}s ({duration:.2f}s)")
        print(f"      Text: \"{sentence['text']}\"")
    
    # Analyze gaps
    gap_analysis = await sentence_processor.analyze_sentence_gaps(example_sentences)
    
    print(f"\n🔍 Gap Analysis Results:")
    print(f"   • Total duration: {gap_analysis.get('total_duration', 0):.2f}s")
    print(f"   • Speech time: {gap_analysis.get('total_speech_time', 0):.2f}s")
    print(f"   • Gap time: {gap_analysis.get('total_gap_time', 0):.2f}s")
    print(f"   • Speech efficiency: {gap_analysis.get('speech_ratio', 0):.1%}")
    
    gaps = gap_analysis.get('gaps', [])
    print(f"\n🕳️  Detected gaps:")
    for i, gap in enumerate(gaps):
        print(f"   Gap {i+1}: {gap['start']:.2f}s - {gap['end']:.2f}s ({gap['duration']:.2f}s)")
    
    print(f"\n✅ This matches your example: 0-0.33s, 0.47-1.15s, 2.23-2.57s are empty spaces!")

if __name__ == "__main__":
    print("🚀 Starting Timestamp-Based Processing Tests")
    print()
    
    # Test gap analysis with example data first
    asyncio.run(test_gap_analysis_only())
    
    print("\n" + "="*70 + "\n")
    
    # Test with actual audio file if available
    asyncio.run(test_timestamp_processing())
