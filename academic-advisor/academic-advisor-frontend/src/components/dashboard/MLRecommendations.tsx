// src/components/dashboard/MLRecommendations.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  TrendingUp,
  Award,
  ChevronRight,
  Info,
  Star,
  Target,
  Brain,
  ThumbsUp,
  MessageSquare,
  Loader2,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Briefcase,
  GraduationCap,
  Code,
  Building,
  DollarSign,
  BookOpen,
  Zap,
  BarChart3,
  ArrowUpRight,
  Lightbulb,
  Trophy,
  X,
} from 'lucide-react';
import { 
  mlService, 
  ElectiveRecommendation, 
  HonoursRecommendation, 
  CareerRecommendation,
  CumulativeRecommendationResponse,
  ScoreBreakdown,
  RankingExplanation,
  ConfidenceMetrics  
} from '../../services/ml.service';
import toast from 'react-hot-toast';

// ==================== SCORE BREAKDOWN VISUAL COMPONENT ====================

interface ScoreBreakdownVisualizerProps {
  breakdown: ScoreBreakdown;
  matchScore: number;
}

const ScoreBreakdownVisualizer: React.FC<ScoreBreakdownVisualizerProps> = ({ breakdown, matchScore }) => {
  const { academic_component, interest_component, project_component } = breakdown;
  
  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl p-5 border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-800 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          Score Breakdown
        </h4>
        <div className="text-right">
          <span className="text-2xl font-bold text-purple-600">{matchScore.toFixed(1)}%</span>
          <p className="text-xs text-gray-500">Cumulative Score</p>
        </div>
      </div>
      
      {/* Visual Bars */}
      <div className="space-y-4">
        {/* Academic Component */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-sm font-medium text-gray-700">Academic Performance</span>
              <span className="text-xs text-gray-400">(40% weight)</span>
            </div>
            <span className="text-sm font-bold text-blue-600">
              {academic_component.score.toFixed(1)}/{academic_component.max_possible}
            </span>
          </div>
          <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${academic_component.percentage}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="absolute h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full"
            />
            <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white mix-blend-difference">
              {academic_component.percentage.toFixed(0)}%
            </span>
          </div>
          {/* Contributing Subjects */}
          {academic_component.contributing_subjects && academic_component.contributing_subjects.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {academic_component.contributing_subjects.slice(0, 4).map((subj, i) => (
                <span
                  key={i}
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    subj.status === 'strong' ? 'bg-green-100 text-green-700' :
                    subj.status === 'adequate' ? 'bg-blue-100 text-blue-700' :
                    'bg-orange-100 text-orange-700'
                  }`}
                >
                  {subj.subject}: {subj.score}%
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Interest Component */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-purple-500" />
              <span className="text-sm font-medium text-gray-700">Interest Alignment</span>
              <span className="text-xs text-gray-400">(30% weight)</span>
            </div>
            <span className="text-sm font-bold text-purple-600">
              {interest_component.score.toFixed(1)}/{interest_component.max_possible}
            </span>
          </div>
          <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${interest_component.percentage}%` }}
              transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
              className="absolute h-full bg-gradient-to-r from-purple-400 to-purple-600 rounded-full"
            />
            <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white mix-blend-difference">
              {interest_component.percentage.toFixed(0)}%
            </span>
          </div>
          {/* Matched Interests */}
          {interest_component.matched_interests && interest_component.matched_interests.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {interest_component.matched_interests.map((interest, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                  {interest.interest}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Project Component */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-sm font-medium text-gray-700">Project Portfolio</span>
              <span className="text-xs text-gray-400">(30% weight)</span>
            </div>
            <span className="text-sm font-bold text-green-600">
              {project_component.score.toFixed(1)}/{project_component.max_possible}
            </span>
          </div>
          <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${project_component.percentage}%` }}
              transition={{ duration: 1, delay: 0.4, ease: "easeOut" }}
              className="absolute h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full"
            />
            <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white mix-blend-difference">
              {project_component.percentage.toFixed(0)}%
            </span>
          </div>
          {/* Relevant Projects */}
          {project_component.relevant_projects && project_component.relevant_projects.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {project_component.relevant_projects.slice(0, 3).map((proj, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                  {proj.title} ({proj.relevance_score}%)
                </span>
              ))}
            </div>
          )}
          {project_component.missing_project_skills && project_component.missing_project_skills.length > 0 && (
            <div className="mt-2">
              <span className="text-xs text-orange-600">
                Missing: {project_component.missing_project_skills.slice(0, 3).join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Semantic Similarity */}
      {interest_component.semantic_similarity > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-gray-600">
              AI Semantic Match: <span className="font-medium text-gray-800">{(interest_component.semantic_similarity * 100).toFixed(0)}%</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// ==================== RANKING EXPLANATION COMPONENT ====================

interface RankingExplanationCardProps {
  explanation: RankingExplanation;
}

const RankingExplanationCard: React.FC<RankingExplanationCardProps> = ({ explanation }) => {
  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-200">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
            explanation.rank === 1 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
            explanation.rank === 2 ? 'bg-gradient-to-br from-gray-400 to-gray-600' :
            'bg-gradient-to-br from-orange-400 to-orange-600'
          }`}>
            #{explanation.rank}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-800">
              Ranked #{explanation.rank} of {explanation.total_options}
            </p>
            <p className="text-xs text-gray-500">{explanation.why_this_rank}</p>
          </div>
        </div>
        {explanation.rank === 1 && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium flex items-center gap-1">
            <Trophy className="w-3 h-3" />
            Top Pick
          </span>
        )}
      </div>

      {/* Comparison */}
      {explanation.vs_other_electives && explanation.vs_other_electives.length > 0 && (
        <div className="mb-3">
          {explanation.vs_other_electives.map((comp, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <ArrowUpRight className={`w-4 h-4 ${comp.score_difference > 0 ? 'text-green-500' : 'text-red-500'}`} />
              <span className="text-gray-600">{comp.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Improvement Tips */}
      {explanation.improvement_tips && explanation.improvement_tips.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">How to Improve</p>
          {explanation.improvement_tips.slice(0, 2).map((tip, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-gray-700">
              <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
              <span>{tip}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ==================== CONFIDENCE INDICATOR ====================

interface ConfidenceIndicatorProps {
  confidence: ConfidenceMetrics;
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({ confidence }) => {
  const getConfidenceColor = (value: number) => {
    if (value >= 0.8) return 'text-green-600 bg-green-100';
    if (value >= 0.6) return 'text-blue-600 bg-blue-100';
    if (value >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mb-4">
      <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${getConfidenceColor(confidence.overall)}`}>
        {(confidence.overall * 100).toFixed(0)}% Confidence
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className={confidence.factors.has_marks ? 'text-green-500' : 'text-gray-300'}>
          {confidence.factors.has_marks ? '✓' : '○'} Marks ({confidence.factors.marks_count})
        </span>
        <span className={confidence.factors.has_interests ? 'text-green-500' : 'text-gray-300'}>
          {confidence.factors.has_interests ? '✓' : '○'} Interests ({confidence.factors.interest_count})
        </span>
        <span className={confidence.factors.has_projects ? 'text-green-500' : 'text-gray-300'}>
          {confidence.factors.has_projects ? '✓' : '○'} Projects ({confidence.factors.project_count})
        </span>
      </div>
    </div>
  );
};

// ==================== INTERFACES ====================

interface FeedbackModal {
  isOpen: boolean;
  type: 'elective' | 'honours' | 'career' | null;
  itemId: string | null;
  itemName: string;
}

interface ModelInfo {
  models_used: string[];
  is_ml_trained: boolean;
  version: string;
  cached?: boolean;
  cached_at?: string;
}

// ==================== MAIN COMPONENT ====================

export const MLRecommendations: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [electives, setElectives] = useState<ElectiveRecommendation[]>([]);
  const [openElectives, setOpenElectives] = useState<ElectiveRecommendation[]>([]);
  const [honours, setHonours] = useState<HonoursRecommendation[]>([]);
  const [careers, setCareers] = useState<CareerRecommendation[]>([]);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [computationTime, setComputationTime] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'electives' | 'open_electives' | 'honours' | 'careers'>('electives');
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  
  // Feedback state
  const [feedbackModal, setFeedbackModal] = useState<FeedbackModal>({
    isOpen: false,
    type: null,
    itemId: null,
    itemName: ''
  });
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackText, setFeedbackText] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Roadmap state
  const [roadmapModal, setRoadmapModal] = useState<{
    isOpen: boolean;
    data: any;
    loading: boolean;
    electiveName: string;
  }>({ isOpen: false, data: null, loading: false, electiveName: '' });
  const [chosenElective, setChosenElective] = useState<string | null>(
    localStorage.getItem('chosen_elective') || null
  );

  // ── Handle Choose Elective ──
  const handleChooseElective = async (code: string, name: string, isOE: boolean = false) => {
    try {
      const semester = parseInt(localStorage.getItem('userSemester') || '5');
      await mlService.recordElectiveChoice(code, name, isOE, semester);
      setChosenElective(code);
      localStorage.setItem('chosen_elective', code);
      alert(`✅ Your choice of "${name}" has been recorded! This will help improve future recommendations.`);
    } catch (error) {
      console.error('Failed to record choice:', error);
      alert('Failed to record your choice. Please try again.');
    }
  };

  // ── Handle View Roadmap ──
  const handleViewRoadmap = async (code: string, name: string, isOE: boolean = false) => {
    setRoadmapModal({ isOpen: true, data: null, loading: true, electiveName: name });
    try {
      const data = await mlService.getImprovementRoadmap(code, isOE);
      setRoadmapModal({ isOpen: true, data, loading: false, electiveName: name });
    } catch (error: any) {
      console.error('Failed to get roadmap:', error);
      // Show error in the modal instead of closing it
      setRoadmapModal({
        isOpen: true,
        data: { error: true, message: error?.response?.data?.detail || 'Failed to load roadmap. Please try again.' },
        loading: false,
        electiveName: name
      });
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async (forceRefresh: boolean = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      
      const data: CumulativeRecommendationResponse = await mlService.getRecommendations(
        true,
        true,
        true,
        forceRefresh
      );
      
      setElectives(data.electives || []);
      setOpenElectives(data.open_electives || []);
      setHonours(data.honours || []);
      setCareers(data.careers || []);
      setModelInfo(data.model_info || null);
      setComputationTime(data.computation_time_ms || 0);
      
      if (forceRefresh) {
        toast.success('Recommendations refreshed!');
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      toast.error('Failed to load recommendations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchRecommendations(true);
  };

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const submitFeedback = async () => {
    if (!feedbackModal.type || !feedbackModal.itemId) return;

    try {
      setSubmittingFeedback(true);
      await mlService.submitRecommendationFeedback(
        feedbackModal.type,
        feedbackModal.itemId,
        feedbackRating,
        feedbackText
      );
      
      toast.success('Thank you for your feedback! This helps improve recommendations.');
      closeFeedbackModal();
      
      await fetchRecommendations(true);
    } catch (error) {
      toast.error('Failed to submit feedback');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const openFeedbackModal = (type: 'elective' | 'honours' | 'career', itemId: string, itemName: string) => {
    setFeedbackModal({ isOpen: true, type, itemId, itemName });
    setFeedbackRating(3);
    setFeedbackText('');
  };

  const closeFeedbackModal = () => {
    setFeedbackModal({ isOpen: false, type: null, itemId: null, itemName: '' });
  };

  const getMatchColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getMatchLabel = (score: number) => {
    if (score >= 80) return 'Excellent Match';
    if (score >= 60) return 'Good Match';
    if (score >= 40) return 'Fair Match';
    return 'Consider Exploring';
  };

  const getMatchGradient = (score: number) => {
    if (score >= 80) return 'from-green-400 to-green-600';
    if (score >= 60) return 'from-blue-400 to-blue-600';
    if (score >= 40) return 'from-yellow-400 to-yellow-600';
    return 'from-gray-400 to-gray-600';
  };

  const getEligibilityColor = (eligible: boolean) => {
    return eligible 
      ? 'text-green-600 bg-green-50 border-green-200' 
      : 'text-red-600 bg-red-50 border-red-200';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl shadow-sm border">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-purple-200 rounded-full"></div>
          <div className="absolute top-0 left-0 w-16 h-16 border-4 border-purple-600 rounded-full border-t-transparent animate-spin"></div>
        </div>
        <p className="mt-4 text-lg font-medium text-gray-700">Analyzing your profile...</p>
        <p className="text-sm text-gray-500">Combining marks, interests & projects</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
              <Brain className="w-7 h-7" />
              AI-Powered Recommendations
            </h2>
            <p className="text-purple-100 max-w-2xl">
              Personalized suggestions based on your academic performance (40%), 
              declared interests (30%), and project portfolio (30%)
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors disabled:opacity-50"
            title="Refresh Recommendations"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        
        {/* Model Info */}
        <div className="mt-4 flex flex-wrap gap-3">
          {modelInfo && (
            <>
              <div className="bg-white/20 rounded-lg px-3 py-1.5 text-sm">
                <span className="opacity-80">Models:</span>
                <span className="ml-2 font-semibold">
                  {modelInfo.models_used.join(' + ')}
                </span>
              </div>
              <div className="bg-white/20 rounded-lg px-3 py-1.5 text-sm">
                <span className="opacity-80">ML Trained:</span>
                <span className="ml-2 font-semibold">
                  {modelInfo.is_ml_trained ? '✓ Yes' : '○ Rule-Based'}
                </span>
              </div>
              {computationTime > 0 && (
                <div className="bg-white/20 rounded-lg px-3 py-1.5 text-sm">
                  <span className="opacity-80">Computed in:</span>
                  <span className="ml-2 font-semibold">{computationTime.toFixed(0)}ms</span>
                </div>
              )}
              {modelInfo.cached && (
                <div className="bg-yellow-400/30 rounded-lg px-3 py-1.5 text-sm">
                  <span>📦 Cached result</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border p-2">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('electives')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'electives'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Program ({electives.length})
          </button>
          <button
            onClick={() => setActiveTab('open_electives')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'open_electives'
                ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            Open Electives ({openElectives.length})
          </button>
          <button
            onClick={() => setActiveTab('honours')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'honours'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Award className="w-4 h-4" />
            Honours ({honours.length})
          </button>
          <button
            onClick={() => setActiveTab('careers')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'careers'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Target className="w-4 h-4" />
            Careers ({careers.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {/* ==================== ELECTIVES TAB ==================== */}
        {activeTab === 'electives' && (
          <motion.div
            key="electives"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {electives.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
                <Sparkles className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Elective Recommendations</h3>
                <p className="text-gray-500">
                  Add your academic data, interests, and projects to get personalized recommendations.
                </p>
              </div>
            ) : (
              electives.map((elective, index) => (
                <motion.div
                  key={elective.elective_code}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">{elective.elective_name}</h3>
                        <span className="text-sm text-gray-500 font-mono">({elective.elective_code})</span>
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                          {elective.credits} Credits
                        </span>
                        {elective.pair && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                            {elective.pair}
                          </span>
                        )}
                      </div>

                      {/* Confidence Indicator */}
                      {elective.confidence && (
                        <ConfidenceIndicator confidence={elective.confidence} />
                      )}

                      {/* Score Breakdown Visualizer */}
                      {elective.score_breakdown && (
                        <div className="my-4">
                          <ScoreBreakdownVisualizer 
                            breakdown={elective.score_breakdown} 
                            matchScore={elective.match_score}
                          />
                        </div>
                      )}

                      {/* Ranking Explanation */}
                      {elective.ranking_explanation && (
                        <div className="my-4">
                          <RankingExplanationCard explanation={elective.ranking_explanation} />
                        </div>
                      )}

                      {/* Legacy Match Bar (fallback if no breakdown) */}
                      {!elective.score_breakdown && (
                        <div className="mb-4">
                          <div className="flex items-center gap-4">
                            <div className="flex-1 max-w-sm">
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Match Score</span>
                                <span className="font-bold text-gray-900">{elective.match_score.toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${elective.match_score}%` }}
                                  transition={{ duration: 1, delay: index * 0.1 }}
                                  className={`h-full rounded-full bg-gradient-to-r ${getMatchGradient(elective.match_score)}`}
                                />
                              </div>
                            </div>
                            <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getMatchColor(elective.match_score)}`}>
                              {getMatchLabel(elective.match_score)}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Explanation (shown if no detailed breakdown) */}
                      {!elective.score_breakdown && elective.match_explanation && (
                        <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-4 mb-4">
                          <div className="flex items-start gap-2">
                            <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-gray-700 whitespace-pre-line">{elective.match_explanation}</p>
                          </div>
                        </div>
                      )}

                      {/* Skills & Career */}
                      <div className="grid grid-cols-2 gap-4">
                        {elective.skill_alignment && elective.skill_alignment.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Skills You'll Gain
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {elective.skill_alignment.map((skill) => (
                                <span key={skill} className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md text-xs font-medium">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {elective.career_relevance && elective.career_relevance.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Career Paths
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {elective.career_relevance.map((career) => (
                                <span key={career} className="px-2.5 py-1 bg-green-50 text-green-700 rounded-md text-xs font-medium">
                                  {career}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Skill Gaps */}
                      {elective.skill_gaps && elective.skill_gaps.length > 0 && (
                        <div className="mt-4 pt-4 border-t">
                          <button
                            onClick={() => toggleExpand(elective.elective_code)}
                            className="flex items-center gap-2 text-sm text-orange-600 hover:text-orange-700"
                          >
                            <AlertTriangle className="w-4 h-4" />
                            <span>{elective.skill_gaps.length} areas to improve</span>
                            <ChevronRight className={`w-4 h-4 transition-transform ${
                              expandedItems.has(elective.elective_code) ? 'rotate-90' : ''
                            }`} />
                          </button>
                          
                          <AnimatePresence>
                            {expandedItems.has(elective.elective_code) && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                              >
                                <div className="mt-3 space-y-2">
                                  {elective.skill_gaps.map((gap, i) => (
                                    <div key={i} className="bg-orange-50 rounded-lg p-3">
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="font-medium text-gray-800">{gap.subject}</span>
                                        <span className={`text-xs px-2 py-0.5 rounded ${
                                          gap.importance === 'High' 
                                            ? 'bg-red-100 text-red-700' 
                                            : gap.importance === 'Medium'
                                            ? 'bg-yellow-100 text-yellow-700'
                                            : 'bg-gray-100 text-gray-700'
                                        }`}>
                                          {gap.importance} Priority
                                        </span>
                                      </div>
                                      <div className="flex items-center gap-2 text-sm">
                                        <span className="text-gray-600">Current: {gap.current_score}%</span>
                                        <span className="text-gray-400">→</span>
                                        <span className="text-green-600">Target: {gap.target_score}%</span>
                                        <span className="text-orange-600 font-medium">
                                          (Gap: {gap.gap} marks)
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 ml-4">
                      <button
                        onClick={() => handleChooseElective(elective.elective_code, elective.elective_name, false)}
                        disabled={chosenElective === elective.elective_code}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          chosenElective === elective.elective_code
                            ? 'bg-green-100 text-green-700 cursor-default'
                            : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        }`}
                        title={chosenElective === elective.elective_code ? 'Already chosen' : 'Record this as your choice'}
                      >
                        {chosenElective === elective.elective_code ? '✓ Chosen' : 'Choose This'}
                      </button>
                      {/* <button
                        onClick={() => handleViewRoadmap(elective.elective_code, elective.elective_name, false)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-orange-100 text-orange-700 hover:bg-orange-200 transition"
                        title="View improvement roadmap"
                      >
                        📋 Roadmap
                      </button> */}
                      <button
                        onClick={() => openFeedbackModal('elective', elective.elective_code, elective.elective_name)}
                        className="p-2 hover:bg-purple-50 rounded-lg transition text-gray-500 hover:text-purple-600"
                        title="Give Feedback"
                      >
                        <MessageSquare className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* ==================== OPEN ELECTIVES TAB ==================== */}
        {activeTab === 'open_electives' && (
          <motion.div
            key="open_electives"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {openElectives.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
                <BookOpen className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Open Elective Recommendations</h3>
                <p className="text-gray-500">
                  Open electives are typically offered in Semester 7. Add your academic data to get personalized recommendations.
                </p>
              </div>
            ) : (
              openElectives.map((elective, index) => (
                <motion.div
                  key={elective.elective_code}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold text-gray-900">{elective.elective_name}</h3>
                        <span className="text-sm text-gray-500 font-mono">({elective.elective_code})</span>
                        <span className="px-2 py-1 bg-teal-100 text-teal-700 rounded-full text-xs font-medium">
                          {elective.credits} Credits
                        </span>
                        <span className="px-2 py-1 bg-cyan-100 text-cyan-700 rounded-full text-xs font-medium">
                          Open Elective
                        </span>
                      </div>

                      {/* Confidence Indicator */}
                      {elective.confidence && (
                        <ConfidenceIndicator confidence={elective.confidence} />
                      )}

                      {/* Score Breakdown Visualizer */}
                      {elective.score_breakdown && (
                        <div className="my-4">
                          <ScoreBreakdownVisualizer 
                            breakdown={elective.score_breakdown} 
                            matchScore={elective.match_score}
                          />
                        </div>
                      )}

                      {/* Ranking Explanation */}
                      {elective.ranking_explanation && (
                        <div className="my-4">
                          <RankingExplanationCard explanation={elective.ranking_explanation} />
                        </div>
                      )}

                      {/* Match Bar (fallback) */}
                      {!elective.score_breakdown && (
                        <div className="mb-4">
                          <div className="flex items-center gap-4">
                            <div className="flex-1 max-w-sm">
                              <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-600">Match Score</span>
                                <span className="font-bold text-gray-900">{elective.match_score.toFixed(1)}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${elective.match_score}%` }}
                                  transition={{ duration: 1, delay: index * 0.1 }}
                                  className={`h-full rounded-full bg-gradient-to-r ${getMatchGradient(elective.match_score)}`}
                                />
                              </div>
                            </div>
                            <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getMatchColor(elective.match_score)}`}>
                              {getMatchLabel(elective.match_score)}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Explanation */}
                      {!elective.score_breakdown && elective.match_explanation && (
                        <div className="bg-gradient-to-r from-teal-50 to-cyan-50 rounded-lg p-4 mb-4">
                          <div className="flex items-start gap-2">
                            <Info className="w-4 h-4 text-teal-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-gray-700 whitespace-pre-line">{elective.match_explanation}</p>
                          </div>
                        </div>
                      )}

                      {/* Skills & Career */}
                      <div className="grid grid-cols-2 gap-4">
                        {elective.skill_alignment && elective.skill_alignment.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Skills You'll Gain
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {elective.skill_alignment.map((skill) => (
                                <span key={skill} className="px-2.5 py-1 bg-teal-50 text-teal-700 rounded-md text-xs font-medium">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {elective.career_relevance && elective.career_relevance.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Career Paths
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {elective.career_relevance.map((career) => (
                                <span key={career} className="px-2.5 py-1 bg-green-50 text-green-700 rounded-md text-xs font-medium">
                                  {career}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 ml-4">
                      <button
                        onClick={() => handleChooseElective(elective.elective_code, elective.elective_name, true)}
                        disabled={chosenElective === elective.elective_code}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          chosenElective === elective.elective_code
                            ? 'bg-green-100 text-green-700 cursor-default'
                            : 'bg-teal-100 text-teal-700 hover:bg-teal-200'
                        }`}
                        title={chosenElective === elective.elective_code ? 'Already chosen' : 'Record this as your choice'}
                      >
                        {chosenElective === elective.elective_code ? '✓ Chosen' : 'Choose This'}
                      </button>
                      {/* <button
                        onClick={() => handleViewRoadmap(elective.elective_code, elective.elective_name, true)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium bg-orange-100 text-orange-700 hover:bg-orange-200 transition"
                        title="View improvement roadmap"
                      >
                        📋 Roadmap
                      </button> */}
                      <button
                        onClick={() => openFeedbackModal('elective', elective.elective_code, elective.elective_name)}
                        className="p-2 hover:bg-teal-50 rounded-lg transition text-gray-500 hover:text-teal-600"
                        title="Give Feedback"
                      >
                        <MessageSquare className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* ==================== HONOURS TAB ==================== */}
        {activeTab === 'honours' && (
          <motion.div
            key="honours"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {honours.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
                <Award className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Honours/Minor Recommendations</h3>
                <p className="text-gray-500">
                  Complete your profile to get personalized honours and minor programme suggestions.
                </p>
              </div>
            ) : (
              honours.map((program, index) => (
                <motion.div
                  key={program.program}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`p-2 rounded-lg ${
                          program.type === 'honours' 
                            ? 'bg-yellow-100' 
                            : 'bg-blue-100'
                        }`}>
                          {program.type === 'honours' ? (
                            <GraduationCap className="w-5 h-5 text-yellow-600" />
                          ) : (
                            <BookOpen className="w-5 h-5 text-blue-600" />
                          )}
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{program.program}</h3>
                          <span className={`text-xs font-medium uppercase tracking-wide ${
                            program.type === 'honours' ? 'text-yellow-600' : 'text-blue-600'
                          }`}>
                            {program.type === 'honours' ? 'Honours Programme' : 'Minor Programme'}
                          </span>
                        </div>
                      </div>
                      
                      {/* Match Score & Eligibility */}
                      <div className="flex items-center gap-4 mb-4">
                        <div className="flex-1 max-w-sm">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Match Score</span>
                            <span className="font-bold text-gray-900">{program.match_score.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${program.match_score}%` }}
                              transition={{ duration: 1, delay: index * 0.1 }}
                              className={`h-full rounded-full bg-gradient-to-r ${getMatchGradient(program.match_score)}`}
                            />
                          </div>
                        </div>
                        <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getMatchColor(program.match_score)}`}>
                          {getMatchLabel(program.match_score)}
                        </span>
                        <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${getEligibilityColor(program.eligibility)}`}>
                          {program.eligibility ? (
                            <>
                              <CheckCircle className="w-4 h-4" />
                              Eligible
                            </>
                          ) : (
                            <>
                              <XCircle className="w-4 h-4" />
                              Not Eligible
                            </>
                          )}
                        </span>
                      </div>

                      {/* CGPA Requirement */}
                      <div className="bg-gray-50 rounded-lg p-3 mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-gray-500" />
                          <span className="text-sm text-gray-600">Required CGPA:</span>
                          <span className="font-bold text-gray-900">{program.required_cgpa.toFixed(1)}</span>
                        </div>
                        {!program.eligibility && (
                          <span className="text-sm text-red-600">
                            Need {(program.required_cgpa - 7.0).toFixed(1)} more CGPA points
                          </span>
                        )}
                      </div>

                      {/* Explanation */}
                      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 mb-4">
                        <div className="flex items-start gap-2">
                          <Info className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-gray-700">{program.explanation}</p>
                        </div>
                      </div>

                      {/* Skills & Careers */}
                      <div className="grid grid-cols-2 gap-4">
                        {program.skills_gained && program.skills_gained.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Skills You'll Gain
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {program.skills_gained.map((skill) => (
                                <span key={skill} className="px-2.5 py-1 bg-purple-50 text-purple-700 rounded-md text-xs font-medium">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {program.career_paths && program.career_paths.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                              Career Opportunities
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {program.career_paths.map((career) => (
                                <span key={career} className="px-2.5 py-1 bg-green-50 text-green-700 rounded-md text-xs font-medium">
                                  {career}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 ml-4">
                      <button
                        onClick={() => openFeedbackModal('honours', program.program, program.program)}
                        className="p-2 hover:bg-purple-50 rounded-lg transition text-gray-500 hover:text-purple-600"
                        title="Give Feedback"
                      >
                        <MessageSquare className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}

        {/* ==================== CAREERS TAB ==================== */}
        {activeTab === 'careers' && (
          <motion.div
            key="careers"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {careers.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
                <Target className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Career Recommendations</h3>
                <p className="text-gray-500">
                  Add your skills, interests, and projects to get career path suggestions.
                </p>
              </div>
            ) : (
              careers.map((career, index) => (
                <motion.div
                  key={career.career}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-100 to-blue-100">
                          <Briefcase className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{career.career}</h3>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="flex items-center gap-1 text-sm text-green-600">
                              <DollarSign className="w-4 h-4" />
                              {career.salary_range}
                            </span>
                            <span className={`flex items-center gap-1 text-sm ${
                              career.growth_potential === 'Very High' || career.growth_potential === 'High'
                                ? 'text-green-600'
                                : 'text-yellow-600'
                            }`}>
                              <TrendingUp className="w-4 h-4" />
                              {career.growth_potential} Growth
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Match Score & Eligibility */}
                      <div className="flex items-center gap-4 mb-4">
                        <div className="flex-1 max-w-sm">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Match Score</span>
                            <span className="font-bold text-gray-900">{career.match_score.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${career.match_score}%` }}
                              transition={{ duration: 1, delay: index * 0.1 }}
                              className={`h-full rounded-full bg-gradient-to-r ${getMatchGradient(career.match_score)}`}
                            />
                          </div>
                        </div>
                        <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getMatchColor(career.match_score)}`}>
                          {getMatchLabel(career.match_score)}
                        </span>
                        <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${getEligibilityColor(career.cgpa_eligible)}`}>
                          {career.cgpa_eligible ? (
                            <>
                              <CheckCircle className="w-4 h-4" />
                              CGPA Eligible ({career.required_cgpa}+)
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="w-4 h-4" />
                              Need {career.required_cgpa} CGPA
                            </>
                          )}
                        </span>
                      </div>

                      {/* Top Companies */}
                      {career.top_companies && career.top_companies.length > 0 && (
                        <div className="mb-4">
                          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Building className="w-3 h-3" />
                            Top Hiring Companies
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {career.top_companies.map((company) => (
                              <span key={company} className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium">
                                {company}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Missing Skills */}
                      {career.missing_skills && career.missing_skills.length > 0 && (
                        <div className="bg-orange-50 rounded-lg p-4 mb-4">
                          <p className="text-xs text-orange-600 mb-2 font-medium uppercase tracking-wide flex items-center gap-1">
                            <Zap className="w-3 h-3" />
                            Skills to Develop
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {career.missing_skills.map((skill) => (
                              <span key={skill} className="px-2.5 py-1 bg-orange-100 text-orange-700 rounded-md text-xs font-medium">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Preparation Path */}
                      {career.preparation_path && career.preparation_path.length > 0 && (
                        <div className="mb-4">
                          <button
                            onClick={() => toggleExpand(`career-${career.career}`)}
                            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            <BookOpen className="w-4 h-4" />
                            <span>Preparation Roadmap</span>
                            <ChevronRight className={`w-4 h-4 transition-transform ${
                              expandedItems.has(`career-${career.career}`) ? 'rotate-90' : ''
                            }`} />
                          </button>
                          
                          <AnimatePresence>
                            {expandedItems.has(`career-${career.career}`) && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                              >
                                <div className="mt-3 space-y-2">
                                  {career.preparation_path.map((step, i) => (
                                    <div key={i} className="flex items-start gap-3 bg-blue-50 rounded-lg p-3">
                                      <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                                        {i + 1}
                                      </div>
                                      <span className="text-sm text-gray-700">{step}</span>
                                    </div>
                                  ))}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}

                      {/* Certifications */}
                      {career.required_certifications && career.required_certifications.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">
                            Recommended Certifications
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {career.required_certifications.map((cert) => (
                              <span key={cert} className="px-2.5 py-1 bg-purple-50 text-purple-700 rounded-md text-xs font-medium flex items-center gap-1">
                                <Award className="w-3 h-3" />
                                {cert}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 ml-4">
                      <button
                        onClick={() => openFeedbackModal('career', career.career, career.career)}
                        className="p-2 hover:bg-purple-50 rounded-lg transition text-gray-500 hover:text-purple-600"
                        title="Give Feedback"
                      >
                        <MessageSquare className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ==================== FEEDBACK MODAL ==================== */}
      <AnimatePresence>
        {feedbackModal.isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={closeFeedbackModal}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl p-6 max-w-md w-full shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <MessageSquare className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Rate This Recommendation
                  </h3>
                  <p className="text-sm text-gray-500">{feedbackModal.itemName}</p>
                </div>
              </div>
              
              {/* Rating */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">How accurate was this recommendation?</p>
                <div className="flex gap-2 justify-center">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setFeedbackRating(rating)}
                      className={`p-3 rounded-lg transition-all transform hover:scale-110 ${
                        feedbackRating >= rating
                          ? 'bg-yellow-400 text-white shadow-lg'
                          : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                      }`}
                    >
                      <Star className="w-6 h-6" fill={feedbackRating >= rating ? 'currentColor' : 'none'} />
                    </button>
                  ))}
                </div>
                <p className="text-center text-sm text-gray-500 mt-2">
                  {feedbackRating === 1 && 'Not relevant at all'}
                  {feedbackRating === 2 && 'Slightly relevant'}
                  {feedbackRating === 3 && 'Moderately relevant'}
                  {feedbackRating === 4 && 'Very relevant'}
                  {feedbackRating === 5 && 'Perfectly matched!'}
                </p>
              </div>

              {/* Feedback Text */}
              <div className="mb-4">
                <label className="block text-sm text-gray-600 mb-2">
                  Additional comments (optional)
                </label>
                <textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder="Tell us why this recommendation was or wasn't helpful..."
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                  rows={3}
                />
              </div>

              {/* Info */}
              <div className="bg-blue-50 rounded-lg p-3 mb-4">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-blue-700">
                    Your feedback helps improve our AI recommendations. 
                    High-quality feedback is used to train better models.
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={submitFeedback}
                  disabled={submittingFeedback}
                  className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {submittingFeedback ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <ThumbsUp className="w-4 h-4" />
                      Submit Feedback
                    </>
                  )}
                </button>
                <button
                  onClick={closeFeedbackModal}
                  disabled={submittingFeedback}
                  className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* ==================== ROADMAP MODAL ==================== */}
      <AnimatePresence>
        {roadmapModal.isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setRoadmapModal({ ...roadmapModal, isOpen: false })}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-orange-500 to-amber-500 text-white p-6 rounded-t-2xl">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold">📋 Improvement Roadmap</h3>
                    <p className="text-orange-100 text-sm mt-1">{roadmapModal.electiveName}</p>
                  </div>
                  <button
                    onClick={() => setRoadmapModal({ ...roadmapModal, isOpen: false })}
                    className="p-2 hover:bg-white/20 rounded-lg transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6">
                {roadmapModal.loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
                    <span className="ml-3 text-gray-600">Generating roadmap...</span>
                  </div>
                ) : roadmapModal.data?.error ? (
                  <div className="text-center py-8">
                    <AlertTriangle className="w-12 h-12 mx-auto text-orange-400 mb-4" />
                    <h4 className="font-semibold text-gray-700 mb-2">Could not load roadmap</h4>
                    <p className="text-gray-500 text-sm">{roadmapModal.data.message}</p>
                    <button
                      onClick={() => setRoadmapModal({ ...roadmapModal, isOpen: false })}
                      className="mt-4 px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition text-sm"
                    >
                      Close
                    </button>
                  </div>
                ) : roadmapModal.data ? (
                  <div className="space-y-6">
                    {/* Readiness Assessment */}
                    {roadmapModal.data.readiness && (
                    <div className="bg-gradient-to-r from-gray-50 to-orange-50 rounded-xl p-5">
                      <h4 className="font-semibold text-gray-800 mb-3">🎯 Readiness Assessment</h4>
                      <div className="flex items-center gap-4">
                        <div className="relative w-20 h-20">
                          <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="16" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                            <circle
                              cx="18" cy="18" r="16" fill="none"
                              stroke={roadmapModal.data.readiness.percentage >= 70 ? '#22c55e' : roadmapModal.data.readiness.percentage >= 50 ? '#f59e0b' : '#ef4444'}
                              strokeWidth="3" strokeDasharray={`${roadmapModal.data.readiness.percentage} 100`}
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-lg font-bold">{roadmapModal.data.readiness.percentage}%</span>
                          </div>
                        </div>
                        <div>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            roadmapModal.data.readiness.level === 'Ready' ? 'bg-green-100 text-green-700' :
                            roadmapModal.data.readiness.level === 'Moderate' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {roadmapModal.data.readiness.level}
                          </span>
                          <p className="text-sm text-gray-600 mt-2">{roadmapModal.data.readiness.message}</p>
                        </div>
                      </div>
                    </div>
                    )}

                    {/* Prerequisite Analysis */}
                    {roadmapModal.data.prerequisite_analysis?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-3">📚 Prerequisite Subjects</h4>
                        <div className="space-y-2">
                          {roadmapModal.data.prerequisite_analysis.map((prereq: any, i: number) => (
                            <div key={i} className={`rounded-lg p-3 border ${
                              prereq.status === 'strong' ? 'bg-green-50 border-green-200' :
                              prereq.status === 'needs_improvement' ? 'bg-yellow-50 border-yellow-200' :
                              'bg-red-50 border-red-200'
                            }`}>
                              <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                  <span className={`w-2 h-2 rounded-full ${
                                    prereq.status === 'strong' ? 'bg-green-500' :
                                    prereq.status === 'needs_improvement' ? 'bg-yellow-500' : 'bg-red-500'
                                  }`} />
                                  <span className="font-medium text-gray-800">{prereq.subject}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className="text-sm text-gray-600">Score: {prereq.current_score}%</span>
                                  <span className={`text-xs px-2 py-0.5 rounded ${
                                    prereq.importance === 'Critical' ? 'bg-red-100 text-red-700' :
                                    prereq.importance === 'Important' ? 'bg-orange-100 text-orange-700' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>{prereq.importance}</span>
                                </div>
                              </div>
                              {prereq.gap > 0 && (
                                <div className="mt-2">
                                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                                    <div
                                      className={`h-1.5 rounded-full ${
                                        prereq.status === 'strong' ? 'bg-green-500' :
                                        prereq.status === 'needs_improvement' ? 'bg-yellow-500' : 'bg-red-500'
                                      }`}
                                      style={{ width: `${Math.min(prereq.current_score, 100)}%` }}
                                    />
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1">Gap: {prereq.gap} marks to target ({prereq.target_score}%)</p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Study Plan */}
                    {roadmapModal.data.study_plan?.weeks?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-3">📅 {roadmapModal.data.study_plan.total_weeks}-Week Study Plan</h4>
                        <div className="space-y-3">
                          {roadmapModal.data.study_plan.weeks.map((week: any) => (
                            <div key={week.week} className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                              <h5 className="font-medium text-blue-800 mb-2">Week {week.week}</h5>
                              <div className="space-y-1">
                                {week.goals?.map((goal: string, i: number) => (
                                  <p key={i} className="text-sm text-gray-700 flex items-start gap-2">
                                    <span className="text-blue-500 mt-0.5">•</span> {goal}
                                  </p>
                                ))}
                              </div>
                              <div className="mt-2 space-y-1">
                                {week.activities?.map((activity: string, i: number) => (
                                  <p key={i} className="text-xs text-gray-500 flex items-start gap-2">
                                    <span>→</span> {activity}
                                  </p>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Skills to Gain */}
                    {roadmapModal.data.skills_to_gain?.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-2">💡 Skills You'll Gain</h4>
                        <div className="flex flex-wrap gap-2">
                          {roadmapModal.data.skills_to_gain.map((skill: string) => (
                            <span key={skill} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-xs font-medium">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No roadmap data available.</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MLRecommendations;