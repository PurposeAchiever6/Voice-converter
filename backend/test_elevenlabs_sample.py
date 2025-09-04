#!/usr/bin/env python3
"""
ElevenLabs Test Script - Generate 10-second audio sample
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

async def test_elevenlabs_generation():
    """Test ElevenLabs audio generation with a 10-second sample"""
    
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
        
        # Get user info to verify API key
        print("\n👤 Getting user account info...")
        try:
            user_info = await elevenlabs_service.get_user_info()
            print(f"✅ Account: {user_info.get('first_name', 'Unknown')} {user_info.get('last_name', '')}")
            
            # Check subscription info if available
            subscription = user_info.get('subscription', {})
            if subscription:
                print(f"📊 Subscription: {subscription.get('tier', 'Unknown')}")
                character_count = subscription.get('character_count', 0)
                character_limit = subscription.get('character_limit', 0)
                print(f"📈 Characters used: {character_count}/{character_limit}")
        except Exception as e:
            print(f"⚠️  Could not get user info: {e}")
        
        # Get voice information
        print(f"\n🎤 Getting voice information for ID: {settings.ELEVENLABS_VOICE_ID}")
        try:
            voice_info = await elevenlabs_service.get_voice_info(settings.ELEVENLABS_VOICE_ID)
            print(f"✅ Voice Name: {voice_info.get('name', 'Unknown')}")
            print(f"✅ Voice Category: {voice_info.get('category', 'Unknown')}")
            
            # Show voice settings if available
            voice_settings = voice_info.get('settings', {})
            if voice_settings:
                print(f"🎛️  Voice Settings:")
                print(f"   - Stability: {voice_settings.get('stability', 'N/A')}")
                print(f"   - Similarity Boost: {voice_settings.get('similarity_boost', 'N/A')}")
                print(f"   - Style: {voice_settings.get('style', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Could not get voice info: {e}")
        
        # Generate test text for approximately 10 seconds of audio
        # Average speaking rate is about 150-160 words per minute
        # For 10 seconds, we need about 25-27 words
        test_text = """
        This is a test of the ElevenLabs text-to-speech API. 
        We are generating a ten-second audio sample to verify 
        that the voice cloning service is working correctly 
        with the current configuration and API credentials.
        """
        
        print(f"\n📝 Test text ({len(test_text.split())} words):")
        print(f"'{test_text.strip()}'")
        
        # Generate audio
        print("\n🎵 Generating audio sample...")
        output_filename = "elevenlabs_test_10s_sample"
        
        try:
            audio_path = await elevenlabs_service.generate_speech(
                text=test_text.strip(),
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
                # WAV file size ≈ sample_rate * channels * bit_depth/8 * duration
                # Assuming 22050 Hz, mono, 16-bit: ~44KB per second
                estimated_duration = file_size / (22050 * 1 * 2)  # 2 bytes per sample for 16-bit
                print(f"⏱️  Estimated duration: {estimated_duration:.1f} seconds")
                
                print(f"\n🎉 SUCCESS! Audio sample generated at: {audio_path}")
                print(f"🔊 You can play this file to test the voice quality.")
                
            else:
                print("❌ Error: Output file was not created")
                
        except Exception as e:
            print(f"❌ Audio generation failed: {e}")
            raise
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"ElevenLabs test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("🎤 ElevenLabs Audio Generation Test")
    print("=" * 50)
    
    success = await test_elevenlabs_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
        print("🎵 Check the outputs directory for your audio file.")
    else:
        print("❌ Test failed. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
