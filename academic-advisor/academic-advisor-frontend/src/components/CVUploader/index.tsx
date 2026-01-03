// src/components/CVUploader/index.tsx
import React, { useState, useCallback } from 'react';
import { UploadZone } from './UploadZone';
import { useCVParser } from '.././../hooks/useCVParser';
import { useErrorHandler } from '.././../hooks/useErrorHandler';
import { CVFile, ParsedCV } from '../../types/cv.types';
import { validateFile } from '../../utils/validation';
import { motion } from 'framer-motion';

export const CVUploader: React.FC<{
  onSuccess: (data: ParsedCV) => void;
  onError?: (error: Error) => void;
  maxSize?: number;
  acceptedFormats?: string[];
}> = ({ 
  onSuccess, 
  onError,
  maxSize = 10 * 1024 * 1024, // 10MB
  acceptedFormats = ['.pdf', '.doc', '.docx']
}) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const { parseCV, extractSkills } = useCVParser();
  const { handleError } = useErrorHandler();

  const handleFileUpload = useCallback(async (files: File[]) => {
    const file = files[0];
    
    try {
      // Validate file
      const validation = validateFile(file, { maxSize, acceptedFormats });
      if (!validation.isValid) {
        throw new Error(validation.error);
      }

      setIsProcessing(true);
      setUploadProgress(0);

      // Create progress simulation
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // Parse CV
      const parsedData = await parseCV(file, {
        onProgress: (progress: number) => setUploadProgress(progress)
      });

      // Extract skills
      const skills = await extractSkills(parsedData.content);

      clearInterval(progressInterval);
      setUploadProgress(100);

      const result: ParsedCV = {
        ...parsedData,
        skills,
        metadata: {
          fileName: file.name,
          fileSize: file.size,
          uploadedAt: new Date(),
          mimeType: file.type
        }
      };

      onSuccess(result);
    } catch (error) {
      handleError(error as Error);
      onError?.(error as Error);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  }, [parseCV, extractSkills, handleError, maxSize, acceptedFormats, onSuccess, onError]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <UploadZone
        onFilesAccepted={handleFileUpload}
        progress={uploadProgress}
        isProcessing={isProcessing}
        acceptedFormats={acceptedFormats}
        maxSize={maxSize}
      />
    </motion.div>
  );
};