// src/components/dashboard/sections/FacultyProfileEdit.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  User, Mail, Phone, MapPin, Briefcase, GraduationCap,
  BookOpen, Award, Save, X, Plus, Trash2, Loader2, ArrowLeft,
  Clock, Globe, FileText, CheckCircle
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import { useAuth } from '../../../contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// ── Stable sub-components (defined OUTSIDE to prevent re-creation on re-render) ──

const Section: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode; delay?: number }> = ({ title, icon, children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay }}
    className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
  >
    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
      {icon}
      {title}
    </h3>
    <div className="space-y-4">{children}</div>
  </motion.div>
);

const TextField: React.FC<{
  field: string; label: string; placeholder?: string; type?: string; required?: boolean;
  value: any; onChange: (field: string, value: any) => void;
}> = ({ field, label, placeholder, type = 'text', required, value, onChange }) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    <input
      type={type}
      value={value || ''}
      onChange={e => onChange(field, type === 'number' ? Number(e.target.value) : e.target.value)}
      placeholder={placeholder}
      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
    />
  </div>
);

const TagInput: React.FC<{
  field: string; label: string; placeholder: string;
  items: string[]; onAdd: (field: string, value: string) => void; onRemove: (field: string, index: number) => void;
}> = ({ field, label, placeholder, items, onAdd, onRemove }) => {
  const [input, setInput] = useState('');
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {items.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm">
            {item}
            <button type="button" onClick={() => onRemove(field, i)} className="hover:text-red-500">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); onAdd(field, input); setInput(''); } }}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
        <button
          type="button"
          onClick={() => { onAdd(field, input); setInput(''); }}
          className="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

interface FacultyProfileEditProps {
  facultyId: string;
  facultyData: any;
  onBack: () => void;
}

const FacultyProfileEdit: React.FC<FacultyProfileEditProps> = ({
  facultyId,
  facultyData,
  onBack,
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);

  const profile = facultyData?.uniform_profile;
  const isNewProfile = !profile;

  // ── Form State ──────────────────────────────────────────────
  const [form, setForm] = useState({
    // Personal
    name: '',
    phone: '',
    photo_url: '',
    // Academic
    highest_degree: '',
    specialization: '',
    graduation_university: '',
    graduation_year: '',
    // Position
    designation: '',
    department: '',
    institution: '',
    years_of_experience: 0,
    joining_year: '',
    // Research
    primary_research_areas: [] as string[],
    secondary_interests: [] as string[],
    research_keywords: [] as string[],
    // Teaching
    current_subjects: [] as string[],
    past_subjects: [] as string[],
    preferred_teaching_areas: [] as string[],
    // Availability
    office_location: '',
    office_hours: '',
    preferred_meeting_duration: 30,
    // Publications
    total_publications: 0,
    journal_papers: 0,
    conference_papers: 0,
    h_index: 0,
    notable_works: [] as string[],
    // Others
    awards: [] as string[],
    certifications: [] as string[],
    patents: [] as string[],
    languages: [] as string[],
    professional_memberships: [] as string[],
    industry_experience: [] as string[],
  });

  // ── Populate from existing data ─────────────────────────────
  useEffect(() => {
    if (profile) {
      setForm({
        name: profile.personal_info?.name || facultyData?.name || '',
        phone: profile.personal_info?.phone || '',
        photo_url: profile.personal_info?.photo_url || '',
        highest_degree: profile.academic_qualifications?.highest_degree || '',
        specialization: profile.academic_qualifications?.specialization || '',
        graduation_university: profile.academic_qualifications?.university || '',
        graduation_year: profile.academic_qualifications?.graduation_year || '',
        designation: profile.current_position?.designation || '',
        department: profile.current_position?.department || '',
        institution: profile.current_position?.institution || '',
        years_of_experience: profile.current_position?.years_of_experience || 0,
        joining_year: profile.current_position?.joining_year || '',
        primary_research_areas: safeArr(profile.research_expertise?.primary_areas),
        secondary_interests: safeArr(profile.research_expertise?.secondary_interests),
        research_keywords: safeArr(profile.research_expertise?.keywords),
        current_subjects: safeArr(profile.teaching?.current_subjects),
        past_subjects: safeArr(profile.teaching?.past_subjects),
        preferred_teaching_areas: safeArr(profile.teaching?.preferred_areas),
        office_location: profile.availability?.office_location || '',
        office_hours: profile.availability?.office_hours || '',
        preferred_meeting_duration: profile.availability?.preferred_meeting_duration || 30,
        total_publications: profile.publications?.total_count || 0,
        journal_papers: profile.publications?.journal_papers || 0,
        conference_papers: profile.publications?.conference_papers || 0,
        h_index: profile.publications?.h_index || 0,
        notable_works: safeArr(profile.publications?.notable_works),
        awards: safeArr(profile.others?.awards),
        certifications: safeArr(profile.others?.certifications),
        patents: safeArr(profile.others?.patents),
        languages: safeArr(profile.others?.languages),
        professional_memberships: safeArr(profile.others?.professional_memberships),
        industry_experience: safeArr(profile.others?.industry_experience),
      });
    } else if (facultyData) {
      // New profile — pre-fill from top-level faculty data
      setForm(prev => ({
        ...prev,
        name: facultyData.name || '',
        department: facultyData.department || '',
        designation: facultyData.designation || '',
      }));
    }
  }, [profile, facultyData]);

  // ── Helpers ─────────────────────────────────────────────────
  const safeArr = (val: any): string[] => {
    if (!val || !Array.isArray(val)) return [];
    return val.map((v: any) => typeof v === 'string' ? v : (v?.name || v?.title || JSON.stringify(v))).filter(Boolean);
  };

  const updateField = useCallback((field: string, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  }, []);

  const addToList = useCallback((field: string, value: string) => {
    if (!value.trim()) return;
    setForm(prev => ({ ...prev, [field]: [...(prev as any)[field], value.trim()] }));
  }, []);

  const removeFromList = useCallback((field: string, index: number) => {
    setForm(prev => ({ ...prev, [field]: (prev as any)[field].filter((_: any, i: number) => i !== index) }));
  }, []);

  // ── Save ────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    try {
      // Convert string years to int | null for Pydantic
      const gradYear = form.graduation_year ? parseInt(String(form.graduation_year), 10) || null : null;
      const joinYear = form.joining_year ? parseInt(String(form.joining_year), 10) || null : null;
      // industry_experience: backend expects Optional[str], frontend stores string[]
      const industryExp = Array.isArray(form.industry_experience)
        ? form.industry_experience.join('; ')
        : form.industry_experience || null;

      if (isNewProfile) {
        // Use /setup for first-time profile creation
        const setupPayload = {
          ...form,
          graduation_year: gradYear,
          joining_year: joinYear,
          industry_experience: industryExp,
          all_degrees: [{
            degree: form.highest_degree,
            field: form.specialization,
            institution: form.graduation_university,
            year: gradYear,
          }],
          available_slots: [],
        };
        await apiClient.post('/faculty-profile/setup', setupPayload);
        toast.success('Profile created successfully!');
      } else {
        // Use /update for existing profiles
        const updatePayload = {
          ...form,
          graduation_year: gradYear,
          joining_year: joinYear,
          industry_experience: industryExp,
        };
        await apiClient.put('/faculty-profile/update', updatePayload);
        toast.success('Profile updated successfully!');
      }
      // Invalidate cache so dashboard refreshes
      queryClient.invalidateQueries({ queryKey: ['faculty-profile'] });
      queryClient.invalidateQueries({ queryKey: ['faculty-profile-view'] });
      // Go back to profile view
      setTimeout(() => onBack(), 500);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      // detail can be a string OR an array of Pydantic validation errors [{type,loc,msg,input,url}]
      let msg = 'Failed to save profile';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        msg = detail.map((e: any) => typeof e === 'string' ? e : (e?.msg || JSON.stringify(e))).join(', ');
      }
      toast.error(msg);
      console.error('Profile save error:', error);
    } finally {
      setSaving(false);
    }
  };

  // Sub-components are defined OUTSIDE the main component (above)
  // to prevent re-creation on every render

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isNewProfile ? 'Complete Your Profile' : 'Edit Profile'}
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              {isNewProfile ? 'Fill in your details to set up your faculty profile' : 'Update your professional information'}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={onBack} className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !form.name.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Info banner for new profiles */}
      {isNewProfile && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 flex items-start gap-3">
          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800 dark:text-blue-300">No CV? No problem!</p>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Fill in the form below to create your profile manually. You can always upload a CV later from your profile page.</p>
          </div>
        </motion.div>
      )}

      {/* Personal Information */}
      <Section title="Personal Information" icon={<User className="w-5 h-5 text-indigo-600" />} delay={0.05}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField field="name" label="Full Name" placeholder="Dr. John Doe" required value={form.name} onChange={updateField} />
          <TextField field="phone" label="Phone Number" placeholder="+91 98765 43210" value={form.phone} onChange={updateField} />
        </div>
        <TextField field="photo_url" label="Photo URL" placeholder="https://..." value={form.photo_url} onChange={updateField} />
      </Section>

      {/* Academic Qualifications */}
      <Section title="Academic Qualifications" icon={<GraduationCap className="w-5 h-5 text-purple-600" />} delay={0.1}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField field="highest_degree" label="Highest Degree" placeholder="Ph.D., M.Tech, M.E." required value={form.highest_degree} onChange={updateField} />
          <TextField field="specialization" label="Specialization" placeholder="Computer Science, AI/ML" value={form.specialization} onChange={updateField} />
          <TextField field="graduation_university" label="University" placeholder="University of Mumbai" value={form.graduation_university} onChange={updateField} />
          <TextField field="graduation_year" label="Graduation Year" placeholder="2015" value={form.graduation_year} onChange={updateField} />
        </div>
      </Section>

      {/* Current Position */}
      <Section title="Current Position" icon={<Briefcase className="w-5 h-5 text-green-600" />} delay={0.15}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField field="designation" label="Designation" placeholder="Assistant Professor" required value={form.designation} onChange={updateField} />
          <TextField field="department" label="Department" placeholder="Information Technology" required value={form.department} onChange={updateField} />
          <TextField field="institution" label="Institution" placeholder="FCRIT, Vashi" value={form.institution} onChange={updateField} />
          <TextField field="years_of_experience" label="Years of Experience" type="number" value={form.years_of_experience} onChange={updateField} />
          <TextField field="joining_year" label="Joining Year" placeholder="2018" value={form.joining_year} onChange={updateField} />
        </div>
      </Section>

      {/* Research */}
      <Section title="Research & Expertise" icon={<BookOpen className="w-5 h-5 text-emerald-600" />} delay={0.2}>
        <TagInput field="primary_research_areas" label="Primary Research Areas (max 5)" placeholder="e.g. Machine Learning" items={form.primary_research_areas} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="secondary_interests" label="Secondary Interests" placeholder="e.g. Data Mining" items={form.secondary_interests} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="research_keywords" label="Research Keywords" placeholder="e.g. NLP, Deep Learning" items={form.research_keywords} onAdd={addToList} onRemove={removeFromList} />
      </Section>

      {/* Teaching */}
      <Section title="Teaching" icon={<GraduationCap className="w-5 h-5 text-blue-600" />} delay={0.25}>
        <TagInput field="current_subjects" label="Current Subjects" placeholder="e.g. Operating Systems" items={form.current_subjects} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="past_subjects" label="Past Subjects" placeholder="e.g. Data Structures" items={form.past_subjects} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="preferred_teaching_areas" label="Preferred Teaching Areas" placeholder="e.g. AI/ML" items={form.preferred_teaching_areas} onAdd={addToList} onRemove={removeFromList} />
      </Section>

      {/* Availability */}
      <Section title="Availability" icon={<Clock className="w-5 h-5 text-amber-600" />} delay={0.3}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextField field="office_location" label="Office Location" placeholder="Room 301, 3rd Floor" value={form.office_location} onChange={updateField} />
          <TextField field="office_hours" label="Office Hours" placeholder="Mon-Fri 10:00-17:00" value={form.office_hours} onChange={updateField} />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Meeting Duration (mins)</label>
            <select
              value={form.preferred_meeting_duration}
              onChange={e => updateField('preferred_meeting_duration', Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
            >
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
              <option value={45}>45 minutes</option>
              <option value={60}>60 minutes</option>
            </select>
          </div>
        </div>
      </Section>

      {/* Publications */}
      <Section title="Publications" icon={<FileText className="w-5 h-5 text-indigo-600" />} delay={0.35}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <TextField field="total_publications" label="Total" type="number" value={form.total_publications} onChange={updateField} />
          <TextField field="journal_papers" label="Journal Papers" type="number" value={form.journal_papers} onChange={updateField} />
          <TextField field="conference_papers" label="Conference Papers" type="number" value={form.conference_papers} onChange={updateField} />
          <TextField field="h_index" label="h-Index" type="number" value={form.h_index} onChange={updateField} />
        </div>
        <TagInput field="notable_works" label="Notable Works" placeholder="e.g. Paper title..." items={form.notable_works} onAdd={addToList} onRemove={removeFromList} />
      </Section>

      {/* Awards & Others */}
      <Section title="Awards, Certifications & More" icon={<Award className="w-5 h-5 text-yellow-600" />} delay={0.4}>
        <TagInput field="awards" label="Awards" placeholder="e.g. Best Paper Award 2023" items={form.awards} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="certifications" label="Certifications" placeholder="e.g. AWS Certified" items={form.certifications} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="patents" label="Patents" placeholder="e.g. Patent title" items={form.patents} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="languages" label="Languages" placeholder="e.g. English, Hindi" items={form.languages} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="professional_memberships" label="Professional Memberships" placeholder="e.g. IEEE, ACM" items={form.professional_memberships} onAdd={addToList} onRemove={removeFromList} />
        <TagInput field="industry_experience" label="Industry Experience" placeholder="e.g. Software Engineer at TCS (2010-2015)" items={form.industry_experience} onAdd={addToList} onRemove={removeFromList} />
      </Section>

      {/* Bottom Save Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 border border-gray-200 dark:border-gray-700 flex items-center justify-between sticky bottom-4"
      >
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {isNewProfile ? 'Fill required fields and save to create your profile' : 'Review your changes and save'}
        </p>
        <div className="flex gap-3">
          <button onClick={onBack} className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-sm">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !form.name.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium shadow-lg shadow-indigo-600/20"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {saving ? 'Saving...' : isNewProfile ? 'Create Profile' : 'Save Changes'}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default FacultyProfileEdit;
