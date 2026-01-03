// src/components/common/CTALink.tsx
import React, { useState, useCallback, memo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ExternalLink, 
  ArrowRight, 
  Loader,
  CheckCircle,
  Clock,
  Lock
} from 'lucide-react';
import { routeConfig } from '../../routes/AppRouter';
import Modal from './Modal';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useAuth } from '../../hooks/useAuth';
import { submitFeatureRequest } from '../../services/github.service';
import toast from 'react-hot-toast';

interface CTALinkProps {
  to: string;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'gradient' | 'outline';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  external?: boolean;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  showArrow?: boolean;
  analyticsEvent?: string;
  requireAuth?: boolean;
  fullWidth?: boolean;
  animated?: boolean;
  glowEffect?: boolean;
  trustBadge?: string;
  ariaLabel?: string;
  prefetch?: boolean;
}

const CTALink: React.FC<CTALinkProps> = memo(({
  to,
  children,
  variant = 'primary',
  size = 'md',
  external = false,
  className = '',
  onClick,
  disabled = false,
  loading = false,
  icon,
  rightIcon,
  showArrow = false,
  analyticsEvent,
  requireAuth = false,
  fullWidth = false,
  animated = true,
  glowEffect = false,
  trustBadge,
  ariaLabel,
  prefetch = true,
}) => {
  const navigate = useNavigate();
  const { trackEvent } = useAnalytics();
  const { isAuthenticated, user } = useAuth();
  const [showComingSoonModal, setShowComingSoonModal] = useState(false);
  const [featureRequestLoading, setFeatureRequestLoading] = useState(false);
  const [requestedFeature, setRequestedFeature] = useState('');

  // ✅ Improved route validation (handles external + dynamic routes)
  const isValidRoute = useCallback(() => {
    // Always allow external links
    if (external || to.startsWith('http') || to.startsWith('mailto:') || to.startsWith('tel:')) {
      return true;
    }

    // Check if the exact route exists
    if (Object.values(routeConfig).some(route => route.path === to)) {
      return true;
    }

    // Check for dynamic routes (with parameters)
    return Object.values(routeConfig).some(route => {
      if (route.path.includes(':')) {
        // Convert route path to regex pattern
        const pattern = route.path
          .replace(/:\w+/g, '([^/]+)') // Convert params to capture groups
          .replace(/\//g, '\\/'); // Escape slashes
        
        const regex = new RegExp(`^${pattern}$`);
        return regex.test(to);
      }
      return false;
    });
  }, [to, external]);

  const isExternalLink = external || to.startsWith('http://') || to.startsWith('https://');
  const isVideoLink = to.includes('youtube.com') || to.includes('vimeo.com');
  const isMailLink = to.startsWith('mailto:');
  const isTelLink = to.startsWith('tel:');

  const handleClick = useCallback(async (e: React.MouseEvent) => {
    if (disabled || loading) {
      e.preventDefault();
      return;
    }

    // Track analytics
    if (analyticsEvent) {
      trackEvent('cta_click', {
        label: analyticsEvent,
        destination: to,
        variant,
        authenticated: isAuthenticated,
        userId: user?.id,
      });
    }

    // Check authentication requirement
    if (requireAuth && !isAuthenticated) {
      e.preventDefault();
      toast.error('Please login to continue');
      navigate('/login', { state: { redirectTo: to } });
      return;
    }

    // Handle custom onClick
    if (onClick) {
      onClick();
    }

    // Handle special links
    if (isMailLink || isTelLink) {
      return; // Let browser handle naturally
    }

    // Handle external links
    if (isExternalLink) {
      e.preventDefault();
      if (isVideoLink) {
        window.open(to, '_blank', 'noopener,noreferrer,width=1200,height=800');
      } else {
        window.open(to, '_blank', 'noopener,noreferrer');
      }
      return;
    }

    // Handle internal navigation
    if (!isValidRoute() && !isExternalLink) {
      e.preventDefault();
      setRequestedFeature(to);
      setShowComingSoonModal(true);
      trackEvent('feature_requested', { 
        feature: to,
        userId: user?.id,
      });
    }
  }, [
    to, 
    isValidRoute, 
    isExternalLink, 
    isVideoLink,
    isMailLink,
    isTelLink,
    onClick, 
    trackEvent, 
    analyticsEvent, 
    variant,
    isAuthenticated,
    requireAuth,
    navigate,
    user,
    disabled,
    loading,
  ]);

  const handleFeatureRequest = async (description: string) => {
    setFeatureRequestLoading(true);
    try {
      await submitFeatureRequest({
        title: `Feature Request: ${requestedFeature}`,
        description,
        userId: user?.id,
        userEmail: user?.email,
      });
      
      toast.success('Feature request submitted successfully!');
      trackEvent('feature_request_submitted', {
        feature: requestedFeature,
        userId: user?.id,
      });
      setShowComingSoonModal(false);
    } catch (error) {
      toast.error('Failed to submit feature request. Please try again.');
    } finally {
      setFeatureRequestLoading(false);
    }
  };

  // Size classes
  const sizeClasses = {
    xs: 'px-3 py-1.5 text-xs',
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
    xl: 'px-10 py-5 text-xl',
  };

  // Variant classes
  const variantClasses = {
    primary: `
      bg-gradient-to-r from-indigo-600 to-purple-600 
      text-white hover:from-indigo-700 hover:to-purple-700 
      shadow-lg hover:shadow-xl
      ${glowEffect ? 'shadow-indigo-500/25' : ''}
    `,
    secondary: `
      bg-white text-purple-600 
      border-2 border-purple-600 hover:bg-purple-50
      shadow-md hover:shadow-lg
    `,
    ghost: `
      text-purple-600 hover:bg-purple-50
      hover:text-purple-700
    `,
    gradient: `
      bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500
      text-white hover:from-pink-600 hover:via-purple-600 hover:to-indigo-600
      shadow-xl hover:shadow-2xl
      ${glowEffect ? 'shadow-purple-500/30' : ''}
    `,
    outline: `
      border-2 border-gray-300 text-gray-700
      hover:border-purple-600 hover:text-purple-600
      hover:bg-purple-50
    `,
  };

  const baseClasses = `
    inline-flex items-center justify-center
    font-semibold rounded-xl
    transition-all duration-200
    focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    relative overflow-hidden
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `;

  // Content with loading state
  const buttonContent = (
    <>
      {animated && variant === 'gradient' && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0"
          animate={{ x: ['100%', '-100%'] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        />
      )}
      
      {loading && (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="mr-2"
        >
          <Loader className="h-4 w-4" />
        </motion.div>
      )}
      
      {icon && !loading && <span className="mr-2">{icon}</span>}
      <span className="relative z-10">{children}</span>
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
      {showArrow && !rightIcon && (
        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
      )}
      {isExternalLink && !rightIcon && !showArrow && (
        <ExternalLink className="ml-2 h-4 w-4" />
      )}
      {trustBadge && (
        <span className="ml-2 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-bold">
          {trustBadge}
        </span>
      )}
      {requireAuth && !isAuthenticated && (
        <Lock className="ml-2 h-4 w-4 text-gray-400" />
      )}
    </>
  );

  const MotionWrapper = animated ? motion.div : 'div';
  const motionProps = animated ? {
    whileHover: { scale: disabled || loading ? 1 : 1.02 },
    whileTap: { scale: disabled || loading ? 1 : 0.98 },
  } : {};

  // Render external link
  if (isExternalLink || isMailLink || isTelLink) {
    return (
      <MotionWrapper {...motionProps} className="inline-block">
        <a
          href={to}
          target={isExternalLink ? '_blank' : undefined}
          rel={isExternalLink ? 'noopener noreferrer' : undefined}
          className={`${baseClasses} group`}
          onClick={handleClick}
          aria-label={ariaLabel || String(children)}
          aria-disabled={disabled || loading}
        >
          {buttonContent}
        </a>
      </MotionWrapper>
    );
  }

  // Render internal link
  return (
    <>
      <MotionWrapper {...motionProps} className="inline-block">
        {isValidRoute() && !disabled && !loading ? (
          <Link
            to={to}
            className={`${baseClasses} group`}
            onClick={handleClick}
            aria-label={ariaLabel || String(children)}
            // Remove the invalid prefetch prop
          >
            {buttonContent}
          </Link>
        ) : (
          <button
            className={`${baseClasses} group`}
            onClick={handleClick}
            disabled={disabled || loading}
            aria-label={ariaLabel || String(children)}
            aria-busy={loading}
          >
            {buttonContent}
          </button>
        )}
      </MotionWrapper>

      {/* Coming Soon Modal */}
      <Modal
        isOpen={showComingSoonModal}
        onClose={() => setShowComingSoonModal(false)}
        title="Feature Coming Soon"
        size="md"
      >
        <div className="p-6">
          <div className="flex items-center justify-center mb-6">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="h-20 w-20 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-full flex items-center justify-center"
            >
              <Clock className="h-10 w-10 text-white" />
            </motion.div>
          </div>
          
          <div className="text-center mb-6">
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              This feature is under development
            </h3>
            <p className="text-gray-600">
              We're working hard to bring you this functionality. 
              Want to be notified when it's ready?
            </p>
          </div>

          <div className="space-y-4">
            <textarea
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
              rows={3}
              placeholder="Tell us what you'd like to see in this feature... (optional)"
              onChange={(e) => setRequestedFeature(prev => `${prev} - ${e.target.value}`)}
            />
            
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => handleFeatureRequest(requestedFeature)}
                disabled={featureRequestLoading}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all flex items-center justify-center"
              >
                {featureRequestLoading ? (
                  <>
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Request Feature & Get Notified
                  </>
                )}
              </button>
              
              <button
                onClick={() => setShowComingSoonModal(false)}
                className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all"
              >
                Close
              </button>
            </div>
          </div>
          
          <div className="mt-4 text-center text-xs text-gray-500">
            Your request will be sent to our development team
          </div>
        </div>
      </Modal>
    </>
  );
});

CTALink.displayName = 'CTALink';

export default CTALink;