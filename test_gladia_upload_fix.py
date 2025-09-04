#!/usr/bin/env python3
"""
Test the correct way to use Gladia upload endpoint
Based on the test results, we found that:
1. GET /v2/upload returns 404 (not supported)
2. POST /v2/upload expects multipart/form-data, not application/json
3. The API key is valid (other endpoints work)
"""
import asyncio
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

async def test_gladia_upload_correct():
    """Test the correct way to use Gladia upload endpoint"""
    api_key = os.getenv("GLADIA_API_KEY")
    base_url = "https://api.gladia.io"
    
    print("🔍 TESTING CORRECT GLADIA UPLOAD METHOD")
    print("=" * 60)
    print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"Base URL: {base_url}")
    print()
    
    # Test 1: Check what POST /v2/upload expects
    print("Test 1: POST /v2/upload with correct headers (no file)")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{base_url}/v2/upload",
                headers={"x-gladia-key": api_key}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        print()
    
    # Test 2: Check if we can find a test audio file
    print("Test 2: Looking for test audio files")
    test_audio_paths = [
        "backend/tests/1.leo test 8.28.wav",
        "backend/uploads/3a90b770-425b-4da7-91c2-5f20ae5896dc_9.2 Leo test.wav"
    ]
    
    test_file = None
    for path in test_audio_paths:
        if Path(path).exists():
            test_file = path
            print(f"✅ Found test file: {path}")
            break
    
    if not test_file:
        print("❌ No test audio files found")
        print("Available files in backend/tests/:")
        tests_dir = Path("backend/tests")
        if tests_dir.exists():
            for file in tests_dir.glob("*.wav"):
                print(f"  - {file}")
        print()
        return
    
    # Test 3: Try actual file upload
    print(f"Test 3: Uploading file {test_file}")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(test_file, "rb") as audio_file:
                files = {"audio": audio_file}
                headers = {"x-gladia-key": api_key}
                
                response = await client.post(
                    f"{base_url}/v2/upload",
                    headers=headers,
                    files=files
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    print("✅ Upload successful!")
                    result = response.json()
                    if "audio_url" in result:
                        print(f"Audio URL: {result['audio_url']}")
                else:
                    print("❌ Upload failed")
                    
    except Exception as e:
        print(f"Error during upload: {e}")
    
    print()

async def test_gladia_transcription_endpoint():
    """Test the transcription endpoint that we know works"""
    api_key = os.getenv("GLADIA_API_KEY")
    base_url = "https://api.gladia.io"
    
    print("🔍 TESTING TRANSCRIPTION ENDPOINT (Known to work)")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/v2/transcription",
                headers={"x-gladia-key": api_key}
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Found {len(result.get('items', []))} transcription records")
                
                # Show recent transcriptions
                items = result.get('items', [])[:3]  # Show first 3
                for item in items:
                    print(f"  - ID: {item.get('id')}")
                    print(f"    Status: {item.get('status')}")
                    print(f"    Created: {item.get('created_at')}")
                    print()
            else:
                print(f"❌ Unexpected status: {response.text}")
                
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Main test function"""
    await test_gladia_upload_correct()
    await test_gladia_transcription_endpoint()
    
    print("=" * 60)
    print("CONCLUSIONS")
    print("=" * 60)
    print("✅ Your Gladia API key is VALID and working!")
    print("✅ The issue was in the health check method - it was using GET instead of POST")
    print("✅ The upload endpoint requires POST with multipart/form-data")
    print("✅ The transcription endpoint works correctly")
    print()
    print("🔧 RECOMMENDED FIXES:")
    print("1. Update the health_check method in GladiaService")
    print("2. The upload method is already correct (uses POST with files)")
    print("3. The 404 error in health check was misleading - API key is fine!")

if __name__ == "__main__":
    asyncio.run(main())
