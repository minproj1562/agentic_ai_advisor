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
  ThumbsDown,
  MessageSquare,
  Loader2
} from 'lucide-react';
import { mlService, ElectiveRecommendation, HonoursRecommendation, CareerRecommendation } from '../../services/ml.service';
import toast from 'react-hot-toast';

interface FeedbackModal {
  isOpen: boolean;
  type: 'elective' | 'honours' | 'career' | null;
  itemId: string | null;
  itemName: string;
}

export const MLRecommendations: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [electives, setElectives] = useState<ElectiveRecommendation[]>([]);
  const [honours, setHonours] = useState<HonoursRecommendation[]>([]);
  const [careers, setCareers] = useState<CareerRecommendation[]>([]);
  const [activeTab, setActiveTab] = useState<'electives' | 'honours' | 'careers'>('electives');
  
  // Feedback state
  const [feedbackModal, setFeedbackModal] = useState<FeedbackModal>({
    isOpen: false,
    type: null,
    itemId: null,
    itemName: ''
  });
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackText, setFeedbackText] = useState('');

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const data = await mlService.getRecommendations();
      
      setElectives(data.electives || []);
      setHonours(data.honours || []);
      setCareers(data.careers || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      toast.error('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async () => {
    if (!feedbackModal.type || !feedbackModal.itemId) return;

    try {
      await mlService.submitRecommendationFeedback(
        feedbackModal.type,
        feedbackModal.itemId,
        feedbackRating,
        feedbackText
      );
      
      toast.success('Thank you for your feedback!');
      closeFeedbackModal();
      
      // Refresh recommendations
      await fetchRecommendations();
    } catch (error) {
      toast.error('Failed to submit feedback');
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

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-3">Analyzing your profile for recommendations...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 via-pink-500 to-blue-600 rounded-xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Brain className="w-7 h-7" />
          AI-Powered Recommendations
        </h2>
        <p className="text-purple-100">
          Personalized suggestions based on your interests, academic performance, and project portfolio
        </p>
        <div className="mt-4 flex gap-4">
          <div className="bg-white/20 rounded-lg px-3 py-1">
            <span className="text-xs">ML Models Used:</span>
            <span className="ml-2 font-semibold">Sentence Transformers + KNN + Logistic Regression</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border p-2">
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('electives')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'electives'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Electives ({electives.length})
          </button>
          <button
            onClick={() => setActiveTab('honours')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'honours'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Award className="w-4 h-4" />
            Honours/Minors ({honours.length})
          </button>
          <button
            onClick={() => setActiveTab('careers')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
              activeTab === 'careers'
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Target className="w-4 h-4" />
            Career Paths ({careers.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {/* Electives Tab */}
        {activeTab === 'electives' && (
          <motion.div
            key="electives"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {electives.map((elective, index) => (
              <motion.div
                key={elective.elective_code}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold">{elective.elective_name}</h3>
                      <span className="text-sm text-gray-500">({elective.elective_code})</span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                        {elective.credits} Credits
                      </span>
                    </div>
                    
                    {/* Match Score Visual */}
                    <div className="mb-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 max-w-xs">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Match Score</span>
                            <span className="font-bold">{elective.match_score}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${elective.match_score}%` }}
                              transition={{ duration: 1, delay: index * 0.1 }}
                              className={`h-2 rounded-full bg-gradient-to-r ${
                                elective.match_score >= 80
                                  ? 'from-green-400 to-green-600'
                                  : elective.match_score >= 60
                                  ? 'from-blue-400 to-blue-600'
                                  : 'from-yellow-400 to-yellow-600'
                              }`}
                            />
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getMatchColor(elective.match_score)}`}>
                          {getMatchLabel(elective.match_score)}
                        </span>
                      </div>
                    </div>

                    {/* Explanation */}
                    <div className="bg-gray-50 rounded-lg p-3 mb-3">
                      <p className="text-sm text-gray-700">{elective.match_explanation}</p>
                    </div>

                    {/* Recommendation Basis */}
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <div className="text-center">
                        <p className="text-xs text-gray-500">Interest Match</p>
                        <p className="font-bold text-purple-600">
                          {Math.round(elective.recommendation_basis.interests_weight)}%
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-500">Performance Match</p>
                        <p className="font-bold text-blue-600">
                          {Math.round(elective.recommendation_basis.performance_weight)}%
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-500">Project Match</p>
                        <p className="font-bold text-green-600">
                          {Math.round(elective.recommendation_basis.projects_weight)}%
                        </p>
                      </div>
                    </div>

                    {/* Skills & Career */}
                    <div className="flex gap-4">
                      {elective.skill_alignment.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-gray-500 mb-1">Skills Aligned:</p>
                          <div className="flex flex-wrap gap-1">
                            {elective.skill_alignment.map((skill) => (
                              <span key={skill} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {elective.career_relevance.length > 0 && (
                        <div className="flex-1">
                          <p className="text-xs text-gray-500 mb-1">Career Paths:</p>
                          <div className="flex flex-wrap gap-1">
                            {elective.career_relevance.map((career) => (
                              <span key={career} className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs">
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
                      onClick={() => openFeedbackModal('elective', elective.elective_code, elective.elective_name)}
                      className="p-2 hover:bg-gray-100 rounded-lg transition"
                      title="Give Feedback"
                    >
                      <MessageSquare className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* Similar structure for Honours and Careers tabs... */}
      </AnimatePresence>

      {/* Feedback Modal */}
      <AnimatePresence>
        {feedbackModal.isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={closeFeedbackModal}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="bg-white rounded-xl p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4">
                Feedback for {feedbackModal.itemName}
              </h3>
              
              {/* Rating */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">How accurate was this recommendation?</p>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setFeedbackRating(rating)}
                      className={`p-2 rounded-lg transition ${
                        feedbackRating >= rating
                          ? 'bg-yellow-400 text-white'
                          : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      <Star className="w-5 h-5" fill={feedbackRating >= rating ? 'currentColor' : 'none'} />
                    </button>
                  ))}
                </div>
              </div>

              {/* Feedback Text */}
              <textarea
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                placeholder="Additional comments (optional)"
                className="w-full px-3 py-2 border rounded-lg mb-4"
                rows={3}
              />

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={submitFeedback}
                  className="flex-1 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:shadow-lg transition"
                >
                  Submit Feedback
                </button>
                <button
                  onClick={closeFeedbackModal}
                  className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};