// src/components/dashboard/sections/FacultyProfileView.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  User, Mail, Phone, MapPin, Clock, Calendar,
  GraduationCap, Briefcase, BookOpen, Award,
  Edit, Globe, Linkedin, Settings, CheckCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface FacultyProfileViewProps {
  facultyId: string;
  facultyData: any;
}

const FacultyProfileView: React.FC<FacultyProfileViewProps> = ({
  facultyId,
  facultyData
}) => {
  const navigate = useNavigate();
  const profile = facultyData?.uniform_profile;

  if (!profile) {
    return (
      <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl shadow-lg">
        <User className="w-16 h-16 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Profile Not Complete
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Complete your profile setup to view this section
        </p>
        <button
          onClick={() => navigate('/faculty/profile-setup')}
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Complete Profile
        </button>
      </div>
    );
  }

  const sections = [
    {
      title: 'Personal Information',
      icon: User,
      items: [
        { label: 'Name', value: profile.personal_info?.name },
        { label: 'Email', value: profile.personal_info?.email },
        { label: 'Phone', value: profile.personal_info?.phone },
      ]
    },
    {
      title: 'Academic Qualifications',
      icon: GraduationCap,
      items: [
        { label: 'Highest Degree', value: profile.academic_qualifications?.highest_degree },
        { label: 'Specialization', value: profile.academic_qualifications?.specialization },
        { label: 'University', value: profile.academic_qualifications?.university },
        { label: 'Graduation Year', value: profile.academic_qualifications?.graduation_year },
      ]
    },
    {
      title: 'Current Position',
      icon: Briefcase,
      items: [
        { label: 'Designation', value: profile.current_position?.designation },
        { label: 'Department', value: profile.current_position?.department },
        { label: 'Institution', value: profile.current_position?.institution },
        { label: 'Experience', value: `${profile.current_position?.years_of_experience || 0} years` },
      ]
    },
    {
      title: 'Availability',
      icon: Clock,
      items: [
        { label: 'Office Location', value: profile.availability?.office_location },
        { label: 'Office Hours', value: profile.availability?.office_hours },
        { label: 'Meeting Duration', value: `${profile.availability?.preferred_meeting_duration || 30} mins` },
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            My Profile
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your professional profile information
          </p>
        </div>
        <button
          onClick={() => navigate('/faculty/profile-setup')}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <Edit className="w-4 h-4" />
          Edit Profile
        </button>
      </div>

      {/* Profile Card */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
          {/* Avatar */}
          <div className="relative">
            {profile.personal_info?.photo_url ? (
              <img
                src={profile.personal_info.photo_url}
                alt={profile.personal_info?.name}
                className="w-32 h-32 rounded-full object-cover border-4 border-white/30"
              />
            ) : (
              <div className="w-32 h-32 bg-white/20 rounded-full flex items-center justify-center text-4xl font-bold">
                {profile.personal_info?.name?.charAt(0) || 'F'}
              </div>
            )}
            {facultyData?.profile_setup_complete && (
              <div className="absolute bottom-0 right-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center border-2 border-white">
                <CheckCircle className="w-5 h-5" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-3xl font-bold mb-1">
              {profile.personal_info?.name}
            </h1>
            <p className="text-indigo-100 text-lg mb-2">
              {profile.current_position?.designation}
            </p>
            <p className="text-indigo-200 mb-4">
              {profile.current_position?.department} • {profile.current_position?.institution}
            </p>
            
            <div className="flex flex-wrap justify-center md:justify-start gap-4 text-sm">
              <span className="flex items-center gap-1">
                <Mail className="w-4 h-4" />
                {profile.personal_info?.email}
              </span>
              {profile.personal_info?.phone && (
                <span className="flex items-center gap-1">
                  <Phone className="w-4 h-4" />
                  {profile.personal_info.phone}
                </span>
              )}
              {profile.availability?.office_location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {profile.availability.office_location}
                </span>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 bg-white/10 rounded-xl p-4">
            <div className="text-center">
              <p className="text-2xl font-bold">{facultyData?.mentee_count || 0}</p>
              <p className="text-xs text-indigo-200">Mentees</p>
            </div>
            <div className="text-center border-x border-white/20">
              <p className="text-2xl font-bold">{profile.publications?.total_count || 0}</p>
              <p className="text-xs text-indigo-200">Publications</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">{profile.current_position?.years_of_experience || 0}+</p>
              <p className="text-xs text-indigo-200">Years Exp.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Profile Sections */}
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

      {/* Research & Teaching */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Research Areas */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-green-600" />
            Research Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {profile.research_expertise?.primary_areas?.map((area: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm font-medium"
              >
                {area}
              </span>
            ))}
            {profile.research_expertise?.secondary_interests?.map((area: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
              >
                {area}
              </span>
            ))}
          </div>
        </div>

        {/* Teaching Subjects */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-purple-600" />
            Teaching Subjects
          </h3>
          <div className="flex flex-wrap gap-2">
            {profile.teaching?.current_subjects?.map((subject: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium"
              >
                {subject}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Awards & Others */}
      {profile.others && (profile.others.awards?.length > 0 || profile.others.certifications?.length > 0) && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-600" />
            Awards & Certifications
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {profile.others.awards?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Awards</h4>
                <ul className="space-y-2">
                  {profile.others.awards.map((award: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-900 dark:text-white">
                      <Award className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
                      {award}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {profile.others.certifications?.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Certifications</h4>
                <ul className="space-y-2">
                  {profile.others.certifications.map((cert: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-900 dark:text-white">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      {cert}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FacultyProfileView;