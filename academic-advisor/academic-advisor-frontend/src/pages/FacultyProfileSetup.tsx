// src/components/dashboard/sections/FacultyProfileView.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  User,
  Mail,
  Phone,
  MapPin,
  GraduationCap,
  Briefcase,
  BookOpen,
  Brain,
  Clock,
  Award,
  FileText,
  Edit3,
  Upload,
  Eye,
  EyeOff,
  Check,
  X,
  Loader2,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Calendar,
  Globe,
  Linkedin,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Settings,
  Shield
} from 'lucide-react';
import apiClient from '../services/api.service';
import { useAuth } from '../contexts/AuthContext';

// Types
interface FacultyProfile {
  user_id: string;
  name: string;
  email: string;
  department: string;
  designation: string;
  status: string;
  profile_setup_complete: boolean;
  profile_completeness: number;
  uniform_profile: UniformProfile | null;
  cv_url: string | null;
  cv_uploaded_at: string | null;
  mentee_count: number;
  available_slots_count: number;
  created_at: string;
  updated_at: string;
}

interface UniformProfile {
  personal_info: {
    name: string;
    email: string;
    phone?: string;
    photo_url?: string;
  };
  academic_qualifications: {
    highest_degree: string;
    specialization: string;
    university: string;
    graduation_year?: number;
    all_degrees: Array<{
      degree: string;
      field: string;
      institution: string;
      year?: number;
    }>;
  };
  current_position: {
    designation: string;
    department: string;
    institution: string;
    years_of_experience: number;
    joining_year?: number;
  };
  research_expertise: {
    primary_areas: string[];
    secondary_interests: string[];
    keywords: string[];
  };
  teaching: {
    current_subjects: string[];
    past_subjects: string[];
    preferred_areas: string[];
  };
  availability: {
    office_location: string;
    office_hours: string;
    available_slots: Array<{
      day: string;
      start_time: string;
      end_time: string;
      venue: string;
    }>;
    preferred_meeting_duration: number;
  };
  publications?: {
    total_count: number;
    journal_papers: number;
    conference_papers: number;
    notable_works: string[];
    h_index?: number;
  };
  others: Record<string, any>;
  visibility?: {
    phone: string;
    email: string;
    office_location: string;
  };
  profile_completeness: number;
  last_updated: string;
}

interface ProfileSection {
  id: string;
  title: string;
  icon: React.ElementType;
  completeness: number;
}

// Profile Completeness Bar
const CompletenessBar: React.FC<{ value: number }> = ({ value }) => {
  const getColor = () => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600 dark:text-gray-400">Profile Completeness</span>
        <span className="font-medium text-gray-900 dark:text-white">{Math.round(value)}%</span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className={`h-full ${getColor()} rounded-full`}
        />
      </div>
    </div>
  );
};

// Section Card Component
const ProfileSection: React.FC<{
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
  onEdit?: () => void;
  editable?: boolean;
}> = ({ title, icon: Icon, children, defaultOpen = true, onEdit, editable = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
            <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
        </div>
        <div className="flex items-center gap-2">
          {editable && onEdit && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              className="p-1.5 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 rounded-lg transition-colors"
            >
              <Edit3 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            </button>
          )}
          {isOpen ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-gray-200 dark:border-gray-700"
          >
            <div className="p-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Tag Display
const TagList: React.FC<{ tags: string[]; color?: string }> = ({ tags, color = 'indigo' }) => {
  if (!tags || tags.length === 0) {
    return <span className="text-gray-400 text-sm italic">Not specified</span>;
  }

  const colorClasses: Record<string, string> = {
    indigo: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  };

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, idx) => (
        <span
          key={idx}
          className={`px-3 py-1 rounded-full text-sm font-medium ${colorClasses[color]}`}
        >
          {tag}
        </span>
      ))}
    </div>
  );
};

// Info Row
const InfoRow: React.FC<{
  icon: React.ElementType;
  label: string;
  value?: string | number | null;
  isPrivate?: boolean;
}> = ({ icon: Icon, label, value, isPrivate }) => (
  <div className="flex items-start gap-3 py-2">
    <Icon className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
    <div className="flex-1 min-w-0">
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      <div className="flex items-center gap-2">
        <p className="text-gray-900 dark:text-white font-medium">
          {value || <span className="text-gray-400 italic">Not specified</span>}
        </p>
        {isPrivate && (
          <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-500">
            Private
          </span>
        )}
      </div>
    </div>
  </div>
);

// Availability Slot Card
const SlotCard: React.FC<{
  slot: { day: string; start_time: string; end_time: string; venue: string };
  onRemove?: () => void;
}> = ({ slot, onRemove }) => (
  <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
    <div className="flex items-center gap-3">
      <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
        <Calendar className="w-4 h-4 text-green-600 dark:text-green-400" />
      </div>
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{slot.day}</p>
        <p className="text-sm text-gray-500">
          {slot.start_time} - {slot.end_time} • {slot.venue}
        </p>
      </div>
    </div>
    {onRemove && (
      <button
        onClick={onRemove}
        className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors"
      >
        <Trash2 className="w-4 h-4 text-red-500" />
      </button>
    )}
  </div>
);

// Main Component
const FacultyProfileView: React.FC<{
  facultyId?: string;
  facultyData?: FacultyProfile;
}> = ({ facultyId, facultyData: initialData }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [showVisibilitySettings, setShowVisibilitySettings] = useState(false);

  // Fetch profile data
  const { data: profile, isLoading, error, refetch } = useQuery({
    queryKey: ['faculty-profile', facultyId || user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/faculty-profile/me');
      return response.data as FacultyProfile;
    },
    initialData: initialData,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch completeness details
  const { data: completenessData } = useQuery({
    queryKey: ['faculty-completeness'],
    queryFn: async () => {
      const response = await apiClient.get('/faculty-profile/completeness');
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });

  // Navigate to edit page
  const handleEditProfile = () => {
    navigate('/faculty/profile-edit', {
      state: {
        editMode: true,
        profile: profile
      }
    });
  };

  // Navigate to specific section edit
  const handleEditSection = (section: string) => {
    navigate('/faculty/profile-edit', {
      state: {
        editMode: true,
        profile: profile,
        initialStep: section
      }
    });
  };

  // Re-upload CV
  const handleReuploadCV = () => {
    navigate('/faculty/profile-setup', {
      state: {
        editMode: true,
        profile: profile,
        reuploadCV: true
      }
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Failed to load profile
        </h3>
        <button
          onClick={() => refetch()}
          className="text-indigo-600 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  const up = profile.uniform_profile;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2" />
        
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              {/* Profile Photo */}
              <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-white/20 flex items-center justify-center text-3xl font-bold flex-shrink-0 overflow-hidden">
                {up?.personal_info?.photo_url ? (
                  <img
                    src={up.personal_info.photo_url}
                    alt={profile.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  profile.name.charAt(0).toUpperCase()
                )}
              </div>
              
              <div>
                <h1 className="text-2xl md:text-3xl font-bold">{profile.name}</h1>
                <p className="text-white/80 text-lg mt-1">
                  {up?.current_position?.designation || profile.designation}
                </p>
                <p className="text-white/60 mt-1">
                  {up?.current_position?.department || profile.department}
                </p>
                
                <div className="flex flex-wrap gap-4 mt-3 text-sm">
                  <span className="flex items-center gap-1">
                    <Mail className="w-4 h-4" />
                    {profile.email}
                  </span>
                  {up?.personal_info?.phone && (
                    <span className="flex items-center gap-1">
                      <Phone className="w-4 h-4" />
                      {up.personal_info.phone}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleEditProfile}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 
                           rounded-lg transition-colors"
              >
                <Edit3 className="w-4 h-4" />
                Edit Profile
              </button>
              
              <button
                onClick={() => setShowVisibilitySettings(!showVisibilitySettings)}
                className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 
                           rounded-lg transition-colors"
              >
                <Shield className="w-4 h-4" />
                Privacy
              </button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{up?.current_position?.years_of_experience || 0}</p>
              <p className="text-sm text-white/70">Years Experience</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{up?.publications?.total_count || 0}</p>
              <p className="text-sm text-white/70">Publications</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{profile.mentee_count}</p>
              <p className="text-sm text-white/70">Mentees</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{profile.available_slots_count}</p>
              <p className="text-sm text-white/70">Meeting Slots</p>
            </div>
          </div>
        </div>
      </div>

      {/* Profile Completeness */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <CompletenessBar value={profile.profile_completeness} />
        
        {completenessData?.missing_fields?.length > 0 && (
          <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <p className="text-sm text-yellow-700 dark:text-yellow-300 font-medium mb-1">
              Missing Information:
            </p>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              {completenessData.missing_fields.join(', ')}
            </p>
          </div>
        )}
        
        {completenessData?.recommendations?.length > 0 && (
          <div className="mt-3 space-y-1">
            {completenessData.recommendations.map((rec: string, idx: number) => (
              <p key={idx} className="text-sm text-gray-500 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                {rec}
              </p>
            ))}
          </div>
        )}
      </div>

      {/* CV Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Curriculum Vitae</h3>
              {profile.cv_uploaded_at ? (
                <p className="text-sm text-gray-500">
                  Uploaded {new Date(profile.cv_uploaded_at).toLocaleDateString()}
                </p>
              ) : (
                <p className="text-sm text-gray-500">No CV uploaded</p>
              )}
            </div>
          </div>
          
          <div className="flex gap-2">
            {profile.cv_url && (
              <a
                href={profile.cv_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 
                           dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View
              </a>
            )}
            <button
              onClick={handleReuploadCV}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white 
                         rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Upload className="w-4 h-4" />
              {profile.cv_url ? 'Re-upload' : 'Upload CV'}
            </button>
          </div>
        </div>
      </div>

      {/* Profile Sections */}
      {up && (
        <div className="space-y-4">
          {/* Academic Qualifications */}
          <ProfileSection
            title="Academic Qualifications"
            icon={GraduationCap}
            onEdit={() => handleEditSection('academic')}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoRow
                icon={GraduationCap}
                label="Highest Degree"
                value={up.academic_qualifications?.highest_degree}
              />
              <InfoRow
                icon={BookOpen}
                label="Specialization"
                value={up.academic_qualifications?.specialization}
              />
              <InfoRow
                icon={MapPin}
                label="University"
                value={up.academic_qualifications?.university}
              />
              <InfoRow
                icon={Calendar}
                label="Graduation Year"
                value={up.academic_qualifications?.graduation_year}
              />
            </div>
            
            {up.academic_qualifications?.all_degrees?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  All Degrees
                </h4>
                <div className="space-y-2">
                  {up.academic_qualifications.all_degrees.map((deg, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                    >
                      <p className="font-medium text-gray-900 dark:text-white">
                        {deg.degree} in {deg.field}
                      </p>
                      <p className="text-sm text-gray-500">
                        {deg.institution} {deg.year && `• ${deg.year}`}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ProfileSection>

          {/* Current Position */}
          <ProfileSection
            title="Current Position"
            icon={Briefcase}
            onEdit={() => handleEditSection('position')}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InfoRow
                icon={Briefcase}
                label="Designation"
                value={up.current_position?.designation}
              />
              <InfoRow
                icon={BookOpen}
                label="Department"
                value={up.current_position?.department}
              />
              <InfoRow
                icon={MapPin}
                label="Institution"
                value={up.current_position?.institution}
              />
              <InfoRow
                icon={Clock}
                label="Years of Experience"
                value={up.current_position?.years_of_experience ? `${up.current_position.years_of_experience} years` : null}
              />
            </div>
          </ProfileSection>

          {/* Research Expertise */}
          <ProfileSection
            title="Research & Expertise"
            icon={Brain}
            onEdit={() => handleEditSection('research')}
          >
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Primary Research Areas
                </h4>
                <TagList tags={up.research_expertise?.primary_areas || []} color="indigo" />
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Secondary Interests
                </h4>
                <TagList tags={up.research_expertise?.secondary_interests || []} color="purple" />
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Keywords / Skills
                </h4>
                <TagList tags={up.research_expertise?.keywords || []} color="blue" />
              </div>
            </div>
          </ProfileSection>

          {/* Teaching */}
          <ProfileSection
            title="Teaching"
            icon={BookOpen}
            onEdit={() => handleEditSection('teaching')}
          >
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Currently Teaching
                </h4>
                <TagList tags={up.teaching?.current_subjects || []} color="green" />
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Previously Taught
                </h4>
                <TagList tags={up.teaching?.past_subjects || []} color="blue" />
              </div>
            </div>
          </ProfileSection>

          {/* Availability */}
          <ProfileSection
            title="Availability"
            icon={Clock}
            onEdit={() => handleEditSection('availability')}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <InfoRow
                icon={MapPin}
                label="Office Location"
                value={up.availability?.office_location}
                isPrivate={up.visibility?.office_location === 'private'}
              />
              <InfoRow
                icon={Clock}
                label="Office Hours"
                value={up.availability?.office_hours}
              />
            </div>
            
            {up.availability?.available_slots?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Meeting Slots
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {up.availability.available_slots.map((slot, idx) => (
                    <SlotCard key={idx} slot={slot} />
                  ))}
                </div>
              </div>
            )}
          </ProfileSection>

          {/* Publications */}
          {up.publications && up.publications.total_count > 0 && (
            <ProfileSection
              title="Publications"
              icon={FileText}
              onEdit={() => handleEditSection('others')}
            >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {up.publications.total_count}
                  </p>
                  <p className="text-sm text-gray-500">Total</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {up.publications.journal_papers}
                  </p>
                  <p className="text-sm text-gray-500">Journal Papers</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {up.publications.conference_papers}
                  </p>
                  <p className="text-sm text-gray-500">Conference Papers</p>
                </div>
                {up.publications.h_index && (
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {up.publications.h_index}
                    </p>
                    <p className="text-sm text-gray-500">h-Index</p>
                  </div>
                )}
              </div>
              
              {up.publications.notable_works?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Notable Works
                  </h4>
                  <ul className="space-y-2">
                    {up.publications.notable_works.map((work, idx) => (
                      <li
                        key={idx}
                        className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2"
                      >
                        <span className="text-indigo-500 mt-1">•</span>
                        {work}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </ProfileSection>
          )}

          {/* Others */}
          {up.others && Object.keys(up.others).length > 0 && (
            <ProfileSection
              title="Additional Information"
              icon={Award}
              onEdit={() => handleEditSection('others')}
              defaultOpen={false}
            >
              <div className="space-y-4">
                {up.others.awards?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Awards & Honors
                    </h4>
                    <TagList tags={up.others.awards} color="purple" />
                  </div>
                )}
                
                {up.others.certifications?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Certifications
                    </h4>
                    <TagList tags={up.others.certifications} color="green" />
                  </div>
                )}
                
                {up.others.languages?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Languages
                    </h4>
                    <TagList tags={up.others.languages} color="blue" />
                  </div>
                )}
                
                {up.others.professional_memberships?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Professional Memberships
                    </h4>
                    <TagList tags={up.others.professional_memberships} color="indigo" />
                  </div>
                )}
              </div>
            </ProfileSection>
          )}
        </div>
      )}

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        Last updated: {new Date(profile.updated_at).toLocaleString()}
      </div>
    </div>
  );
};

export default FacultyProfileView;