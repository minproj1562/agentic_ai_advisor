// src/services/cloudinary.service.ts

interface CloudinaryUploadResponse {
  secure_url: string;
  public_id: string;
  format: string;
  resource_type: string;
  created_at: string;
  bytes: number;
  width?: number;
  height?: number;
  url: string;
  thumbnail_url?: string;
}

class CloudinaryService {
  private cloudName: string;
  private uploadPreset: string;
  private baseUrl: string;

  constructor() {
    this.cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || '';
    this.uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || '';
    this.baseUrl = `https://api.cloudinary.com/v1_1/${this.cloudName}`;
    
    if (!this.cloudName || !this.uploadPreset) {
      console.warn('Cloudinary configuration missing. Please check your environment variables.');
    }
  }

  /**
   * Upload a file to Cloudinary
   */
  async uploadFile(
    file: File, 
    folder: string = 'student_projects',
    onProgress?: (progress: number) => void
  ): Promise<CloudinaryUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', this.uploadPreset);
      formData.append('folder', folder);
      
      // Add tags for better organization
      formData.append('tags', 'student_project,portfolio');
      
      // Auto-detect resource type
      const resourceType = this.getResourceType(file);
      const uploadUrl = `${this.baseUrl}/${resourceType}/upload`;

      // Create XMLHttpRequest to track progress
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && onProgress) {
            const progress = Math.round((e.loaded / e.total) * 100);
            onProgress(progress);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload'));
        });

        xhr.open('POST', uploadUrl);
        xhr.send(formData);
      });

    } catch (error: any) {
      console.error('Error uploading to Cloudinary:', error);
      throw new Error(`Failed to upload file: ${error.message}`);
    }
  }

  /**
   * Upload multiple files
   */
  async uploadMultipleFiles(
    files: File[],
    folder: string = 'student_projects',
    onProgress?: (fileIndex: number, progress: number) => void
  ): Promise<CloudinaryUploadResponse[]> {
    const uploadPromises = files.map((file, index) => 
      this.uploadFile(
        file, 
        folder,
        (progress) => onProgress?.(index, progress)
      )
    );

    return Promise.all(uploadPromises);
  }

  /**
   * Upload base64 image
   */
  async uploadBase64(
    base64Data: string,
    folder: string = 'student_projects'
  ): Promise<CloudinaryUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', base64Data);
      formData.append('upload_preset', this.uploadPreset);
      formData.append('folder', folder);

      const response = await fetch(`${this.baseUrl}/image/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      console.error('Error uploading base64 to Cloudinary:', error);
      throw error;
    }
  }

  /**
   * Delete a file from Cloudinary (requires signed request)
   * Note: For unsigned uploads, deletion must be done from backend
   */
  async deleteFile(publicId: string): Promise<boolean> {
    console.warn('Deletion requires signed requests. Implement this on your backend.');
    return false;
  }

  /**
   * Get optimized URL for an uploaded image
   */
  getOptimizedUrl(
    publicId: string, 
    options: {
      width?: number;
      height?: number;
      quality?: 'auto' | number;
      format?: 'auto' | 'webp' | 'jpg' | 'png';
      crop?: 'fill' | 'fit' | 'scale' | 'thumb';
    } = {}
  ): string {
    const { 
      width = 800, 
      height, 
      quality = 'auto', 
      format = 'auto',
      crop = 'fill'
    } = options;

    let transformation = `q_${quality},f_${format}`;
    
    if (width) transformation += `,w_${width}`;
    if (height) transformation += `,h_${height}`;
    if (crop) transformation += `,c_${crop}`;

    return `https://res.cloudinary.com/${this.cloudName}/image/upload/${transformation}/${publicId}`;
  }

  /**
   * Get thumbnail URL
   */
  getThumbnailUrl(publicId: string, size: number = 150): string {
    return this.getOptimizedUrl(publicId, {
      width: size,
      height: size,
      crop: 'thumb',
      quality: 'auto'
    });
  }

  /**
   * Determine resource type based on file type
   */
  private getResourceType(file: File): string {
    const type = file.type.toLowerCase();
    
    if (type.startsWith('image/')) return 'image';
    if (type.startsWith('video/')) return 'video';
    if (type === 'application/pdf') return 'image'; // PDFs can be handled as images
    
    // For other files, use 'raw'
    return 'raw';
  }

  /**
   * Validate file before upload
   */
  validateFile(file: File, maxSizeMB: number = 10): { valid: boolean; error?: string } {
    const maxSize = maxSizeMB * 1024 * 1024; // Convert to bytes
    
    if (file.size > maxSize) {
      return { 
        valid: false, 
        error: `File size exceeds ${maxSizeMB}MB limit` 
      };
    }

    // Check file type
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf', 'text/plain', 'text/markdown',
      'application/msword', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/zip', 'application/x-tar'
    ];

    if (!allowedTypes.includes(file.type) && !file.type.startsWith('image/')) {
      return { 
        valid: false, 
        error: 'File type not supported' 
      };
    }

    return { valid: true };
  }
}

export const cloudinaryService = new CloudinaryService();