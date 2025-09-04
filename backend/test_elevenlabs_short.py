#!/usr/bin/env python3
"""
ElevenLabs Test Script - Generate short audio sample (low credit usage)
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.elevenlabs_service import ElevenLabsService
from app.utils.config import get_settings, validate_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_elevenlabs_short():
    """Test ElevenLabs audio generation with minimal credit usage"""
    
    try:
        # Validate settings
        print("🔧 Validating configuration...")
        validate_settings()
        settings = get_settings()
        
        print(f"✅ API Key: {settings.ELEVENLABS_API_KEY[:20]}...")
        print(f"✅ Voice ID: {settings.ELEVENLABS_VOICE_ID}")
        print(f"✅ Model ID: {settings.ELEVENLABS_MODEL_ID}")
        
        # Initialize ElevenLabs service
        print("\n🚀 Initializing ElevenLabs service...")
        elevenlabs_service = ElevenLabsService()
        
        # Test API connection
        print("🔍 Testing API connection...")
        is_healthy = await elevenlabs_service.health_check()
        if not is_healthy:
            raise Exception("ElevenLabs API health check failed")
        print("✅ API connection successful!")
        
        # Get user info to check remaining credits
        print("\n👤 Checking account credits...")
        try:
            user_info = await elevenlabs_service.get_user_info()
            subscription = user_info.get('subscription', {})
            if subscription:
                character_count = subscription.get('character_count', 0)
                character_limit = subscription.get('character_limit', 0)
                remaining = character_limit - character_count
                print(f"📈 Credits remaining: {remaining}")
                
                if remaining < 50:
                    print("⚠️  Warning: Very low credits remaining!")
                    print("💡 Consider using a shorter text or waiting for quota reset.")
        except Exception as e:
            print(f"⚠️  Could not get user info: {e}")
        
        # Use very short text to minimize credit usage
        # This should be about 2-3 seconds of audio and use minimal credits
        test_text = "Hello, this is a test."
        
        print(f"\n📝 Test text ({len(test_text.split())} words, {len(test_text)} characters):")
        print(f"'{test_text}'")
        print(f"💰 Estimated credits needed: ~{len(test_text) * 7} (rough estimate)")
        
        # Generate audio
        print("\n🎵 Generating audio sample...")
        output_filename = "elevenlabs_test_short_sample"
        
        try:
            audio_path = await elevenlabs_service.generate_speech(
                text=test_text,
                voice_id=settings.ELEVENLABS_VOICE_ID,
                output_filename=output_filename
            )
            
            print(f"✅ Audio generated successfully!")
            print(f"📁 Output file: {audio_path}")
            
            # Check if file exists and get size
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # Estimate duration (rough calculation for WAV files)
                estimated_duration = file_size / (22050 * 1 * 2)  # 2 bytes per sample for 16-bit
                print(f"⏱️  Estimated duration: {estimated_duration:.1f} seconds")
                
                print(f"\n🎉 SUCCESS! Audio sample generated at: {audio_path}")
                print(f"🔊 You can play this file to test the voice quality.")
                
                # Check credits after generation
                print("\n💰 Checking remaining credits after generation...")
                try:
                    user_info_after = await elevenlabs_service.get_user_info()
                    subscription_after = user_info_after.get('subscription', {})
                    if subscription_after:
                        character_count_after = subscription_after.get('character_count', 0)
                        character_limit_after = subscription_after.get('character_limit', 0)
                        remaining_after = character_limit_after - character_count_after
                        print(f"📈 Credits remaining after generation: {remaining_after}")
                except Exception as e:
                    print(f"⚠️  Could not check credits after generation: {e}")
                
            else:
                print("❌ Error: Output file was not created")
                
        except Exception as e:
            print(f"❌ Audio generation failed: {e}")
            if "quota_exceeded" in str(e):
                print("💡 Tip: Your ElevenLabs quota is exceeded. Try again after your quota resets.")
                print("💡 Or use an even shorter text like 'Test' (4 characters).")
            raise
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"ElevenLabs test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🎤 ElevenLabs Short Audio Test (Low Credit Usage)")
    print("=" * 60)
    
    success = await test_elevenlabs_short()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test completed successfully!")
        print("🎵 Check the outputs directory for your audio file.")
        print("💡 For longer audio, wait for your quota to reset or upgrade your plan.")
    else:
        print("❌ Test failed. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
