#!/usr/bin/env python3
"""
Debug script to test Gladia API connection and identify the upload failure issue
"""
import asyncio
import httpx
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv("backend/.env")

GLADIA_API_KEY = os.getenv("GLADIA_API_KEY")
GLADIA_API_URL = "https://api.gladia.io"

async def test_gladia_connection():
    """Test basic Gladia API connection"""
    print("=== Testing Gladia API Connection ===")
    print(f"API Key: {GLADIA_API_KEY[:10]}..." if GLADIA_API_KEY else "No API Key found")
    print(f"API URL: {GLADIA_API_URL}")
    
    if not GLADIA_API_KEY:
        print("❌ ERROR: No Gladia API key found in environment")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test basic API endpoint
            response = await client.get(
                f"{GLADIA_API_URL}/v2/upload",
                headers={"x-gladia-key": GLADIA_API_KEY}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Text: {response.text[:500]}...")
            
            if response.status_code in [200, 401, 405]:  # 405 might be expected for GET on upload endpoint
                print("✅ API connection successful")
                return True
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

async def test_audio_upload():
    """Test audio file upload to Gladia"""
    print("\n=== Testing Audio Upload ===")
    
    # Find the failed audio file
    audio_file = "backend/uploads/3a90b770-425b-4da7-91c2-5f20ae5896dc_9.2 Leo test.wav"
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print(f"Audio file: {audio_file}")
    print(f"File size: {os.path.getsize(audio_file)} bytes")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_file, "rb") as f:
                files = {"audio": f}
                headers = {"x-gladia-key": GLADIA_API_KEY}
                
                print("Uploading audio file...")
                response = await client.post(
                    f"{GLADIA_API_URL}/v2/upload",
                    headers=headers,
                    files=files
                )
                
                print(f"Upload Status Code: {response.status_code}")
                print(f"Upload Response: {response.text}")
                
                if response.status_code == 200:
                    print("✅ Audio upload successful")
                    return response.json()
                else:
                    print(f"❌ Upload failed with status {response.status_code}")
                    return False
                    
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

async def test_api_key_validity():
    """Test if the API key is valid"""
    print("\n=== Testing API Key Validity ===")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try a simple authenticated request
            response = await client.get(
                f"{GLADIA_API_URL}/v2/transcription",
                headers={"x-gladia-key": GLADIA_API_KEY}
            )
            
            print(f"Auth test status: {response.status_code}")
            print(f"Auth test response: {response.text[:200]}...")
            
            if response.status_code == 401:
                print("❌ API key is invalid or expired")
                return False
            elif response.status_code in [200, 400, 405]:  # 400/405 might be expected for GET without params
                print("✅ API key appears to be valid")
                return True
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
                return True  # Assume valid if not explicitly 401
                
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        return False

async def main():
    """Run all diagnostic tests"""
    print("🔍 Gladia API Diagnostic Tool")
    print("=" * 50)
    
    # Test 1: Basic connection
    connection_ok = await test_gladia_connection()
    
    # Test 2: API key validity
    if connection_ok:
        key_valid = await test_api_key_validity()
    else:
        key_valid = False
    
    # Test 3: Audio upload (only if previous tests pass)
    if connection_ok and key_valid:
        upload_result = await test_audio_upload()
    else:
        upload_result = False
    
    print("\n" + "=" * 50)
    print("🏁 DIAGNOSTIC SUMMARY")
    print(f"Connection: {'✅ OK' if connection_ok else '❌ FAILED'}")
    print(f"API Key: {'✅ VALID' if key_valid else '❌ INVALID'}")
    print(f"Upload: {'✅ OK' if upload_result else '❌ FAILED'}")
    
    if not connection_ok:
        print("\n💡 RECOMMENDATION: Check network connection and API URL")
    elif not key_valid:
        print("\n💡 RECOMMENDATION: Check API key in .env file")
    elif not upload_result:
        print("\n💡 RECOMMENDATION: Check audio file format and size")
    else:
        print("\n✅ All tests passed - the issue might be elsewhere")

if __name__ == "__main__":
    asyncio.run(main())
