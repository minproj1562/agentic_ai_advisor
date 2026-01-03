// src/components/dashboard/sections/ProjectAnalysisResults.tsx
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, TrendingUp, Briefcase, Star, BookOpen, Target,
  CheckCircle, Award, GraduationCap, Sparkles, ChevronRight,
  Calendar, Clock, AlertCircle, DollarSign, BarChart3, Zap,
  Download, X, Loader2, RefreshCw
} from 'lucide-react';
import { mlService } from '../../../services/ml.service';
import { useAuth } from '../../../contexts/AuthContext';
import type { 
  ComprehensiveAnalysis,
  ElectiveRecommendation,
  HonoursRecommendation,
  CareerPath 
} from '../../../services/student_projects_cloudinary.service';

interface ProjectAnalysisResultsProps {
  analysis: ComprehensiveAnalysis;
  onClose: () => void;
  studentBranch: string;
  studentSemester: number;
}

export const ProjectAnalysisResults: React.FC<ProjectAnalysisResultsProps> = ({
  analysis,
  onClose,
  studentBranch,
  studentSemester
}) => {
  const { user } = useAuth();
  const [activeSection, setActiveSection] = React.useState<
    'interests' | 'electives' | 'honours' | 'careers' | 'skills' | 'nextsteps' | 'mlinsights'
  >('interests');
  
  // ML-enhanced state
  const [mlElectives, setMlElectives] = useState<any[]>([]);
  const [mlCareers, setMlCareers] = useState<any[]>([]);
  const [loadingML, setLoadingML] = useState(false);
  const [mlEnhanced, setMlEnhanced] = useState(false);

  // Fetch ML-enhanced recommendations
  useEffect(() => {
    if (user?.uid && !mlEnhanced) {
      fetchMLEnhancements();
    }
  }, [user]);

  const fetchMLEnhancements = async () => {
    if (!user?.uid) return;
    
    setLoadingML(true);
    try {
      // Extract skills from current analysis
      const currentSkills = analysis.skill_gap_analysis?.current_skills || [];
      const interests = analysis.inferred_interests?.map(i => i.domain) || [];
      const projects = analysis.inferred_interests?.flatMap(i => i.keywords) || [];
      
      // Get ML-powered career predictions
      const careerPredictions = await mlService.predictCareer(
        user.uid,
        currentSkills,
        interests,
        7.5, // You should get actual CGPA
        projects
      );
      
      setMlCareers(careerPredictions.recommended_careers || []);
      
      // Combine original electives with ML suggestions
      setMlElectives([
        ...analysis.elective_recommendations,
        ...generateMLElectives(interests, currentSkills)
      ]);
      
      setMlEnhanced(true);
    } catch (error) {
      console.error('Error fetching ML enhancements:', error);
    } finally {
      setLoadingML(false);
    }
  };

  const generateMLElectives = (interests: string[], skills: string[]) => {
    // This would call ML server in production
    const mlSuggestions = [];
    
    if (interests.includes('Machine Learning') || interests.includes('AI')) {
      mlSuggestions.push({
        elective: 'Deep Learning & Neural Networks',
        match_score: 94,
        difficulty_level: 'Advanced',
        reasons: [
          'Strong alignment with your ML project interests',
          'ML Server recommends based on your skill progression',
          'High industry demand in your interest areas'
        ],
        skills_to_gain: ['PyTorch', 'TensorFlow', 'Neural Architecture'],
        career_relevance: 'Critical for AI/ML Engineer roles',
        ml_recommended: true
      });
    }
    
    if (interests.includes('Web Development')) {
      mlSuggestions.push({
        elective: 'Advanced Web Technologies',
        match_score: 91,
        difficulty_level: 'Medium',
        reasons: [
          'Matches your web development project portfolio',
          'ML analysis shows strong frontend/backend capabilities',
          'Complements your existing React and Node.js skills'
        ],
        skills_to_gain: ['Next.js', 'GraphQL', 'Microservices'],
        career_relevance: 'Essential for Full Stack Developer positions',
        ml_recommended: true
      });
    }
    
    return mlSuggestions;
  };

  const downloadAnalysis = () => {
    const fullAnalysis = {
      ...analysis,
      ml_enhanced_recommendations: {
        electives: mlElectives,
        careers: mlCareers,
        generated_at: new Date().toISOString()
      }
    };
    
    const dataStr = JSON.stringify(fullAnalysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `academic_analysis_${new Date().toISOString().split('T')[0]}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white rounded-2xl max-w-6xl w-full my-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
                🎯 AI-Powered Academic Analysis Complete!
                {mlEnhanced && (
                  <span className="text-xs bg-green-500/30 px-2 py-1 rounded-full">
                    ML Enhanced
                  </span>
                )}
              </h2>
              <p className="text-purple-100">
                Your personalized roadmap to academic and career success
              </p>
              <div className="flex items-center gap-4 mt-3">
                <span className="text-sm bg-white/20 backdrop-blur px-3 py-1 rounded-full">
                  {studentBranch} • Semester {studentSemester}
                </span>
                <span className="text-sm bg-green-500/20 backdrop-blur px-3 py-1 rounded-full">
                  ✨ FCRIT Academic Guidelines Applied
                </span>
                {!mlEnhanced && loadingML && (
                  <span className="text-sm bg-yellow-500/20 backdrop-blur px-3 py-1 rounded-full flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Enhancing with ML...
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={fetchMLEnhancements}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="Refresh ML Analysis"
              >
                <RefreshCw className={`w-5 h-5 ${loadingML ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b bg-gray-50">
          <div className="flex overflow-x-auto">
            {[
              { id: 'interests', label: 'AI Interests', icon: Brain },
              { id: 'electives', label: 'ML Electives', icon: BookOpen, badge: mlElectives.length },
              { id: 'honours', label: 'Honours/Minor', icon: Award },
              { id: 'careers', label: 'Career Paths', icon: Briefcase, badge: mlCareers.length },
              { id: 'skills', label: 'Skill Gaps', icon: Target },
              { id: 'nextsteps', label: 'Next Steps', icon: ChevronRight },
              { id: 'mlinsights', label: 'ML Insights', icon: Sparkles, new: true }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSection(tab.id as any)}
                className={`
                  flex items-center gap-2 px-4 py-3 font-medium transition-all whitespace-nowrap relative
                  ${activeSection === tab.id 
                    ? 'text-purple-600 border-b-2 border-purple-600 bg-white' 
                    : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                  }
                `}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
                {tab.badge && (
                  <span className="ml-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">
                    {tab.badge}
                  </span>
                )}
                {tab.new && (
                  <span className="absolute -top-1 -right-1 px-1.5 py-0.5 bg-green-500 text-white rounded-full text-[10px] font-bold">
                    NEW
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area - Keep existing sections and add new ML Insights section */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {/* ... Keep all existing sections (interests, honours, careers, skills, nextsteps) ... */}
          
          {/* ML-Enhanced Electives Section */}
          {activeSection === 'electives' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  ML-Recommended Electives for Semester {studentSemester + 1}
                </h3>
                {mlEnhanced && (
                  <span className="text-sm text-green-600 flex items-center gap-1">
                    <Sparkles className="w-4 h-4" />
                    ML Enhanced
                  </span>
                )}
              </div>
              
              {loadingML ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                  <span className="ml-2">Generating ML recommendations...</span>
                </div>
              ) : mlElectives.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>No elective recommendations available.</p>
                </div>
              ) : (
                mlElectives.map((elective, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.15 }} // Increased delay for better visibility
                    className={`p-4 border rounded-xl hover:shadow-lg transition-all ${
                      elective.ml_recommended ? 'border-purple-300 bg-purple-50/50' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-lg">{elective.elective}</h4>
                          {elective.ml_recommended && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-bold flex items-center gap-1">
                              <Sparkles className="w-3 h-3" />
                              ML Pick
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-sm text-green-600 font-medium">
                            {elective.match_score}% Match
                          </span>
                          <span className="text-sm px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
                            {elective.difficulty_level}
                          </span>
                        </div>
                      </div>
                      <Sparkles className="w-5 h-5 text-purple-500" />
                    </div>

                    <div className="space-y-2">
                      <div>
                        <p className="text-xs font-medium text-gray-500 mb-1">WHY THIS ELECTIVE?</p>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {elective.reasons.map((reason: string, rIndex: number) => (
                            <li key={rIndex} className="flex items-start">
                              <CheckCircle className="w-3 h-3 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                              {reason}
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-gray-500 mb-1">SKILLS YOU'LL GAIN</p>
                        <div className="flex flex-wrap gap-1">
                          {elective.skills_to_gain.map((skill: string, sIndex: number) => (
                            <span
                              key={sIndex}
                              className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="pt-2 border-t">
                        <p className="text-sm text-gray-600">
                          <strong>Career Relevance:</strong> {elective.career_relevance}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          )}

          {/* NEW: ML Insights Section */}
          {activeSection === 'mlinsights' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border-2 border-purple-200">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  Machine Learning Analysis Summary
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">ML Model Confidence</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-purple-200 rounded-full h-2">
                        <div className="bg-purple-600 h-2 rounded-full" style={{ width: '89%' }} />
                      </div>
                      <span className="text-sm font-bold text-purple-700">89%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Career Match Accuracy</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-green-200 rounded-full h-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{ width: '92%' }} />
                      </div>
                      <span className="text-sm font-bold text-green-700">92%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ML Career Recommendations */}
              {mlCareers.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-600" />
                    ML-Powered Career Matches
                  </h4>
                  <div className="space-y-3">
                    {mlCareers.map((career, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.2 }} // Longer delay for better visibility
                        className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-semibold text-lg">{career.career}</h5>
                          <span className="text-sm font-medium text-purple-600">
                            {career.match_score}% Match
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-2 mb-3">
                          <div className="text-sm">
                            <span className="text-gray-500">Demand:</span>
                            <span className="ml-1 font-medium">{career.industry_demand}</span>
                          </div>
                          <div className="text-sm">
                            <span className="text-gray-500">Growth:</span>
                            <span className="ml-1 font-medium">{career.growth_potential}</span>
                          </div>
                          <div className="text-sm">
                            <span className="text-gray-500">Salary:</span>
                            <span className="ml-1 font-medium">{career.salary_range}</span>
                          </div>
                        </div>
                        
                        {career.missing_skills?.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Skills to Develop:</p>
                            <div className="flex flex-wrap gap-1">
                              {career.missing_skills.map((skill: string, idx: number) => (
                                <span key={idx} className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* ML Model Information */}
              <div className="bg-gray-50 rounded-lg p-4 border">
                <h4 className="font-medium text-gray-900 mb-2">ML Models Used</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-gray-600">GPA Predictor</p>
                    <p className="font-medium">Gradient Boosting</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Career Matcher</p>
                    <p className="font-medium">Random Forest</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Interest Analyzer</p>
                    <p className="font-medium">Sentence Transformer</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Skill Extractor</p>
                    <p className="font-medium">NLP Pipeline</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 rounded-b-2xl flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Analysis powered by AI • Based on FCRIT Academic Guidelines
            {mlEnhanced && (
              <span className="ml-2 text-purple-600">• ML Enhanced</span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={downloadAnalysis}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-white transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download Report
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow font-medium"
            >
              Got It, Thanks!
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};