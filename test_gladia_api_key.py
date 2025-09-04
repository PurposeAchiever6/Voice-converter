#!/usr/bin/env python3
"""
Comprehensive Gladia API Key Test Script
Tests various Gladia API endpoints to diagnose API key issues
"""
import asyncio
import httpx
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env")

class GladiaAPITester:
    def __init__(self):
        self.api_key = os.getenv("GLADIA_API_KEY")
        self.base_url = "https://api.gladia.io"
        self.headers = {
            "x-gladia-key": self.api_key,
            "Content-Type": "application/json"
        }
        
    def print_config(self):
        """Print current configuration"""
        print("=" * 60)
        print("GLADIA API CONFIGURATION")
        print("=" * 60)
        print(f"API Key: {self.api_key[:8]}...{self.api_key[-8:] if self.api_key else 'NOT SET'}")
        print(f"Base URL: {self.base_url}")
        print(f"Headers: {json.dumps({k: v[:20] + '...' if k == 'x-gladia-key' and len(v) > 20 else v for k, v in self.headers.items()}, indent=2)}")
        print()

    async def test_api_key_validity(self):
        """Test if API key is valid by checking various endpoints"""
        print("=" * 60)
        print("TESTING API KEY VALIDITY")
        print("=" * 60)
        
        if not self.api_key:
            print("❌ ERROR: No API key found in environment variables")
            return False
            
        # Test different endpoints to find which ones work
        endpoints_to_test = [
            ("/v2/upload", "GET", "Upload endpoint check"),
            ("/v2/transcription", "GET", "Transcription endpoint check"),
            ("/v2/account", "GET", "Account endpoint check"),
            ("/v2/credits", "GET", "Credits endpoint check"),
            ("/v2/models", "GET", "Models endpoint check"),
            ("/", "GET", "Root endpoint check"),
            ("/health", "GET", "Health endpoint check"),
            ("/status", "GET", "Status endpoint check")
        ]
        
        results = []
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint, method, description in endpoints_to_test:
                try:
                    print(f"Testing {description}: {method} {self.base_url}{endpoint}")
                    
                    if method == "GET":
                        response = await client.get(
                            f"{self.base_url}{endpoint}",
                            headers={"x-gladia-key": self.api_key}
                        )
                    else:
                        response = await client.post(
                            f"{self.base_url}{endpoint}",
                            headers=self.headers
                        )
                    
                    status_code = response.status_code
                    
                    # Interpret status codes
                    if status_code == 200:
                        status = "✅ SUCCESS"
                    elif status_code == 401:
                        status = "🔑 UNAUTHORIZED (Invalid API key)"
                    elif status_code == 403:
                        status = "🚫 FORBIDDEN (API key valid but no permission)"
                    elif status_code == 404:
                        status = "❓ NOT FOUND (Endpoint doesn't exist)"
                    elif status_code == 405:
                        status = "❌ METHOD NOT ALLOWED"
                    elif status_code == 429:
                        status = "⏰ RATE LIMITED"
                    elif status_code >= 500:
                        status = "🔥 SERVER ERROR"
                    else:
                        status = f"❓ UNKNOWN ({status_code})"
                    
                    print(f"  → {status_code}: {status}")
                    
                    # Try to get response content
                    try:
                        content = response.text[:200] + "..." if len(response.text) > 200 else response.text
                        if content.strip():
                            print(f"  → Response: {content}")
                    except:
                        pass
                    
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": status_code,
                        "description": description,
                        "success": status_code in [200, 201]
                    })
                    
                except Exception as e:
                    print(f"  → ❌ ERROR: {str(e)}")
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": None,
                        "description": description,
                        "error": str(e),
                        "success": False
                    })
                
                print()
        
        return results

    async def test_upload_endpoint_detailed(self):
        """Test the upload endpoint in detail"""
        print("=" * 60)
        print("DETAILED UPLOAD ENDPOINT TEST")
        print("=" * 60)
        
        # Test different ways to access the upload endpoint
        test_variations = [
            ("GET", "/v2/upload", {"x-gladia-key": self.api_key}),
            ("POST", "/v2/upload", {"x-gladia-key": self.api_key}),
            ("GET", "/upload", {"x-gladia-key": self.api_key}),
            ("POST", "/upload", {"x-gladia-key": self.api_key}),
            ("GET", "/v2/upload", {"Authorization": f"Bearer {self.api_key}"}),
            ("POST", "/v2/upload", {"Authorization": f"Bearer {self.api_key}"}),
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for method, endpoint, headers in test_variations:
                try:
                    print(f"Testing: {method} {self.base_url}{endpoint}")
                    print(f"Headers: {headers}")
                    
                    if method == "GET":
                        response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                    else:
                        response = await client.post(f"{self.base_url}{endpoint}", headers=headers)
                    
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text[:300]}...")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"Error: {str(e)}")
                    print("-" * 40)

    async def test_api_documentation_endpoints(self):
        """Test common API documentation endpoints"""
        print("=" * 60)
        print("TESTING DOCUMENTATION ENDPOINTS")
        print("=" * 60)
        
        doc_endpoints = [
            "/docs",
            "/swagger",
            "/api-docs",
            "/openapi.json",
            "/v2/docs",
            "/v2/swagger"
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in doc_endpoints:
                try:
                    print(f"Testing: {self.base_url}{endpoint}")
                    response = await client.get(f"{self.base_url}{endpoint}")
                    print(f"  → {response.status_code}: {response.reason_phrase}")
                    
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        print(f"  → Content-Type: {content_type}")
                        
                except Exception as e:
                    print(f"  → Error: {str(e)}")
                
                print()

    async def run_all_tests(self):
        """Run all tests"""
        print("🔍 GLADIA API KEY COMPREHENSIVE TEST")
        print("=" * 60)
        
        self.print_config()
        
        # Test API key validity
        results = await self.test_api_key_validity()
        
        # Test upload endpoint in detail
        await self.test_upload_endpoint_detailed()
        
        # Test documentation endpoints
        await self.test_api_documentation_endpoints()
        
        # Summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = [r for r in results if r.get("success", False)]
        failed_tests = [r for r in results if not r.get("success", False)]
        
        print(f"✅ Successful tests: {len(successful_tests)}")
        print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            print("\nSuccessful endpoints:")
            for test in successful_tests:
                print(f"  - {test['method']} {test['endpoint']}: {test['description']}")
        
        if failed_tests:
            print("\nFailed endpoints:")
            for test in failed_tests:
                status = test.get('status_code', 'ERROR')
                print(f"  - {test['method']} {test['endpoint']}: {status} - {test['description']}")
        
        # Recommendations
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        
        if not self.api_key:
            print("❌ No API key found. Please set GLADIA_API_KEY in your .env file.")
        elif any(r.get('status_code') == 401 for r in results):
            print("🔑 API key appears to be invalid. Please check your GLADIA_API_KEY.")
        elif any(r.get('status_code') == 403 for r in results):
            print("🚫 API key is valid but lacks permissions. Check your Gladia account.")
        elif all(r.get('status_code') == 404 for r in results if r.get('status_code')):
            print("❓ All endpoints return 404. Possible issues:")
            print("   - API base URL might be incorrect")
            print("   - API version might have changed")
            print("   - Gladia API might be down")
        else:
            print("✅ API key appears to be working for some endpoints.")

async def main():
    """Main test function"""
    tester = GladiaAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
