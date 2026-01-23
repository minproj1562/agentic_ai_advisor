// src/components/dashboard/AcademicInsights.tsx

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Target,
  BookOpen,
  Award,
  ChevronRight,
  Loader2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Sparkles,
  GraduationCap,
  Clock,
  Star,
  AlertCircle
} from 'lucide-react';
import { mlService, AcademicRecommendations, WeaknessData } from '../../services/ml.service';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface AcademicInsightsProps {
  onViewElectives?: () => void;
  onViewWeaknesses?: () => void;
}

export const AcademicInsights: React.FC<AcademicInsightsProps> = ({
  onViewElectives,
  onViewWeaknesses
}) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState<AcademicRecommendations | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.uid) {
      fetchRecommendations();
    }
    
    // Listen for academic data updates
    const handleAcademicUpdate = () => {
      fetchRecommendations();
    };
    
    window.addEventListener('academicDataUpdated', handleAcademicUpdate);
    
    return () => {
      window.removeEventListener('academicDataUpdated', handleAcademicUpdate);
    };
  }, [user]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await mlService.getAcademicRecommendations();
      setRecommendations(data);
      
      // Show toast for critical weaknesses
      const criticalWeaknesses = data.weaknesses?.filter(w => w.severity === 'critical') || [];
      if (criticalWeaknesses.length > 0) {
        toast.error(`⚠️ ${criticalWeaknesses.length} critical weakness${criticalWeaknesses.length > 1 ? 'es' : ''} detected!`, {
          duration: 5000
        });
      }
      
    } catch (err: any) {
      console.error('Error fetching recommendations:', err);
      setError(err.message || 'Failed to fetch recommendations');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'low': return 'bg-green-100 text-green-700 border-green-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <XCircle className="w-5 h-5 text-red-600" />;
      case 'high': return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      case 'medium': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'low': return <CheckCircle className="w-5 h-5 text-green-600" />;
      default: return <Target className="w-5 h-5 text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
          <span className="ml-3 text-gray-600">Analyzing your academic data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <XCircle className="w-6 h-6 text-red-600" />
            <div>
              <p className="font-medium text-red-900">Unable to Load Recommendations</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchRecommendations}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!recommendations) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-center space-x-3">
          <GraduationCap className="w-6 h-6 text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">Add Your Academic Data</p>
            <p className="text-sm text-blue-700">
              Enter your semester scores to get AI-powered recommendations
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Student Info */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Brain className="w-7 h-7" />
              Academic Recommendations
            </h2>
            <p className="text-blue-100 mt-1">
              AI-powered insights based on your academic performance
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">Current CGPA</p>
            <p className="text-3xl font-bold">{recommendations.student_info.cgpa.toFixed(2)}</p>
            <p className="text-xs text-blue-200">
              {recommendations.student_info.branch} • Sem {recommendations.student_info.semester}
            </p>
          </div>
        </div>
        
        <button
          onClick={fetchRecommendations}
          className="mt-4 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Analysis
        </button>
      </div>

      {/* Weaknesses Section */}
      {recommendations.weaknesses && recommendations.weaknesses.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Target className="w-5 h-5 text-orange-600" />
              Areas Needing Improvement
            </h3>
            {onViewWeaknesses && (
              <button
                onClick={onViewWeaknesses}
                className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
              >
                View All <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
          
          <div className="space-y-3">
            {recommendations.weaknesses.slice(0, 3).map((weakness, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`p-4 rounded-lg border ${getSeverityColor(weakness.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getSeverityIcon(weakness.severity)}
                    <div>
                      <h4 className="font-semibold">{weakness.subject}</h4>
                      <p className="text-sm mt-1">
                        Score: {weakness.average_score.toFixed(1)}% • Gap: {weakness.gap.toFixed(1)}%
                      </p>
                      {weakness.topics.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {weakness.topics.slice(0, 3).map((topic, tIndex) => (
                            <span
                              key={tIndex}
                              className="px-2 py-0.5 bg-white/50 rounded text-xs"
                            >
                              {topic}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <span className="text-xs font-medium uppercase">{weakness.severity}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Curriculum Recommendations */}
      {recommendations.curriculum_recommendations && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Immediate Actions */}
          {recommendations.curriculum_recommendations.immediate_actions?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-red-600" />
                Immediate Actions
              </h3>
              <div className="space-y-3">
                {recommendations.curriculum_recommendations.immediate_actions.map((action: any, index: number) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border-l-4 ${
                      action.priority === 'critical' || action.priority === 'high'
                        ? 'border-red-500 bg-red-50'
                        : 'border-yellow-500 bg-yellow-50'
                    }`}
                  >
                    <p className="font-medium text-sm">{action.action}</p>
                    {action.reason && (
                      <p className="text-xs text-gray-600 mt-1">{action.reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Honours/Minor Eligibility */}
          {recommendations.curriculum_recommendations.honours_minor_eligibility && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Award className="w-5 h-5 text-purple-600" />
                Honours/Minor Programs
              </h3>
              
              {recommendations.curriculum_recommendations.honours_minor_eligibility.eligible ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-800">You're Eligible!</span>
                  </div>
                  <p className="text-sm text-green-700">
                    {recommendations.curriculum_recommendations.honours_minor_eligibility.message}
                  </p>
                  
                  {recommendations.curriculum_recommendations.honours_minor_eligibility.available_programs && (
                    <div className="mt-3 space-y-2">
                      {recommendations.curriculum_recommendations.honours_minor_eligibility.available_programs.slice(0, 3).map((program: any, index: number) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span>{program.program}</span>
                          <span className="text-green-600 font-medium">{program.type}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    <span className="font-medium text-yellow-800">Not Yet Eligible</span>
                  </div>
                  <p className="text-sm text-yellow-700">
                    {recommendations.curriculum_recommendations.honours_minor_eligibility.message}
                  </p>
                  {recommendations.curriculum_recommendations.honours_minor_eligibility.cgpa_gap && (
                    <p className="text-sm text-yellow-600 mt-2">
                      Gap: {recommendations.curriculum_recommendations.honours_minor_eligibility.cgpa_gap.toFixed(2)} CGPA
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Interest-Based Recommendations */}
      {recommendations.interest_based_recommendations && recommendations.interest_based_recommendations.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Recommended Based on Your Interests
            </h3>
            {onViewElectives && (
              <button
                onClick={onViewElectives}
                className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
              >
                View All Electives <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.interest_based_recommendations.slice(0, 3).map((rec: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg border border-purple-200"
              >
                <h4 className="font-semibold text-purple-900">{rec.elective_name}</h4>
                <div className="flex items-center gap-2 mt-2">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm text-purple-700">{rec.match_score}% match</span>
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  Based on: {rec.interest}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Focus Areas */}
      {recommendations.curriculum_recommendations?.focus_areas?.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Your Strong Areas
          </h3>
          <div className="flex flex-wrap gap-2">
            {recommendations.curriculum_recommendations.focus_areas.map((area: any, index: number) => (
              <span
                key={index}
                className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
              >
                {area.area} ({area.average_score.toFixed(0)}%)
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AcademicInsights;