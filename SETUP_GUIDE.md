# Voice Converter Setup Guide

This guide will help you set up and run the Voice Converter application locally.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- FFmpeg (for audio processing)

### API Keys Required
- **Gladia API Key**: For speech-to-text conversion
- **ElevenLabs API Key**: For voice cloning
- **ElevenLabs Voice ID**: The specific voice you want to clone
- **AWS S3 Credentials** (optional): For cloud storage
- **File.io API Key** (optional): Alternative cloud storage

## Installation

### 1. Clone and Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
```

Required environment variables:
```env
# API Keys
GLADIA_API_KEY=your_gladia_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# AWS S3 (optional but recommended)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1

# File.io (fallback option)
FILEIO_API_KEY=your_fileio_api_key_here
```

### 3. Setup Frontend

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Install FFmpeg

#### Windows
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract and add to your PATH environment variable

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

## Running the Application

### 1. Start Backend Server

```bash
cd backend

# Activate virtual environment if not already active
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Start the server
python start.py
```

The backend will be available at: http://localhost:8000

### 2. Start Frontend Development Server

```bash
cd frontend

# Start React development server
npm start
```

The frontend will be available at: http://localhost:3000

## API Key Setup Instructions

### Gladia API Key
1. Sign up at https://gladia.io/
2. Go to your dashboard
3. Generate an API key
4. Add it to your `.env` file as `GLADIA_API_KEY`

### ElevenLabs API Key and Voice ID
1. Sign up at https://elevenlabs.io/
2. Go to your profile settings
3. Generate an API key
4. Go to Voice Lab to find or create voice IDs
5. Add both to your `.env` file

### AWS S3 Setup (Optional)
1. Create an AWS account
2. Create an S3 bucket
3. Create IAM user with S3 permissions
4. Add credentials to `.env` file

### File.io Setup (Optional)
1. Sign up at https://file.io/
2. Get your API key from the dashboard
3. Add it to your `.env` file

## Testing the Application

### 1. Health Check
Visit http://localhost:8000/health to check if all services are working.

### 2. Upload Test Audio
1. Prepare a short audio file (WAV, MP3, M4A, FLAC, or OGG)
2. Open http://localhost:3000
3. Enter your ElevenLabs Voice ID
4. Upload the audio file
5. Click "Start Voice Conversion"
6. Monitor the progress
7. Download the result when complete

### 3. API Testing
You can also test the API directly:

```bash
# Health check
curl http://localhost:8000/health

# Upload file (replace with your file and voice ID)
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_audio_file.wav" \
  -F "voice_id=your_voice_id"
```

## Troubleshooting

### Common Issues

#### 1. "Missing required environment variables"
- Ensure all required API keys are set in your `.env` file
- Check that the `.env` file is in the `backend` directory

#### 2. "FFmpeg not found"
- Install FFmpeg and ensure it's in your system PATH
- Restart your terminal after installation

#### 3. "Upload failed" or "Processing failed"
- Check your API keys are valid and have sufficient credits
- Ensure your audio file is in a supported format and under 100MB
- Check the backend logs for detailed error messages

#### 4. "Health check failed"
- Verify your internet connection
- Check that API keys are correct
- Ensure external services (Gladia, ElevenLabs) are accessible

#### 5. Frontend not connecting to backend
- Ensure backend is running on port 8000
- Check that CORS is properly configured
- Verify the proxy setting in `frontend/package.json`

### Log Files
- Backend logs are saved to `backend/logs/voice_converter.log`
- Check these logs for detailed error information

### Performance Tips
- Use shorter audio files for testing (under 1 minute)
- Ensure stable internet connection for API calls
- Monitor your API usage limits

## Production Deployment

For production deployment:

1. Set up proper environment variables
2. Use a production WSGI server like Gunicorn
3. Set up reverse proxy with Nginx
4. Use a proper database for job tracking (Redis/PostgreSQL)
5. Implement proper logging and monitoring
6. Set up SSL certificates
7. Configure proper CORS settings

## Support

If you encounter issues:
1. Check the logs in `backend/logs/`
2. Verify all API keys and configurations
3. Test with smaller audio files first
4. Check the GitHub repository for known issues
