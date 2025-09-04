# Continuous With Spaces API Documentation

## Overview

The `continuous_with_spaces` functionality has been successfully implemented in the backend API. This feature is based on the workflow from `test_continuous_workflow_add_space.py` and provides continuous voice conversion while maintaining original timestamps with empty segments.

## API Endpoint

### POST /upload

Upload an audio file and process it with the continuous_with_spaces mode.

#### Parameters

- `file` (required): Audio file to process
- `voice_id` (optional): ElevenLabs voice ID to use
- `continuous_with_spaces` (optional, boolean): Set to `true` to enable this mode

#### Example Request

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_audio_file.wav" \
  -F "continuous_with_spaces=true" \
  -F "voice_id=your_voice_id"
```

#### Response

```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "File uploaded successfully, processing started"
}
```

## How It Works

1. **Transcription**: The audio is transcribed using Gladia service to get sentence timestamps
2. **Voice Cloning**: Each sentence is processed through ElevenLabs to generate voice clones
3. **Timeline Reconstruction**: The final audio is built by:
   - Adding empty segments to maintain original timing
   - Placing voice-cloned sentences at their original timestamps
   - Padding the end to match original duration

## Key Features

- **Timestamp Preservation**: Maintains exact timing from the original audio
- **Empty Space Handling**: Adds silent segments where needed
- **Duration Matching**: Output duration matches the original audio
- **Progress Tracking**: Real-time progress updates during processing

## Processing Modes Comparison

| Mode | Description | Duration | Gaps |
|------|-------------|----------|------|
| `continuous_with_spaces` | Maintains original timestamps with empty segments | Same as original | Preserved |
| `continuous` | Concatenates sentences without gaps | Shorter | Removed |
| `timestamp_based` | Filters empty spaces and processes valid sentences | Variable | Filtered |
| `same_length` | Maintains duration but eliminates gaps | Same as original | Eliminated |

## Status Monitoring

### GET /status/{job_id}

Monitor the processing status of your job.

#### Response

```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "progress": 75,
  "message": "Creating continuous audio with timestamp synchronization",
  "download_url": null,
  "error": null
}
```

#### Status Values

- `queued`: Job is waiting to be processed
- `processing`: Job is currently being processed
- `completed`: Job completed successfully
- `failed`: Job failed with an error

## Download Results

### GET /download/{job_id}

Download the processed audio file once the job is completed.

## Example Usage

```python
import requests
import time

# Upload file
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f},
        data={"continuous_with_spaces": "true"}
    )

job_id = response.json()["job_id"]

# Monitor progress
while True:
    status = requests.get(f"http://localhost:8000/status/{job_id}").json()
    print(f"Progress: {status['progress']}% - {status['message']}")
    
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    
    time.sleep(2)

# Download result
result = requests.get(f"http://localhost:8000/download/{job_id}")
with open("output.wav", "wb") as f:
    f.write(result.content)
```

## Technical Implementation

The implementation includes:

1. **ContinuousVoiceConverter Class**: Handles the complete workflow
2. **Timestamp Synchronization**: Uses pydub to create timeline-accurate audio
3. **Progress Tracking**: Updates job status throughout the process
4. **Error Handling**: Comprehensive error handling and cleanup
5. **Temporary File Management**: Automatic cleanup of intermediate files

## Testing

Use the provided test script to verify functionality:

```bash
cd backend
python test_continuous_api.py
```

This will test the complete workflow including upload, processing, and download.
