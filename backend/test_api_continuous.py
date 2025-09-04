"""
Test script for the continuous mode API
"""
import requests
import time
import json
from pathlib import Path

def test_continuous_api():
    """Test the API with continuous mode"""
    
    # API base URL
    base_url = "http://localhost:8000"
    
    # Test file path
    test_file = Path("tests/1.leo test 8.28.wav")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print("🎵 Testing Voice Converter API with Continuous Mode")
    print("=" * 60)
    
    try:
        # Step 1: Upload file with continuous=True
        print("1. Uploading file with continuous mode...")
        
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "audio/wav")}
            data = {"continuous": "true"}  # Enable continuous mode
            
            response = requests.post(f"{base_url}/upload", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
        
        upload_result = response.json()
        job_id = upload_result["job_id"]
        print(f"   ✅ Upload successful, job ID: {job_id}")
        
        # Step 2: Monitor processing status
        print("\n2. Monitoring processing status...")
        
        while True:
            response = requests.get(f"{base_url}/status/{job_id}")
            
            if response.status_code != 200:
                print(f"❌ Status check failed: {response.status_code}")
                return False
            
            status = response.json()
            print(f"   📊 Status: {status['status']} - {status['progress']}% - {status['message']}")
            
            if status["status"] == "completed":
                print("   ✅ Processing completed!")
                break
            elif status["status"] == "failed":
                print(f"   ❌ Processing failed: {status.get('error', 'Unknown error')}")
                return False
            
            time.sleep(2)  # Wait 2 seconds before checking again
        
        # Step 3: Download result
        print("\n3. Downloading result...")
        
        response = requests.get(f"{base_url}/download/{job_id}")
        
        if response.status_code == 200:
            # Check if it's a direct file download or a JSON response with URL
            content_type = response.headers.get('content-type', '')
            
            if 'audio' in content_type:
                # Direct file download
                output_file = f"outputs/api_test_continuous_{job_id}.wav"
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, "wb") as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                print(f"   ✅ File downloaded: {output_file}")
                print(f"   📊 File size: {file_size:,} bytes")
                
            else:
                # JSON response with download URL
                download_info = response.json()
                print(f"   ✅ Download URL: {download_info.get('download_url', 'N/A')}")
        else:
            print(f"❌ Download failed: {response.status_code} - {response.text}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 Continuous API test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_comparison():
    """Test both modes for comparison"""
    print("\n🔄 Testing both modes for comparison...")
    
    # Test original mode
    print("\n📊 Testing original mode (with gaps)...")
    # You can implement this if needed
    
    # Test continuous mode
    print("\n📊 Testing continuous mode (no gaps)...")
    return test_continuous_api()

if __name__ == "__main__":
    print("Starting API test...\n")
    
    # First check if server is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server first:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        exit(1)
    
    # Run the test
    success = test_continuous_api()
    
    if success:
        print("\n🎉 All API tests PASSED!")
    else:
        print("\n❌ API tests FAILED.")
    
    exit(0 if success else 1)
