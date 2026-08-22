// src/components/dashboard/AIInsightsDashboard.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  Award,
  Target,
  BookOpen,
  Users,
  Briefcase,
  Calendar,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  Star,
  Activity,
  BarChart3,
  PieChart,
  LineChart,
  Sparkles,
  Zap,
  Shield,
  Trophy,
  Rocket,
  Building,
  GraduationCap,
  Code,
  Database,
  Globe,
  Cpu,
  Cloud,
  Lock,
  GitBranch,
  Terminal,
  X // Added X icon
} from 'lucide-react';
import { mlService, ComprehensiveStudentAnalysis } from '../../services/ml.service';
import { useAuth } from '../../contexts/AuthContext';

// Remove chart.js imports and replace with simple visualization components

interface AIInsightsDashboardProps {
  studentId: string;
  semester: number;
  branch: string;
}

// Simple chart components to replace react-chartjs-2
const SimpleLineChart: React.FC<{ data: number[]; labels: string[]; color?: string }> = ({ 
  data, 
  labels, 
  color = 'purple' 
}) => {
  const maxValue = Math.max(...data, 10);
  const minValue = Math.min(...data, 0);
  
  return (
    <div className="relative h-48 w-full">
      <div className="absolute inset-0 flex items-end space-x-2">
        {data.map((value, index) => (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div
              className={`w-full bg-gradient-to-t from-${color}-400 to-${color}-600 rounded-t transition-all duration-500`}
              style={{ 
                height: `${((value - minValue) / (maxValue - minValue)) * 100}%`,
                maxHeight: '90%'
              }}
            />
            <span className="text-xs text-gray-600 mt-1">{labels[index]}</span>
            <span className="text-xs font-medium text-gray-900">{value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const SimpleRadarChart: React.FC<{ 
  skills: { name: string; current: number; required: number }[] 
}> = ({ skills }) => {
  return (
    <div className="space-y-3">
      {skills.map((skill, index) => (
        <div key={index} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="font-medium">{skill.name}</span>
            <span className="text-gray-600">{skill.current}/{skill.required}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-purple-500 to-indigo-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(skill.current / skill.required) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const SimpleDoughnutChart: React.FC<{ 
  data: { label: string; value: number; color: string }[] 
}> = ({ data }) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative w-32 h-32">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-bold">{data[0]?.value}%</div>
            <div className="text-xs text-gray-600">Top Match</div>
          </div>
        </div>
        <svg className="w-32 h-32 transform -rotate-90">
          {data.map((item, index) => {
            const percentage = (item.value / total) * 100;
            const circumference = 2 * Math.PI * 40;
            const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;
            
            return (
              <circle
                key={index}
                cx="50%"
                cy="50%"
                r="40"
                fill="none"
                stroke={item.color}
                strokeWidth="8"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={0}
                className="transition-all duration-500"
              />
            );
          })}
        </svg>
      </div>
      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm">{item.label}: {item.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const AIInsightsDashboard: React.FC<AIInsightsDashboardProps> = ({
  studentId,
  semester,
  branch
}) => {
  const [analysis, setAnalysis] = useState<ComprehensiveStudentAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedInsight, setSelectedInsight] = useState<string>('overview');
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedCareerPath, setSelectedCareerPath] = useState<any>(null);

  useEffect(() => {
    fetchComprehensiveAnalysis();
  }, [studentId]);

  const fetchComprehensiveAnalysis = async () => {
    try {
      setLoading(true);
      const data = await mlService.getComprehensiveAnalysis(studentId);
      setAnalysis(data);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      // Use mock data for development
      setAnalysis(getMockAnalysis());
    } finally {
      setLoading(false);
    }
  };

  // Mock data for development
  const getMockAnalysis = (): ComprehensiveStudentAnalysis => {
    return {
      studentId,
      timestamp: new Date().toISOString(),
      performanceMetrics: {
        cgpa: 8.2,
        sgpa: [7.5, 8.0, 8.2, 8.5, 8.7, 8.2],
        attendanceRate: 85,
        assignmentCompletionRate: 90,
        subjectWisePerformance: [
          {
            subjectName: 'Data Structures',
            grade: 'A',
            score: 85,
            difficulty: 4,
            improvement: 5,
            recommendations: ['Practice tree algorithms', 'Solve LeetCode problems']
          },
          {
            subjectName: 'Database Systems',
            grade: 'B+',
            score: 78,
            difficulty: 3,
            improvement: -2,
            recommendations: ['Study normalization', 'Practice SQL queries']
          }
        ],
        strengthAreas: ['Programming', 'Algorithms', 'Web Development'],
        weaknessAreas: ['Database Design', 'System Architecture'],
        performanceTrend: 'improving',
        predictedCGPA: 8.5,
        riskLevel: 'low'
      },
      careerInsights: [
        {
          domain: 'Software Engineering',
          matchScore: 85,
          requiredSkills: [
            {
              name: 'JavaScript',
              currentLevel: 80,
              requiredLevel: 90,
              importance: 9,
              learningResources: []
            }
          ],
          currentSkillGap: 15,
          recommendedCourses: [],
          industryDemand: 95,
          salaryRange: { min: 600000, max: 2000000, median: 1200000 },
          topCompanies: [
            { name: 'Google', sector: 'Tech', hiringProbability: 80, requiredCGPA: 7.5, preferredSkills: ['DSA', 'System Design'] }
          ],
          preparationRoadmap: [
            {
              semester: 6,
              courses: ['Advanced Algorithms', 'Cloud Computing'],
              skills: ['System Design', 'AWS'],
              projects: ['Microservices Architecture'],
              certifications: ['AWS Certified'],
              internships: ['Backend Development'],
              milestone: 'Build scalable systems'
            }
          ]
        }
      ],
      personalizedRecommendations: {
        immediateActions: [
          { priority: 'high', action: 'Improve database concepts', deadline: '2024-12-01', impact: 8, effort: 6 }
        ],
        shortTermGoals: [],
        longTermGoals: [],
        skillDevelopmentPlan: [],
        mentorshipSuggestions: [],
        networkingOpportunities: []
      },
      projectAnalysis: {
        totalProjects: 5,
        domainDistribution: { 'Web Development': 3, 'AI/ML': 2 },
        skillCoverage: 75,
        innovationScore: 70,
        industryRelevance: 80,
        portfolioStrength: 75,
        missingAreas: ['Mobile Development', 'DevOps'],
        suggestedProjects: []
      },
      peerComparison: {
        percentile: 85,
        averageCGPA: 7.8,
        yourPosition: 15,
        totalStudents: 120,
        strengths: ['Programming Skills', 'Project Work'],
        areasToImprove: ['Theory Subjects', 'Database Concepts'],
        topPerformers: []
      },
      futureProjections: {
        expectedGraduation: {
          expectedCGPA: 8.4,
          confidence: 85,
          risks: ['Database course performance'],
          opportunities: ['Strong programming skills']
        },
        placementProbability: 88,
        expectedPackageRange: { min: 800000, max: 1800000 },
        topMatchingCompanies: [
          { name: 'Microsoft', sector: 'Tech', hiringProbability: 75, requiredCGPA: 8.0, preferredSkills: ['C#', '.NET'] }
        ],
        preparednessScore: 82,
        timeToReadiness: 3
      }
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Brain className="w-16 h-16 mx-auto text-purple-600 animate-pulse mb-4" />
          <p className="text-gray-600">AI is analyzing your academic data...</p>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  const { performanceMetrics, careerInsights, personalizedRecommendations, projectAnalysis, peerComparison, futureProjections } = analysis;

  // Mock chart data
  const performanceTrendData = [7.5, 8.0, 8.2, 8.5, 8.7, 8.2];
  const performanceLabels = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Current'];
  
  const skillsData = [
    { name: 'Programming', current: 75, required: 90 },
    { name: 'Problem Solving', current: 80, required: 85 },
    { name: 'System Design', current: 60, required: 80 },
    { name: 'Database', current: 70, required: 75 },
    { name: 'Web Dev', current: 85, required: 80 },
    { name: 'AI/ML', current: 65, required: 70 }
  ];

  const careerMatchData = [
    { label: 'Software Eng', value: 85, color: 'rgb(147, 51, 234)' },
    { label: 'Data Science', value: 75, color: 'rgb(59, 130, 246)' },
    { label: 'Cloud Engineer', value: 70, color: 'rgb(16, 185, 129)' },
    { label: 'DevOps', value: 65, color: 'rgb(251, 146, 60)' },
    { label: 'ML Engineer', value: 60, color: 'rgb(244, 63, 94)' }
  ];

  return (
    <div className="space-y-6">
      {/* AI Analysis Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 rounded-2xl p-8 text-white relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center">
                <Brain className="w-10 h-10 mr-3" />
                AI-Powered Academic Insights
              </h1>
              <p className="text-purple-100">
                Personalized analysis and recommendations powered by machine learning
              </p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-6 h-6" />
                <div>
                  <p className="text-sm text-purple-100">Analysis Score</p>
                  <p className="text-2xl font-bold">{Math.round((performanceMetrics.cgpa ?? 0) * 10)}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Current CGPA</p>
                  <p className="text-2xl font-bold">{(performanceMetrics.cgpa ?? 0).toFixed(2)}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2">
                <p className="text-xs text-purple-200">
                  Predicted: {performanceMetrics.predictedCGPA.toFixed(2)}
                </p>
                <div className="w-full bg-white/20 rounded-full h-1 mt-1">
                  <div
                    className="bg-white h-1 rounded-full transition-all duration-500"
                    style={{ width: `${((performanceMetrics.cgpa ?? 0) / 10) * 100}%` }}
                  />
                </div>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Career Match</p>
                  <p className="text-2xl font-bold">
                    {careerInsights[0]?.matchScore.toFixed(0)}%
                  </p>
                </div>
                <Target className="w-8 h-8 text-purple-200" />
              </div>
              <p className="text-xs text-purple-200 mt-2">
                Top: {careerInsights[0]?.domain}
              </p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Placement Ready</p>
                  <p className="text-2xl font-bold">
                    {futureProjections.placementProbability}%
                  </p>
                </div>
                <Briefcase className="w-8 h-8 text-purple-200" />
              </div>
              <p className="text-xs text-purple-200 mt-2">
                In {futureProjections.timeToReadiness} months
              </p>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Peer Rank</p>
                  <p className="text-2xl font-bold">
                    Top {peerComparison?.percentile ?? 0}%
                  </p>
                </div>
                <Trophy className="w-8 h-8 text-purple-200" />
              </div>
              <p className="text-xs text-purple-200 mt-2">
                #{peerComparison?.yourPosition ?? 0} of {peerComparison?.totalStudents ?? 0}
              </p>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-sm p-2">
        <div className="flex space-x-2 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'performance', label: 'Performance', icon: TrendingUp },
            { id: 'career', label: 'Career Paths', icon: Briefcase },
            { id: 'skills', label: 'Skills Gap', icon: Code },
            { id: 'recommendations', label: 'Recommendations', icon: Sparkles },
            { id: 'projects', label: 'Projects', icon: GitBranch },
            { id: 'placement', label: 'Placement', icon: Building }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedInsight(tab.id)}
              className={`
                flex items-center space-x-2 px-4 py-2 rounded-lg transition-all whitespace-nowrap
                ${selectedInsight === tab.id
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-100'
                }
              `}
            >
              <tab.icon className="w-4 h-4" />
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Sections */}
      <AnimatePresence mode="wait">
        {/* Overview Section */}
        {selectedInsight === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Performance Trend */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <LineChart className="w-5 h-5 mr-2 text-purple-600" />
                Performance Trend
              </h3>
              <SimpleLineChart data={performanceTrendData} labels={performanceLabels} />
            </div>

            {/* Career Match Distribution */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <PieChart className="w-5 h-5 mr-2 text-purple-600" />
                Career Match Analysis
              </h3>
              <SimpleDoughnutChart data={careerMatchData} />
            </div>

            {/* Skills Radar */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Cpu className="w-5 h-5 mr-2 text-purple-600" />
                Skills Assessment
              </h3>
              <SimpleRadarChart skills={skillsData} />
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-purple-600" />
                AI Recommendations
              </h3>
              <div className="space-y-3">
                {personalizedRecommendations.immediateActions.slice(0, 4).map((action, index) => (
                  <motion.div
                    key={index}
                    whileHover={{ x: 5 }}
                    className={`
                      p-3 rounded-lg border-l-4 cursor-pointer
                      ${action.priority === 'high' 
                        ? 'border-red-500 bg-red-50'
                        : action.priority === 'medium'
                        ? 'border-yellow-500 bg-yellow-50'
                        : 'border-green-500 bg-green-50'
                      }
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{action.action}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          Impact: {action.impact}/10 • Effort: {action.effort}/10
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Career Paths Analysis */}
        {selectedInsight === 'career' && (
          <motion.div
            key="career"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">AI-Recommended Career Paths</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {careerInsights.slice(0, 6).map((career, index) => (
                  <motion.div
                    key={index}
                    whileHover={{ scale: 1.02 }}
                    className="border rounded-xl p-4 cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => setSelectedCareerPath(career)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900">{career.domain}</h4>
                        <p className="text-xs text-gray-500 mt-1">
                          Match Score: {career.matchScore.toFixed(0)}%
                        </p>
                      </div>
                      <div className="relative">
                        <svg className="w-12 h-12 transform -rotate-90">
                          <circle
                            cx="24"
                            cy="24"
                            r="20"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            className="text-gray-200"
                          />
                          <circle
                            cx="24"
                            cy="24"
                            r="20"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                            strokeDasharray={`${career.matchScore * 1.26} 126`}
                            className="text-purple-600"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold">
                          {career.matchScore.toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Skill Gap</span>
                        <span className={`font-medium ${
                          (career.currentSkillGap ?? 0) < 30 ? 'text-green-600'
                            : (career.currentSkillGap ?? 0) < 60 ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}>
                          {career.currentSkillGap}%
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Industry Demand</span>
                        <div className="flex items-center">
                          <TrendingUp className={`w-3 h-3 mr-1 ${
                            (career.industryDemand ?? 0) > 70 ? 'text-green-500'
                              : (career.industryDemand ?? 0) > 40 ? 'text-yellow-500'
                              : 'text-red-500'
                          }`} />
                          <span className="font-medium">{career.industryDemand}%</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Salary Range</span>
                        <span className="font-medium text-green-600">
                          ₹{(career.salaryRange.median / 100000).toFixed(1)}L
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-gray-600 mb-2">Top Skills Needed:</p>
                      <div className="flex flex-wrap gap-1">
                        {career.requiredSkills?.slice(0, 3).map((skill: any, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                          >
                            {skill.name}
                          </span>
                        ))}
                      </div>
                    </div>

                    <button className="mt-3 w-full py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg text-sm font-medium hover:shadow-lg transition-shadow">
                      View Roadmap
                    </button>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Career Path Detail Modal */}
      <AnimatePresence>
        {selectedCareerPath && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            onClick={() => setSelectedCareerPath(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedCareerPath.domain} Roadmap</h2>
                    <p className="text-gray-600 mt-1">
                      Personalized learning path to achieve your career goals
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedCareerPath(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Roadmap Steps */}
                <div>
                  <h3 className="font-semibold mb-4">Your Learning Roadmap</h3>
                  <div className="space-y-4">
                    {selectedCareerPath.preparationRoadmap?.map((step: any, index: number) => (
                      <div key={index} className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-10 h-10 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                            {step.semester}
                          </div>
                        </div>
                        <div className="flex-1 border rounded-lg p-4">
                          <h4 className="font-medium mb-2">Semester {step.semester} Goals</h4>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {step.courses.length > 0 && (
                              <div>
                                <p className="text-xs text-gray-600 mb-1">Courses to Take</p>
                                <div className="space-y-1">
                                  {step.courses.map((course: string, idx: number) => (
                                    <div key={idx} className="text-sm flex items-center">
                                      <BookOpen className="w-3 h-3 mr-1 text-blue-500" />
                                      {course}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {step.skills.length > 0 && (
                              <div>
                                <p className="text-xs text-gray-600 mb-1">Skills to Develop</p>
                                <div className="space-y-1">
                                  {step.skills.map((skill: string, idx: number) => (
                                    <div key={idx} className="text-sm flex items-center">
                                      <Code className="w-3 h-3 mr-1 text-green-500" />
                                      {skill}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>

                          <div className="mt-3 p-2 bg-purple-50 rounded text-sm">
                            <strong>Milestone:</strong> {step.milestone}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};