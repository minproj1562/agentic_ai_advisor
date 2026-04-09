// src/components/dashboard/ChangePassword.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, Eye, EyeOff, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import apiClient from '../../services/api.service';

const passwordSchema = z.object({
  current_password: z.string().min(8, 'Password must be at least 8 characters'),
  new_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[a-z]/, 'Must contain at least one lowercase letter')
    .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
    .regex(/\d/, 'Must contain at least one number'),
  confirm_password: z.string().min(8, 'Please confirm your password'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

type PasswordFormData = z.infer<typeof passwordSchema>;

export const ChangePassword: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  });

  const newPassword = watch('new_password');

  const getPasswordStrength = (password: string): number => {
    if (!password) return 0;
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[a-z]/.test(password)) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/\d/.test(password)) strength += 25;
    return strength;
  };

  const strength = getPasswordStrength(newPassword);

  const onSubmit = async (data: PasswordFormData) => {
    try {
      setLoading(true);
      const response = await apiClient.post('/auth/student/change-password', data);

      if (response.data.success) {
        setSuccess(true);
        toast.success('Password changed successfully!');
        reset();
        setTimeout(() => {
          setSuccess(false);
          onClose?.();
        }, 2000);
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to change password';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="flex flex-col items-center justify-center p-8"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
          className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4"
        >
          <CheckCircle className="w-10 h-10 text-green-600" />
        </motion.div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">Password Changed!</h3>
        <p className="text-gray-600 text-center">Your password has been updated successfully.</p>
      </motion.div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Lock className="w-6 h-6 text-blue-600" />
          Change Password
        </h2>
        <p className="text-sm text-gray-600 mt-1">Update your account password</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Current Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Password
          </label>
          <div className="relative">
            <input
              {...register('current_password')}
              type={showCurrent ? 'text' : 'password'}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 pr-10 ${
                errors.current_password ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Enter current password"
            />
            <button
              type="button"
              onClick={() => setShowCurrent(!showCurrent)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.current_password && (
            <p className="text-xs text-red-600 mt-1">{errors.current_password.message}</p>
          )}
        </div>

        {/* New Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            New Password
          </label>
          <div className="relative">
            <input
              {...register('new_password')}
              type={showNew ? 'text' : 'password'}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 pr-10 ${
                errors.new_password ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Enter new password"
            />
            <button
              type="button"
              onClick={() => setShowNew(!showNew)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {/* Password Strength Indicator */}
          {newPassword && (
            <div className="mt-2">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${strength}%` }}
                  className={`h-full transition-all ${
                    strength < 50
                      ? 'bg-red-500'
                      : strength < 75
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                />
              </div>
              <p className="text-xs mt-1 text-gray-600">
                Password strength:{' '}
                <span
                  className={
                    strength < 50
                      ? 'text-red-600 font-medium'
                      : strength < 75
                      ? 'text-yellow-600 font-medium'
                      : 'text-green-600 font-medium'
                  }
                >
                  {strength < 50 ? 'Weak' : strength < 75 ? 'Medium' : 'Strong'}
                </span>
              </p>
            </div>
          )}

          {errors.new_password && (
            <p className="text-xs text-red-600 mt-1">{errors.new_password.message}</p>
          )}

          {/* Requirements */}
          <div className="mt-2 text-xs text-gray-500 space-y-1">
            <p className={newPassword?.length >= 8 ? 'text-green-600' : ''}>
              ✓ At least 8 characters
            </p>
            <p className={/[a-z]/.test(newPassword || '') ? 'text-green-600' : ''}>
              ✓ One lowercase letter
            </p>
            <p className={/[A-Z]/.test(newPassword || '') ? 'text-green-600' : ''}>
              ✓ One uppercase letter
            </p>
            <p className={/\d/.test(newPassword || '') ? 'text-green-600' : ''}>
              ✓ One number
            </p>
          </div>
        </div>

        {/* Confirm Password */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confirm New Password
          </label>
          <div className="relative">
            <input
              {...register('confirm_password')}
              type={showConfirm ? 'text' : 'password'}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 pr-10 ${
                errors.confirm_password ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Confirm new password"
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="text-xs text-red-600 mt-1">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Changing Password...
            </>
          ) : (
            'Change Password'
          )}
        </button>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="w-full py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        )}
      </form>
    </div>
  );
};