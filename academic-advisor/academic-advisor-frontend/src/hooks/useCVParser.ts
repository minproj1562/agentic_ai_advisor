// src/hooks/useCVParser.ts
import { useState, useCallback } from 'react';
import { ParserService } from '../services/parser.service';
import { ExtractionService } from '../services/extraction.service';
import { ParsedCV, ExtractedSkills } from '../types/cv.types';

export const useCVParser = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const parserService = new ParserService();
  const extractionService = new ExtractionService();

  const parseCV = useCallback(async (
    file: File,
    options?: { onProgress?: (progress: number) => void }
  ): Promise<ParsedCV> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const parsed = await parserService.parse(file, {
        onProgress: options?.onProgress
      });
      
      return parsed;
    } catch (err) {
      const error = err as Error;
      setError(error);
      console.error('CV Parsing error:', error, { file: file.name });
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const extractSkills = useCallback(async (
    text: string
  ): Promise<ExtractedSkills[]> => {
    try {
      return await extractionService.extractSkills(text);
    } catch (err) {
      const error = err as Error;
      console.error('Skills Extraction error:', error);
      throw error;
    }
  }, []);

  const extractExperience = useCallback(async (
    text: string
  ): Promise<any> => {
    try {
      return await extractionService.extractExperience(text);
    } catch (err) {
      const error = err as Error;
      console.error('Experience Extraction error:', error);
      throw error;
    }
  }, []);

  return {
    parseCV,
    extractSkills,
    extractExperience,
    isLoading,
    error
  };
};