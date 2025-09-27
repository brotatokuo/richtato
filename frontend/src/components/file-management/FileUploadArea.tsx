import React from 'react';
import { Upload, X, RefreshCw, AlertCircle } from 'lucide-react';
import { FileUploadState } from './types';

interface FileUploadAreaProps {
  isDragOver: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  uploads?: FileUploadState[];
  onCancelUpload?: (index: number) => void;
  onRetryUpload?: (index: number) => void;
}

export const FileUploadArea: React.FC<FileUploadAreaProps> = ({
  isDragOver,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileSelect,
  uploads = [],
  onCancelUpload,
  onRetryUpload,
}) => {
  const handleClick = () => {
    const fileInput = document.getElementById(
      'file-upload'
    ) as HTMLInputElement;
    fileInput?.click();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading':
        return 'text-blue-600';
      case 'uploaded':
        return 'text-green-600';
      case 'processing':
        return 'text-yellow-600';
      case 'vectorized':
        return 'text-green-700';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'uploading':
        return 'Uploading';
      case 'uploaded':
        return 'Uploaded';
      case 'processing':
        return 'Processing';
      case 'vectorized':
        return 'Complete';
      case 'error':
        return 'Error';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
          isDragOver
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary hover:bg-primary/5'
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={handleClick}
      >
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">
          {isDragOver ? 'Drop files here' : 'Drag and drop files here'}
        </h3>
        <p className="text-muted-foreground mb-4">or click to select files</p>
        <input
          type="file"
          multiple
          onChange={onFileSelect}
          className="hidden"
          id="file-upload"
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.svg,.mp4,.mov,.avi"
        />
      </div>

      {/* Upload Progress List */}
      {uploads.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-sm text-gray-700">Upload Progress</h4>
          {uploads.map((upload, index) => (
            <div
              key={index}
              className="border rounded-lg p-4 bg-white shadow-sm"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {upload.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(upload.file.size)}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`text-xs font-medium ${getStatusColor(upload.status)}`}
                  >
                    {getStatusText(upload.status)}
                  </span>
                  {upload.status === 'error' &&
                    upload.error &&
                    onRetryUpload && (
                      <button
                        onClick={() => onRetryUpload(index)}
                        className="text-blue-600 hover:text-blue-800 p-1"
                        title="Retry upload"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                    )}
                  {upload.status !== 'vectorized' && onCancelUpload && (
                    <button
                      onClick={() => onCancelUpload(index)}
                      className="text-gray-400 hover:text-red-600 p-1"
                      title="Cancel upload"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              {(upload.status === 'uploading' ||
                upload.status === 'processing') && (
                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      upload.status === 'uploading'
                        ? 'bg-blue-600'
                        : 'bg-yellow-500'
                    }`}
                    style={{ width: `${upload.progress}%` }}
                  ></div>
                </div>
              )}

              {/* Error Message */}
              {upload.status === 'error' && upload.error && (
                <div className="flex items-center text-red-600 text-xs mt-2">
                  <AlertCircle className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="truncate">{upload.error}</span>
                </div>
              )}

              {/* Success Message */}
              {upload.status === 'vectorized' && (
                <div className="text-green-600 text-xs mt-2">
                  ✓ Upload complete and processed
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
