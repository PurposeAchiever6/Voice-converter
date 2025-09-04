import React, { useState, useEffect } from 'react';
import { AudioWaveform, Settings, Info, AlertTriangle } from 'lucide-react';
import FileUpload from './components/FileUpload';
import ProgressTracker from './components/ProgressTracker';
import { 
  voiceConverterAPI, 
  downloadFile, 
  downloadFromUrl 
} from './services/api';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [voiceId, setVoiceId] = useState('');
  const [jobStatus, setJobStatus] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [healthStatus, setHealthStatus] = useState(null);

  // Check API health on component mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await voiceConverterAPI.healthCheck();
      setHealthStatus(health);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthStatus({ status: 'unhealthy', error: err.message });
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    setJobStatus(null);
    setUploadProgress(0);
  };

  const handleStartProcessing = async () => {
    if (!selectedFile) {
      setError('Please select an audio file first.');
      return;
    }

    if (!voiceId.trim()) {
      setError('Please enter an ElevenLabs Voice ID.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Upload file and start processing
      const uploadResult = await voiceConverterAPI.uploadAudio(
        selectedFile,
        voiceId.trim(),
        setUploadProgress
      );

      console.log('Upload successful:', uploadResult);

      // Start polling for status
      const finalStatus = await voiceConverterAPI.pollJobStatus(
        uploadResult.job_id,
        (status) => {
          console.log('Status update:', status);
          setJobStatus(status);
        }
      );

      // Processing completed successfully
      setIsProcessing(false);
      console.log('Processing completed:', finalStatus);

    } catch (err) {
      console.error('Processing failed:', err);
      setError(err.message);
      setIsProcessing(false);
      
      // If there's a partial job status, keep it visible so user can see progress
      if (jobStatus && jobStatus.status === 'processing') {
        // Don't clear the job status, let user see the last known progress
        console.log('Keeping last known status visible for user reference');
      }
    }
  };

  const handleDownload = async () => {
    if (!jobStatus || !jobStatus.download_url) {
      setError('No download URL available.');
      return;
    }

    try {
      const result = await voiceConverterAPI.downloadResult(jobStatus.job_id);
      
      if (result.blob) {
        // Direct file download
        downloadFile(result.blob, result.filename);
      } else if (result.download_url) {
        // External URL download
        downloadFromUrl(result.download_url, `converted_${jobStatus.job_id}.wav`);
      } else {
        throw new Error('Invalid download response');
      }
    } catch (err) {
      console.error('Download failed:', err);
      setError(`Download failed: ${err.message}`);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setJobStatus(null);
    setIsProcessing(false);
    setError(null);
    setUploadProgress(0);
    setVoiceId('');
  };

  const isFormDisabled = isProcessing || (jobStatus && jobStatus.status === 'processing');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <AudioWaveform className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Voice Converter</h1>
              <p className="text-sm text-gray-500">
                Transform audio files using AI voice cloning technology
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Health Status Warning */}
        {healthStatus && healthStatus.status !== 'healthy' && (
          <div className="mb-6 p-4 bg-error-50 border border-error-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-error-500" />
              <div>
                <p className="text-sm font-medium text-error-800">
                  API Health Check Failed
                </p>
                <p className="text-sm text-error-600">
                  Some services may not be available. Please check your configuration.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Configuration Section */}
        {!jobStatus && (
          <div className="space-y-6">
            {/* Voice ID Input */}
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <Settings className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Configuration</h2>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="voiceId" className="block text-sm font-medium text-gray-700 mb-2">
                    ElevenLabs Voice ID *
                  </label>
                  <input
                    type="text"
                    id="voiceId"
                    value={voiceId}
                    onChange={(e) => setVoiceId(e.target.value)}
                    placeholder="Enter your ElevenLabs voice ID"
                    className="input-field"
                    disabled={isFormDisabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    You can find voice IDs in your ElevenLabs dashboard
                  </p>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <FileUpload
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
              disabled={isFormDisabled}
            />

            {/* Upload Progress */}
            {uploadProgress > 0 && uploadProgress < 100 && (
              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Uploading...</span>
                  <span className="text-sm text-gray-500">{uploadProgress}%</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Start Processing Button */}
            <div className="flex justify-center">
              <button
                onClick={handleStartProcessing}
                disabled={!selectedFile || !voiceId.trim() || isFormDisabled}
                className="btn-primary px-8 py-3 text-lg"
              >
                {isProcessing ? 'Starting Processing...' : 'Start Voice Conversion'}
              </button>
            </div>
          </div>
        )}

        {/* Progress Tracker */}
        {jobStatus && (
          <ProgressTracker
            status={jobStatus}
            onDownload={handleDownload}
            onReset={handleReset}
          />
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-error-50 border border-error-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-error-500 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-error-800">Error</p>
                <p className="text-sm text-error-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-12 card">
          <div className="flex items-center space-x-3 mb-4">
            <Info className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">How it works</h2>
          </div>
          
          <div className="space-y-3 text-sm text-gray-600">
            <p>
              <strong>1. Upload:</strong> Select an audio file (WAV, MP3, M4A, FLAC, or OGG format, max 100MB)
            </p>
            <p>
              <strong>2. Configure:</strong> Enter your ElevenLabs Voice ID for voice cloning
            </p>
            <p>
              <strong>3. Process:</strong> Our AI will transcribe the audio, clone it with the specified voice, and match timing
            </p>
            <p>
              <strong>4. Download:</strong> Get your converted audio file automatically
            </p>
          </div>
          
          <div className="mt-4 p-3 bg-primary-50 rounded-lg">
            <p className="text-xs text-primary-700">
              <strong>Note:</strong> You need valid API keys for Gladia (speech-to-text) and ElevenLabs (voice cloning) 
              configured on the server for this application to work.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <p className="text-center text-sm text-gray-500">
            Voice Converter - Powered by Gladia STT and ElevenLabs Voice Cloning
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
