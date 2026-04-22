// src/pages/Login.tsx
<<<<<<< HEAD
import React, { useState, useEffect } from 'react';
=======
import React, { useState, useMemo } from 'react';
>>>>>>> 0e99d011 (faculty email)
import { useNavigate, Link } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import {
<<<<<<< HEAD
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  AlertCircle,
  UserCheck,
  Users,
  Shield,
  Hash,
  Info,
=======
  Mail, Lock, Eye, EyeOff, Loader2,
  AlertCircle, UserCheck, Users, Shield,
>>>>>>> 0e99d011 (faculty email)
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { auth } from '../services/firebase.config';
import toast from 'react-hot-toast';

<<<<<<< HEAD
// ✅ Separate schemas for each user type
const studentLoginSchema = z.object({
  userType: z.literal('student'),
  roll_number: z.string().min(1, 'Roll number is required').length(7, 'Roll number must be 7 digits'),
  password: z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean(),
});

const facultyLoginSchema = z.object({
  userType: z.literal('faculty'),
  email: z.string().min(1, 'Email is required').email('Invalid email format'),
  password: z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean(),
});

const adminLoginSchema = z.object({
  userType: z.literal('admin'),
  email: z.string().min(1, 'Email is required').email('Invalid email format'),
  password: z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean(),
});

// ✅ Type definitions
type StudentLoginData = z.infer<typeof studentLoginSchema>;
type FacultyLoginData = z.infer<typeof facultyLoginSchema>;
type AdminLoginData = z.infer<typeof adminLoginSchema>;
type LoginFormData = StudentLoginData | FacultyLoginData | AdminLoginData;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
=======
// ✅ Import our new hook — no hardcoded emails
import { useFacultyEmails } from '../hooks/useFacultyEmails';

// ─── Constants ────────────────────────────────────────────────────────────────

const FACULTY_EMAIL_DOMAIN = '@fcrit.ac.in';

// ─── Validation helpers ───────────────────────────────────────────────────────

/**
 * Format validation only — no network call.
 * Must match: firstname.lastname@fcrit.ac.in (letters only)
 */
const isFacultyEmail = (email: string): boolean => {
  const lower = email.toLowerCase().trim();
  if (!lower.endsWith(FACULTY_EMAIL_DOMAIN)) return false;
  const local = lower.split('@')[0];
  return /^[a-z]+\.[a-z]+$/.test(local);
};

// ─── Zod schemas ──────────────────────────────────────────────────────────────

const baseSchema = z.object({
  email:      z.string().min(1, 'Email is required').email('Invalid email format'),
  password:   z.string().min(1, 'Password is required').min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean(),
});

// Faculty gets extra email format validation on top of base
const facultySchema = baseSchema.extend({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email format')
    .refine(
      (val) => val.toLowerCase().trim().endsWith(FACULTY_EMAIL_DOMAIN),
      { message: `Faculty email must end with ${FACULTY_EMAIL_DOMAIN}` }
    )
    .refine(
      (val) => isFacultyEmail(val),
      { message: 'Faculty email must be: firstname.lastname@fcrit.ac.in' }
    ),
});

type LoginFormData = z.infer<typeof baseSchema>;
type UserType = 'student' | 'faculty' | 'admin';

// ─── Component ────────────────────────────────────────────────────────────────

const Login: React.FC = () => {
  const navigate                      = useNavigate();
  const { login, resetPassword }      = useAuth();
  const [showPassword, setShowPassword]       = useState(false);
  const [isSubmitting, setIsSubmitting]       = useState(false);
>>>>>>> 0e99d011 (faculty email)
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [userType, setUserType]               = useState<UserType>('student');

  // ✅ Fetch faculty emails from MongoDB — replaces ALL hardcoded lists
  // This runs automatically and caches for 5 minutes
  const {
    data:      facultyEmailsData,
    isLoading: emailsLoading,
  } = useFacultyEmails();

  // Build a Set for O(1) lookup — recalculates only when data changes
  const approvedEmailSet = useMemo<Set<string>>(() => {
    if (!facultyEmailsData?.emails?.length) return new Set<string>();
    return new Set(
      facultyEmailsData.emails.map((e) => e.email.toLowerCase().trim())
    );
  }, [facultyEmailsData]);

  // ── Form setup ────────────────────────────────────────────────────────────

  const activeSchema = userType === 'faculty' ? facultySchema : baseSchema;

  // ✅ Dynamic schema based on userType
  const getSchema = () => {
    switch (userType) {
      case 'student':
        return studentLoginSchema;
      case 'faculty':
        return facultyLoginSchema;
      case 'admin':
        return adminLoginSchema;
    }
  };

  // ✅ Dynamic default values
  const getDefaultValues = (): any => {
    switch (userType) {
      case 'student':
        return { userType: 'student' as const, roll_number: '', password: '', rememberMe: false };
      case 'faculty':
        return { userType: 'faculty' as const, email: '', password: '', rememberMe: false };
      case 'admin':
        return { userType: 'admin' as const, email: '', password: '', rememberMe: false };
    }
  };

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    watch,
    reset,
<<<<<<< HEAD
  } = useForm<any>({
    resolver: zodResolver(getSchema()),
    defaultValues: getDefaultValues(),
=======
  } = useForm<LoginFormData>({
    resolver: zodResolver(activeSchema),
    defaultValues: { email: '', password: '', rememberMe: false },
>>>>>>> 0e99d011 (faculty email)
  });

  // ✅ Watch the correct field based on userType
  const emailValue = userType !== 'student' ? watch('email') : '';

<<<<<<< HEAD
  // ✅ Reset form when userType changes
  useEffect(() => {
    reset(getDefaultValues());
  }, [userType]);

  // ---------- Google Sign-In ----------
  const handleGoogleSignIn = async () => {
    if (userType === 'student') {
      toast.error('Google Sign-In is not available for students. Please use your roll number.');
=======
  // Reset form when switching tabs
  const handleTabChange = (type: UserType) => {
    setUserType(type);
    reset({ email: '', password: '', rememberMe: false });
  };

  // ── Helpers ───────────────────────────────────────────────────────────────

  const dashboardPathForRole = (role: string): string => {
    switch (role) {
      case 'faculty': return '/faculty/dashboard';
      case 'admin':   return '/admin/dashboard';
      default:        return '/student/dashboard';
    }
  };

  const roleLabel = (role: string): string => {
    switch (role) {
      case 'faculty': return 'Faculty';
      case 'admin':   return 'Admin';
      default:        return 'Student';
    }
  };

  const mismatchMessage = (actualRole: string): string =>
    `You are registered as ${roleLabel(actualRole)}. ` +
    `Please switch to the ${roleLabel(actualRole)} login tab.`;

  // ── Live email hint for faculty tab ──────────────────────────────────────
  // Shows color-coded feedback as the user types their email

  const getFacultyEmailHint = (): {
    type: 'error' | 'warning' | 'success' | null;
    message: string;
  } => {
    // Only show for faculty tab, only when something is typed
    if (!emailValue || userType !== 'faculty') {
      return { type: null, message: '' };
    }

    const lower = emailValue.toLowerCase().trim();

    // Check 1: Must end with @fcrit.ac.in
    if (!lower.endsWith(FACULTY_EMAIL_DOMAIN)) {
      return {
        type: 'error',
        message: `Faculty email must end with ${FACULTY_EMAIL_DOMAIN}`,
      };
    }

    // Check 2: Must match firstname.lastname format
    if (!isFacultyEmail(lower)) {
      return {
        type: 'error',
        message: 'Format: firstname.lastname@fcrit.ac.in (letters only)',
      };
    }

    // Check 3: Still loading DB emails — don't show anything yet
    if (emailsLoading) {
      return { type: null, message: '' };
    }

    // Check 4: Is this email registered in MongoDB?
    if (!approvedEmailSet.has(lower)) {
      return {
        type: 'warning',
        // ✅ Dynamic message — from DB, not hardcoded list
        message: '⚠ This email is not registered in the system',
      };
    }

    // All checks passed
    return { type: 'success', message: '✓ Registered faculty email' };
  };

  const emailHint = getFacultyEmailHint();

  // ── Google Sign-In ────────────────────────────────────────────────────────

  const handleGoogleSignIn = async () => {
    // Faculty cannot use Google Sign-In
    if (userType === 'faculty') {
      toast.error(
        'Faculty must sign in with their institutional email and password.'
      );
>>>>>>> 0e99d011 (faculty email)
      return;
    }

    setIsGoogleLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });

      const result = await signInWithPopup(auth, provider);
<<<<<<< HEAD
      // Navigation handled by AuthContext
      toast.success('Google sign-in successful!');
=======
      const user   = result.user;

      // Block @fcrit.ac.in emails from Google sign-in
      if (user.email?.endsWith(FACULTY_EMAIL_DOMAIN)) {
        toast.error(
          'Faculty must use the Faculty tab and sign in with email & password.'
        );
        await auth.signOut();
        return;
      }

      const userDoc = await getDoc(doc(db, 'users', user.uid));
      if (userDoc.exists()) {
        const userData = userDoc.data();
        const userRole = userData.role || 'student';

        if (userRole !== userType) {
          toast.error(mismatchMessage(userRole));
          await auth.signOut();
          return;
        }

        toast.success('Login successful!');
        navigate(dashboardPathForRole(userRole));
      } else {
        toast.error('No account found. Please register first.');
        await auth.signOut();
        navigate('/register', {
          state: {
            googleData: {
              email:       user.email,
              displayName: user.displayName,
              photoURL:    user.photoURL,
            },
          },
        });
      }
>>>>>>> 0e99d011 (faculty email)
    } catch (error: any) {
      if (error.code === 'auth/popup-closed-by-user') {
        toast.error('Sign-in cancelled');
      } else if (error.code === 'auth/popup-blocked') {
        toast.error('Popup blocked. Please allow popups for this site.');
      } else {
        toast.error('Google sign-in failed. Please try again.');
      }
    } finally {
      setIsGoogleLoading(false);
    }
  };

<<<<<<< HEAD
  // ---------- Form Submit ----------
  const onSubmit: SubmitHandler<any> = async (data) => {
    setIsSubmitting(true);
    try {
      if (userType === 'student') {
        // ✅ Student login with roll_number
        const studentData = data as StudentLoginData;
        await login({
          roll_number: studentData.roll_number,
          password: studentData.password,
          rememberMe: studentData.rememberMe ?? false,
          userType: 'student',
        });
      } else {
        // ✅ Faculty/Admin login with email
        const emailData = data as FacultyLoginData | AdminLoginData;
        await login({
          email: emailData.email,
          password: emailData.password,
          rememberMe: emailData.rememberMe ?? false,
          userType,
        });
=======
  // ── Email/Password Sign-In ────────────────────────────────────────────────

  const onSubmit: SubmitHandler<LoginFormData> = async (data) => {
    // Extra guard before hitting Firebase
    if (userType === 'faculty' && !isFacultyEmail(data.email)) {
      setError('email', {
        message: 'Faculty email must be: firstname.lastname@fcrit.ac.in',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        email:      data.email,
        password:   data.password,
        rememberMe: data.rememberMe ?? false,
        userType,
      });

      const user = auth.currentUser;
      if (user) {
        const userDoc = await getDoc(doc(db, 'users', user.uid));
        if (userDoc.exists()) {
          const userData = userDoc.data();
          const userRole = userData.role || 'student';

          if (userRole !== userType) {
            setError('root', { message: mismatchMessage(userRole) });
            await auth.signOut();
            return;
          }

          toast.success('Login successful!');
          navigate(dashboardPathForRole(userRole), { replace: true });
        }
>>>>>>> 0e99d011 (faculty email)
      }
    } catch (error: any) {
      console.error('Login error:', error);

      // Handle specific errors
      if (error.message?.includes('Student not found')) {
        setError('roll_number', { message: 'Student not found with this roll number' });
      } else if (error.message?.includes('Invalid roll number or password')) {
        setError('password', { message: 'Invalid credentials. Check your roll number and password.' });
      } else if (error.message?.includes('Incorrect password')) {
        setError('password', { message: 'Incorrect password' });
      } else if (error.message?.includes('Invalid email')) {
        if (userType !== 'student') {
          setError('email', { message: 'Invalid email format' });
        }
      } else if (error.message?.includes('switch to the')) {
        setError('root', { message: error.message });
      } else if (error.code === 'auth/too-many-requests') {
        setError('root', {
          message: 'Too many failed attempts. Please try again later or reset your password.',
        });
      } else {
        setError('root', {
          message: error.message || 'Login failed. Please try again.',
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

<<<<<<< HEAD
  // ---------- Forgot Password ----------
  const handleForgotPassword = () => {
    if (userType === 'student') {
      toast('Contact admin for password reset', {
        icon: 'ℹ️',
        duration: 3000,
        style: {
          borderRadius: '10px',
          background: '#3b82f6',
          color: '#fff',
        },
      });
    } else {
      if (!emailValue) {
        setError('email', { message: 'Please enter your email first' });
        return;
=======
  // ── Forgot Password ───────────────────────────────────────────────────────

  const handleForgotPassword = async () => {
    if (!emailValue) {
      setError('email', { message: 'Please enter your email first' });
      return;
    }
    try {
      await resetPassword(emailValue);
      toast.success('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      if (error.code === 'auth/user-not-found') {
        setError('email', { message: 'No account found with this email' });
      } else {
        toast.error('Failed to send reset email. Please try again.');
>>>>>>> 0e99d011 (faculty email)
      }
      // Navigate to password reset or trigger email
      toast.success('Password reset email sent! Check your inbox.');
    }
  };

<<<<<<< HEAD
  // ---------- Dynamic styles ----------
  const accentClasses: Record<typeof userType, { btn: string; ring: string }> = {
=======
  // ── Styles ────────────────────────────────────────────────────────────────

  const accentClasses: Record<UserType, { btn: string; ring: string }> = {
>>>>>>> 0e99d011 (faculty email)
    student: {
      btn:  'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
      ring: 'focus:ring-blue-500 focus:border-blue-500',
    },
    faculty: {
      btn:  'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500',
      ring: 'focus:ring-purple-500 focus:border-purple-500',
    },
    admin: {
      btn:  'bg-red-600 hover:bg-red-700 focus:ring-red-500',
      ring: 'focus:ring-red-500 focus:border-red-500',
    },
  };

<<<<<<< HEAD
  const placeholders: Record<typeof userType, string> = {
    student: '5023152',
    faculty: 'professor@university.edu',
    admin: 'admin@university.edu',
  };

=======
  const placeholders: Record<UserType, string> = {
    student: 'student@university.edu',
    faculty: 'firstname.lastname@fcrit.ac.in',
    admin:   'admin@university.edu',
  };

  // ── Render ────────────────────────────────────────────────────────────────

>>>>>>> 0e99d011 (faculty email)
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full space-y-8"
      >
<<<<<<< HEAD
        {/* Title */}
=======
        {/* ── Title ── */}
>>>>>>> 0e99d011 (faculty email)
        <div className="text-center">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-6 text-3xl font-extrabold text-gray-900"
          >
            Smart Academic Advisor
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-2 text-sm text-gray-600"
          >
            Sign in to access your personalized academic dashboard
          </motion.p>
        </div>

<<<<<<< HEAD
        {/* Role Tabs */}
=======
        {/* ── Role Tabs ── */}
>>>>>>> 0e99d011 (faculty email)
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="flex space-x-3"
        >
          {(['student', 'faculty', 'admin'] as const).map((type) => {
            const icons = {
              student: <Users className="h-5 w-5" />,
              faculty: <UserCheck className="h-5 w-5" />,
              admin:   <Shield className="h-5 w-5" />,
            };
            const activeColors: Record<UserType, string> = {
              student: 'bg-blue-600 text-white shadow-lg transform scale-105',
              faculty: 'bg-purple-600 text-white shadow-lg transform scale-105',
              admin:   'bg-red-600 text-white shadow-lg transform scale-105',
            };
            return (
              <button
                key={type}
                type="button"
                onClick={() => handleTabChange(type)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all duration-200 flex items-center justify-center space-x-2 ${
                  userType === type ? activeColors[type] : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {icons[type]}
                <span className="capitalize">{type}</span>
              </button>
            );
          })}
        </motion.div>

<<<<<<< HEAD
        {/* Form */}
=======
        {/* ── Faculty info box — shown only on faculty tab ── */}
        <AnimatePresence>
          {userType === 'faculty' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-3 text-sm text-purple-700"
            >
              <p className="font-medium mb-1">Faculty Login</p>
              <p className="text-xs text-purple-600">
                Use your institutional email:{' '}
                <span className="font-mono font-semibold">
                  firstname.lastname@fcrit.ac.in
                </span>
              </p>
              <p className="text-xs text-purple-500 mt-1">
                Example: poonam.bari@fcrit.ac.in
              </p>
              {/* ✅ Default password reminder for first-time faculty login */}
              <div className="mt-2 pt-2 border-t border-purple-200">
                <p className="text-xs text-purple-600">
                  🔐 First time logging in? Your default password is{' '}
                  <code className="font-mono font-semibold bg-purple-100 px-1 py-0.5 rounded">
                    Fcrit@123
                  </code>
                  . You will be asked to change it after login.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Form card ── */}
>>>>>>> 0e99d011 (faculty email)
        <motion.form
          key={userType}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-xl"
          onSubmit={handleSubmit(onSubmit)}
          noValidate
        >
<<<<<<< HEAD
          {/* Root Error */}
=======
          {/* Root error banner */}
>>>>>>> 0e99d011 (faculty email)
          <AnimatePresence>
            {errors.root && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`border px-4 py-3 rounded-lg flex items-start ${
                  errors.root.message?.includes('switch')
                    ? 'bg-yellow-50 border-yellow-200 text-yellow-700'
                    : 'bg-red-50 border-red-200 text-red-700'
                }`}
              >
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
                <span className="text-sm">{errors.root.message}</span>
              </motion.div>
            )}
          </AnimatePresence>

<<<<<<< HEAD
          <div className="space-y-6">
            {/* Student Form - Roll Number */}
            {userType === 'student' && (
              <>
                <div>
                  <label htmlFor="roll_number" className="block text-sm font-medium text-gray-700 mb-1">
                    Roll Number
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Hash className={`h-5 w-5 ${errors.roll_number ? 'text-red-500' : 'text-gray-400'}`} />
                    </div>
                    <input
                      {...register('roll_number')}
                      type="text"
                      autoComplete="username"
                      className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                        errors.roll_number
                          ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                          : `border-gray-300 ${accentClasses[userType].ring}`
                      }`}
                      placeholder={placeholders[userType]}
                      maxLength={7}
                    />
                  </div>
                  {errors.roll_number && (
                    <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-1 text-sm text-red-600">
                      {errors.roll_number.message as string}
                    </motion.p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">Enter your 7-digit roll number</p>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-blue-700">
                      <p className="font-medium mb-1">First time logging in?</p>
                      <p>
                        Your default password is: <code className="bg-blue-100 px-1 rounded">RollNumber@AdmissionYear</code>
                      </p>
                      <p className="mt-1">
                        Example: <code className="bg-blue-100 px-1 rounded">5023152@2023</code>
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Faculty/Admin Form - Email */}
            {(userType === 'faculty' || userType === 'admin') && (
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className={`h-5 w-5 ${errors.email ? 'text-red-500' : 'text-gray-400'}`} />
                  </div>
                  <input
                    {...register('email')}
                    type="email"
                    autoComplete="email"
                    className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                      errors.email
                        ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                        : `border-gray-300 ${accentClasses[userType].ring}`
=======
          <div className="space-y-4">
            {/* ── Email field ── */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email Address
                {userType === 'faculty' && (
                  <span className="ml-2 text-xs text-purple-500 font-normal">
                    (firstname.lastname@fcrit.ac.in)
                  </span>
                )}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail
                    className={`h-5 w-5 ${
                      errors.email ? 'text-red-500' : 'text-gray-400'
>>>>>>> 0e99d011 (faculty email)
                    }`}
                    placeholder={placeholders[userType]}
                  />
                </div>
<<<<<<< HEAD
                {errors.email && (
                  <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-1 text-sm text-red-600">
                    {errors.email.message as string}
                  </motion.p>
                )}
              </div>
            )}

            {/* Password - Common for all */}
=======
                <input
                  {...register('email')}
                  id="email"
                  type="email"
                  autoComplete="email"
                  className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                    errors.email
                      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                      : `border-gray-300 ${accentClasses[userType].ring}`
                  }`}
                  placeholder={placeholders[userType]}
                />
              </div>

              {/* Zod validation error */}
              {errors.email && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-1 text-sm text-red-600"
                >
                  {errors.email.message}
                </motion.p>
              )}

              {/* Live hint — only shown when no zod error and on faculty tab */}
              {!errors.email && emailHint.type && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`mt-1 text-xs ${
                    emailHint.type === 'success' ? 'text-green-600'
                    : emailHint.type === 'warning' ? 'text-yellow-600'
                    : 'text-red-600'
                  }`}
                >
                  {emailHint.message}
                </motion.p>
              )}
            </div>

            {/* ── Password field ── */}
>>>>>>> 0e99d011 (faculty email)
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className={`h-5 w-5 ${errors.password ? 'text-red-500' : 'text-gray-400'}`} />
                </div>
                <input
                  {...register('password')}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className={`block w-full pl-10 pr-10 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
                    errors.password
                      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                      : `border-gray-300 ${accentClasses[userType].ring}`
                  }`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword
                    ? <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    : <Eye   className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  }
                </button>
              </div>
              {errors.password && (
                <motion.p initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mt-1 text-sm text-red-600">
                  {errors.password.message as string}
                </motion.p>
              )}
            </div>

<<<<<<< HEAD
            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  {...register('rememberMe')}
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  Remember me
                </label>
              </div>

              <button type="button" onClick={handleForgotPassword} className="text-sm text-blue-600 hover:text-blue-500 font-medium">
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
=======
          {/* ── Remember me + Forgot password ── */}
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                {...register('rememberMe')}
                id="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label
                htmlFor="remember-me"
                className="ml-2 block text-sm text-gray-700"
              >
                Remember me
              </label>
            </div>
>>>>>>> 0e99d011 (faculty email)
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                isSubmitting ? 'bg-gray-400 cursor-not-allowed' : accentClasses[userType].btn
              }`}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin h-5 w-5 mr-2" />
                  Signing in...
                </>
              ) : (
                `Sign in as ${userType.charAt(0).toUpperCase() + userType.slice(1)}`
              )}
            </button>

<<<<<<< HEAD
            {/* Google Sign In - Only for Faculty/Admin */}
            {(userType === 'faculty' || userType === 'admin') && (
=======
          {/* ── Submit button ── */}
          <button
            type="submit"
            disabled={isSubmitting}
            className={`w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              isSubmitting
                ? 'bg-gray-400 cursor-not-allowed'
                : accentClasses[userType].btn
            }`}
          >
            {isSubmitting ? (
>>>>>>> 0e99d011 (faculty email)
              <>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or continue with</span>
                  </div>
                </div>

<<<<<<< HEAD
                <button
                  type="button"
                  onClick={handleGoogleSignIn}
                  disabled={isGoogleLoading}
                  className={`w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 ${
                    isGoogleLoading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {isGoogleLoading ? (
                    <>
                      <Loader2 className="animate-spin h-5 w-5 mr-2" />
                      Signing in with Google...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                        <path
                          fill="#4285F4"
                          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        />
                        <path
                          fill="#34A853"
                          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        />
                        <path
                          fill="#FBBC05"
                          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                        />
                        <path
                          fill="#EA4335"
                          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        />
                      </svg>
                      Sign in with Google
                    </>
                  )}
                </button>

                {/* Register Link */}
                <div className="text-center">
                  <span className="text-sm text-gray-600">
                    Don&apos;t have an account?{' '}
                    <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
                      Sign up
                    </Link>
                  </span>
                </div>
              </>
            )}

            {/* Student - Contact Admin */}
            {userType === 'student' && (
              <div className="text-center text-xs text-gray-500">
                <p>🔒 Contact admin if you can't access your account</p>
              </div>
            )}
=======
          {/* ── Google Sign-In — students & admins only ── */}
          {userType !== 'faculty' && (
            <>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">
                    Or continue with
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={isGoogleLoading}
                className={`w-full flex justify-center items-center py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 ${
                  isGoogleLoading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isGoogleLoading ? (
                  <>
                    <Loader2 className="animate-spin h-5 w-5 mr-2" />
                    Signing in with Google...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                  </>
                )}
              </button>
            </>
          )}

          {/* ── Register link ── */}
          <div className="text-center">
            <span className="text-sm text-gray-600">
              Don&apos;t have an account?{' '}
              <Link
                to="/register"
                className="font-medium text-blue-600 hover:text-blue-500"
              >
                Sign up
              </Link>
            </span>
>>>>>>> 0e99d011 (faculty email)
          </div>
        </motion.form>
      </motion.div>
    </div>
  );
};

export default Login;