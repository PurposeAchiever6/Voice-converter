import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2, 
  Upload,
  Mic,
  Volume2,
  Layers,
  Cloud,
  Download
} from 'lucide-react';

const ProgressTracker = ({ status, onDownload, onReset }) => {
  if (!status) return null;

  const getStatusColor = () => {
    switch (status.status) {
      case 'completed':
        return 'text-success-600';
      case 'failed':
        return 'text-error-600';
      case 'processing':
      case 'queued':
        return 'text-primary-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = () => {
    const iconClass = `w-6 h-6 ${getStatusColor()}`;
    
    switch (status.status) {
      case 'completed':
        return <CheckCircle className={iconClass} />;
      case 'failed':
        return <XCircle className={iconClass} />;
      case 'processing':
        return <Loader2 className={`${iconClass} animate-spin`} />;
      case 'queued':
        return <Clock className={iconClass} />;
      default:
        return <Clock className={iconClass} />;
    }
  };

  const getProgressSteps = () => {
    const steps = [
      { key: 'upload', label: 'Upload', icon: Upload, threshold: 10 },
      { key: 'transcribe', label: 'Speech-to-Text', icon: Mic, threshold: 30 },
      { key: 'clone', label: 'Voice Cloning', icon: Volume2, threshold: 80 },
      { key: 'process', label: 'Audio Processing', icon: Layers, threshold: 90 },
      { key: 'upload_cloud', label: 'Cloud Upload', icon: Cloud, threshold: 100 },
    ];

    return steps.map((step, index) => {
      const isActive = status.progress >= step.threshold;
      const isCurrent = status.progress >= (steps[index - 1]?.threshold || 0) && 
                       status.progress < step.threshold;
      
      return {
        ...step,
        isActive,
        isCurrent,
        isCompleted: status.progress > step.threshold
      };
    });
  };

  const progressSteps = getProgressSteps();

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Processing Status
            </h3>
            <p className="text-sm text-gray-500">Job ID: {status.job_id}</p>
          </div>
        </div>
        
        <div className="w-16 h-16">
          <CircularProgressbar
            value={status.progress}
            text={`${status.progress}%`}
            styles={buildStyles({
              textSize: '24px',
              pathColor: status.status === 'failed' ? '#ef4444' : 
                        status.status === 'completed' ? '#22c55e' : '#3b82f6',
              textColor: '#374151',
              trailColor: '#e5e7eb',
              backgroundColor: '#f3f4f6',
            })}
          />
        </div>
      </div>

      {/* Progress Steps */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          {progressSteps.map((step, index) => {
            const StepIcon = step.icon;
            return (
              <div key={step.key} className="flex flex-col items-center space-y-2">
                <div className={`
                  p-3 rounded-full border-2 transition-all duration-300
                  ${step.isCompleted ? 'bg-success-100 border-success-500' :
                    step.isCurrent ? 'bg-primary-100 border-primary-500 animate-pulse' :
                    step.isActive ? 'bg-primary-50 border-primary-300' :
                    'bg-gray-50 border-gray-300'}
                `}>
                  <StepIcon className={`w-4 h-4 ${
                    step.isCompleted ? 'text-success-600' :
                    step.isCurrent ? 'text-primary-600' :
                    step.isActive ? 'text-primary-500' :
                    'text-gray-400'
                  }`} />
                </div>
                <span className={`text-xs font-medium ${
                  step.isActive ? 'text-gray-900' : 'text-gray-500'
                }`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
        
        {/* Progress Bar */}
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className={`p-4 rounded-lg border ${
        status.status === 'completed' ? 'status-success' :
        status.status === 'failed' ? 'status-error' :
        'status-processing'
      }`}>
        <p className="text-sm font-medium">
          {status.message}
        </p>
        
        {status.error && (
          <p className="text-sm mt-2 text-error-600">
            Error: {status.error}
          </p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center mt-6">
        <button
          onClick={onReset}
          className="btn-secondary"
        >
          Start New Conversion
        </button>
        
        {status.status === 'completed' && status.download_url && (
          <button
            onClick={onDownload}
            className="btn-primary flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Download Result</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default ProgressTracker;
