// src/components/dashboard/sections/ProjectAnalysisResults.tsx

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Brain,
  Sparkles,
  BookOpen,
  Award,
  Briefcase,
  TrendingUp,
  ChevronRight,
  CheckCircle,
  Clock,
  Target,
  Code,
  GraduationCap,
  Star,
  AlertTriangle,
  Download,
  Share2
} from 'lucide-react';
import { ProjectAnalysisResult } from '../../../services/ml.service';

interface ProjectAnalysisResultsProps {
  analysis: ProjectAnalysisResult;
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
  const [activeTab, setActiveTab] = useState<'interests' | 'electives' | 'honours' | 'career' | 'skills' | 'next'>('interests');

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-500 bg-red-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-green-500 bg-green-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-3">
                <Brain className="w-8 h-8" />
                AI Project Analysis Complete
              </h2>
              <p className="text-purple-100 mt-1">
                Personalized insights for {studentBranch} - Semester {studentSemester}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                Confidence: {(analysis.metadata.confidence_score * 100).toFixed(0)}%
              </span>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-4 gap-4 mt-6">
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{analysis.inferred_interests.length}</p>
              <p className="text-xs text-purple-100">Interests Found</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{analysis.elective_recommendations.length}</p>
              <p className="text-xs text-purple-100">Electives Matched</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{analysis.honours_minor_recommendations.length}</p>
              <p className="text-xs text-purple-100">Programmes</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold">{analysis.career_paths.length}</p>
              <p className="text-xs text-purple-100">Career Paths</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b bg-gray-50">
          <div className="flex overflow-x-auto">
            {[
              { id: 'interests', label: 'Interests', icon: Sparkles },
              { id: 'electives', label: 'Electives', icon: BookOpen },
              { id: 'honours', label: 'Honours/Minor', icon: Award },
              { id: 'career', label: 'Career Paths', icon: Briefcase },
              { id: 'skills', label: 'Skill Gaps', icon: Code },
              { id: 'next', label: 'Next Steps', icon: Target }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-5 py-4 font-medium transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'text-purple-600 border-b-2 border-purple-600 bg-white'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          <AnimatePresence mode="wait">
            {/* Interests Tab */}
            {activeTab === 'interests' && (
              <motion.div
                key="interests"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">AI-Detected Interests from Your Project</h3>
                
                {analysis.inferred_interests.length > 0 ? (
                  <div className="grid gap-4">
                    {analysis.inferred_interests.map((interest, index) => (
                      <div
                        key={index}
                        className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-semibold text-lg text-purple-900">{interest.domain}</h4>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1 ${getConfidenceColor(interest.confidence)}`}>
                              {(interest.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-gray-600">Industry Relevance</p>
                            <p className="font-bold text-purple-600">{(interest.industryRelevance * 100).toFixed(0)}%</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mt-4">
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">RELATED SKILLS</p>
                            <div className="flex flex-wrap gap-1">
                              {interest.relatedSkills.slice(0, 5).map((skill, sIndex) => (
                                <span
                                  key={sIndex}
                                  className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">CAREER PATHS</p>
                            <div className="flex flex-wrap gap-1">
                              {interest.careerPaths.slice(0, 3).map((career, cIndex) => (
                                <span
                                  key={cIndex}
                                  className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs"
                                >
                                  {career}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        
                        {interest.keywords.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-purple-200">
                            <p className="text-xs text-gray-500">
                              Detected from: {interest.keywords.slice(0, 5).join(', ')}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No specific interests detected. Add more details to your project!</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Electives Tab */}
            {activeTab === 'electives' && (
              <motion.div
                key="electives"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">Recommended Electives for You</h3>
                
                {analysis.elective_recommendations.length > 0 ? (
                  <div className="space-y-3">
                    {analysis.elective_recommendations.map((elective, index) => (
                      <div
                        key={index}
                        className="p-4 bg-white border rounded-xl hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-900">{elective.elective}</h4>
                            <p className="text-sm text-gray-600">{elective.code}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-yellow-500" />
                            <span className="font-bold text-purple-600">{elective.match_score}%</span>
                          </div>
                        </div>
                        
                        <div className="mt-3">
                          <p className="text-xs font-medium text-gray-500 mb-1">WHY THIS ELECTIVE?</p>
                          <ul className="space-y-1">
                            {elective.reasons.map((reason, rIndex) => (
                              <li key={rIndex} className="text-sm text-gray-700 flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                                {reason}
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        <div className="mt-3 flex flex-wrap gap-1">
                          {elective.skills_to_gain.map((skill, sIndex) => (
                            <span
                              key={sIndex}
                              className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                        
                        <div className="mt-3 flex items-center justify-between text-sm">
                          <span className="text-gray-600">{elective.career_relevance}</span>
                          <span className={`px-2 py-1 rounded ${
                            elective.difficulty_level === 'High' ? 'bg-red-100 text-red-700' :
                            elective.difficulty_level === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                            {elective.difficulty_level}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No elective recommendations available yet.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Honours/Minor Tab */}
            {activeTab === 'honours' && (
              <motion.div
                key="honours"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">Honours & Minor Programme Recommendations</h3>
                
                {analysis.honours_minor_recommendations.length > 0 ? (
                  <div className="grid gap-4">
                    {analysis.honours_minor_recommendations.map((program, index) => (
                      <div
                        key={index}
                        className="p-5 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <Award className={`w-5 h-5 ${program.type === 'Honours' ? 'text-amber-600' : 'text-blue-600'}`} />
                              <h4 className="font-bold text-lg">{program.program}</h4>
                            </div>
                            <span className={`inline-block mt-1 px-2 py-1 rounded text-xs font-medium ${
                              program.type === 'Honours' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                            }`}>
                              {program.type}
                            </span>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-amber-600">{program.match_score}%</p>
                            <p className="text-xs text-gray-600">Match Score</p>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mt-4">
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">COURSES</p>
                            <ul className="space-y-1">
                              {program.courses.map((course, cIndex) => (
                                <li key={cIndex} className="text-sm text-gray-700">• {course}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">CAREER PATHS</p>
                            <ul className="space-y-1">
                              {program.career_paths.slice(0, 4).map((career, cIndex) => (
                                <li key={cIndex} className="text-sm text-gray-700">• {career}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        
                        <div className="mt-4 pt-3 border-t border-amber-200 flex items-center justify-between text-sm">
                          <span className="text-gray-600">
                            <GraduationCap className="w-4 h-4 inline mr-1" />
                            {program.credits} Credits • {program.semester_commitment}
                          </span>
                        </div>
                        
                        {program.reasons.length > 0 && (
                          <div className="mt-3 p-3 bg-white/50 rounded-lg">
                            <p className="text-xs font-medium text-gray-500 mb-1">WHY THIS PROGRAMME?</p>
                            <p className="text-sm text-gray-700">{program.reasons[0]}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Award className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No programme recommendations available yet.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Career Paths Tab */}
            {activeTab === 'career' && (
              <motion.div
                key="career"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">AI-Mapped Career Paths</h3>
                
                {analysis.career_paths.length > 0 ? (
                  <div className="space-y-4">
                    {analysis.career_paths.map((career, index) => (
                      <div
                        key={index}
                        className="p-5 bg-white border rounded-xl hover:shadow-lg transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-bold text-xl text-gray-900">{career.title}</h4>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="text-green-600 font-medium">{career.salary_range}</span>
                              <span className={`px-2 py-1 rounded text-xs ${
                                career.market_demand === 'Very High' ? 'bg-green-100 text-green-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {career.market_demand} Demand
                              </span>
                              <span className="text-gray-600 text-sm">{career.growth_potential} Growth</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="relative w-16 h-16">
                              <svg className="w-16 h-16 transform -rotate-90">
                                <circle
                                  cx="32" cy="32" r="28"
                                  fill="none" stroke="#e5e7eb" strokeWidth="4"
                                />
                                <circle
                                  cx="32" cy="32" r="28"
                                  fill="none" stroke="#7c3aed" strokeWidth="4"
                                  strokeDasharray={`${career.match_score * 1.76} 176`}
                                />
                              </svg>
                              <span className="absolute inset-0 flex items-center justify-center font-bold text-purple-600">
                                {career.match_score}%
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">REQUIRED SKILLS</p>
                            <div className="flex flex-wrap gap-1">
                              {career.required_skills.map((skill, sIndex) => (
                                <span
                                  key={sIndex}
                                  className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">TOP COMPANIES</p>
                            <div className="flex flex-wrap gap-1">
                              {career.companies_hiring.slice(0, 4).map((company, cIndex) => (
                                <span
                                  key={cIndex}
                                  className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                                >
                                  {company}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                        
                        {career.honours_program && (
                          <div className="mt-3 p-2 bg-amber-50 rounded flex items-center gap-2">
                            <Award className="w-4 h-4 text-amber-600" />
                            <span className="text-sm text-amber-800">
                              Recommended Honours: <strong>{career.honours_program}</strong>
                            </span>
                          </div>
                        )}
                        
                        <div className="mt-4">
                          <p className="text-xs font-medium text-gray-500 mb-2">PREPARATION PATH</p>
                          <div className="flex flex-wrap gap-2">
                            {career.preparation_path.slice(0, 3).map((step, sIndex) => (
                              <span
                                key={sIndex}
                                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs flex items-center gap-1"
                              >
                                <span className="w-4 h-4 bg-purple-600 text-white rounded-full flex items-center justify-center text-xs">
                                  {sIndex + 1}
                                </span>
                                {step}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No career paths identified yet.</p>
                  </div>
                )}
              </motion.div>
            )}

            {/* Skills Gap Tab */}
            {activeTab === 'skills' && (
              <motion.div
                key="skills"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">Skill Gap Analysis</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Current Skills */}
                  <div className="bg-green-50 border border-green-200 rounded-xl p-4">
                    <h4 className="font-medium text-green-800 mb-3 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Your Current Skills ({analysis.skill_gap_analysis.current_skills.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {analysis.skill_gap_analysis.current_skills.map((skill, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {/* Skill Gaps */}
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <h4 className="font-medium text-red-800 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Skills to Develop ({analysis.skill_gap_analysis.skill_gaps.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {analysis.skill_gap_analysis.skill_gaps.slice(0, 10).map((skill, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                
                {/* Priority Skills */}
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                  <h4 className="font-medium text-purple-800 mb-3 flex items-center gap-2">
                    <Star className="w-5 h-5" />
                    Priority Skills to Learn
                  </h4>
                  <div className="space-y-3">
                    {analysis.skill_gap_analysis.priority_skills.map((skill, index) => (
                      <div key={index} className="bg-white p-3 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{skill}</span>
                          <span className="text-sm text-purple-600">High Priority</span>
                        </div>
                        {analysis.skill_gap_analysis.learning_resources[skill] && (
                          <div className="mt-2 space-y-1">
                            {analysis.skill_gap_analysis.learning_resources[skill].slice(0, 2).map((resource: any, rIndex: number) => (
                              <p key={rIndex} className="text-xs text-gray-600">
                                • {resource.platform}: {resource.course}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Completeness */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-blue-800">Skill Completeness</h4>
                      <p className="text-sm text-blue-600">
                        Estimated learning time: {analysis.skill_gap_analysis.estimated_learning_time}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-blue-600">
                        {analysis.skill_gap_analysis.completeness_percentage}%
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${analysis.skill_gap_analysis.completeness_percentage}%` }}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* Next Steps Tab */}
            {activeTab === 'next' && (
              <motion.div
                key="next"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-4"
              >
                <h3 className="text-lg font-semibold mb-4">Your Personalized Action Plan</h3>
                
                {analysis.next_steps.length > 0 ? (
                  <div className="space-y-3">
                    {analysis.next_steps.map((step, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-xl border-l-4 ${getPriorityColor(step.priority)}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                step.category === 'Academic' ? 'bg-blue-100 text-blue-700' :
                                step.category === 'Skills' ? 'bg-green-100 text-green-700' :
                                step.category === 'Portfolio' ? 'bg-purple-100 text-purple-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {step.category}
                              </span>
                              <span className="text-xs text-gray-500">
                                <Clock className="w-3 h-3 inline mr-1" />
                                {step.deadline}
                              </span>
                            </div>
                            <h4 className="font-semibold text-gray-900">{step.action}</h4>
                            <p className="text-sm text-gray-600 mt-1">{step.details}</p>
                          </div>
                          <ChevronRight className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Target className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No action items available yet.</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 p-4 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Analysis generated at {new Date(analysis.metadata.analysis_date).toLocaleString()}
          </p>
          <div className="flex items-center gap-3">
            <button className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Download Report
            </button>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow"
            >
              Done
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ProjectAnalysisResults;