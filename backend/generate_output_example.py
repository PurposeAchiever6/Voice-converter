"""
Output file generator for Voice Converter Backend API
Generates example output files to demonstrate the continuous_with_spaces functionality
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from pydub import AudioSegment
import time

class OutputGenerator:
    """Generates example output files for demonstration"""
    
    def __init__(self):
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_sample_audio(self, duration_seconds: float = 10.0) -> str:
        """Generate a sample audio file for testing"""
        # Create a simple tone audio for demonstration
        sample_rate = 44100
        duration_ms = int(duration_seconds * 1000)
        
        # Generate a simple sine wave tone
        import math
        frequency = 440  # A4 note
        samples = []
        
        for i in range(int(sample_rate * duration_seconds)):
            t = i / sample_rate
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * t))
            samples.append(sample)
        
        # Create audio segment
        audio = AudioSegment(
            samples,
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        
        # Save sample audio
        sample_path = self.output_dir / "sample_input.wav"
        audio.export(str(sample_path), format="wav")
        
        return str(sample_path)
    
    def generate_continuous_with_spaces_example(self) -> Dict[str, Any]:
        """Generate an example of continuous_with_spaces output"""
        
        # Simulate the workflow from test_continuous_workflow_add_space.py
        example_data = {
            "workflow_name": "continuous_with_spaces",
            "description": "Maintains original timestamps with empty segments",
            "input_file": "sample_input.wav",
            "processing_steps": [
                {
                    "step": 1,
                    "name": "Transcription",
                    "description": "Extract sentences with timestamps using Gladia API",
                    "example_output": {
                        "sentences": [
                            {
                                "text": "Hello, this is a test sentence.",
                                "start_time": 0.5,
                                "end_time": 2.8
                            },
                            {
                                "text": "This is the second sentence with a gap before it.",
                                "start_time": 4.2,
                                "end_time": 7.1
                            },
                            {
                                "text": "And this is the final sentence.",
                                "start_time": 8.5,
                                "end_time": 10.2
                            }
                        ],
                        "total_sentences": 3,
                        "original_duration": 12.0
                    }
                },
                {
                    "step": 2,
                    "name": "Voice Cloning",
                    "description": "Generate voice clones for each sentence using ElevenLabs",
                    "example_output": {
                        "cloned_files": [
                            "temp_sentence_0.wav",
                            "temp_sentence_1.wav", 
                            "temp_sentence_2.wav"
                        ],
                        "voice_id": "pNInz6obpgDQGcFmaJgB",
                        "processing_time": "45.2s"
                    }
                },
                {
                    "step": 3,
                    "name": "Timeline Reconstruction",
                    "description": "Create final audio maintaining original timestamps with empty segments",
                    "example_output": {
                        "timeline": [
                            {"type": "silence", "duration": 0.5, "reason": "gap_before_sentence_1"},
                            {"type": "speech", "duration": 2.3, "sentence": 1, "original_duration": 2.3},
                            {"type": "silence", "duration": 1.4, "reason": "gap_between_sentences"},
                            {"type": "speech", "duration": 2.9, "sentence": 2, "original_duration": 2.9},
                            {"type": "silence", "duration": 1.4, "reason": "gap_between_sentences"},
                            {"type": "speech", "duration": 1.7, "sentence": 3, "original_duration": 1.7},
                            {"type": "silence", "duration": 1.8, "reason": "final_padding"}
                        ],
                        "final_duration": 12.0,
                        "original_duration": 12.0,
                        "duration_match": "perfect"
                    }
                },
                {
                    "step": 4,
                    "name": "Cleanup",
                    "description": "Remove temporary files",
                    "example_output": {
                        "deleted_files": 3,
                        "cleanup_status": "success"
                    }
                }
            ],
            "final_output": {
                "file_path": "outputs/continuous_with_spaces_example.wav",
                "duration": 12.0,
                "file_size": "1.2MB",
                "format": "WAV",
                "sample_rate": 44100,
                "channels": 1,
                "characteristics": [
                    "Maintains original timing",
                    "Preserves gaps and pauses",
                    "Same duration as input",
                    "Voice-cloned speech segments",
                    "Silent segments for timing"
                ]
            },
            "comparison_with_other_modes": {
                "continuous": {
                    "description": "Concatenates sentences without gaps",
                    "duration": "shorter",
                    "gaps": "removed",
                    "use_case": "Faster playback, no pauses"
                },
                "timestamp_based": {
                    "description": "Filters empty spaces and processes valid sentences",
                    "duration": "variable",
                    "gaps": "filtered",
                    "use_case": "Efficient processing, removes long silences"
                },
                "same_length": {
                    "description": "Maintains duration but eliminates gaps",
                    "duration": "same as original",
                    "gaps": "eliminated",
                    "use_case": "Consistent timing without pauses"
                },
                "continuous_with_spaces": {
                    "description": "Maintains original timestamps with empty segments",
                    "duration": "same as original",
                    "gaps": "preserved",
                    "use_case": "Perfect timing match, natural speech rhythm"
                }
            }
        }
        
        return example_data
    
    def generate_api_usage_example(self) -> Dict[str, Any]:
        """Generate API usage examples"""
        
        api_examples = {
            "upload_request": {
                "method": "POST",
                "url": "http://localhost:8000/upload",
                "headers": {
                    "Content-Type": "multipart/form-data"
                },
                "form_data": {
                    "file": "@audio_file.wav",
                    "continuous_with_spaces": "true",
                    "voice_id": "pNInz6obpgDQGcFmaJgB"
                },
                "curl_example": """curl -X POST "http://localhost:8000/upload" \\
  -F "file=@audio_file.wav" \\
  -F "continuous_with_spaces=true" \\
  -F "voice_id=pNInz6obpgDQGcFmaJgB" """
            },
            "upload_response": {
                "status_code": 200,
                "body": {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "queued",
                    "message": "File uploaded successfully, processing started"
                }
            },
            "status_check": {
                "method": "GET",
                "url": "http://localhost:8000/status/{job_id}",
                "response_examples": [
                    {
                        "stage": "processing",
                        "body": {
                            "job_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "processing",
                            "progress": 45,
                            "message": "Processing sentence 2/5 for continuous workflow",
                            "download_url": None,
                            "error": None
                        }
                    },
                    {
                        "stage": "completed",
                        "body": {
                            "job_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "completed",
                            "progress": 100,
                            "message": "Processing completed successfully",
                            "download_url": "file:///path/to/output.wav",
                            "error": None
                        }
                    }
                ]
            },
            "download_request": {
                "method": "GET",
                "url": "http://localhost:8000/download/{job_id}",
                "response": {
                    "content_type": "audio/wav",
                    "filename": "converted_{job_id}.wav",
                    "description": "Binary audio file content"
                }
            }
        }
        
        return api_examples
    
    def generate_test_results_template(self) -> Dict[str, Any]:
        """Generate a template for test results"""
        
        test_template = {
            "test_metadata": {
                "test_name": "Backend API Comprehensive Test",
                "test_file": "tests/1.leo test 8.28.wav",
                "api_url": "http://localhost:8000",
                "timestamp": time.time(),
                "test_duration": "estimated 2-5 minutes"
            },
            "expected_results": {
                "health_check": {
                    "expected": True,
                    "description": "API should be running and services accessible"
                },
                "gap_analysis": {
                    "expected": {
                        "success": True,
                        "sentences_count": "> 0",
                        "analysis": {
                            "total_gap_time": "> 0",
                            "speech_ratio": "0.0 - 1.0"
                        }
                    },
                    "description": "Should analyze audio gaps and provide recommendations"
                },
                "continuous_with_spaces": {
                    "expected": {
                        "success": True,
                        "output_file": "test_output_continuous_with_spaces_{job_id}.wav",
                        "processing_time": "< 300 seconds",
                        "progress_history": "should show step-by-step progress"
                    },
                    "description": "Main test - should process audio with continuous_with_spaces mode"
                },
                "other_modes": {
                    "continuous": {"expected": "should start successfully"},
                    "timestamp_based": {"expected": "should start successfully"},
                    "original": {"expected": "should start successfully"}
                }
            },
            "success_criteria": {
                "minimum_success_rate": "80%",
                "critical_tests": [
                    "health_check",
                    "continuous_with_spaces"
                ],
                "output_file_requirements": [
                    "File should exist",
                    "File size > 0 bytes",
                    "File format should be WAV",
                    "Duration should match or be close to original"
                ]
            }
        }
        
        return test_template
    
    async def generate_all_outputs(self) -> Dict[str, str]:
        """Generate all output files"""
        
        print("📁 Generating output files...")
        
        generated_files = {}
        
        # 1. Generate workflow example
        workflow_data = self.generate_continuous_with_spaces_example()
        workflow_file = self.output_dir / "continuous_with_spaces_workflow_example.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f, indent=2)
        generated_files["workflow_example"] = str(workflow_file)
        print(f"   ✅ Workflow example: {workflow_file}")
        
        # 2. Generate API usage examples
        api_data = self.generate_api_usage_example()
        api_file = self.output_dir / "api_usage_examples.json"
        with open(api_file, "w") as f:
            json.dump(api_data, f, indent=2)
        generated_files["api_examples"] = str(api_file)
        print(f"   ✅ API examples: {api_file}")
        
        # 3. Generate test results template
        test_template = self.generate_test_results_template()
        test_file = self.output_dir / "test_results_template.json"
        with open(test_file, "w") as f:
            json.dump(test_template, f, indent=2)
        generated_files["test_template"] = str(test_file)
        print(f"   ✅ Test template: {test_file}")
        
        # 4. Generate sample audio (optional)
        try:
            sample_audio = self.generate_sample_audio()
            generated_files["sample_audio"] = sample_audio
            print(f"   ✅ Sample audio: {sample_audio}")
        except Exception as e:
            print(f"   ⚠️ Sample audio generation failed: {e}")
        
        # 5. Generate README
        readme_content = self.generate_readme(generated_files)
        readme_file = self.output_dir / "README.md"
        with open(readme_file, "w") as f:
            f.write(readme_content)
        generated_files["readme"] = str(readme_file)
        print(f"   ✅ README: {readme_file}")
        
        return generated_files
    
    def generate_readme(self, generated_files: Dict[str, str]) -> str:
        """Generate README for the output files"""
        
        readme = f"""# Voice Converter Backend API - Output Files

This directory contains example output files and documentation for the Voice Converter Backend API, specifically focusing on the `continuous_with_spaces` functionality.

## Generated Files

### 1. Workflow Example (`continuous_with_spaces_workflow_example.json`)
- **Purpose**: Demonstrates the complete workflow of the `continuous_with_spaces` mode
- **Content**: Step-by-step process from transcription to final output
- **Based on**: `test_continuous_workflow_add_space.py` logic

### 2. API Usage Examples (`api_usage_examples.json`)
- **Purpose**: Shows how to use the API endpoints
- **Content**: Request/response examples, curl commands, status monitoring
- **Useful for**: Integration and testing

### 3. Test Results Template (`test_results_template.json`)
- **Purpose**: Template for expected test results
- **Content**: Success criteria, expected outputs, test metadata
- **Useful for**: Validation and debugging

### 4. Sample Audio (`sample_input.wav`)
- **Purpose**: Simple audio file for testing (if generated successfully)
- **Content**: 10-second sine wave tone
- **Note**: Replace with actual speech audio for real testing

### 5. README (`README.md`)
- **Purpose**: This documentation file
- **Content**: Overview of all generated files

## Key Features of continuous_with_spaces Mode

1. **Timestamp Preservation**: Maintains exact timing from original audio
2. **Gap Handling**: Adds silent segments where needed
3. **Duration Matching**: Output duration matches input duration
4. **Voice Cloning**: Replaces speech with cloned voice while preserving timing

## Usage Instructions

1. **Start the API server**:
   ```bash
   cd backend
   python -m app.main
   ```

2. **Run the comprehensive test**:
   ```bash
   python test_backend_api_comprehensive.py
   ```

3. **Check the results**:
   - Test results will be saved to `test_results_backend_api.json`
   - Output audio files will be saved with pattern `test_output_continuous_with_spaces_{{job_id}}.wav`

## API Endpoints

- `POST /upload` - Upload audio file for processing
- `GET /status/{{job_id}}` - Check processing status
- `GET /download/{{job_id}}` - Download processed audio
- `POST /analyze-gaps` - Analyze audio gaps without processing
- `GET /health` - Health check

## Processing Modes Comparison

| Mode | Duration | Gaps | Use Case |
|------|----------|------|----------|
| `continuous_with_spaces` | Same as original | Preserved | Perfect timing match |
| `continuous` | Shorter | Removed | Faster playback |
| `timestamp_based` | Variable | Filtered | Efficient processing |
| `same_length` | Same as original | Eliminated | Consistent timing |

## Files Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

{chr(10).join([f"- {name}: {path}" for name, path in generated_files.items()])}

## Next Steps

1. Test the API with real audio files
2. Verify the continuous_with_spaces functionality
3. Compare outputs with other processing modes
4. Integrate with frontend application

---

*Generated by Voice Converter Backend API Output Generator*
"""
        
        return readme

async def main():
    """Main function to generate all output files"""
    
    print("🎯 Voice Converter Backend API - Output Generator")
    print("=" * 60)
    
    generator = OutputGenerator()
    
    try:
        generated_files = await generator.generate_all_outputs()
        
        print("\n" + "=" * 60)
        print("✅ Output generation completed successfully!")
        print(f"📁 Output directory: {generator.output_dir}")
        print(f"📊 Generated {len(generated_files)} files:")
        
        for name, path in generated_files.items():
            print(f"   - {name}: {path}")
        
        print("\n💡 Next steps:")
        print("   1. Review the generated files")
        print("   2. Run the comprehensive test: python test_backend_api_comprehensive.py")
        print("   3. Check the API functionality with real audio files")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Output generation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
