"""
Simple test for Gladia API
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.gladia_service import GladiaService

async def test_gladia():
    """Simple Gladia test"""
    print("Testing Gladia API...")
    
    service = GladiaService()
    
    # Test file path
    test_file = Path(__file__).parent / "tests" / "1.leo test 8.28.wav"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        print("1. Testing upload...")
        upload_response = await service._upload_audio(str(test_file))
        print(f"   ✅ Upload successful: {upload_response}")
        
        print("2. Testing transcription start...")
        print(f"   Audio URL: {upload_response['audio_url']}")
        
        # Test the transcription start directly
        import httpx
        payload = {
            "audio_url": upload_response["audio_url"],
            "diarization": False,
            "sentences": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{service.base_url}/v2/transcription",
                headers=service.headers,
                json=payload
            )
            
            print(f"   Response status: {response.status_code}")
            print(f"   Response text: {response.text}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   Response JSON: {result}")
                if "id" in result:
                    transcription_id = result["id"]
                    print(f"   ✅ Transcription started: {transcription_id}")
                else:
                    print(f"   ❌ No ID in response")
                    return False
            else:
                print(f"   ❌ Bad status code: {response.status_code}")
                return False
        
        print("3. Testing status check...")
        result = await service._poll_transcription_result(transcription_id)
        print(f"   ✅ Transcription completed")
        
        print("4. Testing result parsing...")
        transcription_result = service._parse_transcription_result(result)
        print(f"   ✅ Parsing successful: {len(transcription_result.sentences)} sentences")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gladia())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
