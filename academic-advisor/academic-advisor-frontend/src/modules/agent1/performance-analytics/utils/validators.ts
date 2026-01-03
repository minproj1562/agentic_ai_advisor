// modules/agent1/performance-analytics/utils/validators.ts
import { z } from 'zod';
import {
  PerformanceTrend,
  PredictionConfig,
  SubjectData,
  WeakArea
} from '../types/analytics.types';

/**
 * Validate analytics data
 */
export function validateAnalyticsData(data: any): PerformanceTrend {
  const schema = z.object({
    studentId: z.string().min(1),
    dataPoints: z.array(z.object({
      date: z.string().datetime(),
      gpa: z.number().min(0).max(4),
      percentile: z.number().min(0).max(100).optional(),
      improvement: z.number().optional(),
      confidence: z.number().min(0).max(1).optional()
    })).min(1),
    currentGPA: z.number().min(0).max(4).optional(),
    percentile: z.number().min(0).max(100).optional(),
    subjects: z.array(z.object({
      id: z.string(),
      name: z.string(),
      category: z.string(),
      credits: z.number().positive(),
      currentGrade: z.number().min(0).max(100),
      classAverage: z.number().min(0).max(100).optional(),
      // FIXED: Made trend required with default value
      trend: z.number().default(0)
    })).optional(),
    lastUpdated: z.string().datetime().optional(),
    projection: z.array(z.any()).optional()
  });

  try {
    return schema.parse(data);
  } catch (error) {
    console.error('Analytics data validation failed:', error);
    throw new Error('Invalid analytics data format');
  }
}

/**
 * Validate prediction configuration
 */
export function validatePredictionData(config: any): PredictionConfig {
  // FIXED: Create a custom refinement to properly type the modelType
  const schema = z.object({
    modelType: z.string().refine((val): val is 'linear' | 'polynomial' | 'exponential' | 'ml' => 
      ['linear', 'polynomial', 'exponential', 'ml'].includes(val),
      { message: 'Model type must be one of: linear, polynomial, exponential, ml' }
    ),
    horizonDays: z.number().positive().max(365),
    confidenceLevel: z.number().min(0.5).max(0.99),
    includeSeasonality: z.boolean(),
    includeExternalFactors: z.boolean(),
    customFeatures: z.array(z.string()).optional(),
    historicalData: z.array(z.object({
      date: z.string(),
      gpa: z.number().min(0).max(4)
    })).min(2)
  });

  try {
    const result = schema.parse(config);
    // FIXED: Explicitly cast to PredictionConfig to ensure proper typing
    return result as PredictionConfig;
  } catch (error) {
    console.error('Prediction config validation failed:', error);
    throw new Error('Invalid prediction configuration');
  }
}

/**
 * Validate subject data
 */
export function validateSubjectData(data: any): SubjectData {
  const schema = z.object({
    id: z.string().min(1),
    name: z.string().min(1),
    category: z.string().min(1),
    credits: z.number().positive(),
    currentGrade: z.number().min(0).max(100),
    previousGrade: z.number().min(0).max(100).optional(),
    classAverage: z.number().min(0).max(100).optional(),
    rank: z.number().positive().optional(),
    totalStudents: z.number().positive().optional(),
    attendance: z.number().min(0).max(100).optional(),
    completedAssignments: z.number().min(0).optional(),
    totalAssignments: z.number().min(0).optional(),
    weakTopics: z.array(z.string()).optional(),
    recommendation: z.string().optional(),
    // FIXED: Made trend required with default value
    trend: z.number().default(0)
  });

  try {
    return schema.parse(data);
  } catch (error) {
    console.error('Subject data validation failed:', error);
    throw new Error('Invalid subject data format');
  }
}

/**
 * Validate email
 */
export function validateEmail(email: string): boolean {
  const schema = z.string().email();
  try {
    schema.parse(email);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate student ID
 */
export function validateStudentId(id: string): boolean {
  const schema = z.string().regex(/^[A-Z0-9]{6,12}$/);
  try {
    schema.parse(id);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate GPA value
 */
export function validateGPA(gpa: number): boolean {
  return gpa >= 0 && gpa <= 4 && !isNaN(gpa);
}

/**
 * Validate date range
 */
export function validateDateRange(startDate: string, endDate: string): boolean {
  try {
    const start = new Date(startDate);
    const end = new Date(endDate);
    return start < end && start <= new Date();
  } catch {
    return false;
  }
}

/**
 * Validate file upload
 */
export function validateFileUpload(file: File, options: {
  maxSize?: number;
  allowedTypes?: string[];
} = {}): { valid: boolean; error?: string } {
  const { maxSize = 10 * 1024 * 1024, allowedTypes = ['application/pdf'] } = options;

  if (file.size > maxSize) {
    return { valid: false, error: `File size exceeds ${maxSize / 1024 / 1024}MB limit` };
  }

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: `File type ${file.type} is not allowed` };
  }

  return { valid: true };
}

/**
 * Sanitize input
 */
export function sanitizeInput(input: any): any {
  if (typeof input === 'string') {
    return input
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/<[^>]+>/g, '')
      .trim();
  }
  
  if (Array.isArray(input)) {
    return input.map(sanitizeInput);
  }
  
  if (typeof input === 'object' && input !== null) {
    const sanitized: any = {};
    for (const key in input) {
      if (input.hasOwnProperty(key)) {
        sanitized[key] = sanitizeInput(input[key]);
      }
    }
    return sanitized;
  }
  
  return input;
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  if (!/[!@#$%^&*]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate course code
 */
export function validateCourseCode(code: string): boolean {
  // Format: ABC123 or ABC-123
  const pattern = /^[A-Z]{2,4}[-]?\d{3,4}$/;
  return pattern.test(code);
}

/**
 * Validate semester format
 */
export function validateSemester(semester: string): boolean {
  // Format: YYYY-season (e.g., 2024-spring)
  const pattern = /^\d{4}-(spring|summer|fall|winter)$/i;
  return pattern.test(semester);
}

/**
 * Validate percentage
 */
export function validatePercentage(value: number): boolean {
  return value >= 0 && value <= 100 && !isNaN(value);
}

/**
 * Validate positive integer
 */
export function validatePositiveInteger(value: number): boolean {
  return Number.isInteger(value) && value > 0;
}

/**
 * Validate URL
 */
export function validateURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate phone number
 */
export function validatePhoneNumber(phone: string): boolean {
  const pattern = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
  return pattern.test(phone);
}

/**
 * Validate array length
 */
export function validateArrayLength(
  array: any[],
  min: number,
  max: number
): boolean {
  return array.length >= min && array.length <= max;
}

/**
 * Validate JSON string
 */
export function validateJSON(jsonString: string): boolean {
  try {
    JSON.parse(jsonString);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate academic year
 */
export function validateAcademicYear(year: number): boolean {
  const currentYear = new Date().getFullYear();
  return year >= currentYear - 10 && year <= currentYear + 2;
}

/**
 * Custom validation error class
 */
export class ValidationError extends Error {
  public field: string;
  public value: any;

  constructor(message: string, field: string, value: any) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
  }
}

/**
 * Batch validation
 */
export function batchValidate(validations: Array<{
  value: any;
  validator: (value: any) => boolean;
  field: string;
  message: string;
}>): { valid: boolean; errors: ValidationError[] } {
  const errors: ValidationError[] = [];

  for (const validation of validations) {
    if (!validation.validator(validation.value)) {
      errors.push(new ValidationError(
        validation.message,
        validation.field,
        validation.value
      ));
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}