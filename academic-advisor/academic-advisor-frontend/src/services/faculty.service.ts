// src/services/faculty.service.ts
import apiClient from './api.service';
import { AxiosResponse } from 'axios';

export interface FacultyProfile {
  user_id: string;
  name: string;
  email: string;
  department: string;
  designation: string;
  status: string;
  profile_setup_complete: boolean;
  profile_completeness: number;
  uniform_profile: any;
  cv_url: string | null;
  cv_uploaded_at: string | null;
  mentee_count: number;
  available_slots_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdatePayload {
  name?: string;
  phone?: string;
  photo_url?: string;
  highest_degree?: string;
  specialization?: string;
  graduation_university?: string;
  graduation_year?: number | null;
  all_degrees?: any[];
  designation?: string;
  department?: string;
  institution?: string;
  years_of_experience?: number;
  joining_year?: number | null;
  primary_research_areas?: string[];
  secondary_interests?: string[];
  research_keywords?: string[];
  current_subjects?: string[];
  past_subjects?: string[];
  preferred_teaching_areas?: string[];
  office_location?: string;
  office_hours?: string;
  preferred_meeting_duration?: number;
  available_slots?: any[];
  total_publications?: number;
  journal_papers?: number;
  conference_papers?: number;
  notable_works?: string[];
  h_index?: number | null;
  awards?: string[];
  certifications?: string[];
  languages?: string[];
  professional_memberships?: string[];
  visibility?: any;
}

class FacultyService {
  private readonly BASE_PATH = '/faculty-profile';

  /**
   * Get current faculty's profile
   */
  async getMyProfile(): Promise<FacultyProfile> {
    const response = await apiClient.get(`${this.BASE_PATH}/me`);
    return response.data;
  }

  /**
   * Update faculty profile
   */
  async updateProfile(updates: ProfileUpdatePayload): Promise<any> {
    const response = await apiClient.put(`${this.BASE_PATH}/update`, updates);
    return response.data;
  }

  /**
   * Complete initial profile setup
   */
  async completeProfileSetup(data: any): Promise<any> {
    const response = await apiClient.post(`${this.BASE_PATH}/setup`, data);
    return response.data;
  }

  /**
   * Upload CV
   */
  async uploadCV(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('cv', file);
    
    const response = await apiClient.post(`${this.BASE_PATH}/cv/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Re-upload CV with merge mode
   */
  async reuploadCV(file: File, mergeMode: 'smart' | 'overwrite' | 'keep_existing' = 'smart'): Promise<any> {
    const formData = new FormData();
    formData.append('cv', file);
    
    const response = await apiClient.post(
      `${this.BASE_PATH}/cv/reupload?merge_mode=${mergeMode}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get profile completeness details
   */
  async getCompleteness(): Promise<any> {
    const response = await apiClient.get(`${this.BASE_PATH}/completeness`);
    return response.data;
  }

  /**
   * Check setup status
   */
  async checkSetupStatus(): Promise<any> {
    const response = await apiClient.get(`${this.BASE_PATH}/check-setup-status`);
    return response.data;
  }

  /**
   * Update availability slots
   */
  async updateAvailability(data: any): Promise<any> {
    const response = await apiClient.put(`${this.BASE_PATH}/availability`, data);
    return response.data;
  }

  /**
   * Add availability slot
   */
  async addSlot(slot: any): Promise<any> {
    const response = await apiClient.post(`${this.BASE_PATH}/availability/slots`, slot);
    return response.data;
  }

  /**
   * Remove availability slot
   */
  async removeSlot(day: string, startTime: string): Promise<any> {
    const response = await apiClient.delete(
      `${this.BASE_PATH}/availability/slots/${day}/${startTime}`
    );
    return response.data;
  }

  /**
   * Get faculty list (for students)
   */
  async getFacultyList(params?: {
    department?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    const response = await apiClient.get(`${this.BASE_PATH}/list`, { params });
    return response.data;
  }

  /**
   * Get faculty student view (public profile)
   */
  async getFacultyStudentView(facultyId: string): Promise<any> {
    const response = await apiClient.get(`${this.BASE_PATH}/${facultyId}/student-view`);
    return response.data;
  }
}

export const facultyService = new FacultyService();
export default facultyService;