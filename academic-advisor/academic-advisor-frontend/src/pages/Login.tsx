// src/pages/Login.tsx
import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mail, Lock, Eye, EyeOff, Loader2, Hash,
  AlertCircle, UserCheck, Users, Shield,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { doc, getDoc } from 'firebase/firestore';
import { db, auth } from '../services/firebase.config';
import { GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import toast from 'react-hot-toast';
import { useFacultyEmails } from '../hooks/useFacultyEmails';

// ─── Constants ────────────────────────────────────────────────────────────────

const FACULTY_EMAIL_DOMAIN = '@fcrit.ac.in';

const isFacultyEmail = (email: string): boolean => {
  const lower = email.toLowerCase().trim();
  if (!lower.endsWith(FACULTY_EMAIL_DOMAIN)) return false;
  return /^[a-z]+\.[a-z]+$/.test(lower.split('@')[0]);
};

// ─── Schemas ──────────────────────────────────────────────────────────────────

const studentSchema = z.object({
  identifier: z
    .string()
    .min(1, 'Roll number is required')
    .regex(/^[0-9]{5,7}$/, 'Roll number must be 5-7 digits'),
  password: z.string().min(1, 'Password is required').min(8, 'Min 8 characters'),
  rememberMe: z.boolean().optional().default(false),
});

const facultySchema = z.object({
  identifier: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email format')
    .refine((v) => v.toLowerCase().trim().endsWith(FACULTY_EMAIL_DOMAIN), {
      message: `Must end with ${FACULTY_EMAIL_DOMAIN}`,
    })
    .refine((v) => isFacultyEmail(v), {
      message: 'Format: firstname.lastname@fcrit.ac.in',
    }),
  password: z.string().min(1, 'Password is required').min(8, 'Min 8 characters'),
  rememberMe: z.boolean().optional().default(false),
});

const adminSchema = z.object({
  identifier: z.string().min(1, 'Email is required').email('Invalid email format'),
  password: z.string().min(1, 'Password is required').min(8, 'Min 8 characters'),
  rememberMe: z.boolean().optional().default(false),
});

type UserType = 'student' | 'faculty' | 'admin';
type LoginFormData = { identifier: string; password: string; rememberMe: boolean };

const getSchema = (type: UserType) => {
  if (type === 'student') return studentSchema;
  if (type === 'faculty') return facultySchema;
  return adminSchema;
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const accentClasses: Record<UserType, { btn: string; ring: string; active: string }> = {
  student: {
    btn:    'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
    ring:   'focus:ring-blue-500 focus:border-blue-500',
    active: 'bg-blue-600 text-white shadow-lg scale-105',
  },
  faculty: {
    btn:    'bg-purple-600 hover:bg-purple-700 focus:ring-purple-500',
    ring:   'focus:ring-purple-500 focus:border-purple-500',
    active: 'bg-purple-600 text-white shadow-lg scale-105',
  },
  admin: {
    btn:    'bg-red-600 hover:bg-red-700 focus:ring-red-500',
    ring:   'focus:ring-red-500 focus:border-red-500',
    active: 'bg-red-600 text-white shadow-lg scale-105',
  },
};

const placeholders: Record<UserType, string> = {
  student: '5023152',
  faculty: 'firstname.lastname@fcrit.ac.in',
  admin:   'admin@fcrit.ac.in',
};

const inputLabels: Record<UserType, string> = {
  student: 'Roll Number',
  faculty: 'Email Address',
  admin:   'Email Address',
};

const roleLabel = (r: string) =>
  r === 'faculty' ? 'Faculty' : r === 'admin' ? 'Admin' : 'Student';

// ─── Inner form component (remounts on userType change via key) ───────────────

interface LoginFormProps {
  userType: UserType;
  onSubmit: (data: LoginFormData) => Promise<void>;
  isSubmitting: boolean;
  onForgotPassword: (identifier: string) => void;
}

const LoginFormInner: React.FC<LoginFormProps> = ({
  userType,
  onSubmit,
  isSubmitting,
  onForgotPassword,
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<LoginFormData>({
    // ✅ Schema is fixed per instance — no dynamic switching needed
    resolver: zodResolver(getSchema(userType)),
    defaultValues: { identifier: '', password: '', rememberMe: false },
  });

  const identifierValue = watch('identifier');
  const { data: facultyEmailsData, isLoading: emailsLoading } = useFacultyEmails();

  const approvedEmailSet = useMemo<Set<string>>(() => {
    if (!facultyEmailsData?.emails?.length) return new Set();
    return new Set(facultyEmailsData.emails.map((e: any) => e.email.toLowerCase().trim()));
  }, [facultyEmailsData]);

  const emailHint = useMemo(() => {
    if (!identifierValue || userType !== 'faculty') return { type: null, message: '' };
    const lower = identifierValue.toLowerCase().trim();
    if (!lower.endsWith(FACULTY_EMAIL_DOMAIN))
      return { type: 'error' as const, message: `Must end with ${FACULTY_EMAIL_DOMAIN}` };
    if (!isFacultyEmail(lower))
      return { type: 'error' as const, message: 'Format: firstname.lastname@fcrit.ac.in' };
    if (emailsLoading) return { type: null, message: '' };
    if (!approvedEmailSet.has(lower))
      return { type: 'warning' as const, message: '⚠ Email not registered in system' };
    return { type: 'success' as const, message: '✓ Registered faculty email' };
  }, [identifierValue, userType, emailsLoading, approvedEmailSet]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {/* Root error */}
      <AnimatePresence>
        {errors.root && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start"
          >
            <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" />
            <span className="text-sm">{errors.root.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Identifier */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {inputLabels[userType]}
          {userType === 'faculty' && (
            <span className="ml-2 text-xs text-purple-400 font-normal">
              (firstname.lastname@fcrit.ac.in)
            </span>
          )}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            {userType === 'student'
              ? <Hash className={`h-5 w-5 ${errors.identifier ? 'text-red-500' : 'text-gray-400'}`} />
              : <Mail className={`h-5 w-5 ${errors.identifier ? 'text-red-500' : 'text-gray-400'}`} />
            }
          </div>
          <input
            {...register('identifier')}
            type={userType === 'student' ? 'text' : 'email'}
            autoComplete={userType === 'student' ? 'username' : 'email'}
            inputMode={userType === 'student' ? 'numeric' : 'email'}
            placeholder={placeholders[userType]}
            className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
              errors.identifier
                ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                : `border-gray-300 ${accentClasses[userType].ring}`
            }`}
          />
        </div>
        {errors.identifier && (
          <p className="mt-1 text-sm text-red-600">{errors.identifier.message}</p>
        )}
        {!errors.identifier && emailHint.type && (
          <p className={`mt-1 text-xs ${
            emailHint.type === 'success' ? 'text-green-600'
            : emailHint.type === 'warning' ? 'text-yellow-600'
            : 'text-red-600'
          }`}>
            {emailHint.message}
          </p>
        )}
      </div>

      {/* Password */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Lock className={`h-5 w-5 ${errors.password ? 'text-red-500' : 'text-gray-400'}`} />
          </div>
          <input
            {...register('password')}
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            placeholder="••••••••"
            className={`block w-full pl-10 pr-10 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
              errors.password
                ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                : `border-gray-300 ${accentClasses[userType].ring}`
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            {showPassword
              ? <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              : <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            }
          </button>
        </div>
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* Remember me + Forgot password */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            {...register('rememberMe')}
            type="checkbox"
            className="h-4 w-4 text-blue-600 border-gray-300 rounded"
          />
          <span className="text-sm text-gray-700">Remember me</span>
        </label>
        <button
          type="button"
          onClick={() => onForgotPassword(identifierValue)}
          className="text-sm text-blue-600 hover:text-blue-500 font-medium"
        >
          Forgot password?
        </button>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full flex justify-center items-center py-3 px-4 rounded-lg text-sm font-medium text-white transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ${
          isSubmitting ? 'bg-gray-400 cursor-not-allowed' : accentClasses[userType].btn
        }`}
      >
        {isSubmitting
          ? <><Loader2 className="animate-spin h-5 w-5 mr-2" />Signing in...</>
          : `Sign in as ${roleLabel(userType)}`
        }
      </button>

      {/* Register link */}
      <p className="text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
          Sign up
        </Link>
      </p>
    </form>
  );
};

// ─── Main Login page ──────────────────────────────────────────────────────────

const Login: React.FC = () => {
  const { login, resetPassword } = useAuth();
  const [userType, setUserType]   = useState<UserType>('student');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotRoll, setForgotRoll] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [resetResult, setResetResult] = useState<{ success: boolean; password?: string } | null>(null);

  const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

  const handleTabChange = (type: UserType) => setUserType(type);

  const handleSubmit = async (data: LoginFormData) => {
    if (userType === 'faculty' && !isFacultyEmail(data.identifier)) return;

    setIsSubmitting(true);
    try {
      const credentials: any = {
        password:   data.password,
        rememberMe: data.rememberMe ?? false,
        userType,
        ...(userType === 'student'
          ? { roll_number: data.identifier }
          : { email: data.identifier }),
      };

      await login(credentials);
    } catch (error: any) {
      console.error('Login error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async (identifier: string) => {
    if (userType === 'student') {
      setForgotRoll(identifier || '');
      setForgotEmail('');
      setResetResult(null);
      setShowForgotModal(true);
      return;
    }
    // Faculty: use Firebase sendPasswordResetEmail
    if (!identifier) {
      toast.error('Please enter your email first.');
      return;
    }
    try {
      await resetPassword(identifier);
      toast.success('Password reset email sent! Check your inbox.');
    } catch {
      toast.error('Failed to send reset email.');
    }
  };

  const handleStudentForgotSubmit = async () => {
    if (!forgotRoll || forgotRoll.length !== 7) {
      toast.error('Enter a valid 7-digit roll number.');
      return;
    }
    if (!forgotEmail || !forgotEmail.includes('@')) {
      toast.error('Enter a valid email address.');
      return;
    }
    setForgotLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/student/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roll_number: forgotRoll, email: forgotEmail }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResetResult({ success: true, password: data.default_password });
        toast.success('Password has been reset!');
      } else {
        toast.error(data.detail || 'Failed to reset password.');
        setResetResult({ success: false });
      }
    } catch {
      toast.error('Server error. Try again later.');
    } finally {
      setForgotLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    if (userType === 'faculty') {
      toast.error('Faculty must use email & password login.');
      return;
    }
    try {
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });
      const result = await signInWithPopup(auth, provider);
      const fbUser = result.user;

      if (fbUser.email?.endsWith(FACULTY_EMAIL_DOMAIN)) {
        toast.error('Faculty must use the Faculty tab.');
        await auth.signOut();
        return;
      }

      const snap = await getDoc(doc(db, 'users', fbUser.uid));
      if (snap.exists()) {
        const userData = snap.data();
        await login({
          email:      fbUser.email || '',
          password:   '',
          userType:   userData.role || 'student',
          rememberMe: false,
        });
      } else {
        toast.error('No account found. Please register first.');
        await auth.signOut();
      }
    } catch (error: any) {
      if (error.code !== 'auth/popup-closed-by-user') {
        toast.error('Google sign-in failed.');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-6"
      >
        {/* Header */}
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900">Smart Academic Advisor</h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to access your personalized academic dashboard
          </p>
        </div>

        {/* Role Tabs */}
        <div className="flex space-x-3">
          {(['student', 'faculty', 'admin'] as const).map((type) => {
            const icons = {
              student: <Users className="h-5 w-5" />,
              faculty: <UserCheck className="h-5 w-5" />,
              admin:   <Shield className="h-5 w-5" />,
            };
            return (
              <button
                key={type}
                type="button"
                onClick={() => handleTabChange(type)}
                disabled={isSubmitting}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                  userType === type
                    ? accentClasses[type].active
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {icons[type]}
                <span className="capitalize">{type}</span>
              </button>
            );
          })}
        </div>

        {/* Info boxes */}
        <AnimatePresence mode="wait">
          {userType === 'student' && (
            <motion.div
              key="student-info"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700"
            >
              <p className="font-medium">Student Login</p>
              <p className="text-xs mt-1">Enter your 7-digit roll number (e.g., 5023152)</p>
              <p className="text-xs mt-1">
                Default password:{' '}
                <code className="bg-blue-100 px-1 rounded">RollNo@AdmissionYear</code>
                {' '}e.g. 5023152@2022
              </p>
            </motion.div>
          )}

          {userType === 'faculty' && (
            <motion.div
              key="faculty-info"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-3 text-sm text-purple-700"
            >
              <p className="font-medium">Faculty Login</p>
              <p className="text-xs mt-1">
                Use: <code className="bg-purple-100 px-1 rounded">firstname.lastname@fcrit.ac.in</code>
              </p>
              <p className="text-xs mt-1">
                Default password: <code className="bg-purple-100 px-1 rounded">Fcrit@123</code>
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Form Card */}
        <div className="bg-white p-8 rounded-xl shadow-xl">
          {/*
            ✅ KEY PROP — forces complete remount when userType changes.
            This is the CORRECT way to switch Zod schemas in react-hook-form.
            No need to mutate form._resolver.
          */}
          <LoginFormInner
            key={userType}
            userType={userType}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            onForgotPassword={handleForgotPassword}
          />
        </div>

        {/* Security notice */}
        <p className="text-center text-xs text-gray-500">
          🔒 Your data is encrypted and secure
        </p>
      </motion.div>

      {/* ✅ Student Forgot Password Modal */}
      <AnimatePresence>
        {showForgotModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowForgotModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl"
            >
              <h3 className="text-xl font-bold text-gray-900 mb-1">🔐 Reset Password</h3>
              <p className="text-sm text-gray-500 mb-5">
                Verify your identity to reset your password to the default.
              </p>

              {resetResult?.success ? (
                <div className="space-y-4">
                  <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                    <p className="text-sm font-medium text-green-800 mb-2">✅ Password reset successful!</p>
                    <p className="text-sm text-green-700">
                      Your new password is:{' '}
                      <code className="bg-green-100 px-2 py-0.5 rounded font-mono font-bold">
                        {resetResult.password}
                      </code>
                    </p>
                    <p className="text-xs text-green-600 mt-2">
                      Please login and change it immediately.
                    </p>
                  </div>
                  <button
                    onClick={() => setShowForgotModal(false)}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Back to Login
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Roll Number</label>
                    <div className="relative">
                      <Hash className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        value={forgotRoll}
                        onChange={(e) => setForgotRoll(e.target.value)}
                        placeholder="e.g. 5023152"
                        maxLength={7}
                        inputMode="numeric"
                        className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Registered Email</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="email"
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        placeholder="your.email@example.com"
                        className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                      />
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      Must match the email registered with your roll number.
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowForgotModal(false)}
                      className="flex-1 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleStudentForgotSubmit}
                      disabled={forgotLoading}
                      className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                    >
                      {forgotLoading ? (
                        <><Loader2 className="w-4 h-4 animate-spin" /> Verifying...</>
                      ) : (
                        'Reset Password'
                      )}
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Login;