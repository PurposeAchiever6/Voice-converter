import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { validateAudioFile, formatFileSize } from '../services/api';

const FileUpload = ({ onFileSelect, disabled = false, selectedFile = null }) => {
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors.some(e => e.code === 'file-too-large')) {
        setError('File is too large. Maximum size is 100MB.');
      } else if (rejection.errors.some(e => e.code === 'file-invalid-type')) {
        setError('Invalid file type. Please upload WAV, MP3, M4A, FLAC, or OGG files.');
      } else {
        setError('File upload failed. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      
      try {
        validateAudioFile(file);
        onFileSelect(file);
      } catch (err) {
        setError(err.message);
      }
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false,
    disabled
  });

  const removeFile = () => {
    setError(null);
    onFileSelect(null);
  };

  const getDropzoneClass = () => {
    let baseClass = 'dropzone';
    
    if (disabled) {
      baseClass += ' opacity-50 cursor-not-allowed';
    } else if (isDragReject) {
      baseClass += ' dropzone-reject';
    } else if (isDragActive) {
      baseClass += ' dropzone-active';
    }
    
    return baseClass;
  };

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div {...getRootProps()} className={getDropzoneClass()}>
          <input {...getInputProps()} />
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-primary-100 rounded-full">
              <Upload className="w-8 h-8 text-primary-600" />
            </div>
            
            <div className="text-center">
              <p className="text-lg font-medium text-gray-900 mb-2">
                {isDragActive ? 'Drop your audio file here' : 'Upload Audio File'}
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Drag and drop your audio file here, or click to browse
              </p>
              <p className="text-xs text-gray-400">
                Supported formats: WAV, MP3, M4A, FLAC, OGG (max 100MB)
              </p>
            </div>
            
            {!disabled && (
              <button
                type="button"
                className="btn-primary"
                onClick={(e) => e.stopPropagation()}
              >
                Choose File
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-100 rounded-lg">
                <File className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            
            {!disabled && (
              <button
                onClick={removeFile}
                className="p-2 text-gray-400 hover:text-error-500 transition-colors"
                title="Remove file"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}
      
      {error && (
        <div className="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-error-500 flex-shrink-0" />
            <p className="text-sm text-error-700">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
