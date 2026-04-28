// src/components/auth/LoginForm.tsx
// Apply the same key-based remount pattern

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mail, Lock, Eye, EyeOff, Loader2,
  AlertCircle, GraduationCap, UserCircle2, Shield, Hash,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

// ─── Schemas (same as Login.tsx) ──────────────────────────────────────────────

const studentSchema = z.object({
  identifier: z
    .string()
    .min(1, 'Roll number is required')
    .regex(/^[0-9]{7}$/, 'Roll number must be exactly 7 digits'),
  password: z.string().min(1, 'Password is required').min(8, 'Min 8 characters'),
  rememberMe: z.boolean().optional().default(false),
});

const facultySchema = z.object({
  identifier: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email format'),
  password: z.string().min(1, 'Password is required').min(8, 'Min 8 characters'),
  rememberMe: z.boolean().optional().default(false),
});

type UserType = 'student' | 'faculty';
type LoginFormData = { identifier: string; password: string; rememberMe: boolean };

// ─── Inner form (schema is fixed per instance) ────────────────────────────────

interface InnerFormProps {
  userType: UserType;
  onSubmit: (data: LoginFormData) => Promise<void>;
  isSubmitting: boolean;
  onForgotPassword: (identifier: string) => void;
  authError: string;
}

const InnerForm: React.FC<InnerFormProps> = ({
  userType, onSubmit, isSubmitting, onForgotPassword, authError
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<LoginFormData>({
    resolver: zodResolver(userType === 'student' ? studentSchema : facultySchema),
    defaultValues: { identifier: '', password: '', rememberMe: false },
  });

  const identifierValue = watch('identifier');

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      {/* Error display */}
      <AnimatePresence>
        {(errors.root || authError) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start"
          >
            <AlertCircle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
            <span className="text-sm">{errors.root?.message || authError}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Identifier */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {userType === 'student' ? 'Roll Number' : 'Email Address'}
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
            inputMode={userType === 'student' ? 'numeric' : 'email'}
            autoComplete={userType === 'student' ? 'username' : 'email'}
            placeholder={userType === 'student' ? '5023152' : 'your.email@university.edu'}
            className={`block w-full pl-10 pr-3 py-3 border rounded-lg focus:outline-none focus:ring-2 transition-colors ${
              errors.identifier
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
            }`}
          />
        </div>
        {errors.identifier && (
          <p className="mt-1 text-sm text-red-600">{errors.identifier.message}</p>
        )}
      </div>

      {/* Password */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
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
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 focus:ring-blue-500'
            }`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            {showPassword
              ? <EyeOff className="h-5 w-5 text-gray-400" />
              : <Eye className="h-5 w-5 text-gray-400" />
            }
          </button>
        </div>
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* Remember + Forgot */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input {...register('rememberMe')} type="checkbox"
            className="h-4 w-4 text-blue-600 border-gray-300 rounded" />
          <span className="text-sm text-gray-700">Remember me</span>
        </label>
        <button type="button" onClick={() => onForgotPassword(identifierValue)}
          className="text-sm text-blue-600 hover:text-blue-500 font-medium">
          Forgot password?
        </button>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={`w-full flex justify-center items-center py-3 px-4 rounded-lg text-sm font-medium text-white transition-all ${
          isSubmitting
            ? 'bg-gray-400 cursor-not-allowed'
            : userType === 'student'
            ? 'bg-blue-600 hover:bg-blue-700'
            : 'bg-purple-600 hover:bg-purple-700'
        }`}
      >
        {isSubmitting
          ? <><Loader2 className="animate-spin h-5 w-5 mr-2" />Signing in...</>
          : `Sign in as ${userType === 'student' ? 'Student' : 'Faculty'}`
        }
      </button>

      <p className="text-center text-sm text-gray-600">
        Don't have an account?{' '}
        <Link to="/register" className="text-blue-600 hover:text-blue-500 font-medium">
          Sign up
        </Link>
      </p>
    </form>
  );
};

// ─── Exported component ───────────────────────────────────────────────────────

export const LoginForm: React.FC = () => {
  const { login, resetPassword } = useAuth();
  const [userType, setUserType]   = useState<UserType>('student');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState('');

  const handleSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true);
    setAuthError('');
    try {
      await login({
        password:   data.password,
        rememberMe: data.rememberMe,
        userType,
        ...(userType === 'student'
          ? { roll_number: data.identifier }
          : { email: data.identifier }),
      });
    } catch (error: any) {
      const msg =
        error.response?.data?.detail ||
        error.message ||
        'Login failed. Please try again.';
      setAuthError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotPassword = async (identifier: string) => {
    if (userType === 'student') {
      setAuthError('Contact your administrator to reset your password.');
      return;
    }
    if (!identifier) { setAuthError('Please enter your email first.'); return; }
    try {
      await resetPassword(identifier);
      setAuthError('');
    } catch { setAuthError('Failed to send reset email.'); }
  };

  const handleTabChange = (type: UserType) => {
    setUserType(type);
    setAuthError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 px-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8">

        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-20 w-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
            <GraduationCap className="h-12 w-12 text-white" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Smart Academic Advisor</h2>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4">
          {(['student', 'faculty'] as const).map((type) => (
            <button key={type} type="button" onClick={() => handleTabChange(type)}
              disabled={isSubmitting}
              className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                userType === type
                  ? type === 'student'
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : 'bg-purple-600 text-white shadow-lg scale-105'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type === 'student' ? <UserCircle2 className="h-5 w-5" /> : <Shield className="h-5 w-5" />}
              <span className="capitalize">{type}</span>
            </button>
          ))}
        </div>

        {/* Form — key forces remount on tab change */}
        <div className="bg-white p-8 rounded-xl shadow-xl">
          <InnerForm
            key={userType}
            userType={userType}
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            onForgotPassword={handleForgotPassword}
            authError={authError}
          />
        </div>
      </motion.div>
    </div>
  );
};