// src/components/dashboard/sections/ProjectAnalysisResults.tsx
import React, { useEffect, useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  Briefcase,
  Star,
  BookOpen,
  Target,
  CheckCircle,
  Award,
  Sparkles,
  ChevronRight,
  Calendar,
  Clock,
  AlertCircle,
  DollarSign,
  BarChart3,
  Download,
  X,
  Loader2,
  RefreshCw,
  Code,
  Trophy
} from 'lucide-react';

// =============================================
// INTERFACES
// =============================================

interface InferredInterest {
  domain: string;
  confidence: number;
  keywords: string[];
  relatedSkills: string[];
  careerPaths: string[];
  industryRelevance: number;
}

interface ElectiveRecommendation {
  elective: string;
  match_score: number;
  reasons: string[];
  skills_to_gain: string[];
  career_relevance: string;
  difficulty_level: string;
  ml_recommended?: boolean;
}

interface HonoursRecommendation {
  program: string;
  type: string;
  match_score: number;
  reasons: string[];
  courses: string[];
  career_paths: string[];
  semester_commitment: string;
  credits: number;
  eligibility_met: boolean;
}

interface CareerPath {
  title: string;
  match_score: number;
  required_skills: string[];
  salary_range: string;
  market_demand: string;
  growth_potential: string;
}

interface SkillGapAnalysis {
  current_skills: string[];
  skill_gaps: string[];
  priority_skills: string[];
  learning_resources: Record<string, string[]>;
  estimated_learning_time: string;
}

interface NextStep {
  category: string;
  action: string;
  deadline: string;
  priority: string;
  details: string;
}

interface ComprehensiveAnalysis {
  inferred_interests: InferredInterest[];
  elective_recommendations: ElectiveRecommendation[];
  honours_minor_recommendations: HonoursRecommendation[];
  career_paths: CareerPath[];
  skill_gap_analysis: SkillGapAnalysis;
  next_steps: NextStep[];
}

interface ProjectAnalysisResultsProps {
  analysis: ComprehensiveAnalysis;
  onClose: () => void;
  studentBranch: string;
  studentSemester: number;
}

type ActiveSection = 
  | 'interests' 
  | 'electives' 
  | 'honours' 
  | 'careers' 
  | 'skills' 
  | 'nextsteps';

// =============================================
// COMPONENT
// =============================================

export const ProjectAnalysisResults: React.FC<ProjectAnalysisResultsProps> = ({
  analysis,
  onClose,
  studentBranch,
  studentSemester
}) => {
  const [activeSection, setActiveSection] = useState<ActiveSection>('interests');
  const isClosingRef = useRef(false);

  // =============================================
  // BODY SCROLL LOCK
  // =============================================
  
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  // =============================================
  // ESCAPE KEY HANDLER
  // =============================================
  
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      }
    };
    
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);

  // =============================================
  // CLOSE HANDLER
  // =============================================
  
  const handleClose = useCallback(() => {
    if (isClosingRef.current) return;
    isClosingRef.current = true;
    onClose();
  }, [onClose]);

  // =============================================
  // STOP EVENT PROPAGATION
  // =============================================
  
  const stopPropagation = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  // =============================================
  // DOWNLOAD ANALYSIS
  // =============================================
  
  const downloadAnalysis = () => {
    const dataStr = JSON.stringify(analysis, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', `analysis_${Date.now()}.json`);
    link.click();
  };

  // =============================================
  // EXTRACT DATA
  // =============================================
  
  const inferredInterests = analysis?.inferred_interests || [];
  const electiveRecommendations = analysis?.elective_recommendations || [];
  const honoursRecommendations = analysis?.honours_minor_recommendations || [];
  const careerPaths = analysis?.career_paths || [];
  const skillGapAnalysis = analysis?.skill_gap_analysis;
  const nextSteps = analysis?.next_steps || [];

  // =============================================
  // TABS CONFIG
  // =============================================
  
  const tabs = [
    { id: 'interests' as const, label: 'AI Interests', icon: Brain, count: inferredInterests.length },
    { id: 'electives' as const, label: 'Electives', icon: BookOpen, count: electiveRecommendations.length },
    { id: 'honours' as const, label: 'Honours/Minor', icon: Award, count: honoursRecommendations.length },
    { id: 'careers' as const, label: 'Careers', icon: Briefcase, count: careerPaths.length },
    { id: 'skills' as const, label: 'Skills', icon: Target },
    { id: 'nextsteps' as const, label: 'Next Steps', icon: ChevronRight, count: nextSteps.length },
  ];

  // =============================================
  // RENDER
  // =============================================

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
      onClick={stopPropagation}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />
      
      {/* Modal Container */}
      <div className="relative w-full max-w-6xl max-h-[90vh] overflow-hidden">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="bg-white rounded-2xl shadow-2xl flex flex-col max-h-[90vh]"
          onClick={stopPropagation}
        >
          
          {/* ===== HEADER ===== */}
          <div className="flex-shrink-0 p-6 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-t-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">
                  🎯 AI-Powered Academic Analysis Complete!
                </h2>
                <p className="text-purple-100">
                  Your personalized roadmap to academic and career success
                </p>
                <div className="flex items-center gap-3 mt-3">
                  <span className="text-sm bg-white/20 px-3 py-1 rounded-full">
                    {studentBranch} • Semester {studentSemester}
                  </span>
                </div>
              </div>
              
              {/* Close Button */}
              <button
                onClick={handleClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                type="button"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* ===== TABS ===== */}
          <div className="flex-shrink-0 border-b bg-gray-50 overflow-x-auto">
            <div className="flex">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-3 font-medium whitespace-nowrap transition-all
                    ${activeSection === tab.id 
                      ? 'text-purple-600 border-b-2 border-purple-600 bg-white' 
                      : 'text-gray-600 hover:text-gray-800 hover:bg-white/50'
                    }
                  `}
                  type="button"
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && tab.count > 0 && (
                    <span className="ml-1 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* ===== CONTENT ===== */}
          <div className="flex-1 overflow-y-auto p-6">
            
            {/* INTERESTS SECTION */}
            {activeSection === 'interests' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Discovered Interests & Domains</h3>
                
                {inferredInterests.length > 0 ? (
                  inferredInterests.map((interest, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 border rounded-xl hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <h4 className="font-semibold text-lg">{interest.domain}</h4>
                          <div className="flex items-center gap-3 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <TrendingUp className="w-4 h-4 text-green-500" />
                              {Math.round(interest.confidence * 100)}% Match
                            </span>
                            <span className="flex items-center gap-1">
                              <Briefcase className="w-4 h-4 text-blue-500" />
                              {Math.round(interest.industryRelevance * 100)}% Industry
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {interest.keywords?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">KEY AREAS</p>
                          <div className="flex flex-wrap gap-1">
                            {interest.keywords.slice(0, 5).map((kw, i) => (
                              <span key={i} className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                                {kw}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {interest.relatedSkills?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">SKILLS TO DEVELOP</p>
                          <div className="flex flex-wrap gap-1">
                            {interest.relatedSkills.slice(0, 4).map((skill, i) => (
                              <span key={i} className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {interest.careerPaths?.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 mb-1">CAREER PATHS</p>
                          <div className="flex flex-wrap gap-1">
                            {interest.careerPaths.slice(0, 3).map((career, i) => (
                              <span key={i} className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs flex items-center">
                                <Star className="w-3 h-3 mr-1" />
                                {career}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p className="text-lg">No interests detected yet.</p>
                    <p className="text-sm mt-2">Upload more projects to get AI-powered insights.</p>
                  </div>
                )}
              </div>
            )}

            {/* ELECTIVES SECTION */}
            {activeSection === 'electives' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">
                  Recommended Electives for Semester {studentSemester + 1}
                </h3>
                
                {electiveRecommendations.length > 0 ? (
                  electiveRecommendations.map((elective, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`p-4 border rounded-xl hover:shadow-lg transition-all ${
                        elective.ml_recommended ? 'border-purple-300 bg-purple-50/50' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-lg">{elective.elective}</h4>
                            {elective.ml_recommended && (
                              <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-bold flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                ML
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-sm text-green-600 font-medium">
                              {elective.match_score}% Match
                            </span>
                            <span className="text-sm px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                              {elective.difficulty_level}
                            </span>
                          </div>
                        </div>
                      </div>

                      {elective.reasons?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">WHY THIS ELECTIVE?</p>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {elective.reasons.map((reason, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {elective.skills_to_gain?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">SKILLS YOU'LL GAIN</p>
                          <div className="flex flex-wrap gap-1">
                            {elective.skills_to_gain.map((skill, i) => (
                              <span key={i} className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {elective.career_relevance && (
                        <div className="pt-3 border-t">
                          <p className="text-sm text-gray-600">
                            <strong>Career:</strong> {elective.career_relevance}
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <BookOpen className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p>No elective recommendations available.</p>
                  </div>
                )}
              </div>
            )}

            {/* HONOURS SECTION */}
            {activeSection === 'honours' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Honours & Minor Recommendations</h3>
                
                {honoursRecommendations.length > 0 ? (
                  honoursRecommendations.map((item, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 border rounded-xl bg-gradient-to-r from-yellow-50 to-orange-50 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <Award className="w-5 h-5 text-orange-600" />
                            <h4 className="font-semibold text-lg">{item.program}</h4>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{item.type}</p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-sm text-green-600 font-medium">
                              {item.match_score}% Match
                            </span>
                            <span className="text-sm px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                              {item.credits} Credits
                            </span>
                          </div>
                        </div>
                        <Trophy className="w-6 h-6 text-orange-500" />
                      </div>

                      {item.reasons?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">WHY THIS PROGRAM?</p>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {item.reasons.map((reason, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {item.courses?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">COURSES</p>
                          <div className="flex flex-wrap gap-1">
                            {item.courses.map((course, i) => (
                              <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                {course}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {item.career_paths?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">CAREER OUTCOMES</p>
                          <div className="flex flex-wrap gap-1">
                            {item.career_paths.map((career, i) => (
                              <span key={i} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs flex items-center">
                                <Briefcase className="w-3 h-3 mr-1" />
                                {career}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="pt-3 border-t flex justify-between text-sm">
                        <span>
                          <strong>Duration:</strong> {item.semester_commitment}
                        </span>
                        <span className={item.eligibility_met ? 'text-green-600' : 'text-red-600'}>
                          {item.eligibility_met ? '✓ Eligible' : '✗ Not Eligible'}
                        </span>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Award className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p>No honours/minor recommendations available.</p>
                  </div>
                )}
              </div>
            )}

            {/* CAREERS SECTION */}
            {activeSection === 'careers' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Career Path Recommendations</h3>
                
                {careerPaths.length > 0 ? (
                  careerPaths.map((career, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 border rounded-xl hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-lg">{career.title}</h4>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-sm text-green-600 font-medium">
                              {career.match_score}% Match
                            </span>
                            <span className="flex items-center gap-1 text-sm text-gray-600">
                              <DollarSign className="w-4 h-4 text-green-500" />
                              {career.salary_range}
                            </span>
                          </div>
                        </div>
                        <Briefcase className="w-6 h-6 text-blue-500" />
                      </div>

                      {career.required_skills?.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-500 mb-1">REQUIRED SKILLS</p>
                          <div className="flex flex-wrap gap-1">
                            {career.required_skills.map((skill, i) => (
                              <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="pt-3 border-t grid grid-cols-2 gap-4">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-blue-500" />
                          <div>
                            <p className="text-xs text-gray-500">Demand</p>
                            <p className="text-sm font-medium">{career.market_demand}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <BarChart3 className="w-4 h-4 text-green-500" />
                          <div>
                            <p className="text-xs text-gray-500">Growth</p>
                            <p className="text-sm font-medium">{career.growth_potential}</p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Briefcase className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p>No career recommendations available.</p>
                  </div>
                )}
              </div>
            )}

            {/* SKILLS SECTION */}
            {activeSection === 'skills' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Skill Gap Analysis</h3>
                
                {skillGapAnalysis ? (
                  <div className="space-y-4">
                    {skillGapAnalysis.current_skills?.length > 0 && (
                      <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-3">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <h4 className="font-semibold">Your Current Skills</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {skillGapAnalysis.current_skills.map((skill, i) => (
                            <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                              ✓ {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {skillGapAnalysis.skill_gaps?.length > 0 && (
                      <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <div className="flex items-center gap-2 mb-3">
                          <AlertCircle className="w-5 h-5 text-orange-600" />
                          <h4 className="font-semibold">Skills to Develop</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {skillGapAnalysis.skill_gaps.map((skill, i) => (
                            <span key={i} className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {skillGapAnalysis.priority_skills?.length > 0 && (
                      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex items-center gap-2 mb-3">
                          <Star className="w-5 h-5 text-blue-600" />
                          <h4 className="font-semibold">Priority Skills to Learn</h4>
                        </div>
                        <div className="space-y-3">
                          {skillGapAnalysis.priority_skills.map((skill, i) => (
                            <div key={i} className="p-3 bg-white rounded-lg">
                              <span className="font-medium">{skill}</span>
                              {skillGapAnalysis.learning_resources?.[skill] && (
                                <div className="mt-2">
                                  <p className="text-xs text-gray-500 mb-1">Resources:</p>
                                  <div className="flex flex-wrap gap-1">
                                    {skillGapAnalysis.learning_resources[skill].map((resource, ri) => (
                                      <span key={ri} className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-xs">
                                        {resource}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {skillGapAnalysis.estimated_learning_time && (
                      <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                        <div className="flex items-center gap-2">
                          <Clock className="w-5 h-5 text-purple-600" />
                          <div>
                            <h4 className="font-semibold">Estimated Learning Time</h4>
                            <p className="text-sm text-gray-600">{skillGapAnalysis.estimated_learning_time}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Target className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p>No skill gap analysis available.</p>
                  </div>
                )}
              </div>
            )}

            {/* NEXT STEPS SECTION */}
            {activeSection === 'nextsteps' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Your Action Plan</h3>
                
                {nextSteps.length > 0 ? (
                  <div className="space-y-3">
                    {nextSteps.map((step, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">
                                {step.category}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                step.priority === 'High' 
                                  ? 'bg-red-100 text-red-700' 
                                  : step.priority === 'Medium'
                                    ? 'bg-yellow-100 text-yellow-700'
                                    : 'bg-green-100 text-green-700'
                              }`}>
                                {step.priority} Priority
                              </span>
                            </div>
                            <h4 className="font-semibold mb-1">{step.action}</h4>
                            <p className="text-sm text-gray-600 mb-2">{step.details}</p>
                            <div className="flex items-center gap-1 text-xs text-gray-500">
                              <Calendar className="w-3 h-3" />
                              <span>{step.deadline}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <ChevronRight className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                    <p>No action steps available.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ===== FOOTER ===== */}
          <div className="flex-shrink-0 p-4 border-t bg-gray-50 rounded-b-2xl flex justify-between items-center">
            <span className="text-sm text-gray-600">
              AI Analysis • {studentBranch} • Semester {studentSemester}
            </span>
            
            <div className="flex gap-3">
              <button
                onClick={downloadAnalysis}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-white flex items-center gap-2 transition-colors"
                type="button"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              
              <button
                onClick={handleClose}
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:shadow-lg transition-shadow"
                type="button"
              >
                Close and Continue
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};