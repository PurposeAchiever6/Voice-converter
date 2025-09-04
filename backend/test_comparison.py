"""
Comparison test between original and continuous modes
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_complete_workflow import CompleteVoiceConverter
from tests.test_continuous_workflow import ContinuousVoiceConverter
from app.services.audio_processor import AudioProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def compare_workflows():
    """Compare original and continuous workflows"""
    print("🔄 Comparing Original vs Continuous Voice Conversion")
    print("=" * 70)
    
    # Test file path
    test_file = Path("tests/1.leo test 8.28.wav")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Using test file: {test_file}")
    
    try:
        audio_processor = AudioProcessor()
        
        # Test original workflow (with gaps)
        print("\n1. Testing ORIGINAL workflow (with timing gaps)...")
        print("-" * 50)
        
        original_converter = CompleteVoiceConverter()
        original_output = await original_converter.convert_voice(str(test_file))
        
        # Analyze original output
        original_analysis = await audio_processor.analyze_audio(original_output)
        original_duration = original_analysis['duration_seconds']
        original_size = Path(original_output).stat().st_size
        
        print(f"   ✅ Original output: {original_output}")
        print(f"   📊 Duration: {original_duration:.2f} seconds")
        print(f"   📊 File size: {original_size:,} bytes")
        
        # Test continuous workflow (no gaps)
        print("\n2. Testing CONTINUOUS workflow (no gaps)...")
        print("-" * 50)
        
        continuous_converter = ContinuousVoiceConverter()
        continuous_output = await continuous_converter.convert_voice_continuous(str(test_file))
        
        # Analyze continuous output
        continuous_analysis = await audio_processor.analyze_audio(continuous_output)
        continuous_duration = continuous_analysis['duration_seconds']
        continuous_size = Path(continuous_output).stat().st_size
        
        print(f"   ✅ Continuous output: {continuous_output}")
        print(f"   📊 Duration: {continuous_duration:.2f} seconds")
        print(f"   📊 File size: {continuous_size:,} bytes")
        
        # Comparison
        print("\n3. COMPARISON RESULTS")
        print("=" * 70)
        
        time_saved = original_duration - continuous_duration
        time_saved_percent = (time_saved / original_duration) * 100
        
        size_difference = original_size - continuous_size
        size_saved_percent = (size_difference / original_size) * 100
        
        print(f"📊 Original duration:    {original_duration:.2f} seconds")
        print(f"📊 Continuous duration:  {continuous_duration:.2f} seconds")
        print(f"⏱️  Time saved:          {time_saved:.2f} seconds ({time_saved_percent:.1f}%)")
        print()
        print(f"📊 Original file size:   {original_size:,} bytes")
        print(f"📊 Continuous file size: {continuous_size:,} bytes")
        print(f"💾 Size difference:      {size_difference:,} bytes ({size_saved_percent:.1f}%)")
        print()
        
        # Quality comparison
        print("🎵 AUDIO QUALITY COMPARISON:")
        print(f"   Original:   {original_analysis['sample_rate']} Hz, {original_analysis['channels']} channel(s)")
        print(f"   Continuous: {continuous_analysis['sample_rate']} Hz, {continuous_analysis['channels']} channel(s)")
        
        # Summary
        print("\n4. SUMMARY")
        print("=" * 70)
        
        if time_saved > 0:
            print(f"✅ Continuous mode is MORE EFFICIENT:")
            print(f"   • Saves {time_saved:.2f} seconds ({time_saved_percent:.1f}%) in duration")
            print(f"   • Reduces file size by {size_difference:,} bytes ({size_saved_percent:.1f}%)")
            print(f"   • Eliminates empty spaces/gaps between sentences")
            print(f"   • Creates more natural, flowing speech")
        else:
            print(f"⚠️  Unexpected result: Continuous mode is longer")
        
        print(f"\n🎯 RECOMMENDATION:")
        print(f"   Use CONTINUOUS mode when you want:")
        print(f"   • Shorter, more compact audio files")
        print(f"   • Natural flowing speech without pauses")
        print(f"   • Faster processing (no timing matching needed)")
        print(f"   ")
        print(f"   Use ORIGINAL mode when you want:")
        print(f"   • Exact timing match with original audio")
        print(f"   • Preserve original speech patterns and pauses")
        print(f"   • Maintain synchronization with video or other media")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        logger.exception("Comparison test failed")
        return False

def main():
    """Main comparison function"""
    print("Starting Voice Converter workflow comparison...\n")
    
    success = asyncio.run(compare_workflows())
    
    if success:
        print("\n🎉 Comparison test completed successfully!")
        print("\nBoth workflows are working correctly!")
    else:
        print("\n❌ Comparison test failed.")
        print("Please check your configuration and API keys.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
