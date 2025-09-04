# Voice Converter

A full-stack application that converts audio files using advanced voice cloning technology. The system transcribes speech from uploaded audio files and regenerates it using ElevenLabs voice cloning, offering multiple processing modes for different use cases.

## 🎯 Features

- **Multi-format Audio Support**: Upload WAV, MP3, M4A, FLAC, and OGG files
- **Advanced Speech-to-Text**: Powered by Gladia API with precise timestamp extraction
- **Voice Cloning**: High-quality voice synthesis using ElevenLabs API
- **Multiple Processing Modes**:
  - **Standard Mode**: Maintains original timing and gaps
  - **Continuous Mode**: Creates seamless audio without gaps (shorter duration)
  - **Same Length Mode**: Preserves original duration while eliminating gaps
  - **Timestamp-based Mode**: Intelligent gap analysis and removal
- **Real-time Progress Tracking**: Monitor processing status with detailed progress updates
- **Gap Analysis**: Analyze audio gaps and empty spaces before processing
- **Modern React Frontend**: Drag-and-drop file upload with progress visualization
- **RESTful API**: Comprehensive FastAPI backend with async processing

## 🏗️ Architecture

```
voice-converter/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── models/            # Pydantic data models
│   │   │   └── audio.py       # Audio processing models
│   │   ├── services/          # Business logic services
│   │   │   ├── audio_processor.py      # Audio manipulation
│   │   │   ├── elevenlabs_service.py   # Voice cloning service
│   │   │   ├── gladia_service.py       # Speech-to-text service
│   │   │   ├── sentence_processor.py   # Sentence-level processing
│   │   │   └── storage_service.py      # File storage handling
│   │   └── utils/             # Utility functions
│   │       ├── config.py      # Configuration management
│   │       └── logger.py      # Logging setup
│   ├── tests/                 # Test files and workflows
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── FileUpload.js  # File upload component
│   │   │   └── ProgressTracker.js # Progress tracking
│   │   ├── services/          # API services
│   │   │   └── api.js         # Backend API integration
│   │   ├── App.js            # Main application component
│   │   └── index.js          # Application entry point
│   ├── package.json          # Node.js dependencies
│   └── public/               # Static assets
├── logs/                     # Application logs
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **FFmpeg** (for audio processing)
- **API Keys**:
  - [Gladia API Key](https://gladia.io/) for speech-to-text
  - [ElevenLabs API Key](https://elevenlabs.io/) for voice cloning

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd Voice-converter
```

#### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
copy .env.example .env
# Edit .env file with your API keys (see Environment Variables section)
```

#### 3. Frontend Setup
```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

### Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# API Keys (Required)
GLADIA_API_KEY=your_gladia_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Application Settings
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
MAX_FILE_SIZE=100000000
ALLOWED_EXTENSIONS=wav,mp3,m4a,flac,ogg

# ElevenLabs Settings
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

**Getting API Keys:**
1. **Gladia API**: Sign up at [gladia.io](https://gladia.io/) and get your API key from the dashboard
2. **ElevenLabs API**: Sign up at [elevenlabs.io](https://elevenlabs.io/), get your API key, and note your preferred voice ID

## 🎮 Running the Application

### Development Mode

#### Start Backend Server
```bash
cd backend
# Ensure virtual environment is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend will be available at: `http://localhost:8000`

#### Start Frontend Server
```bash
cd frontend
npm start
```
Frontend will be available at: `http://localhost:3000`

### Production Mode

#### Backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run build
# Serve the build directory with your preferred web server
```

## 📡 API Documentation

### Core Endpoints

#### Health Check
```http
GET /
GET /health
```

#### File Upload and Processing
```http
POST /upload
Content-Type: multipart/form-data

Parameters:
- file: Audio file (required)
- voice_id: ElevenLabs voice ID (optional)
- continuous: Boolean - creates seamless audio (optional)
- same_length: Boolean - maintains original duration (optional)
- timestamp_based: Boolean - intelligent gap removal (optional)

Response:
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Processing started"
}
```

#### Check Processing Status
```http
GET /status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "processing|completed|failed",
  "progress": 0-100,
  "message": "Current status",
  "download_url": "file_url",
  "error": "error_message"
}
```

#### Download Result
```http
GET /download/{job_id}
```

#### Analyze Audio Gaps
```http
POST /analyze-gaps
Content-Type: multipart/form-data

Parameters:
- file: Audio file to analyze

Response:
{
  "analysis": {
    "total_gap_time": 5.2,
    "speech_ratio": 0.75,
    "filtered_sentences": 15
  },
  "sentences": [...],
  "recommendations": {
    "use_timestamp_based": true,
    "gap_reduction_potential": "5.2s",
    "speech_efficiency": "75.0%"
  }
}
```

## 🎛️ Processing Modes

### 1. Standard Mode (Default)
- Maintains original timing and gaps
- Best for preserving natural speech patterns
- Longest processing time

### 2. Continuous Mode
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@audio.wav" \
  -F "continuous=true"
```
- Creates seamless audio without gaps
- Shorter duration than original
- Faster processing

### 3. Same Length Mode
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@audio.wav" \
  -F "same_length=true"
```
- Preserves original duration
- Eliminates gaps intelligently
- Balanced approach

### 4. Timestamp-based Mode
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@audio.wav" \
  -F "timestamp_based=true"
```
- Advanced gap analysis and removal
- Sentence-by-sentence processing
- Optimal for content with many pauses

## 🧪 Testing

### Run Test Workflows
```bash
cd backend

# Test all processing modes
python test_all_modes.py

# Test specific workflows
python tests/test_continuous_workflow.py
python tests/test_same_length_workflow.py
python tests/test_timestamp_complete.py
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Upload test file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test_audio.wav" \
  -F "voice_id=your_voice_id"
```

## 🔧 Configuration

### File Size Limits
- Default: 100MB
- Modify `MAX_FILE_SIZE` in `.env`

### Supported Formats
- WAV, MP3, M4A, FLAC, OGG
- Modify `ALLOWED_EXTENSIONS` in `.env`

### Voice Models
- Default: `eleven_multilingual_v2`
- Available models: Check ElevenLabs documentation

## 📊 Monitoring and Logs

### Application Logs
```bash
# View logs
tail -f logs/voice_converter.log

# Backend logs (if running with uvicorn)
tail -f backend/logs/app.log
```

### Progress Tracking
The application provides real-time progress updates:
- File upload: 0-10%
- Speech-to-text: 10-30%
- Voice cloning: 30-80%
- Audio processing: 80-90%
- Finalization: 90-100%

## 🚨 Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check Python version
python --version

# Verify virtual environment
which python

# Check dependencies
pip list
```

#### Frontend build fails
```bash
# Clear cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### API Key Issues
- Verify API keys in `.env` file
- Check API key permissions and quotas
- Test API keys with curl:
```bash
# Test Gladia API
curl -H "x-gladia-key: YOUR_API_KEY" https://api.gladia.io/health

# Test ElevenLabs API
curl -H "xi-api-key: YOUR_API_KEY" https://api.elevenlabs.io/v1/voices
```

#### Audio Processing Errors
- Ensure FFmpeg is installed and in PATH
- Check audio file format and size
- Verify file permissions

### Performance Optimization

#### For Large Files
- Use `timestamp_based=true` for files with many gaps
- Consider splitting very large files
- Monitor memory usage during processing

#### For Better Quality
- Use higher quality voice models
- Ensure clean input audio
- Test different voice IDs for best results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Test with sample audio files
4. Create an issue with detailed error information

---

**Note**: This application requires active API subscriptions to Gladia and ElevenLabs services. Processing costs depend on audio duration and API usage.
