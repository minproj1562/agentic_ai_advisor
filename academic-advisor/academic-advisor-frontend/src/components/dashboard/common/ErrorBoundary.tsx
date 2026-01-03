// src/components/dashboard/common/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../../utils/cn'; // Added missing cn import

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  // Simple theme transition utility function
  getThemeTransition = (): string => {
    return 'transition-colors duration-300';
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      return (
        <div className={cn('min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4', this.getThemeTransition())}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-lg w-full"
          >
            <div className={cn('bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden', this.getThemeTransition())}>
              <div className="bg-gradient-to-r from-red-500 to-pink-500 p-6 text-white">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-white/20 rounded-full backdrop-blur-sm">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold">Oops! Something went wrong</h1>
                    <p className="text-white/90 mt-1">
                      We encountered an unexpected error
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="space-y-4">
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <p className="text-sm font-medium text-red-800 dark:text-red-300">
                      Error Message:
                    </p>
                    <p className="mt-1 text-sm text-red-700 dark:text-red-400 font-mono">
                      {this.state.error?.message || 'Unknown error occurred'}
                    </p>
                  </div>

                  <button
                    onClick={this.toggleDetails}
                    className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                  >
                    {this.state.showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    {this.state.showDetails ? 'Hide' : 'Show'} Technical Details
                  </button>

                  <AnimatePresence>
                    {this.state.showDetails && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
                          <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Stack Trace:
                          </p>
                          <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto whitespace-pre-wrap break-words font-mono">
                            {this.state.error?.stack}
                          </pre>
                          
                          {this.state.errorInfo && (
                            <>
                              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mt-4 mb-2">
                                Component Stack:
                              </p>
                              <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto whitespace-pre-wrap break-words font-mono">
                                {this.state.errorInfo.componentStack}
                              </pre>
                            </>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={this.handleReset}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Try Again
                    </button>
                    <button
                      onClick={() => window.location.href = '/'}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
                    >
                      <Home className="w-4 h-4" />
                      Go Home
                    </button>
                  </div>

                  <p className="text-xs text-center text-gray-500 dark:text-gray-400 pt-2">
                    If this problem persists, please contact support with the error details above.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;