// modules/agent1/shared/components/ActionButton.tsx
import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, Check, X, AlertCircle } from 'lucide-react';

interface ActionButtonProps {
  label: string;
  onClick: () => Promise<void> | void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  showSuccessFeedback?: boolean;
  showErrorFeedback?: boolean;
  successMessage?: string;
  errorMessage?: string;
  confirmAction?: boolean;
  confirmMessage?: string;
  className?: string;
}

const ActionButton: React.FC<ActionButtonProps> = ({
  label,
  onClick,
  variant = 'primary',
  size = 'md',
  icon,
  disabled = false,
  loading: externalLoading = false,
  fullWidth = false,
  showSuccessFeedback = true,
  showErrorFeedback = true,
  successMessage = 'Success!',
  errorMessage = 'Something went wrong',
  confirmAction = false,
  confirmMessage = 'Are you sure?',
  className = ''
}) => {
  const [internalLoading, setInternalLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const loading = externalLoading || internalLoading;

  const getVariantClasses = useCallback(() => {
    const baseClasses = 'font-medium rounded-lg transition-all transform active:scale-95';
    
    switch (variant) {
      case 'primary':
        return `${baseClasses} bg-blue-600 text-white hover:bg-blue-700 focus:ring-4 focus:ring-blue-300`;
      case 'secondary':
        return `${baseClasses} bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-4 focus:ring-gray-300`;
      case 'danger':
        return `${baseClasses} bg-red-600 text-white hover:bg-red-700 focus:ring-4 focus:ring-red-300`;
      case 'success':
        return `${baseClasses} bg-green-600 text-white hover:bg-green-700 focus:ring-4 focus:ring-green-300`;
      case 'ghost':
        return `${baseClasses} text-gray-700 hover:bg-gray-100 focus:ring-4 focus:ring-gray-200`;
      default:
        return baseClasses;
    }
  }, [variant]);

  const getSizeClasses = useCallback(() => {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'lg':
        return 'px-6 py-3 text-lg';
      default:
        return 'px-4 py-2 text-base';
    }
  }, [size]);

  const handleClick = useCallback(async () => {
    if (disabled || loading) return;

    if (confirmAction && !showConfirm) {
      setShowConfirm(true);
      return;
    }

    setInternalLoading(true);
    setError(false);
    setSuccess(false);
    setShowConfirm(false);

    try {
      await onClick();
      
      if (showSuccessFeedback) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 2000);
      }
    } catch (err) {
      if (showErrorFeedback) {
        setError(true);
        setTimeout(() => setError(false), 3000);
      }
      console.error('Button action failed:', err);
    } finally {
      setInternalLoading(false);
    }
  }, [disabled, loading, confirmAction, showConfirm, onClick, showSuccessFeedback, showErrorFeedback]);

  const getButtonContent = useCallback(() => {
    if (success) {
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-2"
        >
          <Check className="w-4 h-4" />
          <span>{successMessage}</span>
        </motion.div>
      );
    }

    if (error) {
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          <span>{errorMessage}</span>
        </motion.div>
      );
    }

    if (loading) {
      return (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center gap-2"
        >
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Processing...</span>
        </motion.div>
      );
    }

    return (
      <div className="flex items-center gap-2">
        {icon && <span>{icon}</span>}
        <span>{label}</span>
      </div>
    );
  }, [success, error, loading, icon, label, successMessage, errorMessage]);

  return (
    <div className="relative inline-block">
      <motion.button
        whileHover={{ scale: disabled ? 1 : 1.02 }}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        onClick={handleClick}
        disabled={disabled || loading}
        className={`
          ${getVariantClasses()}
          ${getSizeClasses()}
          ${fullWidth ? 'w-full' : ''}
          ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}
          ${success ? '!bg-green-600' : ''}
          ${error ? '!bg-red-600' : ''}
          ${className}
        `}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={success ? 'success' : error ? 'error' : loading ? 'loading' : 'default'}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {getButtonContent()}
          </motion.div>
        </AnimatePresence>
      </motion.button>

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 z-50"
          >
            <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-4 min-w-[200px]">
              <div className="flex items-start gap-3 mb-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-gray-700">{confirmMessage}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClick}
                  className="flex-1 px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  Confirm
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ActionButton;