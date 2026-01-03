// src/config/environment.ts

interface EnvironmentConfig {
  BACKEND_URL: string;
  CLOUDINARY_CLOUD_NAME: string;
  CLOUDINARY_API_KEY: string;
  CLOUDINARY_API_SECRET: string;
}

// Default configuration
const defaultConfig: EnvironmentConfig = {
  BACKEND_URL: 'http://localhost:8000',
  CLOUDINARY_CLOUD_NAME: '',
  CLOUDINARY_API_KEY: '',
  CLOUDINARY_API_SECRET: ''
};

// Get environment variables with fallbacks
const getEnvConfig = (): EnvironmentConfig => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined') {
    // For Create React App
    if ('process' in window && (window as any).process?.env) {
      const env = (window as any).process.env;
      return {
        BACKEND_URL: env.REACT_APP_BACKEND_URL || defaultConfig.BACKEND_URL,
        CLOUDINARY_CLOUD_NAME: env.REACT_APP_CLOUDINARY_CLOUD_NAME || defaultConfig.CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY: env.REACT_APP_CLOUDINARY_API_KEY || defaultConfig.CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET: env.REACT_APP_CLOUDINARY_API_SECRET || defaultConfig.CLOUDINARY_API_SECRET
      };
    }
    
    // For Vite
    if ('import' in window && (window as any).import?.meta?.env) {
      const env = (window as any).import.meta.env;
      return {
        BACKEND_URL: env.VITE_BACKEND_URL || defaultConfig.BACKEND_URL,
        CLOUDINARY_CLOUD_NAME: env.VITE_CLOUDINARY_CLOUD_NAME || defaultConfig.CLOUDINARY_CLOUD_NAME,
        CLOUDINARY_API_KEY: env.VITE_CLOUDINARY_API_KEY || defaultConfig.CLOUDINARY_API_KEY,
        CLOUDINARY_API_SECRET: env.VITE_CLOUDINARY_API_SECRET || defaultConfig.CLOUDINARY_API_SECRET
      };
    }
  }
  
  // Fallback to default config
  return defaultConfig;
};

export const config = getEnvConfig();