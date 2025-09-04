#!/usr/bin/env python3
"""
Test script to verify the voice converter fixes
"""
import asyncio
import httpx
import json
import time
from pathlib import Path

async def test_voice_converter_fix():
    """Test the voice converter with improved error handling"""
    
    base_url = "http://localhost:8000"
    
    print("🔧 Testing Voice Converter Fix")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data['status']}")
                print(f"   Services: {health_data.get('services', {})}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False
    
    # Test 2: Check if test audio file exists
    print("\n2. Checking for test audio file...")
    test_files = [
        "backend/tests/1.leo test 8.28.wav",
        "backend/uploads/181e2ebb-a7e8-40e0-aced-8f55a04c9d86_9.2 Leo test.wav",
        "backend/uploads/492e1344-6973-4837-aaa2-115e2875527a_9.2 Leo test.wav"
    ]
    
    test_file = None
    for file_path in test_files:
        if Path(file_path).exists():
            test_file = file_path
            print(f"✅ Found test file: {test_file}")
            break
    
    if not test_file:
        print("❌ No test audio file found. Please upload a file through the web interface first.")
        return False
    
    # Test 3: Upload and process with continuous_with_spaces mode
    print("\n3. Testing upload with continuous_with_spaces mode...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(test_file, "rb") as f:
                files = {"file": (Path(test_file).name, f, "audio/wav")}
                data = {"continuous_with_spaces": "true"}
                
                response = await client.post(
                    f"{base_url}/upload",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    upload_data = response.json()
                    job_id = upload_data["job_id"]
                    print(f"✅ Upload successful, job ID: {job_id}")
                    
                    # Test 4: Monitor job progress
                    print("\n4. Monitoring job progress...")
                    max_wait = 300  # 5 minutes
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        status_response = await client.get(f"{base_url}/status/{job_id}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data["status"]
                            progress = status_data["progress"]
                            message = status_data["message"]
                            
                            print(f"   Status: {status} ({progress}%) - {message}")
                            
                            if status == "completed":
                                print("✅ Job completed successfully!")
                                download_url = status_data.get("download_url")
                                if download_url:
                                    print(f"   Download URL: {download_url}")
                                return True
                            elif status == "failed":
                                error = status_data.get("error", "Unknown error")
                                print(f"❌ Job failed: {error}")
                                return False
                            
                            await asyncio.sleep(5)  # Wait 5 seconds before next check
                        else:
                            print(f"❌ Status check failed: {status_response.status_code}")
                            return False
                    
                    print(f"❌ Job timed out after {max_wait} seconds")
                    return False
                    
                else:
                    print(f"❌ Upload failed: {response.status_code} - {response.text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

async def main():
    """Main test function"""
    print("Voice Converter Fix Verification")
    print("This script tests the improved error handling and timeout management")
    print()
    
    success = await test_voice_converter_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The voice converter fix is working properly.")
        print("\nKey improvements implemented:")
        print("• Better error handling in Gladia transcription service")
        print("• Retry logic with exponential backoff in ElevenLabs service")
        print("• Timeout management to prevent hanging")
        print("• Fallback silence generation for failed sentences")
        print("• Progressive polling with better logging")
    else:
        print("❌ Some tests failed. Please check the logs for more details.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
