// src/utils/validation.ts

export interface FileValidationOptions {
  maxSize?: number;
  acceptedFormats?: string[];
  maxFiles?: number;
}

export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export const validateFile = (file: File, options: FileValidationOptions = {}): ValidationResult => {
  const {
    maxSize = 10 * 1024 * 1024, // 10MB default
    acceptedFormats = ['.pdf', '.doc', '.docx'],
    maxFiles = 1
  } = options;

  // Check file size
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `File size must be less than ${(maxSize / (1024 * 1024)).toFixed(0)}MB`
    };
  }

  // Check file type
  const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
  const isValidFormat = acceptedFormats.some(format => {
    if (format.startsWith('.')) {
      return fileExtension === format.toLowerCase();
    }
    return file.type.includes(format.replace('.', ''));
  });

  if (!isValidFormat) {
    return {
      isValid: false,
      error: `File format not supported. Accepted formats: ${acceptedFormats.join(', ')}`
    };
  }

  return { isValid: true };
};

export const validateFiles = (files: File[], options: FileValidationOptions = {}): ValidationResult => {
  const { maxFiles = 1 } = options;

  if (files.length > maxFiles) {
    return {
      isValid: false,
      error: `Maximum ${maxFiles} file${maxFiles > 1 ? 's' : ''} allowed`
    };
  }

  for (const file of files) {
    const validation = validateFile(file, options);
    if (!validation.isValid) {
      return validation;
    }
  }

  return { isValid: true };
};

// Email validation
export const validateEmail = (email: string): ValidationResult => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return {
      isValid: false,
      error: 'Please enter a valid email address'
    };
  }
  return { isValid: true };
};

// Required field validation
export const validateRequired = (value: string, fieldName: string): ValidationResult => {
  if (!value || value.trim().length === 0) {
    return {
      isValid: false,
      error: `${fieldName} is required`
    };
  }
  return { isValid: true };
};

// Length validation
export const validateLength = (value: string, min: number, max: number, fieldName: string): ValidationResult => {
  if (value.length < min) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${min} characters`
    };
  }
  if (value.length > max) {
    return {
      isValid: false,
      error: `${fieldName} must be less than ${max} characters`
    };
  }
  return { isValid: true };
};

// URL validation
export const validateURL = (url: string): ValidationResult => {
  try {
    new URL(url);
    return { isValid: true };
  } catch {
    return {
      isValid: false,
      error: 'Please enter a valid URL'
    };
  }
};

// Number validation
export const validateNumber = (value: string | number, min?: number, max?: number): ValidationResult => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(num)) {
    return {
      isValid: false,
      error: 'Please enter a valid number'
    };
  }

  if (min !== undefined && num < min) {
    return {
      isValid: false,
      error: `Value must be at least ${min}`
    };
  }

  if (max !== undefined && num > max) {
    return {
      isValid: false,
      error: `Value must be less than ${max}`
    };
  }

  return { isValid: true };
};