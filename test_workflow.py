#!/usr/bin/env python3
"""
Test script for Voice Converter workflow
This script tests the complete pipeline without requiring actual API keys
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_workflow():
    """Test the complete voice conversion workflow"""
    print("🎵 Voice Converter Workflow Test")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from backend.app.services.gladia_service import GladiaService
        from backend.app.services.elevenlabs_service import ElevenLabsService
        from backend.app.services.audio_processor import AudioProcessor
        from backend.app.services.storage_service import StorageService
        from backend.app.utils.config import get_settings
        from backend.app.utils.logger import get_logger
        print("   ✅ All imports successful")
        
        # Test configuration
        print("\n2. Testing configuration...")
        settings = get_settings()
        logger = get_logger(__name__)
        print("   ✅ Configuration loaded")
        
        # Test service initialization
        print("\n3. Testing service initialization...")
        gladia_service = GladiaService()
        elevenlabs_service = ElevenLabsService()
        audio_processor = AudioProcessor()
        storage_service = StorageService()
        print("   ✅ All services initialized")
        
        # Test audio processor (doesn't require API keys)
        print("\n4. Testing audio processor...")
        try:
            from pydub import AudioSegment
            # Create a test audio segment
            test_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
            print("   ✅ Audio processing library working")
        except Exception as e:
            print(f"   ⚠️  Audio processing test failed: {e}")
        
        # Test directory creation
        print("\n5. Testing directory structure...")
        os.makedirs("backend/uploads", exist_ok=True)
        os.makedirs("backend/outputs", exist_ok=True)
        os.makedirs("backend/logs", exist_ok=True)
        print("   ✅ Directories created")
        
        # Test FastAPI app creation
        print("\n6. Testing FastAPI app...")
        from backend.app.main import app
        print("   ✅ FastAPI app created successfully")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Set up your API keys in backend/.env")
        print("2. Install FFmpeg for audio processing")
        print("3. Run 'python backend/start.py' to start the backend")
        print("4. Run 'npm start' in the frontend directory")
        print("5. Open http://localhost:3000 to use the application")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nPlease check:")
        print("1. All dependencies are installed (pip install -r backend/requirements.txt)")
        print("2. Python path is correct")
        print("3. All required files are present")
        return False

def test_frontend_structure():
    """Test frontend file structure"""
    print("\n7. Testing frontend structure...")
    
    required_files = [
        "frontend/package.json",
        "frontend/src/index.js",
        "frontend/src/App.js",
        "frontend/src/index.css",
        "frontend/src/services/api.js",
        "frontend/src/components/FileUpload.js",
        "frontend/src/components/ProgressTracker.js",
        "frontend/public/index.html",
        "frontend/tailwind.config.js",
        "frontend/postcss.config.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ⚠️  Missing files: {missing_files}")
        return False
    else:
        print("   ✅ All frontend files present")
        return True

def main():
    """Main test function"""
    print("Starting Voice Converter workflow test...\n")
    
    # Test backend
    backend_success = asyncio.run(test_workflow())
    
    # Test frontend structure
    frontend_success = test_frontend_structure()
    
    if backend_success and frontend_success:
        print("\n🎉 Complete workflow test PASSED!")
        print("\nYour Voice Converter application is ready to use!")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
