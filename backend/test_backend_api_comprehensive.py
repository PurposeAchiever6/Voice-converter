"""
Comprehensive test script for the Voice Converter Backend API
Tests all modes including the continuous_with_spaces functionality
"""
import asyncio
import requests
import time
import json
from pathlib import Path
from typing import Dict, Any

class BackendAPITester:
    """Comprehensive tester for the Voice Converter Backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        
    async def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        try:
            print("🏥 Testing health check endpoint...")
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ Health check passed: {health_data['status']}")
                print(f"   📊 Services: {health_data.get('services', {})}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    async def test_continuous_with_spaces_mode(self, test_file: Path) -> Dict[str, Any]:
        """Test the continuous_with_spaces mode (main focus)"""
        print("\n🎯 Testing continuous_with_spaces mode...")
        
        try:
            # Upload file with continuous_with_spaces=True
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "audio/wav")}
                data = {
                    "continuous_with_spaces": "true",
                    "voice_id": "pNInz6obpgDQGcFmaJgB"  # Default voice ID
                }
                
                response = requests.post(f"{self.base_url}/upload", files=files, data=data)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code} - {response.text}",
                    "job_id": None
                }
            
            upload_result = response.json()
            job_id = upload_result["job_id"]
            print(f"   ✅ Upload successful! Job ID: {job_id}")
            
            # Monitor job progress
            print("   📊 Monitoring job progress...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            progress_history = []
            
            while time.time() - start_time < max_wait_time:
                status_response = requests.get(f"{self.base_url}/status/{job_id}")
                
                if status_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Status check failed: {status_response.status_code}",
                        "job_id": job_id
                    }
                
                status = status_response.json()
                progress_history.append({
                    "timestamp": time.time() - start_time,
                    "progress": status["progress"],
                    "message": status["message"],
                    "status": status["status"]
                })
                
                print(f"      {status['status'].upper()}: {status['progress']}% - {status['message']}")
                
                if status["status"] == "completed":
                    print("   ✅ Job completed successfully!")
                    break
                elif status["status"] == "failed":
                    return {
                        "success": False,
                        "error": f"Job failed: {status.get('error', 'Unknown error')}",
                        "job_id": job_id,
                        "progress_history": progress_history
                    }
                
                time.sleep(3)  # Wait 3 seconds between checks
            else:
                return {
                    "success": False,
                    "error": "Job timed out",
                    "job_id": job_id,
                    "progress_history": progress_history
                }
            
            # Test download
            print("   📥 Testing download...")
            download_response = requests.get(f"{self.base_url}/download/{job_id}")
            
            if download_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Download failed: {download_response.status_code}",
                    "job_id": job_id,
                    "progress_history": progress_history
                }
            
            # Save output file
            output_file = Path(f"test_output_continuous_with_spaces_{job_id}.wav")
            
            if download_response.headers.get('content-type') == 'audio/wav':
                with open(output_file, "wb") as f:
                    f.write(download_response.content)
                print(f"   ✅ Output saved to: {output_file}")
                file_size = output_file.stat().st_size
                print(f"   📊 Output file size: {file_size:,} bytes")
            else:
                download_info = download_response.json()
                print(f"   ℹ️ Download URL: {download_info.get('download_url', 'N/A')}")
            
            return {
                "success": True,
                "job_id": job_id,
                "output_file": str(output_file) if output_file.exists() else None,
                "progress_history": progress_history,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "job_id": None
            }
    
    async def test_other_modes(self, test_file: Path) -> Dict[str, Dict[str, Any]]:
        """Test other processing modes for comparison"""
        modes = {
            "continuous": {"continuous": "true"},
            "timestamp_based": {"timestamp_based": "true"},
            "original": {}  # Default mode
        }
        
        results = {}
        
        for mode_name, mode_params in modes.items():
            print(f"\n🔄 Testing {mode_name} mode...")
            
            try:
                # Upload file
                with open(test_file, "rb") as f:
                    files = {"file": (test_file.name, f, "audio/wav")}
                    data = {
                        "voice_id": "pNInz6obpgDQGcFmaJgB",
                        **mode_params
                    }
                    
                    response = requests.post(f"{self.base_url}/upload", files=files, data=data)
                
                if response.status_code != 200:
                    results[mode_name] = {
                        "success": False,
                        "error": f"Upload failed: {response.status_code}"
                    }
                    continue
                
                job_id = response.json()["job_id"]
                print(f"   Job ID: {job_id}")
                
                # Quick status check (don't wait for completion to save time)
                time.sleep(2)
                status_response = requests.get(f"{self.base_url}/status/{job_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    results[mode_name] = {
                        "success": True,
                        "job_id": job_id,
                        "initial_status": status["status"],
                        "initial_progress": status["progress"],
                        "message": status["message"]
                    }
                    print(f"   ✅ {mode_name} mode started successfully")
                else:
                    results[mode_name] = {
                        "success": False,
                        "error": "Status check failed"
                    }
                    
            except Exception as e:
                results[mode_name] = {
                    "success": False,
                    "error": f"Exception: {str(e)}"
                }
        
        return results
    
    async def test_gap_analysis(self, test_file: Path) -> Dict[str, Any]:
        """Test the gap analysis endpoint"""
        print("\n📊 Testing gap analysis endpoint...")
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "audio/wav")}
                response = requests.post(f"{self.base_url}/analyze-gaps", files=files)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Gap analysis failed: {response.status_code} - {response.text}"
                }
            
            analysis_result = response.json()
            
            print("   ✅ Gap analysis completed!")
            print(f"   📊 Total sentences: {len(analysis_result.get('sentences', []))}")
            
            analysis = analysis_result.get('analysis', {})
            print(f"   📊 Total gap time: {analysis.get('total_gap_time', 0):.2f}s")
            print(f"   📊 Speech ratio: {analysis.get('speech_ratio', 0):.1%}")
            
            recommendations = analysis_result.get('recommendations', {})
            print(f"   💡 Use timestamp_based: {recommendations.get('use_timestamp_based', False)}")
            print(f"   💡 Gap reduction potential: {recommendations.get('gap_reduction_potential', 'N/A')}")
            
            return {
                "success": True,
                "analysis": analysis,
                "sentences_count": len(analysis_result.get('sentences', [])),
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def run_comprehensive_test(self, test_file_path: str) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        test_file = Path(test_file_path)
        
        if not test_file.exists():
            return {
                "success": False,
                "error": f"Test file not found: {test_file_path}",
                "results": {}
            }
        
        print("🧪 Starting Comprehensive Backend API Test")
        print(f"📁 Test file: {test_file}")
        print(f"🌐 API URL: {self.base_url}")
        print("=" * 60)
        
        results = {
            "test_file": str(test_file),
            "api_url": self.base_url,
            "timestamp": time.time()
        }
        
        # Test 1: Health check
        results["health_check"] = await self.test_health_check()
        
        # Test 2: Gap analysis
        results["gap_analysis"] = await self.test_gap_analysis(test_file)
        
        # Test 3: Main test - continuous_with_spaces mode
        results["continuous_with_spaces"] = await self.test_continuous_with_spaces_mode(test_file)
        
        # Test 4: Other modes (quick test)
        results["other_modes"] = await self.test_other_modes(test_file)
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        success_count = 0
        total_tests = 0
        
        # Health check
        total_tests += 1
        if results["health_check"]:
            success_count += 1
            print("✅ Health check: PASSED")
        else:
            print("❌ Health check: FAILED")
        
        # Gap analysis
        total_tests += 1
        if results["gap_analysis"]["success"]:
            success_count += 1
            print("✅ Gap analysis: PASSED")
        else:
            print("❌ Gap analysis: FAILED")
        
        # Continuous with spaces (main test)
        total_tests += 1
        if results["continuous_with_spaces"]["success"]:
            success_count += 1
            print("✅ Continuous with spaces: PASSED")
            if results["continuous_with_spaces"].get("output_file"):
                print(f"   📁 Output file: {results['continuous_with_spaces']['output_file']}")
                print(f"   ⏱️ Processing time: {results['continuous_with_spaces']['processing_time']:.1f}s")
        else:
            print("❌ Continuous with spaces: FAILED")
            print(f"   Error: {results['continuous_with_spaces']['error']}")
        
        # Other modes
        for mode_name, mode_result in results["other_modes"].items():
            total_tests += 1
            if mode_result["success"]:
                success_count += 1
                print(f"✅ {mode_name} mode: STARTED")
            else:
                print(f"❌ {mode_name} mode: FAILED")
        
        overall_success = success_count == total_tests
        results["summary"] = {
            "overall_success": overall_success,
            "passed_tests": success_count,
            "total_tests": total_tests,
            "success_rate": f"{(success_count/total_tests)*100:.1f}%"
        }
        
        print(f"\n🎯 Overall Result: {'PASSED' if overall_success else 'FAILED'}")
        print(f"📊 Success Rate: {results['summary']['success_rate']} ({success_count}/{total_tests})")
        
        return results

async def main():
    """Main test function"""
    # Test file path
    test_file = "tests/1.leo test 8.28.wav"
    
    # Initialize tester
    tester = BackendAPITester()
    
    # Run comprehensive test
    results = await tester.run_comprehensive_test(test_file)
    
    # Save results to file
    results_file = Path("test_results_backend_api.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return results["summary"]["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
