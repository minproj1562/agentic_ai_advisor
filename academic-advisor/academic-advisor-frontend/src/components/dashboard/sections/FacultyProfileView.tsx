// src/components/dashboard/sections/FacultyProfileView.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  User, Mail, Phone, MapPin, Clock, Calendar,
  GraduationCap, Briefcase, BookOpen, Award,
  Edit, Globe, Linkedin, Settings, CheckCircle,
  Loader2, AlertCircle, ExternalLink, Upload, FileText
} from 'lucide-react';
// ✅ FIX 1: Correct import paths (was missing ../../../)
import apiClient from '../../../services/api.service';
import { useAuth } from '../../../contexts/AuthContext';
// ✅ FIX 2: Add useQuery for fresh data fetching
import { useQuery } from '@tanstack/react-query';

interface FacultyProfileViewProps {
  facultyId: string;
  facultyData: any;
  onEditProfile?: () => void;
}

// ==================== CRITICAL HELPER FUNCTIONS ====================

/**
 * ✅ FIX 3: Safely converts ANY value to a renderable string
 * Prevents "Objects are not valid as a React child" error
 */
const safeString = (value: any): string => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'boolean') return String(value);
  if (typeof value === 'object') {
    if ('name' in value) return String(value.name);
    if ('title' in value) return String(value.title);
    if ('value' in value) return String(value.value);
    return JSON.stringify(value);
  }
  return String(value);
};

/**
 * ✅ FIX 4: Safely converts array to string[]
 * Handles arrays of strings, arrays of objects, null/undefined
 */
const safeArray = (arr: any): string[] => {
  if (!arr || !Array.isArray(arr)) return [];
  return arr
    .map((item: any) => safeString(item))
    .filter((s: string) => s.trim().length > 0);
};

// ==================== MAIN COMPONENT ====================

const FacultyProfileView: React.FC<FacultyProfileViewProps> = ({
  facultyId,
  facultyData: initialData,  // ✅ Renamed to make clear it's just initial/fallback data
  onEditProfile,
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // ✅ FIX 5: Always fetch fresh data from API so CV analysis results show immediately
  // Don't rely on prop data which may be stale from dashboard cache
  const { data: freshFacultyData, isLoading, error, refetch } = useQuery({
    queryKey: ['faculty-profile-view', user?.uid],
    queryFn: async () => {
      const response = await apiClient.get('/faculty-profile/me');
      return response.data;
    },
    staleTime: 0,            // Always fetch fresh
    refetchOnMount: true,    // Refetch every time this section is opened
    enabled: !!user?.uid,
  });

  // ✅ FIX 6: Use fresh data if available, fall back to prop data
  const facultyData = freshFacultyData || initialData;
  const profile = facultyData?.uniform_profile;

  // ── Loading State ──────────────────────────────────────────────────────────
  if (isLoading && !initialData) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
        <p className="text-gray-600 dark:text-gray-400 text-sm">Loading your profile...</p>
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────────────────────
  if (error && !initialData) {
    return (
      <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <AlertCircle className="w-14 h-14 mx-auto text-red-500 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Failed to Load Profile
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
          {error instanceof Error ? error.message : 'Unable to fetch profile data.'}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            type="button"
            onClick={() => navigate('/faculty/dashboard')}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 
                       dark:hover:bg-gray-700 rounded-lg transition-colors text-sm"
          >
            Back to Dashboard
          </button>
          <button
            type="button"
            onClick={() => refetch()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 
                       transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ── Incomplete Profile State ───────────────────────────────────────────────
  if (!profile) {
    return (
      <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl shadow-lg px-8">
        <User className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Profile Not Complete
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Complete your profile setup to view this section
        </p>

        {/* Show CV upload status if CV exists but profile not setup */}
        {facultyData?.cv_url && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg inline-block">
            <p className="text-sm text-green-700 dark:text-green-300">
              ✅ CV uploaded — data pre-filled from your CV
            </p>
          </div>
        )}

        {/* ✅ FIX 7: Complete Profile button now uses onEditProfile callback */}
        <div className="flex gap-3 justify-center">
          <button
            type="button"
            onClick={() => {
              if (onEditProfile) {
                onEditProfile();
              } else {
                navigate('/faculty/profile-setup');
              }
            }}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 
                       transition-colors font-medium"
          >
            Complete Profile
          </button>
          {facultyData?.cv_url && (
            <a
              href={facultyData.cv_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 
                         dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 
                         transition-colors text-sm flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              View CV
            </a>
          )}
        </div>

        {/* Show pre-filled data from CV if available */}
        {facultyData?.uniform_profile === null && facultyData?.cv_parsed_data && (
          <div className="mt-6 text-left max-w-sm mx-auto">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 text-center uppercase tracking-wide">
              Extracted from CV
            </p>
            {facultyData.name && (
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 
                              bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2 mb-1">
                <User className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span>{safeString(facultyData.name)}</span>
              </div>
            )}
            {facultyData.designation && (
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 
                              bg-gray-50 dark:bg-gray-700/50 rounded-lg px-3 py-2 mb-1">
                <Briefcase className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                <span>{safeString(facultyData.designation)}</span>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ── Build Sections (ORIGINAL STRUCTURE PRESERVED) ─────────────────────────
  const sections = [
    {
      title: 'Personal Information',
      icon: User,
      items: [
        { label: 'Name',  value: safeString(profile.personal_info?.name) },
        { label: 'Email', value: safeString(profile.personal_info?.email) },
        { label: 'Phone', value: safeString(profile.personal_info?.phone) },
      ]
    },
    {
      title: 'Academic Qualifications',
      icon: GraduationCap,
      items: [
        { label: 'Highest Degree',   value: safeString(profile.academic_qualifications?.highest_degree) },
        { label: 'Specialization',   value: safeString(profile.academic_qualifications?.specialization) },
        { label: 'University',       value: safeString(profile.academic_qualifications?.university) },
        { label: 'Graduation Year',  value: safeString(profile.academic_qualifications?.graduation_year) },
      ]
    },
    {
      title: 'Current Position',
      icon: Briefcase,
      items: [
        { label: 'Designation', value: safeString(profile.current_position?.designation) },
        { label: 'Department',  value: safeString(profile.current_position?.department) },
        { label: 'Institution', value: safeString(profile.current_position?.institution) },
        { label: 'Experience',  value: `${safeString(profile.current_position?.years_of_experience || 0)} years` },
      ]
    },
    {
      title: 'Availability',
      icon: Clock,
      items: [
        { label: 'Office Location',   value: safeString(profile.availability?.office_location) },
        { label: 'Office Hours',      value: safeString(profile.availability?.office_hours) },
        { label: 'Meeting Duration',  value: `${safeString(profile.availability?.preferred_meeting_duration || 30)} mins` },
      ]
    }
  ];

  // ── ORIGINAL RENDER (FULLY PRESERVED + FIXES APPLIED) ────────────────────
  return (
    <div className="space-y-6">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            My Profile
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your professional profile information
          </p>
        </div>
        {/* ✅ FIX 8: Edit Profile now uses onEditProfile callback instead of broken navigation */}
        <button
  type="button"
  onClick={() => {
    if (onEditProfile) {
      onEditProfile();
    } else {
      navigate('/faculty/profile-edit', {
        state: { editMode: true, profile: facultyData }
      });
    }
  }}
  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
>
  <Edit className="w-4 h-4" />
  Edit Profile
</button>
      </div>

      {/* ── Profile Card (ORIGINAL) ─────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <div className="flex flex-col md:flex-row items-center md:items-start gap-6">

          {/* Avatar */}
          <div className="relative">
            {profile.personal_info?.photo_url ? (
              <img
                src={safeString(profile.personal_info.photo_url)}
                alt={safeString(profile.personal_info?.name)}
                className="w-32 h-32 rounded-full object-cover border-4 border-white/30"
              />
            ) : (
              <div className="w-32 h-32 bg-white/20 rounded-full flex items-center justify-center text-4xl font-bold">
                {safeString(profile.personal_info?.name).charAt(0) || 'F'}
              </div>
            )}
            {facultyData?.profile_setup_complete && (
              <div className="absolute bottom-0 right-0 w-8 h-8 bg-green-500 rounded-full 
                              flex items-center justify-center border-2 border-white">
                <CheckCircle className="w-5 h-5" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-3xl font-bold mb-1">
              {safeString(profile.personal_info?.name)}
            </h1>
            <p className="text-indigo-100 text-lg mb-2">
              {safeString(profile.current_position?.designation)}
            </p>
            <p className="text-indigo-200 mb-4">
              {safeString(profile.current_position?.department)} 
              {profile.current_position?.institution ? ` • ${safeString(profile.current_position.institution)}` : ''}
            </p>

            <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm">
              <span className="flex items-center gap-1">
                <Mail className="w-4 h-4" />
                {safeString(profile.personal_info?.email)}
              </span>
              {profile.personal_info?.phone && (
                <span className="flex items-center gap-1">
                  <Phone className="w-4 h-4" />
                  {safeString(profile.personal_info.phone)}
                </span>
              )}
              {profile.availability?.office_location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {safeString(profile.availability.office_location)}
                </span>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 bg-white/10 rounded-xl p-4">
            <div className="text-center">
              <p className="text-2xl font-bold">{safeString(facultyData?.mentee_count || 0)}</p>
              <p className="text-xs text-indigo-200">Mentees</p>
            </div>
            <div className="text-center border-x border-white/20">
              <p className="text-2xl font-bold">{safeString(profile.publications?.total_count || 0)}</p>
              <p className="text-xs text-indigo-200">Publications</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {safeString(profile.current_position?.years_of_experience || 0)}+
              </p>
              <p className="text-xs text-indigo-200">Years Exp.</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── CV Section (NEW) ────────────────────────────────────────────────── */}
      {/* Shows CV upload status and allows re-upload */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Curriculum Vitae</h3>
              <p className="text-sm text-gray-500">
                {facultyData?.cv_uploaded_at
                  ? `Uploaded ${new Date(facultyData.cv_uploaded_at).toLocaleDateString()}`
                  : 'No CV uploaded yet'
                }
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            {facultyData?.cv_url && (
              <a
                href={facultyData.cv_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 
                           dark:hover:bg-indigo-900/20 rounded-lg transition-colors text-sm"
              >
                <ExternalLink className="w-4 h-4" />
                View
              </a>
            )}
            <button
              type="button"
              onClick={() => navigate('/faculty/profile-setup', {
                state: { editMode: true, reuploadCV: true }
              })}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white 
                         rounded-lg hover:bg-indigo-700 transition-colors text-sm"
            >
              <Upload className="w-4 h-4" />
              {facultyData?.cv_url ? 'Re-upload' : 'Upload CV'}
            </button>
          </div>
        </div>
      </div>

      {/* ── Profile Sections (ORIGINAL STRUCTURE) ──────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((section, index) => {
          const Icon = section.icon;
          return (
            <motion.div
              key={section.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Icon className="w-5 h-5 text-indigo-600" />
                {section.title}
              </h3>
              <div className="space-y-3">
                {section.items.map((item, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {item.label}
                    </span>
                    {/* ✅ FIX 9: safeString already applied above in sections array */}
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {item.value || 'Not specified'}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* ── Research & Teaching (ORIGINAL + FIXED) ─────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Research Areas */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-green-600" />
            Research Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {/* ✅ FIX 10: safeArray() prevents object rendering errors */}
            {safeArray(profile.research_expertise?.primary_areas).map((area, i) => (
              <span
                key={`primary-${i}`}
                className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 
                           dark:text-green-300 rounded-full text-sm font-medium"
              >
                {area}
              </span>
            ))}
            {safeArray(profile.research_expertise?.secondary_interests).map((area, i) => (
              <span
                key={`secondary-${i}`}
                className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 
                           dark:text-gray-300 rounded-full text-sm"
              >
                {area}
              </span>
            ))}
            {/* Show empty state if no areas */}
            {safeArray(profile.research_expertise?.primary_areas).length === 0 &&
             safeArray(profile.research_expertise?.secondary_interests).length === 0 && (
              <span className="text-sm text-gray-400 italic">Not specified</span>
            )}
          </div>
        </div>

        {/* Teaching Subjects */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-purple-600" />
            Teaching Subjects
          </h3>
          <div className="flex flex-wrap gap-2">
            {/* ✅ FIX 11: safeArray() prevents object rendering errors */}
            {safeArray(profile.teaching?.current_subjects).map((subject, i) => (
              <span
                key={`subject-${i}`}
                className="px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 
                           dark:text-purple-300 rounded-full text-sm font-medium"
              >
                {subject}
              </span>
            ))}
            {safeArray(profile.teaching?.current_subjects).length === 0 && (
              <span className="text-sm text-gray-400 italic">Not specified</span>
            )}
          </div>
        </div>
      </div>

      {/* ── Meeting Slots (NEW - shows availability slots) ──────────────────── */}
      {profile.availability?.available_slots?.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            Meeting Slots
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {profile.availability.available_slots.map((slot: any, idx: number) => (
              <div
                key={`slot-${idx}`}
                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg flex-shrink-0">
                  <Calendar className="w-4 h-4 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                    {safeString(slot?.day)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {safeString(slot?.start_time)} – {safeString(slot?.end_time)}
                    {slot?.venue ? ` • ${safeString(slot.venue)}` : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Awards & Certifications (ORIGINAL + FIXED) ─────────────────────── */}
      {profile.others && (
        (Array.isArray(profile.others.awards) && profile.others.awards.length > 0) ||
        (Array.isArray(profile.others.certifications) && profile.others.certifications.length > 0)
      ) && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-600" />
            Awards & Certifications
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Array.isArray(profile.others.awards) && profile.others.awards.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Awards</h4>
                <ul className="space-y-2">
                  {/* ✅ FIX 12: safeString() wraps each award to prevent object rendering */}
                  {safeArray(profile.others.awards).map((award, i) => (
                    <li
                      key={`award-${i}`}
                      className="flex items-start gap-2 text-sm text-gray-900 dark:text-white"
                    >
                      <Award className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                      <span>{award}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {Array.isArray(profile.others.certifications) && profile.others.certifications.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Certifications</h4>
                <ul className="space-y-2">
                  {/* ✅ FIX 13: safeString() wraps each cert to prevent object rendering */}
                  {safeArray(profile.others.certifications).map((cert, i) => (
                    <li
                      key={`cert-${i}`}
                      className="flex items-start gap-2 text-sm text-gray-900 dark:text-white"
                    >
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>{cert}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Publications (NEW - shown if data exists) ───────────────────────── */}
      {profile.publications && profile.publications.total_count > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-600" />
            Publications
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {[
              { label: 'Total',             value: profile.publications.total_count },
              { label: 'Journal Papers',    value: profile.publications.journal_papers },
              { label: 'Conference Papers', value: profile.publications.conference_papers },
              { label: 'h-Index',           value: profile.publications.h_index },
            ].filter(({ value }) => value !== null && value !== undefined && value !== 0)
             .map(({ label, value }) => (
              <div key={label} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {safeString(value)}
                </p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          {profile.publications.notable_works?.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Notable Works</h4>
              <ul className="space-y-1">
                {safeArray(profile.publications.notable_works).map((work, idx) => (
                  <li
                    key={`work-${idx}`}
                    className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2"
                  >
                    <span className="text-indigo-500 mt-1 flex-shrink-0">•</span>
                    <span>{work}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── Additional Info ─────────────────────────────────────────────────── */}
      {profile.others && (
        safeArray(profile.others.languages).length > 0 ||
        safeArray(profile.others.professional_memberships).length > 0 ||
        safeArray(profile.others.patents).length > 0
      ) && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-600" />
            Additional Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {safeArray(profile.others.languages).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Languages</h4>
                <div className="flex flex-wrap gap-2">
                  {safeArray(profile.others.languages).map((lang, i) => (
                    <span
                      key={`lang-${i}`}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 
                                 dark:text-blue-300 rounded-full text-sm"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {safeArray(profile.others.professional_memberships).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                  Professional Memberships
                </h4>
                <div className="flex flex-wrap gap-2">
                  {safeArray(profile.others.professional_memberships).map((mem, i) => (
                    <span
                      key={`mem-${i}`}
                      className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 
                                 dark:text-indigo-300 rounded-full text-sm"
                    >
                      {mem}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {safeArray(profile.others.patents).length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Patents</h4>
                <div className="flex flex-wrap gap-2">
                  {safeArray(profile.others.patents).map((pat, i) => (
                    <span
                      key={`pat-${i}`}
                      className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 
                                 dark:text-purple-300 rounded-full text-sm"
                    >
                      {pat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Footer ─────────────────────────────────────────────────────────── */}
      <p className="text-center text-xs text-gray-400 dark:text-gray-500">
        Last updated:{' '}
        {facultyData?.updated_at
          ? new Date(facultyData.updated_at).toLocaleString()
          : 'Unknown'
        }
      </p>
    </div>
  );
};

export default FacultyProfileView;