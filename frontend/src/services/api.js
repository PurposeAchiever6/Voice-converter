import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 300000, // 5 minutes timeout for file uploads
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`Response from ${response.config.url}:`, response.status);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API endpoints
export const voiceConverterAPI = {
  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  },

  // Upload audio file and start processing
  uploadAudio: async (file, voiceId = null, onUploadProgress = null) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (voiceId) {
        formData.append('voice_id', voiceId);
      }

      // Use continuous_with_spaces mode for best quality (matches working test)
      formData.append('continuous_with_spaces', 'true');

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onUploadProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onUploadProgress(percentCompleted);
          }
        },
      });

      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      throw new Error(`Upload failed: ${errorMessage}`);
    }
  },

  // Get job status
  getJobStatus: async (jobId) => {
    try {
      const response = await api.get(`/status/${jobId}`);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      throw new Error(`Failed to get job status: ${errorMessage}`);
    }
  },

  // Download result
  downloadResult: async (jobId) => {
    try {
      const response = await api.get(`/download/${jobId}`, {
        responseType: 'blob', // Important for file downloads
      });

      // Check if response is JSON (error) or blob (file)
      if (response.headers['content-type']?.includes('application/json')) {
        // It's a JSON response with download URL
        const text = await response.data.text();
        const jsonData = JSON.parse(text);
        return jsonData;
      } else {
        // It's a file blob
        return {
          blob: response.data,
          filename: `converted_${jobId}.wav`,
          contentType: response.headers['content-type'] || 'audio/wav'
        };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      throw new Error(`Download failed: ${errorMessage}`);
    }
  },

  // Poll job status until completion
  pollJobStatus: async (jobId, onProgress = null, maxAttempts = 600) => {
    let attempts = 0;
    let consecutiveErrors = 0;
    const maxConsecutiveErrors = 5;
    
    while (attempts < maxAttempts) {
      try {
        const status = await voiceConverterAPI.getJobStatus(jobId);
        
        // Reset consecutive error count on successful request
        consecutiveErrors = 0;
        
        if (onProgress) {
          onProgress(status);
        }

        if (status.status === 'completed') {
          return status;
        } else if (status.status === 'failed') {
          throw new Error(status.error || 'Job failed');
        }

        // Dynamic polling interval based on progress
        let pollInterval = 2000; // Default 2 seconds
        if (status.progress < 20) {
          pollInterval = 3000; // 3 seconds for initial processing
        } else if (status.progress < 50) {
          pollInterval = 2000; // 2 seconds for active processing
        } else if (status.progress < 80) {
          pollInterval = 1500; // 1.5 seconds for final stages
        } else {
          pollInterval = 1000; // 1 second for completion
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
        attempts++;
      } catch (error) {
        consecutiveErrors++;
        
        // If we get too many consecutive errors, fail immediately
        if (consecutiveErrors >= maxConsecutiveErrors) {
          throw new Error(`Polling failed after ${maxConsecutiveErrors} consecutive errors: ${error.message}`);
        }
        
        // If we've reached max attempts, throw the error
        if (attempts >= maxAttempts - 1) {
          throw new Error(`Job processing timeout after ${Math.floor(maxAttempts * 2 / 60)} minutes. The job may still be processing on the server. Please check back later or contact support if the issue persists.`);
        }
        
        // Wait longer before retrying on error
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
      }
    }

    throw new Error(`Job processing timeout after ${Math.floor(maxAttempts * 2 / 60)} minutes. The job may still be processing on the server. Please check back later or contact support if the issue persists.`);
  },
};

// Utility functions
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const downloadFromUrl = (url, filename) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const validateAudioFile = (file) => {
  const allowedTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a', 'audio/flac', 'audio/ogg'];
  const maxSize = 100 * 1024 * 1024; // 100MB
  
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type. Please upload WAV, MP3, M4A, FLAC, or OGG files.');
  }
  
  if (file.size > maxSize) {
    throw new Error('File too large. Maximum size is 100MB.');
  }
  
  return true;
};

export default api;
