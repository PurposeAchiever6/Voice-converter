"""
Test script for the continuous_with_spaces API endpoint
"""
import asyncio
import requests
import time
from pathlib import Path

async def test_continuous_with_spaces_api():
    """Test the new continuous_with_spaces API endpoint"""
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test file path
    test_file = Path("tests/1.leo test 8.28.wav")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please ensure the test audio file exists in backend/tests/")
        return False
    
    try:
        print("🧪 Testing continuous_with_spaces API endpoint...")
        print(f"📁 Using test file: {test_file}")
        
        # Step 1: Upload file with continuous_with_spaces=True
        print("\n1. Uploading file with continuous_with_spaces=True...")
        
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "audio/wav")}
            data = {
                "continuous_with_spaces": "true",
                "voice_id": "pNInz6obpgDQGcFmaJgB"  # Default voice ID
            }
            
            response = requests.post(f"{base_url}/upload", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        upload_result = response.json()
        job_id = upload_result["job_id"]
        print(f"✅ Upload successful! Job ID: {job_id}")
        
        # Step 2: Monitor job status
        print(f"\n2. Monitoring job status...")
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(f"{base_url}/status/{job_id}")
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
            
            status = status_response.json()
            print(f"   Status: {status['status']} | Progress: {status['progress']}% | {status['message']}")
            
            if status["status"] == "completed":
                print("✅ Job completed successfully!")
                break
            elif status["status"] == "failed":
                print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
                return False
            
            time.sleep(2)  # Wait 2 seconds before checking again
        else:
            print("❌ Job timed out")
            return False
        
        # Step 3: Test download endpoint
        print(f"\n3. Testing download endpoint...")
        download_response = requests.get(f"{base_url}/download/{job_id}")
        
        if download_response.status_code != 200:
            print(f"❌ Download failed: {download_response.status_code}")
            return False
        
        # Check if it's a file response or JSON with download URL
        if download_response.headers.get('content-type') == 'audio/wav':
            print("✅ Direct file download successful!")
            output_file = Path(f"test_output_continuous_with_spaces_{job_id}.wav")
            with open(output_file, "wb") as f:
                f.write(download_response.content)
            print(f"📁 Output saved to: {output_file}")
        else:
            download_info = download_response.json()
            print(f"✅ Download URL received: {download_info.get('download_url', 'N/A')}")
        
        print("\n🎉 continuous_with_spaces API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Main test function"""
    print("Starting continuous_with_spaces API test...\n")
    
    success = asyncio.run(test_continuous_with_spaces_api())
    
    if success:
        print("\n✅ All tests PASSED!")
        print("The continuous_with_spaces functionality is working correctly in the API!")
    else:
        print("\n❌ Tests FAILED.")
        print("Please check the API implementation and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
