// src/components/dashboard/common/LoadingSkeleton.tsx
import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import { getThemeTransition } from '../../../utils/theme.utils';

interface LoadingSkeletonProps {
  type?: 'card' | 'table' | 'list' | 'dashboard';
  count?: number;
  className?: string;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  type = 'dashboard',
  count = 1,
  className
}) => {
  const shimmer = {
    initial: { backgroundPosition: '-1000px 0' },
    animate: {
      backgroundPosition: '1000px 0',
      transition: {
        repeat: Infinity,
        duration: 2,
        ease: 'linear'
      }
    }
  };

  const SkeletonBox = ({ className: boxClassName }: { className?: string }) => (
    <motion.div
      className={cn(
        'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700',
        'bg-[length:1000px_100%]',
        'rounded',
        boxClassName,
        getThemeTransition()
      )}
      variants={shimmer}
      initial="initial"
      animate="animate"
    />
  );

  if (type === 'card') {
    return (
      <div className={cn('space-y-4', className, getThemeTransition())}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', getThemeTransition())}>
            <div className="space-y-3">
              <SkeletonBox className="h-6 w-1/3" />
              <SkeletonBox className="h-4 w-full" />
              <SkeletonBox className="h-4 w-5/6" />
              <div className="flex gap-2 mt-4">
                <SkeletonBox className="h-8 w-20" />
                <SkeletonBox className="h-8 w-20" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', className, getThemeTransition())}>
        <SkeletonBox className="h-6 w-1/4 mb-4" />
        <div className="space-y-2">
          <div className="flex gap-4 pb-2 border-b border-gray-200 dark:border-gray-700">
            <SkeletonBox className="h-4 w-1/4" />
            <SkeletonBox className="h-4 w-1/4" />
            <SkeletonBox className="h-4 w-1/4" />
            <SkeletonBox className="h-4 w-1/4" />
          </div>
          {Array.from({ length: count }).map((_, i) => (
            <div key={i} className="flex gap-4 py-2">
              <SkeletonBox className="h-10 w-1/4" />
              <SkeletonBox className="h-10 w-1/4" />
              <SkeletonBox className="h-10 w-1/4" />
              <SkeletonBox className="h-10 w-1/4" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'list') {
    return (
      <div className={cn('space-y-2', className, getThemeTransition())}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className={cn('bg-white dark:bg-gray-800 rounded-lg p-4 shadow', getThemeTransition())}>
            <div className="flex items-center gap-4">
              <SkeletonBox className="h-12 w-12 rounded-full" />
              <div className="flex-1 space-y-2">
                <SkeletonBox className="h-4 w-1/3" />
                <SkeletonBox className="h-3 w-1/2" />
              </div>
              <SkeletonBox className="h-8 w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn('min-h-screen bg-gray-50 dark:bg-gray-900', getThemeTransition())}>
      <div className={cn('bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 h-16 px-6', getThemeTransition())}>
        <div className="flex items-center justify-between h-full">
          <div className="flex items-center gap-4">
            <SkeletonBox className="h-8 w-8 rounded" />
            <SkeletonBox className="h-10 w-10 rounded-full" />
            <div className="space-y-1">
              <SkeletonBox className="h-4 w-32" />
              <SkeletonBox className="h-3 w-24" />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <SkeletonBox className="h-8 w-8 rounded" />
            <SkeletonBox className="h-8 w-8 rounded" />
            <SkeletonBox className="h-8 w-8 rounded" />
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-64px)]">
        <div className={cn('w-64 bg-white dark:bg-gray-800 shadow-md p-4', getThemeTransition())}>
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonBox key={i} className="h-10 w-full rounded-lg" />
            ))}
          </div>
        </div>

        <div className="flex-1 p-6">
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <SkeletonBox className="h-8 w-1/3 mb-2" />
              <SkeletonBox className="h-4 w-1/2" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-md p-6', getThemeTransition())}>
                  <div className="flex items-center justify-between">
                    <div className="space-y-2">
                      <SkeletonBox className="h-3 w-16" />
                      <SkeletonBox className="h-6 w-12" />
                    </div>
                    <SkeletonBox className="h-10 w-10 rounded-full" />
                  </div>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6', getThemeTransition())}>
                  <SkeletonBox className="h-6 w-1/2 mb-4" />
                  <div className="space-y-3">
                    <SkeletonBox className="h-32 w-full" />
                    <SkeletonBox className="h-4 w-full" />
                    <SkeletonBox className="h-4 w-3/4" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSkeleton;