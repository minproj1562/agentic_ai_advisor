// src/components/admin/sections/FacultyManagement.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search, X, CheckCircle, Clock, AlertCircle,
  UserPlus, Mail, Building, Briefcase, Info,
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

// ✅ Fetch emails from MongoDB — no hardcoded list
import { useFacultyEmails } from '../../../hooks/useFacultyEmails';

// ─── Types ────────────────────────────────────────────────────────────────────

interface CreateFacultyForm {
  email:       string;
  name:        string;
  department:  string;
  designation: string;
}

interface FormErrors {
  email?:       string;
  name?:        string;
  department?:  string;
  designation?: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const FCRIT_EMAIL_RE = /^[a-z]+\.[a-z]+@fcrit\.ac\.in$/;

const DEPARTMENTS = ['IT', 'COMP', 'EXTC', 'MECH', 'CIVIL', 'CHEM'];

const DESIGNATIONS = [
  'Assistant Professor',
  'Associate Professor',
  'Professor',
  'HOD',
  'Principal',
  'Visiting Faculty',
];

// ─── Validation ───────────────────────────────────────────────────────────────

function validateForm(form: CreateFacultyForm): FormErrors {
  const errors: FormErrors = {};

  if (!form.email) {
    errors.email = 'Email is required';
  } else if (!FCRIT_EMAIL_RE.test(form.email.toLowerCase())) {
    errors.email =
      'Must be firstname.lastname@fcrit.ac.in (e.g. poonam.bari@fcrit.ac.in)';
  }

  if (!form.name.trim())    errors.name        = 'Name is required';
  if (!form.department)     errors.department  = 'Department is required';
  if (!form.designation)    errors.designation = 'Designation is required';

  return errors;
}

// ─── Status badge ─────────────────────────────────────────────────────────────

const statusBadge = (status: string) => {
  const styles: Record<string, string> = {
    active:        'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    pending_setup: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    on_leave:      'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400',
    inactive:      'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };
  const icons: Record<string, React.ReactNode> = {
    active:        <CheckCircle className="w-3 h-3" />,
    pending_setup: <Clock       className="w-3 h-3" />,
    inactive:      <AlertCircle className="w-3 h-3" />,
  };
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
        styles[status] || styles.inactive
      }`}
    >
      {icons[status]}
      {status.replace(/_/g, ' ')}
    </span>
  );
};

// ─── Component ────────────────────────────────────────────────────────────────

const FacultyManagement: React.FC = () => {
  const queryClient = useQueryClient();

  // ── List state ────────────────────────────────────────────────────────────
  const [search, setSearch]               = useState('');
  const [statusFilter, setStatusFilter]   = useState('');
  const [selectedFaculty, setSelectedFaculty] = useState<any>(null);

  // ── Create-form state ─────────────────────────────────────────────────────
  const [showAddModal, setShowAddModal]           = useState(false);
  const [showRegisteredEmails, setShowRegisteredEmails] = useState(false);
  const [form, setForm] = useState<CreateFacultyForm>({
    email:       '',
    name:        '',
    department:  '',
    designation: 'Assistant Professor',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // ── Queries ───────────────────────────────────────────────────────────────

  // Faculty list from backend
  const { data, isLoading } = useQuery({
    queryKey: ['admin-faculty', search, statusFilter],
    queryFn: async () => {
      const params: any = { limit: 50 };
      if (search)       params.search = search;
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.get('/admin/faculty', { params });
      return res.data;
    },
    staleTime: 30_000,
  });

  // Faculty detail modal
  const { data: facultyDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['admin-faculty-detail', selectedFaculty?.user_id],
    queryFn: async () => {
      const res = await apiClient.get(
        `/admin/faculty/${selectedFaculty.user_id}`
      );
      return res.data;
    },
    enabled: !!selectedFaculty?.user_id,
  });

  // ✅ Registered faculty emails from MongoDB — used for the "click to use" list
  const { data: registeredEmailsData, isLoading: emailsLoading } =
    useFacultyEmails();

  // ── Create mutation ───────────────────────────────────────────────────────

  const createFacultyMutation = useMutation({
    mutationFn: async (payload: CreateFacultyForm) => {
      // ✅ Password is NOT sent — backend uses DEFAULT_FACULTY_PASSWORD
      const res = await apiClient.post('/admin/faculty/create', payload);
      return res.data;
    },
    onSuccess: (responseData) => {
      toast.success(
        `✅ Faculty account created for ${responseData.email}\n` +
        `Default password: Fcrit@123\n` +
        `Faculty will be prompted to change it on first login.`
      );
      queryClient.invalidateQueries({ queryKey: ['admin-faculty'] });
      queryClient.invalidateQueries({ queryKey: ['admin-stats'] });
      // ✅ Invalidate the emails cache so the new faculty appears in the list
      queryClient.invalidateQueries({ queryKey: ['faculty-emails-public'] });
      setShowAddModal(false);
      resetForm();
    },
    onError: (error: any) => {
      const msg =
        error?.response?.data?.detail || 'Failed to create faculty account';
      toast.error(msg);
    },
  });

  // ── Helpers ───────────────────────────────────────────────────────────────

  const resetForm = () => {
    setForm({
      email:       '',
      name:        '',
      department:  '',
      designation: 'Assistant Professor',
    });
    setFormErrors({});
  };

  const handleFieldChange = (
    field: keyof CreateFacultyForm,
    value: string
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));

    // Clear error for this field on change
    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    }

    // Auto-fill name from email when email changes
    if (field === 'email') {
      const match = value.match(/^([a-z]+)\.([a-z]+)@fcrit\.ac\.in$/i);
      if (match) {
        const autoName =
          match[1].charAt(0).toUpperCase() + match[1].slice(1) + ' ' +
          match[2].charAt(0).toUpperCase() + match[2].slice(1);
        setForm((prev) => ({ ...prev, email: value, name: autoName }));
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors = validateForm(form);
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }
    createFacultyMutation.mutate({
      ...form,
      email: form.email.toLowerCase().trim(),
    });
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Faculty Management
        </h2>

        <div className="flex gap-3 w-full sm:w-auto flex-wrap">
          {/* Search */}
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search faculty..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="pending_setup">Pending Setup</option>
            <option value="on_leave">On Leave</option>
            <option value="inactive">Inactive</option>
          </select>

          {/* Add faculty button */}
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            Add Faculty
          </button>
        </div>
      </div>

      {/* ── Faculty Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg animate-pulse"
              >
                <div className="h-12 w-12 bg-gray-200 dark:bg-gray-600 rounded-full mb-4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-1/2" />
              </div>
            ))
          : data?.faculty?.map((f: any) => (
              <motion.div
                key={f.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg hover:shadow-xl transition-all cursor-pointer"
                onClick={() => setSelectedFaculty(f)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {f.name?.charAt(0) || 'F'}
                  </div>
                  {statusBadge(f.status)}
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {f.name}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  {f.designation}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  {f.department}
                </p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">
                    Mentees:{' '}
                    <strong className="text-gray-700 dark:text-gray-300">
                      {f.mentee_count}/{f.max_mentees}
                    </strong>
                  </span>
                  <span className="text-gray-500">
                    Profile:{' '}
                    <strong className="text-gray-700 dark:text-gray-300">
                      {f.profile_completeness}%
                    </strong>
                  </span>
                </div>
                {f.profile_completeness < 100 && (
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-1.5 rounded-full"
                      style={{ width: `${f.profile_completeness}%` }}
                    />
                  </div>
                )}
              </motion.div>
            ))}
      </div>

      {data?.faculty?.length === 0 && !isLoading && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No faculty found
        </div>
      )}

      {/* ── Detail Modal ── */}
      <AnimatePresence>
        {selectedFaculty && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedFaculty(null)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  {facultyDetail?.name || selectedFaculty.name}
                </h3>
                <button
                  onClick={() => setSelectedFaculty(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4 text-sm">
                {detailLoading ? (
                  <div className="animate-pulse space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="h-4 bg-gray-200 dark:bg-gray-600 rounded" />
                    ))}
                  </div>
                ) : facultyDetail ? (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-gray-500">Email:</span><br />
                        <span className="font-medium text-gray-900 dark:text-white break-all">
                          {facultyDetail.email}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Department:</span><br />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {facultyDetail.department}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Designation:</span><br />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {facultyDetail.designation}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Status:</span><br />
                        {statusBadge(facultyDetail.status)}
                      </div>
                      <div>
                        <span className="text-gray-500">Mentees:</span><br />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {facultyDetail.mentee_count}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Meetings:</span><br />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {facultyDetail.meetings_count}
                        </span>
                      </div>
                    </div>
                    {facultyDetail.specializations?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          Specializations
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {facultyDetail.specializations.map((s: string) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {facultyDetail.teaching_subjects?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
                          Teaching
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {facultyDetail.teaching_subjects.map((s: string) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-gray-500">No data</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Add Faculty Modal ── */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => { setShowAddModal(false); resetForm(); }}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <UserPlus className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                      Add Faculty Member
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Creates Firebase Auth + Firestore + MongoDB records
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => { setShowAddModal(false); resetForm(); }}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* ✅ Info box explaining default password */}
              <div className="mx-6 mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex gap-2">
                  <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-blue-700 dark:text-blue-300">
                    <p className="font-semibold mb-1">Email format required:</p>
                    <p className="font-mono">firstname.lastname@fcrit.ac.in</p>
                    <p className="mt-1">
                      Example:{' '}
                      <span className="font-mono">poonam.bari@fcrit.ac.in</span>
                    </p>
                  </div>
                </div>
                {/* ✅ Default password notice */}
                <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-700">
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    🔐 Default password{' '}
                    <code className="font-mono font-semibold bg-blue-100 dark:bg-blue-900/40 px-1 rounded">
                      Fcrit@123
                    </code>{' '}
                    will be set automatically. Faculty will be prompted to
                    change it on first login.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowRegisteredEmails(!showRegisteredEmails)}
                  className="mt-2 text-xs text-blue-600 dark:text-blue-400 underline"
                >
                  {showRegisteredEmails ? 'Hide' : 'Show'} registered faculty emails
                </button>
              </div>

              {/* ✅ Registered emails from MongoDB — not hardcoded */}
              <AnimatePresence>
                {showRegisteredEmails && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mx-6 mt-2 overflow-hidden"
                  >
                    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      {emailsLoading ? (
                        <p className="text-xs text-gray-500">
                          Loading registered emails...
                        </p>
                      ) : (
                        <>
                          <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 mb-2">
                            Registered faculty emails — click to use:
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {(registeredEmailsData?.emails ?? []).map((entry) => (
                              <button
                                key={entry.email}
                                type="button"
                                onClick={() => {
                                  handleFieldChange('email', entry.email);
                                  setShowRegisteredEmails(false);
                                }}
                                title={`${entry.name} — ${entry.department} (${entry.status})`}
                                className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs hover:bg-purple-200 dark:hover:bg-purple-800/50 transition-colors font-mono"
                              >
                                {entry.email}
                              </button>
                            ))}
                            {registeredEmailsData?.emails?.length === 0 && (
                              <p className="text-xs text-gray-500">
                                No faculty registered yet
                              </p>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Form */}
              <form onSubmit={handleSubmit} className="p-6 space-y-4">

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Faculty Email *
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => handleFieldChange('email', e.target.value)}
                      placeholder="firstname.lastname@fcrit.ac.in"
                      className={`w-full pl-9 pr-3 py-2.5 border rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 ${
                        formErrors.email
                          ? 'border-red-400 focus:ring-red-500'
                          : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                      }`}
                    />
                  </div>
                  {formErrors.email && (
                    <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                      {formErrors.email}
                    </p>
                  )}
                </div>

                {/* Name — auto-filled from email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Full Name *{' '}
                    <span className="text-gray-400 font-normal">
                      (auto-filled from email)
                    </span>
                  </label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => handleFieldChange('name', e.target.value)}
                    placeholder="Poonam Bari"
                    className={`w-full px-3 py-2.5 border rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 ${
                      formErrors.name
                        ? 'border-red-400 focus:ring-red-500'
                        : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                    }`}
                  />
                  {formErrors.name && (
                    <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                      {formErrors.name}
                    </p>
                  )}
                </div>

                {/* Department + Designation side by side */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Department */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Department *
                    </label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <select
                        value={form.department}
                        onChange={(e) =>
                          handleFieldChange('department', e.target.value)
                        }
                        className={`w-full pl-9 pr-3 py-2.5 border rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 appearance-none ${
                          formErrors.department
                            ? 'border-red-400 focus:ring-red-500'
                            : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                        }`}
                      >
                        <option value="">Select</option>
                        {DEPARTMENTS.map((d) => (
                          <option key={d} value={d}>{d}</option>
                        ))}
                      </select>
                    </div>
                    {formErrors.department && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                        {formErrors.department}
                      </p>
                    )}
                  </div>

                  {/* Designation */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Designation *
                    </label>
                    <div className="relative">
                      <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <select
                        value={form.designation}
                        onChange={(e) =>
                          handleFieldChange('designation', e.target.value)
                        }
                        className={`w-full pl-9 pr-3 py-2.5 border rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 appearance-none ${
                          formErrors.designation
                            ? 'border-red-400 focus:ring-red-500'
                            : 'border-gray-300 dark:border-gray-600 focus:ring-purple-500'
                        }`}
                      >
                        {DESIGNATIONS.map((d) => (
                          <option key={d} value={d}>{d}</option>
                        ))}
                      </select>
                    </div>
                    {formErrors.designation && (
                      <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                        {formErrors.designation}
                      </p>
                    )}
                  </div>
                </div>

                {/* Submit / Cancel */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => { setShowAddModal(false); resetForm(); }}
                    className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createFacultyMutation.isPending}
                    className="flex-1 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    {createFacultyMutation.isPending ? (
                      <>
                        <svg
                          className="animate-spin w-4 h-4"
                          viewBox="0 0 24 24"
                          fill="none"
                        >
                          <circle
                            className="opacity-25"
                            cx="12" cy="12" r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v8z"
                          />
                        </svg>
                        Creating...
                      </>
                    ) : (
                      <>
                        <UserPlus className="w-4 h-4" />
                        Create Account
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FacultyManagement;