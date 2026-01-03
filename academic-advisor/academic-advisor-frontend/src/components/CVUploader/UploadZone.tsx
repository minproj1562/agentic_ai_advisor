// src/components/CVUploader/UploadZone.tsx
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';

interface UploadZoneProps {
  onFilesAccepted: (files: File[]) => void;
  progress: number;
  isProcessing: boolean;
  acceptedFormats: string[];
  maxSize: number;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFilesAccepted,
  progress,
  isProcessing,
  acceptedFormats,
  maxSize
}) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFilesAccepted(acceptedFiles);
    }
  }, [onFilesAccepted]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptedFormats.reduce((acc, format) => {
      acc[format] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize,
    maxFiles: 1,
    disabled: isProcessing
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'relative border-2 border-dashed rounded-xl p-8 transition-all duration-200',
        'hover:border-indigo-400 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10',
        isDragActive && 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20',
        isDragReject && 'border-red-500 bg-red-50 dark:bg-red-900/20',
        isProcessing && 'pointer-events-none opacity-60',
        'border-gray-300 dark:border-gray-600'
      )}
    >
      <input {...getInputProps()} />
      
      <AnimatePresence mode="wait">
        {isProcessing ? (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center space-y-4"
          >
            <div className="relative mx-auto w-20 h-20">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className="text-gray-200 dark:text-gray-700"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="36"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 36}`}
                  strokeDashoffset={`${2 * Math.PI * 36 * (1 - progress / 100)}`}
                  className="text-indigo-500 transition-all duration-300"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {Math.round(progress)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Processing your CV...
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="upload"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center space-y-4"
          >
            <div className="mx-auto w-16 h-16 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
              {isDragActive ? (
                <FileText className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              ) : (
                <Upload className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              )}
            </div>
            
            <div>
              <p className="text-base font-medium text-gray-900 dark:text-white">
                {isDragActive ? 'Drop your CV here' : 'Upload your CV'}
              </p>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Drag and drop or click to browse
              </p>
            </div>
            
            <div className="text-xs text-gray-400 dark:text-gray-500">
              <p>Accepted formats: {acceptedFormats.join(', ')}</p>
              <p>Max size: {(maxSize / (1024 * 1024)).toFixed(0)}MB</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};