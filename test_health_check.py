#!/usr/bin/env python3
"""
Test script to verify the health check endpoint is working properly
"""
import asyncio
import httpx
import time

async def test_health_check():
    """Test the health check endpoint with timeout"""
    print("Testing health check endpoint...")
    
    try:
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get("http://localhost:8000/health")
            
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Health check completed in {duration:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check endpoint is working properly!")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Health check timed out - the issue is not fixed")
        return False
    except Exception as e:
        print(f"❌ Health check failed with error: {str(e)}")
        return False

async def test_basic_endpoint():
    """Test the basic root endpoint"""
    print("\nTesting basic root endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/")
            
        print(f"✅ Root endpoint working - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
        
    except Exception as e:
        print(f"❌ Root endpoint failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🔍 Testing Voice Converter API endpoints...\n")
    
    # Test basic endpoint first
    basic_ok = await test_basic_endpoint()
    
    if basic_ok:
        # Test health check endpoint
        health_ok = await test_health_check()
        
        if health_ok:
            print("\n🎉 All tests passed! The health check issue has been fixed.")
        else:
            print("\n❌ Health check endpoint still has issues.")
    else:
        print("\n❌ Server is not responding properly.")

if __name__ == "__main__":
    asyncio.run(main())
