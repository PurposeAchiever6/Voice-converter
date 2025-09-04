"""
FastAPI main application for Voice Converter
"""
import os
import uuid
import asyncio
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from .services.audio_processor import AudioProcessor
from .services.gladia_service import GladiaService
from .services.elevenlabs_service import ElevenLabsService
from .services.sentence_processor import SentenceProcessor
from .utils.config import get_settings
from .utils.logger import get_logger
from pydub import AudioSegment

# Initialize settings and logger
settings = get_settings()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Converter API",
    description="API for converting audio files using voice cloning",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for ngrok compatibility
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "ngrok-skip-browser-warning"
    ],
    expose_headers=[
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
        "ngrok-skip-browser-warning"
    ],
)

# Initialize services
audio_processor = AudioProcessor()
gladia_service = GladiaService()
elevenlabs_service = ElevenLabsService()
sentence_processor = SentenceProcessor()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

# Pydantic models
class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    download_url: Optional[str] = None
    error: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

# In-memory job tracking (in production, use Redis or database)
job_status = {}

class ContinuousVoiceConverter:
    """Continuous voice conversion workflow without gaps - maintains original timestamps with empty segments"""
    
    def __init__(self):
        self.gladia_service = gladia_service
        self.elevenlabs_service = elevenlabs_service
        self.audio_processor = audio_processor
        self.settings = settings
        self.temp_files = []  # Track temporary files for cleanup
    
    async def convert_voice_continuous_with_spaces(self, input_audio_path: str, voice_id: str, job_id: str) -> str:
        """
        Convert voice in audio file with continuous workflow maintaining original timestamps
        
        Args:
            input_audio_path: Path to input audio file
            voice_id: ElevenLabs voice ID to use
            job_id: Job ID for tracking
            
        Returns:
            Path to final converted audio file
        """
        try:
            input_path = Path(input_audio_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input audio file not found: {input_audio_path}")
            
            logger.info(f"Job {job_id}: Starting Continuous Voice Conversion with spaces")
            
            # Update job status
            job_status[job_id].progress = 15
            job_status[job_id].message = "Transcribing audio for continuous processing"
            
            # Step 1: Transcribe audio
            transcription_result = await self.gladia_service.transcribe_audio(str(input_path))
            sentence_count = len(transcription_result.sentences)
            logger.info(f"Job {job_id}: Found {sentence_count} sentences")
            
            if sentence_count == 0:
                raise Exception("No sentences found in transcription")
            
            # Step 2: Process each sentence (generate voice clones only)
            logger.info(f"Job {job_id}: Processing {sentence_count} sentences...")
            temp_audio_files = []
            
            for i, sentence in enumerate(transcription_result.sentences):
                # Update progress
                progress = 20 + (i / sentence_count) * 50
                job_status[job_id].progress = int(progress)
                job_status[job_id].message = f"Processing sentence {i+1}/{sentence_count} for continuous workflow"
                
                logger.info(f"Job {job_id}: Processing sentence {i+1}/{sentence_count}: {sentence.text[:50]}...")
                
                # Generate voice clone for this sentence
                temp_cloned_path = await self.elevenlabs_service.generate_speech(
                    sentence.text,
                    voice_id,
                    f"{job_id}_temp_sentence_{i}"
                )
                self.temp_files.append(temp_cloned_path)
                temp_audio_files.append(temp_cloned_path)
                
                logger.info(f"Job {job_id}: Sentence {i+1} voice cloned")
            
            # Step 3: Create continuous final audio with proper spacing
            job_status[job_id].progress = 75
            job_status[job_id].message = "Creating continuous audio with timestamp synchronization"
            
            final_audio_path = await self._create_continuous_audio_with_spaces(
                temp_audio_files,
                transcription_result.sentences,
                input_path,
                job_id
            )
            
            # Step 4: Cleanup temporary files
            job_status[job_id].progress = 95
            job_status[job_id].message = "Cleaning up temporary files"
            
            deleted_count = self._cleanup_temp_files()
            logger.info(f"Job {job_id}: Cleaned up {deleted_count} temporary files")
            
            logger.info(f"Job {job_id}: Continuous voice conversion completed successfully")
            
            return final_audio_path
            
        except Exception as e:
            logger.error(f"Job {job_id}: Continuous voice conversion failed: {str(e)}")
            # Cleanup on error
            self._cleanup_temp_files()
            raise Exception(f"Continuous voice conversion failed: {str(e)}")
    
    async def _create_continuous_audio_with_spaces(
        self, 
        temp_audio_files: list, 
        sentences: list,
        input_path: Path,
        job_id: str
    ) -> str:
        """Create final audio by maintaining original timestamps with empty segments"""
        try:
            # Create output filename (same as working test file)
            output_filename = f"{job_id}_continuous"
            output_path = Path(self.settings.OUTPUT_DIR) / f"{output_filename}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get original audio duration for reference
            original_audio = AudioSegment.from_file(str(input_path))
            original_duration = len(original_audio) / 1000.0
            
            # Start with empty audio
            final_audio = AudioSegment.empty()
            current_position = 0.0  # Track current position in seconds
            
            logger.info(f"Job {job_id}: Building timestamp-synchronized audio timeline...")
            logger.info(f"Job {job_id}: Original duration: {original_duration:.2f}s")
            
            for i, (audio_file, sentence) in enumerate(zip(temp_audio_files, sentences)):
                # Load sentence audio
                sentence_audio = AudioSegment.from_file(audio_file)
                sentence_duration = len(sentence_audio) / 1000.0
                
                # Calculate gap needed before this sentence
                gap_duration = sentence.start_time - current_position
                
                if gap_duration > 0:
                    # Add empty audio segment to maintain timing
                    gap_ms = int(gap_duration * 1000)
                    empty_segment = AudioSegment.silent(duration=gap_ms)
                    final_audio += empty_segment
                    logger.debug(f"Job {job_id}: Added {gap_duration:.2f}s empty segment before sentence {i+1}")
                
                # Add the sentence audio
                final_audio += sentence_audio
                
                # Update current position to end of this sentence
                current_position = sentence.start_time + sentence_duration
                
                logger.debug(f"Job {job_id}: Added sentence {i+1} audio ({sentence_duration:.2f}s) at {sentence.start_time:.2f}s")
            
            # Add final padding if needed to match original duration
            final_duration = len(final_audio) / 1000.0
            if final_duration < original_duration:
                remaining_gap = original_duration - final_duration
                if remaining_gap > 0:
                    gap_ms = int(remaining_gap * 1000)
                    empty_segment = AudioSegment.silent(duration=gap_ms)
                    final_audio += empty_segment
                    logger.debug(f"Job {job_id}: Added final {remaining_gap:.2f}s padding to match original duration")
            
            # Export final audio
            final_audio.export(
                str(output_path),
                format="wav",
                parameters=[
                    "-ar", str(self.audio_processor.sample_rate),
                    "-ac", str(self.audio_processor.channels)
                ]
            )
            
            final_duration = len(final_audio) / 1000.0
            logger.info(f"Job {job_id}: Timestamp-synchronized audio created: {final_duration:.2f}s duration")
            logger.info(f"Job {job_id}: Duration match: Original {original_duration:.2f}s → Output {final_duration:.2f}s")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Job {job_id}: Continuous audio creation failed: {str(e)}")
            raise Exception(f"Continuous audio creation failed: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up all temporary files"""
        deleted_count = 0
        for temp_file in self.temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {str(e)}")
        
        self.temp_files.clear()
        return deleted_count

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Voice Converter API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check external services with timeout but don't fail if they're temporarily unavailable
        services_status = {}
        
        try:
            # Add timeout to prevent hanging
            services_status["gladia"] = await asyncio.wait_for(
                gladia_service.health_check(), 
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("Gladia service health check timed out")
            services_status["gladia"] = {"status": "warning", "message": "Service health check timed out"}
        except Exception as e:
            logger.warning(f"Gladia service health check failed: {str(e)}")
            services_status["gladia"] = {"status": "warning", "message": "Service temporarily unavailable"}
        
        try:
            # Add timeout to prevent hanging
            services_status["elevenlabs"] = await asyncio.wait_for(
                elevenlabs_service.health_check(), 
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("ElevenLabs service health check timed out")
            services_status["elevenlabs"] = {"status": "warning", "message": "Service health check timed out"}
        except Exception as e:
            logger.warning(f"ElevenLabs service health check failed: {str(e)}")
            services_status["elevenlabs"] = {"status": "warning", "message": "Service temporarily unavailable"}
        
        # API is healthy if the core service is running, even if external services have issues
        return {
            "status": "healthy",
            "message": "Voice Converter API is running",
            "services": services_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "healthy",  # Still return healthy for basic API functionality
            "message": "Voice Converter API is running with limited service checks",
            "error": str(e)
        }

@app.post("/upload", response_model=JobResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    voice_id: Optional[str] = Form(None),
    continuous: Optional[str] = Form(None),
    same_length: Optional[str] = Form(None),
    timestamp_based: Optional[str] = Form(None),
    continuous_with_spaces: Optional[str] = Form(None)
):
    """
    Upload audio file and start processing
    
    Args:
        file: Audio file to process
        voice_id: ElevenLabs voice ID to use
        continuous: If True, creates continuous audio without gaps (shorter duration)
        same_length: If True, maintains original duration but eliminates gaps
        timestamp_based: If True, uses sentence-by-sentence processing with timestamp handling to avoid empty spaces
        continuous_with_spaces: If True, creates continuous audio maintaining original timestamps with empty segments (from test_continuous_workflow_add_space.py)
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in settings.ALLOWED_EXTENSIONS.split(','):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate job ID and save file
        job_id = str(uuid.uuid4())
        input_path = Path(settings.UPLOAD_DIR) / f"{job_id}_{file.filename}"
        
        with open(input_path, "wb") as f:
            f.write(content)
        
        # Initialize job status
        job_status[job_id] = ProcessingStatus(
            job_id=job_id,
            status="queued",
            progress=0,
            message="File uploaded successfully, processing queued"
        )
        
        # Start background processing
        background_tasks.add_task(
            process_audio_file, 
            job_id, 
            str(input_path), 
            voice_id or settings.ELEVENLABS_VOICE_ID,
            continuous,
            same_length,
            timestamp_based,
            continuous_with_spaces
        )
        
        logger.info(f"Started processing job {job_id} for file {file.filename}")
        
        return JobResponse(
            job_id=job_id,
            status="queued",
            message="File uploaded successfully, processing started"
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=ProcessingStatus)
async def get_job_status(job_id: str):
    """
    Get processing status for a job
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id]

@app.get("/download/{job_id}")
async def download_result(job_id: str):
    """
    Download processed audio file
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not status.download_url:
        raise HTTPException(status_code=404, detail="Download URL not available")
    
    # If it's a local file, serve it directly
    if status.download_url.startswith("file://"):
        file_path = status.download_url.replace("file://", "")
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="audio/wav",
                filename=f"converted_{job_id}.wav"
            )
    
    # Otherwise, redirect to the cloud URL
    return JSONResponse({
        "download_url": status.download_url,
        "message": "Use the download_url to get the file"
    })

@app.post("/analyze-gaps")
async def analyze_audio_gaps(file: UploadFile = File(...)):
    """
    Analyze gaps and empty spaces in audio file without processing
    
    Args:
        file: Audio file to analyze
        
    Returns:
        Gap analysis results showing empty spaces and sentence timing
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in settings.ALLOWED_EXTENSIONS.split(','):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save temporary file for analysis
        temp_id = str(uuid.uuid4())
        temp_path = Path(settings.UPLOAD_DIR) / f"temp_analysis_{temp_id}_{file.filename}"
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        try:
            # Transcribe audio to get timestamps
            transcription_result = await gladia_service.transcribe_audio(str(temp_path))
            
            # Convert to dictionary format
            sentences_dict = [
                {
                    'text': sentence.text,
                    'start_time': sentence.start_time,
                    'end_time': sentence.end_time
                }
                for sentence in transcription_result.sentences
            ]
            
            # Analyze gaps
            gap_analysis = await sentence_processor.analyze_sentence_gaps(sentences_dict)
            
            # Add sentence details for better understanding
            sentence_details = []
            for i, sentence in enumerate(sentences_dict):
                duration = sentence['end_time'] - sentence['start_time']
                sentence_details.append({
                    'index': i + 1,
                    'text': sentence['text'][:100] + '...' if len(sentence['text']) > 100 else sentence['text'],
                    'start_time': sentence['start_time'],
                    'end_time': sentence['end_time'],
                    'duration': duration,
                    'is_valid': duration >= 0.1 and len(sentence['text'].strip()) >= 2
                })
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "analysis": gap_analysis,
                "sentences": sentence_details,
                "recommendations": {
                    "use_timestamp_based": gap_analysis.get('total_gap_time', 0) > 1.0,
                    "gap_reduction_potential": f"{gap_analysis.get('total_gap_time', 0):.1f}s",
                    "speech_efficiency": f"{gap_analysis.get('speech_ratio', 0):.1%}"
                }
            }
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        logger.error(f"Gap analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_audio_file(job_id: str, input_path: str, voice_id: str, continuous: str = None, same_length: str = None, timestamp_based: str = None, continuous_with_spaces: str = None):
    """
    Background task to process audio file
    """
    try:
        logger.info(f"Starting processing for job {job_id}")
        
        # Convert string parameters to boolean
        continuous_bool = continuous and continuous.lower() == 'true'
        same_length_bool = same_length and same_length.lower() == 'true'
        timestamp_based_bool = timestamp_based and timestamp_based.lower() == 'true'
        continuous_with_spaces_bool = continuous_with_spaces and continuous_with_spaces.lower() == 'true'
        
        logger.info(f"Job {job_id}: Processing modes - continuous: {continuous}, same_length: {same_length}, timestamp_based: {timestamp_based}, continuous_with_spaces: {continuous_with_spaces}")
        logger.info(f"Job {job_id}: Boolean modes - continuous: {continuous_bool}, same_length: {same_length_bool}, timestamp_based: {timestamp_based_bool}, continuous_with_spaces: {continuous_with_spaces_bool}")
        
        # Update status
        job_status[job_id].status = "processing"
        job_status[job_id].progress = 10
        job_status[job_id].message = "Starting audio processing"
        
        # Initialize variables
        processed_chunks = []
        transcription_result = None
        
        if continuous_with_spaces_bool:
            # Continuous with spaces mode: Use the ContinuousVoiceConverter from test_continuous_workflow_add_space.py
            # This handles transcription internally, so no need to do it here
            converter = ContinuousVoiceConverter()
            output_path = await converter.convert_voice_continuous_with_spaces(input_path, voice_id, job_id)
            # No need for additional concatenation as converter handles it
            processed_chunks = []  # Empty since cleanup expects this
            # Note: converter handles its own temp file cleanup
        elif timestamp_based_bool:
            # Step 1: Convert speech to text with timestamps for timestamp-based mode
            logger.info(f"Job {job_id}: Starting STT conversion")
            transcription_result = await gladia_service.transcribe_audio(input_path)
            
            job_status[job_id].progress = 30
            job_status[job_id].message = "Speech-to-text completed, starting voice cloning"
            
            logger.info(f"Job {job_id}: Starting voice cloning for {len(transcription_result.sentences)} sentences")
        else:
            # Step 1: Convert speech to text with timestamps for other modes
            logger.info(f"Job {job_id}: Starting STT conversion")
            transcription_result = await gladia_service.transcribe_audio(input_path)
            
            job_status[job_id].progress = 30
            job_status[job_id].message = "Speech-to-text completed, starting voice cloning"
            
            logger.info(f"Job {job_id}: Starting voice cloning for {len(transcription_result.sentences)} sentences")
        
        if not continuous_with_spaces_bool:
            # Only process other modes if not using continuous_with_spaces
            if timestamp_based_bool:
                # Timestamp-based mode: Use sentence processor to avoid empty spaces
                job_status[job_id].progress = 35
                job_status[job_id].message = "Analyzing sentence gaps and filtering empty spaces"
                
                # Analyze gaps in the original audio
                sentences_dict = [
                    {
                        'text': sentence.text,
                        'start_time': sentence.start_time,
                        'end_time': sentence.end_time
                    }
                    for sentence in transcription_result.sentences
                ]
                
                gap_analysis = await sentence_processor.analyze_sentence_gaps(sentences_dict)
                logger.info(f"Job {job_id}: Gap analysis - {gap_analysis.get('total_gap_time', 0):.2f}s gaps detected")
                
                job_status[job_id].progress = 40
                job_status[job_id].message = f"Processing {gap_analysis.get('filtered_sentences', 0)} valid sentences with timestamp handling"
                
                # Use sentence processor for timestamp-based processing
                output_path = await sentence_processor.process_sentences_with_timestamps(
                    input_path,
                    sentences_dict,
                    voice_id,
                    f"{job_id}_timestamp_based"
                )
                
                # No need for additional concatenation as sentence processor handles it
                processed_chunks = []  # Empty since cleanup expects this
            elif same_length_bool:
                # Same length mode: Generate voice clones and adjust to maintain original duration
                from tests.test_same_length_workflow import SameLengthVoiceConverter
                converter = SameLengthVoiceConverter()
                output_path = await converter.convert_voice_same_length(input_path)
            elif continuous_bool:
                # Continuous mode: Generate voice clones without timing matching
                for i, sentence in enumerate(transcription_result.sentences):
                    # Update progress
                    progress = 30 + (i / len(transcription_result.sentences)) * 50
                    job_status[job_id].progress = int(progress)
                    job_status[job_id].message = f"Processing sentence {i+1}/{len(transcription_result.sentences)}"
                    
                    # Generate voice clone for this sentence (no timing matching)
                    cloned_audio_path = await elevenlabs_service.generate_speech(
                        sentence.text, 
                        voice_id, 
                        f"{job_id}_sentence_{i}"
                    )
                    
                    processed_chunks.append(cloned_audio_path)
                
                job_status[job_id].progress = 80
                job_status[job_id].message = "Concatenating audio chunks"
                
                # Step 3: Concatenate all processed chunks
                logger.info(f"Job {job_id}: Concatenating {len(processed_chunks)} chunks")
                output_path = await audio_processor.concatenate_audio(
                    processed_chunks, 
                    f"{job_id}_continuous"
                )
            else:
                # Original mode: Generate voice clones with timing matching
                for i, sentence in enumerate(transcription_result.sentences):
                    # Update progress
                    progress = 30 + (i / len(transcription_result.sentences)) * 50
                    job_status[job_id].progress = int(progress)
                    job_status[job_id].message = f"Processing sentence {i+1}/{len(transcription_result.sentences)}"
                    
                    # Generate voice clone for this sentence
                    cloned_audio_path = await elevenlabs_service.generate_speech(
                        sentence.text, 
                        voice_id, 
                        f"{job_id}_sentence_{i}"
                    )
                    
                    # Match timing with original audio chunk
                    matched_audio_path = await audio_processor.match_timing(
                        cloned_audio_path,
                        sentence.start_time,
                        sentence.end_time,
                        f"{job_id}_matched_{i}"
                    )
                    
                    processed_chunks.append(matched_audio_path)
                
                job_status[job_id].progress = 80
                job_status[job_id].message = "Concatenating audio chunks"
                
                # Step 3: Concatenate all processed chunks
                logger.info(f"Job {job_id}: Concatenating {len(processed_chunks)} chunks")
                output_path = await audio_processor.concatenate_audio(
                    processed_chunks, 
                    f"{job_id}_final"
                )
        
        job_status[job_id].progress = 90
        job_status[job_id].message = "Finalizing output file"
        
        # Step 4: Set local file URL for download
        logger.info(f"Job {job_id}: Setting up local file serving")
        download_url = f"file://{output_path}"
        
        # Step 5: Complete
        job_status[job_id].status = "completed"
        job_status[job_id].progress = 100
        job_status[job_id].message = "Processing completed successfully"
        job_status[job_id].download_url = download_url
        
        logger.info(f"Job {job_id}: Processing completed successfully")
        
        # Cleanup temporary files
        await cleanup_temp_files(job_id, input_path, processed_chunks, output_path)
        
    except Exception as e:
        logger.error(f"Job {job_id}: Processing failed: {str(e)}")
        job_status[job_id].status = "failed"
        job_status[job_id].error = str(e)
        job_status[job_id].message = f"Processing failed: {str(e)}"

async def cleanup_temp_files(job_id: str, input_path: str, processed_chunks: list, output_path: str):
    """
    Clean up temporary files - removes input file and processed chunks, keeps only output file
    """
    try:
        deleted_count = 0
        
        # Remove input file
        if os.path.exists(input_path):
            os.remove(input_path)
            deleted_count += 1
            logger.debug(f"Job {job_id}: Deleted input file: {input_path}")
        
        # Remove processed chunks
        for chunk_path in processed_chunks:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
                deleted_count += 1
                logger.debug(f"Job {job_id}: Deleted chunk file: {chunk_path}")
        
        # Clean up any remaining temp files with job_id pattern
        # This handles temp files created by ElevenLabs service
        temp_patterns = [
            f"{job_id}_temp_sentence_*",
            f"{job_id}_sentence_*",
            f"{job_id}_matched_*"
        ]
        
        # Check uploads and outputs directories for temp files
        for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR]:
            if os.path.exists(directory):
                for file_path in Path(directory).glob(f"{job_id}_temp_*"):
                    try:
                        if file_path.exists() and str(file_path) != output_path:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Job {job_id}: Deleted temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Job {job_id}: Failed to delete temp file {file_path}: {str(e)}")
        
        # Keep only the final output file
        logger.info(f"Job {job_id}: Cleanup completed - deleted {deleted_count} temp files, kept output: {output_path}")
        
    except Exception as e:
        logger.warning(f"Job {job_id}: Cleanup failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
