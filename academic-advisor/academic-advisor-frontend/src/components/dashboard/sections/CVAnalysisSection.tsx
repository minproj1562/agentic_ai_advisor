// src/components/dashboard/sections/CVAnalysisSection.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDropzone } from 'react-dropzone';
import {
  Upload, FileText, Brain, CheckCircle, RefreshCw,
  Download, Eye, Trash2, Loader2, Award, TrendingUp,
  BookOpen, Briefcase, GraduationCap, Star
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';
import apiClient from '../../../services/api.service';
import { cn } from '../../../utils/cn';

interface CVAnalysisSectionProps {
  facultyId: string;
  facultyData: any;
}

const CVAnalysisSection: React.FC<CVAnalysisSectionProps> = ({
  facultyId,
  facultyData
}) => {
  const queryClient = useQueryClient();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const cvData = facultyData?.cv_url ? {
    url: facultyData.cv_url,
    fileName: facultyData.cv_file_name || 'CV.pdf',
    uploadedAt: facultyData.cv_uploaded_at,
  } : null;

  const profile = facultyData?.uniform_profile;

  // CV Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('cv', file);
      
      const response = await apiClient.post('/faculty-profile/cv/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        }
      });
      
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['faculty-profile'] });
      toast.success('CV uploaded and analyzed successfully!');
      setIsUploading(false);
      setUploadProgress(0);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload CV');
      setIsUploading(false);
      setUploadProgress(0);
    }
  });

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      toast.error('Please upload a PDF file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setIsUploading(true);
    uploadMutation.mutate(file);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled: isUploading
  });

  const handleDownload = () => {
    if (cvData?.url) {
      window.open(cvData.url, '_blank');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          CV & Expertise Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Upload your CV to auto-extract and manage your expertise profile
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CV Upload/Status Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-indigo-600" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                CV Analyzer
              </h3>
            </div>
            {cvData && (
              <div className="flex gap-2">
                <button
                  onClick={handleDownload}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Download CV"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {/* Trigger re-upload */}}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="Re-upload CV"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {!cvData ? (
            // Upload Zone
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
                isDragActive
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400',
                isUploading && 'pointer-events-none opacity-50'
              )}
            >
              <input {...getInputProps()} />

              {isUploading ? (
                <div className="space-y-4">
                  <Loader2 className="w-12 h-12 mx-auto text-indigo-600 animate-spin" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      Analyzing your CV...
                    </p>
                    <div className="mt-2 w-48 mx-auto bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full transition-all"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{uploadProgress}%</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="w-12 h-12 mx-auto text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {isDragActive ? 'Drop your CV here' : 'Drag & drop your CV'}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      PDF only, max 10MB
                    </p>
                  </div>
                  <p className="text-xs text-indigo-600 dark:text-indigo-400">
                    AI will extract your qualifications, experience & skills
                  </p>
                </div>
              )}
            </div>
          ) : (
            // CV Uploaded State
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <FileText className="w-10 h-10 text-green-600" />
                <div className="flex-1">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {cvData.fileName}
                  </p>
                  <p className="text-sm text-gray-500">
                    Uploaded {cvData.uploadedAt 
                      ? formatDistanceToNow(new Date(cvData.uploadedAt), { addSuffix: true })
                      : 'recently'}
                  </p>
                </div>
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>

              {/* Profile Completeness */}
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Profile Extracted
                  </span>
                  <Award className="w-4 h-4 text-yellow-500" />
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-indigo-500 to-purple-500 h-3 rounded-full"
                      style={{ width: `${facultyData?.profile_completeness || 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-indigo-600">
                    {facultyData?.profile_completeness || 0}%
                  </span>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                  <p className="text-2xl font-bold text-indigo-600">
                    {profile?.research_expertise?.primary_areas?.length || 0}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Research Areas</p>
                </div>
                <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">
                    {profile?.publications?.total_count || 0}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Publications</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Expertise Summary Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-500" />
            Expertise Summary
          </h3>

          {profile ? (
            <div className="space-y-4">
              {/* Academic Qualifications */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <GraduationCap className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Qualifications
                  </span>
                </div>
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {profile.academic_qualifications?.highest_degree || 'Not specified'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {profile.academic_qualifications?.specialization}
                    {profile.academic_qualifications?.university && 
                      ` • ${profile.academic_qualifications.university}`}
                  </p>
                </div>
              </div>

              {/* Research Areas */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Research Areas
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.research_expertise?.primary_areas?.map((area: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm"
                    >
                      {area}
                    </span>
                  ))}
                  {(!profile.research_expertise?.primary_areas || 
                    profile.research_expertise.primary_areas.length === 0) && (
                    <span className="text-sm text-gray-500">No research areas specified</span>
                  )}
                </div>
              </div>

              {/* Teaching */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Briefcase className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Teaching Subjects
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {profile.teaching?.current_subjects?.map((subject: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm"
                    >
                      {subject}
                    </span>
                  ))}
                  {(!profile.teaching?.current_subjects || 
                    profile.teaching.current_subjects.length === 0) && (
                    <span className="text-sm text-gray-500">No subjects specified</span>
                  )}
                </div>
              </div>

              {/* Experience */}
              <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Experience</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {profile.current_position?.years_of_experience || 0} years
                  </span>
                </div>
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Position</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {profile.current_position?.designation || 'Not specified'}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <Brain className="w-12 h-12 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-400">
                Upload your CV to see expertise analysis
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Additional Info */}
      {profile?.others && Object.keys(profile.others).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Additional Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profile.others.awards?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Awards & Honors
                </h4>
                <ul className="space-y-1">
                  {profile.others.awards.map((award: string, i: number) => (
                    <li key={i} className="text-sm text-gray-900 dark:text-white flex items-start gap-2">
                      <Award className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                      {award}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {profile.others.certifications?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Certifications
                </h4>
                <ul className="space-y-1">
                  {profile.others.certifications.map((cert: string, i: number) => (
                    <li key={i} className="text-sm text-gray-900 dark:text-white flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      {cert}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {profile.others.languages?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Languages
                </h4>
                <div className="flex flex-wrap gap-2">
                  {profile.others.languages.map((lang: string, i: number) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CVAnalysisSection;