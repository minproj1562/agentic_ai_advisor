// src/types/cv.types.ts

export interface CVFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
}

export interface ParsedCV {
  content: string;
  skills: ExtractedSkills[];
  metadata: {
    fileName: string;
    fileSize: number;
    uploadedAt: Date;
    mimeType: string;
  };
  personalInfo?: {
    name?: string;
    email?: string;
    phone?: string;
    location?: string;
  };
  education?: Education[];
  experience?: Experience[];
  projects?: Project[];
  certifications?: Certification[];
}

export interface ExtractedSkills {
  name: string;
  category?: string;
  confidence: number;
  metadata?: {
    synonyms: string[];
    occurrences: number;
    context: string;
  };
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  startDate: string;
  endDate?: string;
  gpa?: number;
  description?: string;
}

export interface Experience {
  company: string;
  position: string;
  startDate: string;
  endDate?: string;
  description: string;
  technologies?: string[];
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  startDate: string;
  endDate?: string;
  url?: string;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string;
  url?: string;
}

export interface CVParseOptions {
  onProgress?: (progress: number) => void;
  language?: string;
  extractImages?: boolean;
}

export interface CVUploadResponse {
  success: boolean;
  data?: ParsedCV;
  error?: string;
  fileId?: string;
}