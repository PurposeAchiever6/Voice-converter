"""
Comprehensive test for all three voice conversion modes
"""
import asyncio
import sys
from pathlib import Path
from pydub import AudioSegment

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_complete_workflow import CompleteVoiceConverter
from tests.test_continuous_workflow import ContinuousVoiceConverter
from tests.test_same_length_workflow import SameLengthVoiceConverter
from app.services.audio_processor import AudioProcessor
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_all_modes():
    """Test all three voice conversion modes"""
    print("🎵 Testing All Voice Conversion Modes")
    print("=" * 80)
    
    # Test file path
    test_file = Path("tests/1.leo test 8.28.wav")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Using test file: {test_file}")
    
    # Get original audio info
    original_audio = AudioSegment.from_file(str(test_file))
    original_duration = len(original_audio) / 1000.0
    original_size = test_file.stat().st_size
    
    print(f"📊 Original audio: {original_duration:.2f}s, {original_size:,} bytes")
    print()
    
    try:
        audio_processor = AudioProcessor()
        results = {}
        
        # Test 1: Original mode (with timing gaps)
        print("1. Testing ORIGINAL mode (with timing gaps)...")
        print("-" * 60)
        
        original_converter = CompleteVoiceConverter()
        original_output = await original_converter.convert_voice(str(test_file))
        
        # Analyze original output
        original_analysis = await audio_processor.analyze_audio(original_output)
        original_output_duration = original_analysis['duration_seconds']
        original_output_size = Path(original_output).stat().st_size
        
        results['original'] = {
            'duration': original_output_duration,
            'size': original_output_size,
            'path': original_output
        }
        
        print(f"   ✅ Original mode completed")
        print(f"   📊 Duration: {original_output_duration:.2f}s")
        print(f"   📊 File size: {original_output_size:,} bytes")
        print()
        
        # Test 2: Continuous mode (no gaps, shorter)
        print("2. Testing CONTINUOUS mode (no gaps, shorter)...")
        print("-" * 60)
        
        continuous_converter = ContinuousVoiceConverter()
        continuous_output = await continuous_converter.convert_voice_continuous(str(test_file))
        
        # Analyze continuous output
        continuous_analysis = await audio_processor.analyze_audio(continuous_output)
        continuous_duration = continuous_analysis['duration_seconds']
        continuous_size = Path(continuous_output).stat().st_size
        
        results['continuous'] = {
            'duration': continuous_duration,
            'size': continuous_size,
            'path': continuous_output
        }
        
        print(f"   ✅ Continuous mode completed")
        print(f"   📊 Duration: {continuous_duration:.2f}s")
        print(f"   📊 File size: {continuous_size:,} bytes")
        print()
        
        # Test 3: Same length mode (no gaps, same duration)
        print("3. Testing SAME LENGTH mode (no gaps, same duration)...")
        print("-" * 60)
        
        same_length_converter = SameLengthVoiceConverter()
        same_length_output = await same_length_converter.convert_voice_same_length(str(test_file))
        
        # Analyze same length output
        same_length_analysis = await audio_processor.analyze_audio(same_length_output)
        same_length_duration = same_length_analysis['duration_seconds']
        same_length_size = Path(same_length_output).stat().st_size
        
        results['same_length'] = {
            'duration': same_length_duration,
            'size': same_length_size,
            'path': same_length_output
        }
        
        print(f"   ✅ Same length mode completed")
        print(f"   📊 Duration: {same_length_duration:.2f}s")
        print(f"   📊 File size: {same_length_size:,} bytes")
        print()
        
        # Comparison and Analysis
        print("4. COMPREHENSIVE COMPARISON")
        print("=" * 80)
        
        print("📊 DURATION COMPARISON:")
        print(f"   Original audio:     {original_duration:.2f}s")
        print(f"   Original mode:      {original_output_duration:.2f}s")
        print(f"   Continuous mode:    {continuous_duration:.2f}s")
        print(f"   Same length mode:   {same_length_duration:.2f}s")
        print()
        
        print("📊 FILE SIZE COMPARISON:")
        print(f"   Original audio:     {original_size:,} bytes")
        print(f"   Original mode:      {original_output_size:,} bytes")
        print(f"   Continuous mode:    {continuous_size:,} bytes")
        print(f"   Same length mode:   {same_length_size:,} bytes")
        print()
        
        print("📊 EFFICIENCY ANALYSIS:")
        
        # Continuous vs Original
        continuous_time_saved = original_output_duration - continuous_duration
        continuous_time_percent = (continuous_time_saved / original_output_duration) * 100
        continuous_size_saved = original_output_size - continuous_size
        continuous_size_percent = (continuous_size_saved / original_output_size) * 100
        
        print(f"   Continuous vs Original mode:")
        print(f"     Time saved: {continuous_time_saved:.2f}s ({continuous_time_percent:.1f}%)")
        print(f"     Size saved: {continuous_size_saved:,} bytes ({continuous_size_percent:.1f}%)")
        print()
        
        # Same length vs Original duration match
        duration_diff = abs(same_length_duration - original_duration)
        duration_match = duration_diff < 0.1  # Within 0.1 seconds
        
        print(f"   Same length vs Original audio:")
        print(f"     Duration difference: {duration_diff:.2f}s")
        print(f"     Duration match: {'✅ YES' if duration_match else '❌ NO'}")
        print()
        
        print("🎯 MODE RECOMMENDATIONS:")
        print("=" * 80)
        
        print("📌 Use ORIGINAL mode when:")
        print("   • You need exact timing synchronization with video")
        print("   • Preserving original speech patterns is critical")
        print("   • Maintaining lip-sync or other timing dependencies")
        print()
        
        print("📌 Use CONTINUOUS mode when:")
        print("   • You want the most compact, efficient audio")
        print("   • Natural flowing speech without pauses")
        print("   • Storage space and bandwidth are concerns")
        print("   • Creating podcasts, audiobooks, or voice-overs")
        print()
        
        print("📌 Use SAME LENGTH mode when:")
        print("   • You need to eliminate gaps but maintain original duration")
        print("   • Replacing audio in existing media with fixed timing")
        print("   • Maintaining synchronization while improving speech flow")
        print("   • Best of both worlds: no gaps + same duration")
        print()
        
        # Validation
        print("✅ VALIDATION RESULTS:")
        print("=" * 80)
        
        all_passed = True
        
        # Check if all files exist
        for mode, data in results.items():
            if Path(data['path']).exists():
                print(f"   ✅ {mode.title()} mode output file exists")
            else:
                print(f"   ❌ {mode.title()} mode output file missing")
                all_passed = False
        
        # Check duration requirements
        if duration_match:
            print(f"   ✅ Same length mode maintains original duration")
        else:
            print(f"   ❌ Same length mode duration mismatch")
            all_passed = False
        
        if continuous_duration < original_output_duration:
            print(f"   ✅ Continuous mode is shorter than original mode")
        else:
            print(f"   ❌ Continuous mode should be shorter")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        logger.exception("Comprehensive test failed")
        return False

def main():
    """Main test function"""
    print("Starting comprehensive Voice Converter test...\n")
    
    success = asyncio.run(test_all_modes())
    
    if success:
        print("\n🎉 ALL MODES TEST PASSED!")
        print("All three voice conversion modes are working correctly!")
        print("\nYou now have three options:")
        print("1. Original mode - preserves timing gaps")
        print("2. Continuous mode - eliminates gaps, shorter duration")
        print("3. Same length mode - eliminates gaps, maintains duration")
    else:
        print("\n❌ Some modes failed.")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
