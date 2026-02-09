// src/pages/FacultyProfileEdit.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm, Controller, useFieldArray } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  User, Mail, Phone, MapPin, GraduationCap, Briefcase,
  BookOpen, Brain, Clock, Award, FileText, Save, X,
  Loader2, ChevronLeft, ChevronRight, Plus, Trash2,
  Calendar, Check, AlertCircle
} from 'lucide-react';
import apiClient from '../services/api.service';
import { useAuth } from '../contexts/AuthContext';

// Types
interface DegreeInput {
  degree: string;
  field: string;
  institution: string;
  year?: number;
  thesis_title?: string;
}

interface MeetingSlotInput {
  day: string;
  start_time: string;
  end_time: string;
  venue: string;
}

interface ProfileFormData {
  // Personal
  name: string;
  phone: string;
  photo_url: string;
  
  // Academic
  highest_degree: string;
  specialization: string;
  graduation_university: string;
  graduation_year: number | null;
  all_degrees: DegreeInput[];
  
  // Position
  designation: string;
  department: string;
  institution: string;
  years_of_experience: number;
  joining_year: number | null;
  
  // Research
  primary_research_areas: string[];
  secondary_interests: string[];
  research_keywords: string[];
  
  // Teaching
  current_subjects: string[];
  past_subjects: string[];
  preferred_teaching_areas: string[];
  
  // Availability
  office_location: string;
  office_hours: string;
  preferred_meeting_duration: number;
  available_slots: MeetingSlotInput[];
  
  // Publications
  total_publications: number;
  journal_papers: number;
  conference_papers: number;
  notable_works: string[];
  h_index: number | null;
  
  // Others
  awards: string[];
  certifications: string[];
  languages: string[];
  professional_memberships: string[];
}

// Step configuration
const STEPS = [
  { id: 'personal', title: 'Personal Info', icon: User },
  { id: 'academic', title: 'Academic', icon: GraduationCap },
  { id: 'position', title: 'Position', icon: Briefcase },
  { id: 'research', title: 'Research', icon: Brain },
  { id: 'teaching', title: 'Teaching', icon: BookOpen },
  { id: 'availability', title: 'Availability', icon: Clock },
  { id: 'publications', title: 'Publications', icon: FileText },
  { id: 'others', title: 'Additional', icon: Award },
];

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const DEGREE_OPTIONS = ['PhD', 'M.Tech', 'M.E.', 'M.S.', 'M.Sc', 'B.Tech', 'B.E.', 'B.Sc', 'MBA', 'Other'];
const DESIGNATION_OPTIONS = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer', 'Senior Lecturer'];

// Tag Input Component
const TagInput: React.FC<{
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
}> = ({ value = [], onChange, placeholder = 'Type and press Enter', maxTags = 10 }) => {
  const [input, setInput] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      if (value.length < maxTags && !value.includes(input.trim())) {
        onChange([...value, input.trim()]);
      }
      setInput('');
    }
  };

  const removeTag = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {value.map((tag, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 
                       text-indigo-700 dark:text-indigo-300 rounded-full text-sm"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="hover:text-indigo-900 dark:hover:text-indigo-100"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      {value.length < maxTags && (
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
        />
      )}
    </div>
  );
};

// Main Component
const FacultyProfileEdit: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const editMode = location.state?.editMode || false;
  const initialProfile = location.state?.profile;
  const initialStep = location.state?.initialStep;
  
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Set initial step based on navigation state
  useEffect(() => {
    if (initialStep) {
      const stepIndex = STEPS.findIndex(s => s.id === initialStep);
      if (stepIndex >= 0) setCurrentStep(stepIndex);
    }
  }, [initialStep]);

  // Fetch current profile
  const { data: profileData, isLoading } = useQuery({
    queryKey: ['faculty-profile-edit', user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/faculty-profile/me');
      return response.data;
    },
    initialData: initialProfile,
    staleTime: 0, // Always fetch fresh for editing
  });

  // Transform profile data to form data
  const getDefaultValues = (): ProfileFormData => {
    const up = profileData?.uniform_profile;
    
    return {
      // Personal
      name: up?.personal_info?.name || profileData?.name || '',
      phone: up?.personal_info?.phone || '',
      photo_url: up?.personal_info?.photo_url || '',
      
      // Academic
      highest_degree: up?.academic_qualifications?.highest_degree || '',
      specialization: up?.academic_qualifications?.specialization || '',
      graduation_university: up?.academic_qualifications?.university || '',
      graduation_year: up?.academic_qualifications?.graduation_year || null,
      all_degrees: up?.academic_qualifications?.all_degrees || [],
      
      // Position
      designation: up?.current_position?.designation || profileData?.designation || '',
      department: up?.current_position?.department || profileData?.department || '',
      institution: up?.current_position?.institution || '',
      years_of_experience: up?.current_position?.years_of_experience || 0,
      joining_year: up?.current_position?.joining_year || null,
      
      // Research
      primary_research_areas: up?.research_expertise?.primary_areas || [],
      secondary_interests: up?.research_expertise?.secondary_interests || [],
      research_keywords: up?.research_expertise?.keywords || [],
      
      // Teaching
      current_subjects: up?.teaching?.current_subjects || [],
      past_subjects: up?.teaching?.past_subjects || [],
      preferred_teaching_areas: up?.teaching?.preferred_areas || [],
      
      // Availability
      office_location: up?.availability?.office_location || '',
      office_hours: up?.availability?.office_hours || '',
      preferred_meeting_duration: up?.availability?.preferred_meeting_duration || 30,
      available_slots: up?.availability?.available_slots || [],
      
      // Publications
      total_publications: up?.publications?.total_count || 0,
      journal_papers: up?.publications?.journal_papers || 0,
      conference_papers: up?.publications?.conference_papers || 0,
      notable_works: up?.publications?.notable_works || [],
      h_index: up?.publications?.h_index || null,
      
      // Others
      awards: up?.others?.awards || [],
      certifications: up?.others?.certifications || [],
      languages: up?.others?.languages || [],
      professional_memberships: up?.others?.professional_memberships || [],
    };
  };

  const { control, handleSubmit, watch, formState: { errors, isDirty } } = useForm<ProfileFormData>({
    defaultValues: getDefaultValues(),
  });

  // Field arrays for dynamic lists
  const { fields: degreeFields, append: appendDegree, remove: removeDegree } = useFieldArray({
    control,
    name: 'all_degrees',
  });

  const { fields: slotFields, append: appendSlot, remove: removeSlot } = useFieldArray({
    control,
    name: 'available_slots',
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (data: ProfileFormData) => {
      const response = await apiClient.put('/faculty-profile/update', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['faculty-profile'] });
      toast.success('Profile updated successfully!');
      navigate('/faculty/dashboard');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    },
  });

  const onSubmit = async (data: ProfileFormData) => {
    setIsSubmitting(true);
    try {
      await updateMutation.mutateAsync(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (index: number) => {
    setCurrentStep(index);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  // Render step content
  const renderStepContent = () => {
    const stepId = STEPS[currentStep].id;

    switch (stepId) {
      case 'personal':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Full Name *
                </label>
                <Controller
                  name="name"
                  control={control}
                  rules={{ required: 'Name is required' }}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
                {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Phone Number
                </label>
                <Controller
                  name="phone"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="tel"
                      placeholder="+91 XXXXX XXXXX"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Profile Photo URL
              </label>
              <Controller
                name="photo_url"
                control={control}
                render={({ field }) => (
                  <input
                    {...field}
                    type="url"
                    placeholder="https://example.com/photo.jpg"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                )}
              />
            </div>
          </div>
        );

      case 'academic':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Highest Degree *
                </label>
                <Controller
                  name="highest_degree"
                  control={control}
                  rules={{ required: 'Highest degree is required' }}
                  render={({ field }) => (
                    <select
                      {...field}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="">Select Degree</option>
                      {DEGREE_OPTIONS.map(deg => (
                        <option key={deg} value={deg}>{deg}</option>
                      ))}
                    </select>
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Specialization *
                </label>
                <Controller
                  name="specialization"
                  control={control}
                  rules={{ required: 'Specialization is required' }}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="e.g., Machine Learning"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  University
                </label>
                <Controller
                  name="graduation_university"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="University name"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Graduation Year
                </label>
                <Controller
                  name="graduation_year"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      value={field.value ?? ''} // FIX: Convert null to empty string
                      type="number"
                      min={1970}
                      max={new Date().getFullYear()}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>
            </div>

            {/* All Degrees */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  All Degrees
                </label>
                <button
                  type="button"
                  onClick={() => appendDegree({ degree: '', field: '', institution: '', year: undefined })}
                  className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" /> Add Degree
                </button>
              </div>
              
              <div className="space-y-3">
                {degreeFields.map((field, index) => (
                  <div key={field.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <Controller
                        name={`all_degrees.${index}.degree`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} placeholder="Degree" className="input-field" />
                        )}
                      />
                      <Controller
                        name={`all_degrees.${index}.field`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} placeholder="Field" className="input-field" />
                        )}
                      />
                      <Controller
                        name={`all_degrees.${index}.institution`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} placeholder="Institution" className="input-field" />
                        )}
                      />
                      <div className="flex gap-2">
                        <Controller
                          name={`all_degrees.${index}.year`}
                          control={control}
                          render={({ field }) => (
                            <input 
                              {...field} 
                              type="number" 
                              placeholder="Year" 
                              className="input-field flex-1"
                              onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                            />
                          )}
                        />
                        <button
                          type="button"
                          onClick={() => removeDegree(index)}
                          className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'position':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Designation *
                </label>
                <Controller
                  name="designation"
                  control={control}
                  rules={{ required: 'Designation is required' }}
                  render={({ field }) => (
                    <select
                      {...field}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value="">Select Designation</option>
                      {DESIGNATION_OPTIONS.map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Department *
                </label>
                <Controller
                  name="department"
                  control={control}
                  rules={{ required: 'Department is required' }}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="e.g., Computer Science"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Institution
                </label>
                <Controller
                  name="institution"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="College/University name"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Years of Experience
                </label>
                <Controller
                  name="years_of_experience"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="number"
                      min={0}
                      max={50}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>
            </div>
          </div>
        );

      case 'research':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Primary Research Areas (max 5)
              </label>
              <Controller
                name="primary_research_areas"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="e.g., Machine Learning, Deep Learning..."
                    maxTags={5}
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Secondary Interests
              </label>
              <Controller
                name="secondary_interests"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Other areas of interest..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Keywords / Skills
              </label>
              <Controller
                name="research_keywords"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Python, TensorFlow, NLP..."
                  />
                )}
              />
            </div>
          </div>
        );

      case 'teaching':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Currently Teaching
              </label>
              <Controller
                name="current_subjects"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Subjects you currently teach..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Previously Taught
              </label>
              <Controller
                name="past_subjects"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Subjects you taught before..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Preferred Teaching Areas
              </label>
              <Controller
                name="preferred_teaching_areas"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Areas you prefer to teach..."
                  />
                )}
              />
            </div>
          </div>
        );

      case 'availability':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Office Location *
                </label>
                <Controller
                  name="office_location"
                  control={control}
                  rules={{ required: 'Office location is required' }}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="e.g., Room 301, CS Building"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Office Hours
                </label>
                <Controller
                  name="office_hours"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="text"
                      placeholder="e.g., Mon-Wed 10:00-12:00"
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Preferred Meeting Duration (minutes)
                </label>
                <Controller
                  name="preferred_meeting_duration"
                  control={control}
                  render={({ field }) => (
                    <select
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value={15}>15 minutes</option>
                      <option value={30}>30 minutes</option>
                      <option value={45}>45 minutes</option>
                      <option value={60}>60 minutes</option>
                    </select>
                  )}
                />
              </div>
            </div>

            {/* Meeting Slots */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Available Meeting Slots
                </label>
                <button
                  type="button"
                  onClick={() => appendSlot({ day: 'Monday', start_time: '10:00', end_time: '11:00', venue: '' })}
                  className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" /> Add Slot
                </button>
              </div>

              <div className="space-y-3">
                {slotFields.map((field, index) => (
                  <div key={field.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
                      <Controller
                        name={`available_slots.${index}.day`}
                        control={control}
                        render={({ field }) => (
                          <select {...field} className="input-field">
                            {DAYS_OF_WEEK.map(day => (
                              <option key={day} value={day}>{day}</option>
                            ))}
                          </select>
                        )}
                      />
                      <Controller
                        name={`available_slots.${index}.start_time`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} type="time" className="input-field" />
                        )}
                      />
                      <Controller
                        name={`available_slots.${index}.end_time`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} type="time" className="input-field" />
                        )}
                      />
                      <Controller
                        name={`available_slots.${index}.venue`}
                        control={control}
                        render={({ field }) => (
                          <input {...field} placeholder="Venue" className="input-field" />
                        )}
                      />
                      <button
                        type="button"
                        onClick={() => removeSlot(index)}
                        className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded self-center"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'publications':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Total Publications
                </label>
                <Controller
                  name="total_publications"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="number"
                      min={0}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Journal Papers
                </label>
                <Controller
                  name="journal_papers"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="number"
                      min={0}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Conference Papers
                </label>
                <Controller
                  name="conference_papers"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      type="number"
                      min={0}
                      onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  h-Index
                </label>
                <Controller
                  name="h_index"
                  control={control}
                  render={({ field }) => (
                    <input
                      {...field}
                      value={field.value ?? ''} // FIX: Convert null to empty string
                      type="number"
                      min={0}
                      onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : null)}
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg
                                 bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                                 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  )}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Notable Works (max 5)
              </label>
              <Controller
                name="notable_works"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Enter paper/book titles..."
                    maxTags={5}
                  />
                )}
              />
            </div>
          </div>
        );

      case 'others':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Awards & Honors
              </label>
              <Controller
                name="awards"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Awards you've received..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Certifications
              </label>
              <Controller
                name="certifications"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Professional certifications..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Languages
              </label>
              <Controller
                name="languages"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="English, Hindi..."
                  />
                )}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Professional Memberships
              </label>
              <Controller
                name="professional_memberships"
                control={control}
                render={({ field }) => (
                  <TagInput
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="IEEE, ACM..."
                  />
                )}
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                <ChevronLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Edit Profile
                </h1>
                <p className="text-sm text-gray-500">
                  Update your faculty profile information
                </p>
              </div>
            </div>

            <button
              onClick={handleSubmit(onSubmit)}
              disabled={isSubmitting || !isDirty}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg
                         hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Save Changes
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Step Navigation */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-2">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;

              return (
                <button
                  key={step.id}
                  onClick={() => goToStep(index)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                    ${isActive 
                      ? 'bg-indigo-600 text-white' 
                      : isCompleted
                        ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{step.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Form Content */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
              {React.createElement(STEPS[currentStep].icon, { className: 'w-5 h-5 text-indigo-600' })}
              {STEPS[currentStep].title}
            </h2>

            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {renderStepContent()}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 0}
              className="flex items-center gap-2 px-6 py-3 border border-gray-300 dark:border-gray-600
                         text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 
                         dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>

            {currentStep < STEPS.length - 1 ? (
              <button
                type="button"
                onClick={nextStep}
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg
                           hover:bg-indigo-700"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg
                           hover:bg-green-700 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
                Save Profile
              </button>
            )}
          </div>
        </form>
      </div>

      {/* CSS for input fields */}
      <style>{`
        .input-field {
          width: 100%;
          padding: 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.5rem;
          font-size: 0.875rem;
        }
        .dark .input-field {
          background-color: #374151;
          border-color: #4b5563;
          color: white;
        }
        .input-field:focus {
          outline: none;
          ring: 2px;
          ring-color: #6366f1;
          border-color: transparent;
        }
      `}</style>
    </div>
  );
};

export default FacultyProfileEdit;