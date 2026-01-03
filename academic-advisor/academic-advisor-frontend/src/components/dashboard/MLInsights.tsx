// src/components/dashboard/MLInsights.tsx
import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Target,
  Briefcase,
  Clock,
  Award,
  BookOpen,
  ChevronRight,
  Info,
  Loader2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Sparkles,
  BarChart3,
  PieChart
} from 'lucide-react';
import {
  mlService,
  PredictionResponse,
  WeaknessAnalysisResponse,
  CareerPredictionResponse,
  StudentAcademicData,
  SubjectScore
} from '../../services/ml.service';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

interface MLInsightsProps {
  academicData: StudentAcademicData;
  historicalScores: Array<{ semester: number; gpa: number; credits: number }>;
  currentSemester: number;
  subjectScores: SubjectScore[];
  skills?: string[];
  interests?: string[];
  projects?: string[];
}

export const MLInsights: React.FC<MLInsightsProps> = ({
  academicData,
  historicalScores,
  currentSemester,
  subjectScores,
  skills = [],
  interests = [],
  projects = []
}) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [weaknessAnalysis, setWeaknessAnalysis] = useState<WeaknessAnalysisResponse | null>(null);
  const [careerPredictions, setCareerPredictions] = useState<CareerPredictionResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'predictions' | 'weaknesses' | 'careers'>('predictions');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.uid) {
      fetchMLInsights();
    }
  }, [user, academicData]);

  const fetchMLInsights = async () => {
    if (!user?.uid) return;

    setLoading(true);
    setError(null);

    try {
      // Fetch all ML insights in parallel
      const [predictionRes, weaknessRes, careerRes] = await Promise.all([
        mlService.getPredictions(
          user.uid,
          academicData,
          historicalScores,
          currentSemester
        ),
        subjectScores.length > 0 
          ? mlService.analyzeWeaknesses(user.uid, subjectScores, academicData.current_cgpa)
          : null,
        skills.length > 0 || interests.length > 0
          ? mlService.predictCareer(
              user.uid,
              skills,
              interests,
              academicData.current_cgpa,
              projects
            )
          : null
      ]);

      setPredictions(predictionRes);
      if (weaknessRes) setWeaknessAnalysis(weaknessRes);
      if (careerRes) setCareerPredictions(careerRes);

      // Show toast for high-risk students
      if (predictionRes.predictions.risk_level === 'High') {
        toast.error('⚠️ High academic risk detected. Please review recommendations.', {
          duration: 5000
        });
      }
    } catch (err) {
      console.error('Error fetching ML insights:', err);
      setError('Failed to fetch ML insights. Please try again.');
      toast.error('Failed to load AI insights');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'Low': return 'text-green-600 bg-green-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'High': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'declining': return <TrendingDown className="w-5 h-5 text-red-500" />;
      default: return <BarChart3 className="w-5 h-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-purple-600" />
          <p className="mt-4 text-gray-600">Analyzing your academic data with AI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <XCircle className="w-6 h-6 text-red-600" />
            <div>
              <p className="font-medium text-red-900">Error Loading ML Insights</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchMLInsights}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
              <Brain className="w-7 h-7" />
              AI-Powered Academic Insights
            </h2>
            <p className="text-purple-100">
              Personalized predictions and recommendations based on your academic performance
            </p>
          </div>
          <button
            onClick={fetchMLInsights}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="border-b">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('predictions')}
              className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'predictions'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Performance Predictions
            </button>
            <button
              onClick={() => setActiveTab('weaknesses')}
              className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'weaknesses'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <Target className="w-4 h-4" />
              Weakness Analysis
              {weaknessAnalysis?.analysis.weaknesses.length ? (
                <span className="ml-2 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">
                  {weaknessAnalysis.analysis.weaknesses.length}
                </span>
              ) : null}
            </button>
            <button
              onClick={() => setActiveTab('careers')}
              className={`px-6 py-3 font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'careers'
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <Briefcase className="w-4 h-4" />
              Career Paths
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {/* Predictions Tab */}
            {activeTab === 'predictions' && predictions && (
              <motion.div
                key="predictions"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Key Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Next Semester GPA */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-gray-600">Predicted Next GPA</p>
                      <Award className="w-5 h-5 text-blue-600" />
                    </div>
                    <p className="text-3xl font-bold text-blue-900">
                      {predictions.predictions.next_semester_gpa.toFixed(2)}
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      Confidence: {(predictions.predictions.confidence_score * 100).toFixed(0)}%
                    </p>
                  </div>

                  {/* Risk Level */}
                  <div className={`rounded-lg p-4 ${getRiskColor(predictions.predictions.risk_level)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm">Academic Risk</p>
                      <AlertTriangle className="w-5 h-5" />
                    </div>
                    <p className="text-3xl font-bold">
                      {predictions.predictions.risk_level}
                    </p>
                    <p className="text-xs mt-1">
                      Probability: {(predictions.predictions.risk_probability * 100).toFixed(0)}%
                    </p>
                  </div>

                  {/* Expected Graduation CGPA */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-gray-600">Expected Final CGPA</p>
                      <Target className="w-5 h-5 text-green-600" />
                    </div>
                    <p className="text-3xl font-bold text-green-900">
                      {predictions.predictions.expected_graduation_cgpa.toFixed(2)}
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      Improvement Potential: {(predictions.predictions.improvement_potential * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Trend Analysis */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold flex items-center gap-2">
                      Performance Trend
                      {getTrendIcon(predictions.trend_analysis.trend)}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      predictions.trend_analysis.trend === 'improving' 
                        ? 'bg-green-100 text-green-700'
                        : predictions.trend_analysis.trend === 'declining'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {predictions.trend_analysis.trend}
                    </span>
                  </div>
                  {predictions.trend_analysis.average_gpa && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                      <div>
                        <p className="text-xs text-gray-500">Average GPA</p>
                        <p className="font-semibold">{predictions.trend_analysis.average_gpa.toFixed(2)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Best Semester</p>
                        <p className="font-semibold">Semester {predictions.trend_analysis.best_semester}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Worst Semester</p>
                        <p className="font-semibold">Semester {predictions.trend_analysis.worst_semester}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Trend Coefficient</p>
                        <p className="font-semibold">{predictions.trend_analysis.trend_coefficient?.toFixed(3)}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Risk Factors */}
                {predictions.risk_factors.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-4">
                    <h3 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Risk Factors
                    </h3>
                    <ul className="space-y-2">
                      {predictions.risk_factors.map((factor, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                          <span className="text-sm text-red-700">{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* AI Recommendations */}
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    AI Recommendations
                  </h3>
                  <div className="space-y-2">
                    {predictions.recommendations.map((rec, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-purple-600 mt-0.5" />
                        <span className="text-sm text-purple-700">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Weakness Analysis Tab */}
            {activeTab === 'weaknesses' && weaknessAnalysis && (
              <motion.div
                key="weaknesses"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Overall Performance */}
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Overall Performance</p>
                      <p className="text-2xl font-bold text-gray-900 capitalize">
                        {weaknessAnalysis.analysis.overall_performance}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Success Probability</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {(weaknessAnalysis.analysis.success_probability * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Weaknesses List */}
                {weaknessAnalysis.analysis.weaknesses.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-4">Subjects Needing Improvement</h3>
                    <div className="space-y-3">
                      {weaknessAnalysis.analysis.priority_subjects.map((weakness, index) => (
                        <div key={index} className="bg-white border rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h4 className="font-semibold text-lg">{weakness.subject}</h4>
                              <div className="flex items-center gap-4 mt-1">
                                <span className="text-sm text-gray-600">
                                  Current: {weakness.marks}/100
                                </span>
                                <span className="text-sm text-red-600">
                                  Gap: {weakness.gap} marks
                                </span>
                                <span className="text-sm text-blue-600">
                                  {weakness.credits} credits
                                </span>
                              </div>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm ${
                              weakness.performance === 'poor' 
                                ? 'bg-red-100 text-red-700'
                                : 'bg-orange-100 text-orange-700'
                            }`}>
                              {weakness.performance}
                            </span>
                          </div>

                          {weakness.topics.length > 0 && (
                            <div className="mb-3">
                              <p className="text-xs font-medium text-gray-500 mb-2">WEAK TOPICS</p>
                              <div className="flex flex-wrap gap-2">
                                {weakness.topics.map((topic, tIndex) => (
                                  <span
                                    key={tIndex}
                                    className="px-2 py-1 bg-red-50 text-red-700 rounded text-xs"
                                  >
                                    {topic}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">IMPROVEMENT STRATEGY</p>
                            <ul className="space-y-1">
                              {weakness.improvement_strategy.map((strategy, sIndex) => (
                                <li key={sIndex} className="text-sm text-gray-700 flex items-start">
                                  <ChevronRight className="w-3 h-3 text-gray-400 mt-0.5 mr-1" />
                                  {strategy}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Study Plan */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Recommended Study Plan
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-blue-600">Weekly Hours</p>
                      <p className="text-xl font-bold text-blue-900">
                        {weaknessAnalysis.analysis.study_plan.weekly_hours}h
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-blue-600">Daily Hours</p>
                      <p className="text-xl font-bold text-blue-900">
                        {weaknessAnalysis.analysis.study_plan.daily_hours}h
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-blue-600">Effort Required</p>
                      <p className="text-xl font-bold text-blue-900">
                        {weaknessAnalysis.analysis.estimated_effort_hours}h
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-blue-600">CGPA Gap</p>
                      <p className="text-xl font-bold text-blue-900">
                        {weaknessAnalysis.analysis.cgpa_improvement_needed.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  {Object.keys(weaknessAnalysis.analysis.study_plan.focus_distribution).length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-blue-800 mb-2">Time Distribution</p>
                      <div className="space-y-2">
                        {Object.entries(weaknessAnalysis.analysis.study_plan.focus_distribution).map(
                          ([subject, percentage]) => (
                            <div key={subject} className="flex items-center justify-between">
                              <span className="text-sm text-blue-700">{subject}</span>
                              <div className="flex items-center gap-2">
                                <div className="w-32 bg-blue-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: percentage }}
                                  />
                                </div>
                                <span className="text-sm font-medium text-blue-900">{percentage}</span>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  <div className="mt-4">
                    <p className="text-sm font-medium text-blue-800 mb-2">Recommended Resources</p>
                    <ul className="space-y-1">
                      {weaknessAnalysis.analysis.study_plan.recommended_resources.map((resource, index) => (
                        <li key={index} className="text-sm text-blue-700 flex items-center">
                          <BookOpen className="w-3 h-3 mr-2" />
                          {resource}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Career Predictions Tab */}
            {activeTab === 'careers' && careerPredictions && (
              <motion.div
                key="careers"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="space-y-6"
              >
                {/* Career Paths */}
                <div>
                  <h3 className="font-semibold mb-4">Recommended Career Paths</h3>
                  <div className="space-y-4">
                    {careerPredictions.recommended_careers.map((career, index) => (
                      <div key={index} className="bg-white border rounded-lg p-5">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="text-lg font-bold">{career.career}</h4>
                            <div className="flex items-center gap-3 mt-2">
                              <span className="text-sm text-green-600 font-medium">
                                {career.match_score}% Match
                              </span>
                              <span className={`text-sm px-2 py-1 rounded-full ${
                                career.cgpa_eligible 
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-orange-100 text-orange-700'
                              }`}>
                                {career.cgpa_eligible ? 'CGPA Eligible' : 'CGPA Below Requirement'}
                              </span>
                              <span className="text-sm text-gray-600">
                                {career.salary_range}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-500">Growth</p>
                            <p className="font-semibold text-purple-600">{career.growth_potential}</p>
                          </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">TOP COMPANIES</p>
                            <div className="flex flex-wrap gap-2">
                              {career.top_companies.map((company, cIndex) => (
                                <span
                                  key={cIndex}
                                  className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
                                >
                                  {company}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">MISSING SKILLS</p>
                            <div className="flex flex-wrap gap-2">
                              {career.missing_skills.slice(0, 4).map((skill, sIndex) => (
                                <span
                                  key={sIndex}
                                  className="px-2 py-1 bg-red-50 text-red-700 rounded text-xs"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-2">PREPARATION PATH</p>
                          <ol className="space-y-1">
                            {career.preparation_path.map((step, sIndex) => (
                              <li key={sIndex} className="text-sm text-gray-700 flex items-start">
                                <span className="font-medium mr-2">{sIndex + 1}.</span>
                                {step}
                              </li>
                            ))}
                          </ol>
                        </div>

                        <div className="mt-4 pt-4 border-t">
                          <p className="text-xs font-medium text-gray-500 mb-2">CERTIFICATIONS</p>
                          <div className="flex flex-wrap gap-2">
                            {career.required_certifications.map((cert, cIndex) => (
                              <span
                                key={cIndex}
                                className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs"
                              >
                                {cert}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Skill Development Priority */}
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-semibold text-yellow-900 mb-3">Priority Skills to Develop</h3>
                  <div className="flex flex-wrap gap-2">
                    {careerPredictions.skill_development_priority.map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Internship Recommendations */}
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 mb-3">Internship Opportunities</h3>
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {careerPredictions.internship_recommendations.map((internship, index) => (
                      <div key={index} className="bg-white rounded-lg p-3">
                        <h4 className="font-medium text-green-900">{internship.role}</h4>
                        <p className="text-xs text-green-700 mt-1">{internship.duration}</p>
                        <p className="text-xs text-gray-600 mt-2">
                          <strong>Skills:</strong> {internship.skills_to_gain.join(', ')}
                        </p>
                        <p className="text-xs text-green-600 mt-1">
                          <strong>Tip:</strong> {internship.application_tip}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};