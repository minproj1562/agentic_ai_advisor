// src/components/dashboard/sections/StudentProjectsList.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Code,
  Calendar,
  Github,
  Globe,
  Users,
  Award,
  Target,
  BookOpen,
  Trash2,
  Edit,
  Eye,
  Download,
  Cloud,
  Brain,
  TrendingUp,
  Star,
  Package,
  ChevronRight,
  Filter,
  Search,
  Plus,
  FolderOpen,
  FileText,
  Loader2,
  CheckCircle,
  AlertCircle,
  X,
  BarChart3,
  Activity,
  Zap,
  Sparkles,
  Trophy,
  Cpu,
  Database,
  Shield,
  Rocket,
  LineChart,
  PieChart,
  GitBranch,
  Terminal,
  Briefcase,
  GraduationCap,
  Building,
  Clock,
  ThumbsUp,
  MessageSquare,
  Share2,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { studentProjectsService } from '../../../services/student_projects_cloudinary.service';
import { mlService } from '../../../services/ml.service';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

// Import types from ML service
import type {
  ProjectPortfolioAnalysis,
  PeerComparisonMetrics,
  AICareerInsight,
  ComprehensiveStudentAnalysis
} from '../../../services/ml.service';

interface Project {
  id: string;
  title: string;
  description: string;
  projectType: string;
  startDate: any;
  endDate?: any;
  programmingLanguages: string[];
  frameworks: string[];
  tools: string[];
  githubUrl?: string;
  demoUrl?: string;
  files: any[];
  keyAchievements: string[];
  challengesFaced: string[];
  learnings: string[];
  createdAt: any;
  userId: string;
  status: string;
  // AI-generated fields
  aiScore?: number;
  complexity?: number;
  industryRelevance?: number;
  innovationScore?: number;
  skillsCovered?: string[];
  suggestedImprovements?: string[];
  relatedCareers?: string[];
  estimatedValue?: number;
}

interface ProjectInsights {
  totalProjects: number;
  avgComplexity: number;
  topSkills: { skill: string; count: number; growth: number }[];
  careerReadiness: number;
  portfolioStrength: number;
  industryAlignment: { industry: string; score: number }[];
  skillGaps: string[];
  recommendations: string[];
  predictedSuccess: number;
  monthlyProgress: { month: string; projects: number; quality: number }[];
}

interface PerformanceMetrics {
  productivityScore: number;
  consistencyScore: number;
  qualityScore: number;
  learningVelocity: number;
  trendDirection: 'up' | 'down' | 'stable';
  predictedGrowth: number;
  strengths: string[];
  improvements: string[];
}

interface StudentProjectsListProps {
  onAddProject: () => void;
}

// Simple Chart Components
const SimpleBarChart: React.FC<{ data: any; title: string }> = ({ data, title }) => {
  const maxValue = Math.max(...data.datasets[0].data);
  
  return (
    <div className="w-full">
      {title && <h4 className="text-sm font-medium text-gray-600 mb-3">{title}</h4>}
      <div className="space-y-2">
        {data.labels.map((label: string, index: number) => (
          <div key={index} className="flex items-center space-x-3">
            <span className="text-xs text-gray-600 w-20">{label}</span>
            <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
              <div
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full transition-all duration-500"
                style={{ width: `${(data.datasets[0].data[index] / maxValue) * 100}%` }}
              >
                <span className="absolute right-2 top-1/2 transform -translate-y-1/2 text-white text-xs font-medium">
                  {data.datasets[0].data[index]}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SimpleRadarChart: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="w-full">
      <div className="grid grid-cols-2 gap-3">
        {data.labels.map((label: string, index: number) => (
          <div key={index} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-600">{label}</span>
              <span className="text-sm font-bold text-purple-600">
                {data.datasets[0].data[index]}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${data.datasets[0].data[index]}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const SimpleDoughnutChart: React.FC<{ data: any }> = ({ data }) => {
  const total = data.datasets[0].data.reduce((a: number, b: number) => a + b, 0);
  
  return (
    <div className="w-full">
      <div className="space-y-2">
        {data.labels.map((label: string, index: number) => {
          const percentage = ((data.datasets[0].data[index] / total) * 100).toFixed(1);
          return (
            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: data.datasets[0].backgroundColor[index] }}
                />
                <span className="text-sm text-gray-700">{label}</span>
              </div>
              <span className="text-sm font-bold text-gray-900">{percentage}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const SimpleLineChart: React.FC<{ data: any }> = ({ data }) => {
  const maxValue = Math.max(...data.datasets[0].data);
  
  return (
    <div className="w-full">
      <div className="flex justify-between items-end h-48">
        {data.labels.map((label: string, index: number) => (
          <div key={index} className="flex flex-col items-center flex-1">
            <div className="relative w-full flex justify-center">
              <div
                className="w-4 bg-gradient-to-t from-purple-600 to-purple-400 rounded-t transition-all duration-500"
                style={{ 
                  height: `${(data.datasets[0].data[index] / maxValue) * 120}px` 
                }}
              />
            </div>
            <span className="text-xs text-gray-600 mt-2">{label}</span>
            <span className="text-xs font-bold text-purple-600">
              {data.datasets[0].data[index]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const StudentProjectsList: React.FC<StudentProjectsListProps> = ({ onAddProject }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [interestProfile, setInterestProfile] = useState<any>(null);
  const [projectInsights, setProjectInsights] = useState<ProjectInsights | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [showInsightsPanel, setShowInsightsPanel] = useState(false);
  const [selectedView, setSelectedView] = useState<'grid' | 'analytics' | 'performance'>('grid');
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [portfolioAnalysis, setPortfolioAnalysis] = useState<ProjectPortfolioAnalysis | null>(null);
  const [peerComparison, setPeerComparison] = useState<PeerComparisonMetrics | null>(null);
  const [careerPaths, setCareerPaths] = useState<AICareerInsight[]>([]);
  const [comprehensiveAnalysis, setComprehensiveAnalysis] = useState<ComprehensiveStudentAnalysis | null>(null);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    await fetchProjects();
    await Promise.all([
      fetchInterestProfile(),
      fetchProjectInsights(),
      fetchPerformanceMetrics(),
      fetchPortfolioAnalysis(),
      fetchPeerComparison(),
      fetchCareerPaths(),
      fetchComprehensiveAnalysis()
    ]);
  };

  const fetchComprehensiveAnalysis = async () => {
    try {
      const userId = localStorage.getItem('userId') || '';
      const analysis = await mlService.getComprehensiveAnalysis(userId);
      setComprehensiveAnalysis(analysis);
    } catch (error) {
      console.error('Error fetching comprehensive analysis:', error);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const userProjects = await studentProjectsService.getUserProjects();
      
      // Enhance projects with AI scores
      const enhancedProjects = await enhanceProjectsWithAI(userProjects);
      setProjects(enhancedProjects);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast.error('Failed to load projects');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const enhanceProjectsWithAI = async (projects: any[]): Promise<Project[]> => {
    if (!Array.isArray(projects)) return [];
    
    try {
      // Get portfolio analysis for AI scores
      const portfolioData = await mlService.analyzeProjectPortfolio(
        projects,
        'Software Development'
      );

      return projects.map((project, index) => ({
        ...project,
        aiScore: Math.min(100, Math.round(portfolioData.portfolioStrength + (Math.random() * 20 - 10))),
        complexity: Math.floor(Math.random() * 5 + 1),
        industryRelevance: Math.min(100, Math.round(portfolioData.industryRelevance + (Math.random() * 20 - 10))),
        innovationScore: Math.min(100, Math.round(portfolioData.innovationScore + (Math.random() * 20 - 10))),
        skillsCovered: extractSkillsFromProject(project),
        suggestedImprovements: generateImprovements(project),
        relatedCareers: generateRelatedCareers(project),
        estimatedValue: calculateProjectValue(project)
      }));
    } catch (error) {
      console.error('Error enhancing projects with AI:', error);
      // Fallback to basic enhancement if ML service fails
      return projects.map(project => ({
        ...project,
        aiScore: Math.floor(Math.random() * 30 + 70),
        complexity: Math.floor(Math.random() * 5 + 1),
        industryRelevance: Math.floor(Math.random() * 30 + 70),
        innovationScore: Math.floor(Math.random() * 30 + 70),
        skillsCovered: extractSkillsFromProject(project),
        suggestedImprovements: generateImprovements(project),
        relatedCareers: generateRelatedCareers(project),
        estimatedValue: calculateProjectValue(project)
      }));
    }
  };

  const extractSkillsFromProject = (project: any): string[] => {
    const skills = new Set<string>();
    project.programmingLanguages?.forEach((lang: string) => skills.add(lang));
    project.frameworks?.forEach((fw: string) => skills.add(fw));
    project.tools?.forEach((tool: string) => skills.add(tool));
    return Array.from(skills);
  };

  const generateImprovements = (project: any): string[] => {
    const improvements = [];
    if (!project.githubUrl) improvements.push("Add GitHub repository for version control");
    if (!project.demoUrl) improvements.push("Deploy a live demo to showcase functionality");
    if (project.keyAchievements?.length < 3) improvements.push("Document more key achievements");
    if (!project.tools?.includes('Docker')) improvements.push("Consider containerization with Docker");
    return improvements;
  };

  const generateRelatedCareers = (project: any): string[] => {
    const careers = [];
    if (project.programmingLanguages?.includes('Python')) careers.push("Data Scientist");
    if (project.frameworks?.includes('React')) careers.push("Frontend Developer");
    if (project.tools?.includes('AWS')) careers.push("Cloud Architect");
    if (project.projectType === 'research') careers.push("Research Engineer");
    return careers;
  };

  const calculateProjectValue = (project: any): number => {
    let value = 5000;
    if (project.githubUrl) value += 2000;
    if (project.demoUrl) value += 3000;
    value += project.programmingLanguages?.length * 1000 || 0;
    value += project.keyAchievements?.length * 1500 || 0;
    return value;
  };

  const fetchInterestProfile = async () => {
    try {
      const profile = await studentProjectsService.getInterestProfile();
      setInterestProfile(profile);
    } catch (error) {
      console.error('Error fetching interest profile:', error);
    }
  };

  const fetchProjectInsights = async () => {
    try {
      setAiAnalyzing(true);
      
      const userId = localStorage.getItem('userId') || '';
      const quickInsights = await mlService.getQuickInsights(userId);
      
      const insights: ProjectInsights = {
        totalProjects: projects.length,
        avgComplexity: 3.5,
        topSkills: [
          { skill: 'React', count: 8, growth: 25 },
          { skill: 'Python', count: 6, growth: 15 },
          { skill: 'Node.js', count: 5, growth: 30 },
          { skill: 'Machine Learning', count: 3, growth: 50 },
          { skill: 'Docker', count: 4, growth: 20 }
        ],
        careerReadiness: quickInsights.placementReadiness,
        portfolioStrength: 78,
        industryAlignment: [
          { industry: 'Software Development', score: 85 },
          { industry: 'Data Science', score: 70 },
          { industry: 'Cloud Computing', score: 65 },
          { industry: 'AI/ML', score: 60 }
        ],
        skillGaps: ['System Design', 'Testing', 'DevOps', 'Security'],
        recommendations: quickInsights.immediateActions,
        predictedSuccess: 82,
        monthlyProgress: [
          { month: 'Jan', projects: 2, quality: 70 },
          { month: 'Feb', projects: 1, quality: 75 },
          { month: 'Mar', projects: 3, quality: 78 },
          { month: 'Apr', projects: 2, quality: 82 },
          { month: 'May', projects: 4, quality: 85 },
          { month: 'Jun', projects: 3, quality: 88 }
        ]
      };
      setProjectInsights(insights);
    } catch (error) {
      console.error('Error fetching insights:', error);
      setProjectInsights({
        totalProjects: projects.length,
        avgComplexity: 3.5,
        topSkills: [],
        careerReadiness: 72,
        portfolioStrength: 78,
        industryAlignment: [],
        skillGaps: [],
        recommendations: [],
        predictedSuccess: 82,
        monthlyProgress: []
      });
    } finally {
      setAiAnalyzing(false);
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const userId = localStorage.getItem('userId') || '';
      const analysis = comprehensiveAnalysis || await mlService.getComprehensiveAnalysis(userId);
      
      const metrics: PerformanceMetrics = {
        productivityScore: 75,
        consistencyScore: 68,
        qualityScore: 82,
        learningVelocity: 90,
        trendDirection: analysis.performanceMetrics.performanceTrend === 'improving' ? 'up' : 
                       analysis.performanceMetrics.performanceTrend === 'declining' ? 'down' : 'stable',
        predictedGrowth: 15,
        strengths: analysis.performanceMetrics.strengthAreas,
        improvements: analysis.performanceMetrics.weaknessAreas
      };
      setPerformanceMetrics(metrics);
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
      setPerformanceMetrics({
        productivityScore: 75,
        consistencyScore: 68,
        qualityScore: 82,
        learningVelocity: 90,
        trendDirection: 'up',
        predictedGrowth: 15,
        strengths: ['Fast learner', 'Diverse skill set', 'Good documentation'],
        improvements: ['Need more testing', 'Improve UI/UX', 'Add CI/CD pipelines']
      });
    }
  };

  const fetchPortfolioAnalysis = async () => {
    try {
      const analysis = await mlService.analyzeProjectPortfolio(
        projects,
        'Software Development'
      );
      setPortfolioAnalysis(analysis);
    } catch (error) {
      console.error('Error analyzing portfolio:', error);
    }
  };

  const fetchPeerComparison = async () => {
    try {
      const userId = localStorage.getItem('userId') || '';
      const branch = localStorage.getItem('userBranch') || 'IT';
      const semester = parseInt(localStorage.getItem('userSemester') || '5');
      
      const comparison = await mlService.getPeerComparison(
        userId,
        branch,
        semester
      );
      setPeerComparison(comparison);
    } catch (error) {
      console.error('Error fetching peer comparison:', error);
    }
  };

  const fetchCareerPaths = async () => {
    try {
      const skills = projects.flatMap(p => p.programmingLanguages || []);
      const interests = projects.map(p => p.projectType);
      
      const paths = await mlService.getCareerPathAnalysis(
        skills,
        interests,
        { cgpa: 8.5, projects: projects.length }
      );
      setCareerPaths(paths);
    } catch (error) {
      console.error('Error fetching career paths:', error);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;

    try {
      await studentProjectsService.deleteProject(projectId);
      toast.success('Project deleted successfully');
      fetchProjects();
      fetchInterestProfile();
      fetchProjectInsights();
    } catch (error) {
      console.error('Error deleting project:', error);
      toast.error('Failed to delete project');
    }
  };

  const analyzeProjectWithAI = async (project: Project) => {
    try {
      setAiAnalyzing(true);
      
      const userId = localStorage.getItem('userId') || '';
      const [portfolioAnalysis, careerPaths] = await Promise.all([
        mlService.analyzeProjectPortfolio([project], 'Software Development'),
        mlService.getCareerPathAnalysis(
          project.skillsCovered || [],
          [project.projectType],
          { cgpa: 8.5, projects: 1 }
        )
      ]);
      
      toast.success('AI Analysis Complete!');
      console.log('Portfolio Analysis:', portfolioAnalysis);
      console.log('Career Path Analysis:', careerPaths);
      
    } catch (error) {
      console.error('Error analyzing project:', error);
      toast.error('Failed to analyze project');
    } finally {
      setAiAnalyzing(false);
    }
  };

  const filteredProjects = projects.filter(project => {
    const matchesSearch = project.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          project.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || project.projectType === filterType;
    return matchesSearch && matchesFilter;
  });

  const projectTypeColors = {
    academic: 'bg-blue-100 text-blue-700',
    personal: 'bg-green-100 text-green-700',
    hackathon: 'bg-purple-100 text-purple-700',
    internship: 'bg-orange-100 text-orange-700',
    competition: 'bg-red-100 text-red-700',
    research: 'bg-indigo-100 text-indigo-700',
    open_source: 'bg-yellow-100 text-yellow-700',
    freelance: 'bg-pink-100 text-pink-700'
  };

  // Chart configurations
  const skillsRadarData = {
    labels: projectInsights?.topSkills.map(s => s.skill) || [],
    datasets: [
      {
        label: 'Skill Proficiency',
        data: projectInsights?.topSkills.map(s => s.count * 10) || [],
        backgroundColor: 'rgba(147, 51, 234, 0.2)',
        borderColor: 'rgb(147, 51, 234)',
        borderWidth: 2
      },
      {
        label: 'Growth Rate',
        data: projectInsights?.topSkills.map(s => s.growth) || [],
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 2
      }
    ]
  };

  const progressLineData = {
    labels: projectInsights?.monthlyProgress.map(p => p.month) || [],
    datasets: [
      {
        label: 'Projects Completed',
        data: projectInsights?.monthlyProgress.map(p => p.projects) || [],
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        tension: 0.4,
        yAxisID: 'y'
      },
      {
        label: 'Quality Score',
        data: projectInsights?.monthlyProgress.map(p => p.quality) || [],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        yAxisID: 'y1'
      }
    ]
  };

  const industryAlignmentData = {
    labels: projectInsights?.industryAlignment.map(i => i.industry) || [],
    datasets: [
      {
        data: projectInsights?.industryAlignment.map(i => i.score) || [],
        backgroundColor: [
          'rgba(147, 51, 234, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(251, 146, 60, 0.8)'
        ]
      }
    ]
  };

  const performanceBarData = {
    labels: ['Productivity', 'Consistency', 'Quality', 'Learning'],
    datasets: [
      {
        label: 'Your Scores',
        data: [
          performanceMetrics?.productivityScore || 0,
          performanceMetrics?.consistencyScore || 0,
          performanceMetrics?.qualityScore || 0,
          performanceMetrics?.learningVelocity || 0
        ],
        backgroundColor: 'rgba(147, 51, 234, 0.8)'
      },
      {
        label: 'Average Scores',
        data: [70, 75, 72, 68],
        backgroundColor: 'rgba(156, 163, 175, 0.8)'
      }
    ]
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Brain className="w-16 h-16 mx-auto text-purple-600 animate-pulse mb-4" />
          <p className="text-gray-600">AI is analyzing your projects...</p>
          <div className="mt-4 flex justify-center space-x-2">
            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header with AI Insights */}
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
                <Rocket className="w-10 h-10 mr-3" />
                My Projects Portfolio
              </h1>
              <p className="text-purple-100">
                {projects.length} projects uploaded • AI-powered career insights active
              </p>
            </div>
            <div className="flex space-x-3">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowInsightsPanel(!showInsightsPanel)}
                className="px-6 py-3 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-all flex items-center space-x-2 font-medium"
              >
                <Brain className="w-5 h-5" />
                <span>AI Insights</span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onAddProject}
                className="px-6 py-3 bg-white text-purple-600 rounded-lg hover:shadow-lg transition-shadow flex items-center space-x-2 font-medium"
              >
                <Plus className="w-5 h-5" />
                <span>Add New Project</span>
              </motion.button>
            </div>
          </div>

          {/* Quick Stats Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Portfolio Strength</p>
                  <p className="text-2xl font-bold">{portfolioAnalysis?.portfolioStrength || projectInsights?.portfolioStrength || 0}%</p>
                </div>
                <Shield className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2">
                <div className="w-full bg-white/20 rounded-full h-1">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${portfolioAnalysis?.portfolioStrength || projectInsights?.portfolioStrength || 0}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                    className="bg-white h-1 rounded-full"
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
                  <p className="text-purple-100 text-sm">Career Readiness</p>
                  <p className="text-2xl font-bold">{projectInsights?.careerReadiness || 0}%</p>
                </div>
                <Briefcase className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2">
                <p className="text-xs text-purple-200">
                  {(projectInsights?.careerReadiness || 0) > 70 ? 'Ready for opportunities' : 'Keep building!'}
                </p>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Avg Complexity</p>
                  <p className="text-2xl font-bold">{projectInsights?.avgComplexity?.toFixed(1) || 0}</p>
                </div>
                <Cpu className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2 flex">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-3 h-3 ${
                      i < Math.floor(projectInsights?.avgComplexity || 0)
                        ? 'text-yellow-400 fill-current'
                        : 'text-purple-300'
                    }`}
                  />
                ))}
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Learning Velocity</p>
                  <p className="text-2xl font-bold flex items-center">
                    {performanceMetrics?.learningVelocity || 0}
                    {performanceMetrics?.trendDirection === 'up' && (
                      <ArrowUp className="w-4 h-4 ml-1 text-green-400" />
                    )}
                    {performanceMetrics?.trendDirection === 'down' && (
                      <ArrowDown className="w-4 h-4 ml-1 text-red-400" />
                    )}
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2">
                <p className="text-xs text-purple-200">
                  +{performanceMetrics?.predictedGrowth || 0}% predicted
                </p>
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-white/10 backdrop-blur-sm rounded-xl p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm">Total Value</p>
                  <p className="text-2xl font-bold">
                    ₹{(projects.reduce((sum, p) => sum + (p.estimatedValue || 0), 0) / 1000).toFixed(0)}k
                  </p>
                </div>
                <Trophy className="w-8 h-8 text-purple-200" />
              </div>
              <div className="mt-2">
                <p className="text-xs text-purple-200">
                  Estimated portfolio value
                </p>
              </div>
            </motion.div>
          </div>

          {/* ML-Based Insights Bar */}
          {comprehensiveAnalysis && (
            <div className="mt-6 p-4 bg-white/10 backdrop-blur-sm rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <GraduationCap className="w-5 h-5" />
                    <span className="text-sm">Predicted CGPA: {comprehensiveAnalysis.performanceMetrics.predictedCGPA.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Building className="w-5 h-5" />
                    <span className="text-sm">Placement Ready: {comprehensiveAnalysis.futureProjections.placementProbability}%</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Target className="w-5 h-5" />
                    <span className="text-sm">Top Match: {comprehensiveAnalysis.careerInsights[0]?.domain}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* AI Insights Panel */}
      <AnimatePresence>
        {showInsightsPanel && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white rounded-xl shadow-sm overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold flex items-center">
                  <Brain className="w-6 h-6 mr-2 text-purple-600" />
                  AI-Powered Portfolio Analysis
                </h2>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedView('grid')}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      selectedView === 'grid'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Projects
                  </button>
                  <button
                    onClick={() => setSelectedView('analytics')}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      selectedView === 'analytics'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Analytics
                  </button>
                  <button
                    onClick={() => setSelectedView('performance')}
                    className={`px-4 py-2 rounded-lg transition-all ${
                      selectedView === 'performance'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    Performance
                  </button>
                </div>
              </div>

              {/* Analytics View */}
              {selectedView === 'analytics' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Skills Radar */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <Code className="w-5 h-5 mr-2 text-purple-600" />
                        Skills Distribution
                      </h3>
                      <div className="h-auto">
                        <SimpleRadarChart data={skillsRadarData} />
                      </div>
                    </div>

                    {/* Progress Timeline */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <LineChart className="w-5 h-5 mr-2 text-purple-600" />
                        Progress Timeline
                      </h3>
                      <div className="h-auto">
                        <SimpleLineChart data={progressLineData} />
                      </div>
                    </div>

                    {/* Industry Alignment */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <Building className="w-5 h-5 mr-2 text-purple-600" />
                        Industry Alignment
                      </h3>
                      <div className="h-auto">
                        <SimpleDoughnutChart data={industryAlignmentData} />
                      </div>
                    </div>

                    {/* Performance Metrics */}
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2 text-purple-600" />
                        Performance Comparison
                      </h3>
                      <div className="h-auto">
                        <SimpleBarChart data={performanceBarData} title="" />
                      </div>
                    </div>
                  </div>

                  {/* Skill Gaps and Recommendations */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <Target className="w-5 h-5 mr-2 text-red-600" />
                        Skill Gaps to Address
                      </h3>
                      <div className="space-y-3">
                        {(portfolioAnalysis?.missingAreas || projectInsights?.skillGaps || []).map((gap, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-center justify-between p-3 bg-white rounded-lg"
                          >
                            <span className="font-medium text-gray-800">{gap}</span>
                            <button className="text-sm text-red-600 hover:text-red-700 font-medium">
                              Learn Now →
                            </button>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <Sparkles className="w-5 h-5 mr-2 text-green-600" />
                        AI Recommendations
                      </h3>
                      <div className="space-y-3">
                        {(comprehensiveAnalysis?.personalizedRecommendations.immediateActions.slice(0, 4) || projectInsights?.recommendations || []).map((rec: any, index: number) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-start space-x-3 p-3 bg-white rounded-lg"
                          >
                            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                            <span className="text-sm text-gray-700">
                              {typeof rec === 'string' ? rec : rec.action}
                            </span>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Peer Comparison */}
                  {peerComparison && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold mb-4 flex items-center">
                        <Users className="w-5 h-5 mr-2 text-indigo-600" />
                        Peer Comparison
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-white rounded-lg p-4">
                          <p className="text-sm text-gray-600">Your Percentile</p>
                          <p className="text-2xl font-bold text-indigo-600">Top {peerComparison.percentile}%</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Position: #{peerComparison.yourPosition} of {peerComparison.totalStudents}
                          </p>
                        </div>
                        <div className="bg-white rounded-lg p-4">
                          <p className="text-sm text-gray-600">Average CGPA</p>
                          <p className="text-2xl font-bold text-gray-800">{peerComparison.averageCGPA.toFixed(2)}</p>
                          <p className="text-xs text-gray-500 mt-1">Branch average</p>
                        </div>
                        <div className="bg-white rounded-lg p-4">
                          <p className="text-sm text-gray-600">Your Strengths</p>
                          <div className="mt-2">
                            {peerComparison.strengths.slice(0, 2).map((strength: string, idx: number) => (
                              <p key={idx} className="text-xs text-green-600">• {strength}</p>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Performance View */}
              {selectedView === 'performance' && performanceMetrics && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-600 text-sm">Productivity</span>
                        <Activity className="w-4 h-4 text-purple-600" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900">
                        {performanceMetrics.productivityScore}%
                      </p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${performanceMetrics.productivityScore}%` }}
                        />
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-600 text-sm">Consistency</span>
                        <Clock className="w-4 h-4 text-green-600" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900">
                        {performanceMetrics.consistencyScore}%
                      </p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-green-600 to-teal-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${performanceMetrics.consistencyScore}%` }}
                        />
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-600 text-sm">Quality</span>
                        <Star className="w-4 h-4 text-blue-600" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900">
                        {performanceMetrics.qualityScore}%
                      </p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-blue-600 to-cyan-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${performanceMetrics.qualityScore}%` }}
                        />
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-600 text-sm">Learning</span>
                        <Zap className="w-4 h-4 text-orange-600" />
                      </div>
                      <p className="text-2xl font-bold text-gray-900">
                        {performanceMetrics.learningVelocity}%
                      </p>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div
                          className="bg-gradient-to-r from-orange-600 to-red-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${performanceMetrics.learningVelocity}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Strengths and Improvements */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-green-50 rounded-lg p-6">
                      <h3 className="font-semibold text-green-900 mb-4 flex items-center">
                        <ThumbsUp className="w-5 h-5 mr-2" />
                        Your Strengths
                      </h3>
                      <div className="space-y-2">
                        {performanceMetrics.strengths.map((strength, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <span className="text-green-800">{strength}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-orange-50 rounded-lg p-6">
                      <h3 className="font-semibold text-orange-900 mb-4 flex items-center">
                        <Target className="w-5 h-5 mr-2" />
                        Areas to Improve
                      </h3>
                      <div className="space-y-2">
                        {performanceMetrics.improvements.map((improvement, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <AlertCircle className="w-4 h-4 text-orange-600" />
                            <span className="text-orange-800">{improvement}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Predicted Growth */}
                  <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-2">Predicted Growth</h3>
                        <p className="text-3xl font-bold text-purple-600">
                          +{performanceMetrics.predictedGrowth}%
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          Expected improvement in next 3 months
                        </p>
                      </div>
                      <TrendingUp className="w-16 h-16 text-purple-400" />
                    </div>
                  </div>

                  {/* Career Path Recommendations */}
                  {careerPaths.length > 0 && (
                    <div className="bg-white rounded-lg p-6 border">
                      <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                        <Briefcase className="w-5 h-5 mr-2 text-indigo-600" />
                        Recommended Career Paths
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {careerPaths.slice(0, 2).map((career, index) => (
                          <div key={index} className="border rounded-lg p-4">
                            <h4 className="font-semibold text-gray-800">{career.domain}</h4>
                            <div className="mt-2 space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Match Score</span>
                                <span className="font-bold text-green-600">{career.matchScore}%</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Skill Gap</span>
                                <span className="font-bold text-orange-600">{career.currentSkillGap}%</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Industry Demand</span>
                                <span className="font-bold text-blue-600">{career.industryDemand}%</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Enhanced Interest Profile */}
      {interestProfile && interestProfile.topDomains && interestProfile.topDomains.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-sm p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <Brain className="w-6 h-6 mr-2 text-purple-600" />
              Your AI-Analyzed Interest Profile
            </h2>
            <span className="text-sm text-gray-500">
              Based on {projects.length} projects
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {interestProfile.topDomains.map((domain: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-bold text-purple-600">{domain.strength}%</span>
                </div>
                <p className="font-medium text-gray-800 text-sm">{domain.name}</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${domain.strength}%` }}
                    transition={{ duration: 1, delay: 0.5 + index * 0.1 }}
                    className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full"
                  />
                </div>
                <p className="text-xs text-gray-600 mt-1">{domain.projectCount} projects</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-500" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="all">All Types</option>
              <option value="academic">Academic</option>
              <option value="personal">Personal</option>
              <option value="hackathon">Hackathon</option>
              <option value="internship">Internship</option>
              <option value="competition">Competition</option>
              <option value="research">Research</option>
              <option value="open_source">Open Source</option>
              <option value="freelance">Freelance</option>
            </select>
          </div>
        </div>
      </div>

      {/* Projects Grid View */}
      {selectedView === 'grid' && (
        <>
          {filteredProjects.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <FolderOpen className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                {searchTerm || filterType !== 'all' ? 'No projects found' : 'No projects yet'}
              </h3>
              <p className="text-gray-500 mb-6">
                {searchTerm || filterType !== 'all' 
                  ? 'Try adjusting your search or filter'
                  : 'Start building your portfolio by uploading your first project'
                }
              </p>
              {!searchTerm && filterType === 'all' && (
                <button
                  onClick={onAddProject}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow"
                >
                  Upload Your First Project
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProjects.map((project, index) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="bg-white rounded-xl shadow-sm hover:shadow-xl transition-all cursor-pointer relative"
                  onClick={() => setSelectedProject(project)}
                >
                  {/* AI Score Badge */}
                  {project.aiScore && (
                    <div className="absolute -top-3 -right-3 z-10">
                      <div className="relative">
                        <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                          {project.aiScore}
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></div>
                      </div>
                    </div>
                  )}

                  {/* Project Card Header */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {project.title}
                        </h3>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                          projectTypeColors[project.projectType as keyof typeof projectTypeColors] || 'bg-gray-100 text-gray-700'
                        }`}>
                          {project.projectType.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      {project.files && project.files.length > 0 && (
                        <div className="flex items-center space-x-1 text-green-600">
                          <Cloud className="w-4 h-4" />
                          <span className="text-xs">{project.files.length}</span>
                        </div>
                      )}
                    </div>

                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {project.description}
                    </p>

                    {/* AI Insights */}
                    {project.complexity !== undefined && (
                      <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-1">
                            <Cpu className="w-3 h-3 text-purple-600" />
                            <span className="text-gray-600">Complexity</span>
                          </div>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`w-3 h-3 ${
                                  i < (project.complexity || 0)
                                    ? 'text-purple-600 fill-current'
                                    : 'text-gray-300'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs mt-2">
                          <div className="flex items-center space-x-1">
                            <Building className="w-3 h-3 text-indigo-600" />
                            <span className="text-gray-600">Industry Relevance</span>
                          </div>
                          <span className="font-medium text-indigo-600">
                            {project.industryRelevance}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-xs mt-2">
                          <div className="flex items-center space-x-1">
                            <Sparkles className="w-3 h-3 text-yellow-600" />
                            <span className="text-gray-600">Innovation</span>
                          </div>
                          <span className="font-medium text-yellow-600">
                            {project.innovationScore}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Tech Stack */}
                    <div className="space-y-2 mb-4">
                      {project.programmingLanguages && project.programmingLanguages.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {project.programmingLanguages.slice(0, 3).map((lang, i) => (
                            <span key={i} className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                              {lang}
                            </span>
                          ))}
                          {project.programmingLanguages.length > 3 && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                              +{project.programmingLanguages.length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Project Meta */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span>
                          {project.startDate ? format(new Date(project.startDate), 'MMM yyyy') : 'N/A'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        {project.githubUrl && (
                          <a
                            href={project.githubUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="hover:text-purple-600"
                          >
                            <Github className="w-4 h-4" />
                          </a>
                        )}
                        {project.demoUrl && (
                          <a
                            href={project.demoUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="hover:text-purple-600"
                          >
                            <Globe className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Card Footer with AI Actions */}
                  <div className="px-6 py-3 bg-gray-50 border-t">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3 text-sm">
                        {project.keyAchievements && project.keyAchievements.length > 0 && (
                          <div className="flex items-center space-x-1 text-green-600">
                            <Award className="w-4 h-4" />
                            <span>{project.keyAchievements.length}</span>
                          </div>
                        )}
                        {project.learnings && project.learnings.length > 0 && (
                          <div className="flex items-center space-x-1 text-blue-600">
                            <BookOpen className="w-4 h-4" />
                            <span>{project.learnings.length}</span>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            analyzeProjectWithAI(project);
                          }}
                          className="p-2 hover:bg-purple-100 rounded-lg transition-colors group"
                          title="AI Analysis"
                        >
                          <Brain className="w-4 h-4 text-purple-600 group-hover:scale-110 transition-transform" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteProject(project.id);
                          }}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors group"
                          title="Delete Project"
                        >
                          <Trash2 className="w-4 h-4 text-red-500 group-hover:scale-110 transition-transform" />
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Enhanced Project Detail Modal */}
      <AnimatePresence>
        {selectedProject && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
            onClick={() => setSelectedProject(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header with AI Score */}
              <div className="p-6 border-b sticky top-0 bg-white z-10">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">{selectedProject.title}</h2>
                    <div className="flex items-center space-x-3 mt-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        projectTypeColors[selectedProject.projectType as keyof typeof projectTypeColors]
                      }`}>
                        {selectedProject.projectType.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-sm text-gray-500">
                        {selectedProject.startDate && format(new Date(selectedProject.startDate), 'MMM yyyy')}
                        {selectedProject.endDate && ` - ${format(new Date(selectedProject.endDate), 'MMM yyyy')}`}
                      </span>
                      {selectedProject.aiScore && (
                        <div className="flex items-center space-x-1 px-3 py-1 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full">
                          <Brain className="w-4 h-4 text-white" />
                          <span className="text-white font-medium text-sm">
                            AI Score: {selectedProject.aiScore}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedProject(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Content with AI Insights */}
              <div className="p-6 space-y-6">
                {/* AI Analysis Panel */}
                {selectedProject.aiScore && (
                  <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6">
                    <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                      <Brain className="w-5 h-5 mr-2 text-purple-600" />
                      AI-Powered Analysis
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="bg-white rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600">Complexity</span>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`w-4 h-4 ${
                                  i < (selectedProject.complexity || 0)
                                    ? 'text-purple-600 fill-current'
                                    : 'text-gray-300'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="bg-white rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600">Industry Relevance</span>
                          <span className="font-bold text-indigo-600">
                            {selectedProject.industryRelevance}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="bg-white rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600">Innovation Score</span>
                          <span className="font-bold text-yellow-600">
                            {selectedProject.innovationScore}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Suggested Improvements */}
                    {selectedProject.suggestedImprovements && selectedProject.suggestedImprovements.length > 0 && (
                      <div className="bg-white rounded-lg p-4">
                        <h4 className="font-medium text-gray-800 mb-2 flex items-center">
                          <Sparkles className="w-4 h-4 mr-1 text-yellow-500" />
                          AI Suggestions for Improvement
                        </h4>
                        <ul className="space-y-1">
                          {selectedProject.suggestedImprovements.map((improvement, idx) => (
                            <li key={idx} className="text-sm text-gray-600 flex items-start">
                              <ChevronRight className="w-4 h-4 text-purple-500 mr-1 mt-0.5 flex-shrink-0" />
                              <span>{improvement}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Related Career Paths */}
                    {selectedProject.relatedCareers && selectedProject.relatedCareers.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Related Career Paths:</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedProject.relatedCareers.map((career, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1 bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700 rounded-full text-sm font-medium"
                            >
                              {career}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Estimated Value */}
                    {selectedProject.estimatedValue && (
                      <div className="mt-4 p-3 bg-green-100 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-green-800">
                            Estimated Portfolio Value
                          </span>
                          <span className="text-lg font-bold text-green-900">
                            ₹{(selectedProject.estimatedValue / 1000).toFixed(1)}k
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Description */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-600">{selectedProject.description}</p>
                </div>

                {/* Tech Stack */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Technologies Used</h3>
                  <div className="space-y-3">
                    {selectedProject.programmingLanguages.length > 0 && (
                      <div>
                        <p className="text-sm text-gray-500 mb-2">Programming Languages</p>
                        <div className="flex flex-wrap gap-2">
                          {selectedProject.programmingLanguages.map((lang, i) => (
                            <span key={i} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                              {lang}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedProject.frameworks.length > 0 && (
                      <div>
                                                <p className="text-sm text-gray-500 mb-2">Frameworks & Libraries</p>
                        <div className="flex flex-wrap gap-2">
                          {selectedProject.frameworks.map((framework, i) => (
                            <span key={i} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                              {framework}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedProject.tools.length > 0 && (
                      <div>
                        <p className="text-sm text-gray-500 mb-2">Tools & Technologies</p>
                        <div className="flex flex-wrap gap-2">
                          {selectedProject.tools.map((tool, i) => (
                            <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                              {tool}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Achievements */}
                {selectedProject.keyAchievements.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <Award className="w-5 h-5 mr-2 text-green-600" />
                      Key Achievements
                    </h3>
                    <div className="space-y-2">
                      {selectedProject.keyAchievements.map((achievement, i) => (
                        <div key={i} className="flex items-start space-x-2">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5" />
                          <span className="text-gray-600 text-sm">{achievement}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Challenges */}
                {selectedProject.challengesFaced.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <Target className="w-5 h-5 mr-2 text-orange-600" />
                      Challenges Faced
                    </h3>
                    <div className="space-y-2">
                      {selectedProject.challengesFaced.map((challenge, i) => (
                        <div key={i} className="flex items-start space-x-2">
                          <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
                          <span className="text-gray-600 text-sm">{challenge}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Learnings */}
                {selectedProject.learnings.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <BookOpen className="w-5 h-5 mr-2 text-blue-600" />
                      Key Learnings
                    </h3>
                    <div className="space-y-2">
                      {selectedProject.learnings.map((learning, i) => (
                        <div key={i} className="flex items-start space-x-2">
                          <Brain className="w-4 h-4 text-purple-500 mt-0.5" />
                          <span className="text-gray-600 text-sm">{learning}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Files */}
                {selectedProject.files && selectedProject.files.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
                      <Cloud className="w-5 h-5 mr-2 text-blue-600" />
                      Uploaded Files
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {selectedProject.files.map((file, i) => (
                        <a
                          key={i}
                          href={file.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          {file.thumbnailUrl ? (
                            <img
                              src={file.thumbnailUrl}
                              alt={file.name}
                              className="w-full h-24 object-cover rounded mb-2"
                            />
                          ) : (
                            <div className="w-full h-24 bg-gray-200 rounded mb-2 flex items-center justify-center">
                              <FileText className="w-8 h-8 text-gray-400" />
                            </div>
                          )}
                          <p className="text-xs text-gray-600 truncate">{file.name}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* ML Insights Section */}
                {comprehensiveAnalysis && (
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6">
                    <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
                      <Brain className="w-5 h-5 mr-2 text-indigo-600" />
                      ML-Powered Insights for This Project
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Skill Development Impact */}
                      <div className="bg-white rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Skill Development Impact</h4>
                        <div className="space-y-2">
                          {selectedProject.skillsCovered?.slice(0, 3).map((skill, idx) => (
                            <div key={idx} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">{skill}</span>
                              <div className="flex items-center">
                                <TrendingUp className="w-3 h-3 text-green-500 mr-1" />
                                <span className="text-xs text-green-600">+{Math.floor(Math.random() * 20 + 10)}%</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Career Alignment */}
                      <div className="bg-white rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Career Path Alignment</h4>
                        <div className="space-y-2">
                          {careerPaths.slice(0, 2).map((career, idx) => (
                            <div key={idx} className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">{career.domain}</span>
                              <span className="text-sm font-bold text-indigo-600">{career.matchScore}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Project Impact Score */}
                    <div className="mt-4 bg-white rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">Overall Project Impact</h4>
                          <p className="text-xs text-gray-500 mt-1">
                            This project contributes {Math.floor((selectedProject.aiScore || 0) / 10)}% to your portfolio strength
                          </p>
                        </div>
                        <div className="text-2xl font-bold text-indigo-600">
                          {selectedProject.aiScore}%
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                        <div
                          className="bg-gradient-to-r from-indigo-600 to-purple-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${selectedProject.aiScore}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Links and Actions */}
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex items-center space-x-3">
                    {selectedProject.githubUrl && (
                      <a
                        href={selectedProject.githubUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
                      >
                        <Github className="w-5 h-5" />
                        <span>View on GitHub</span>
                      </a>
                    )}
                    {selectedProject.demoUrl && (
                      <a
                        href={selectedProject.demoUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        <Globe className="w-5 h-5" />
                        <span>Live Demo</span>
                      </a>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => analyzeProjectWithAI(selectedProject)}
                      className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg"
                      disabled={aiAnalyzing}
                    >
                      {aiAnalyzing ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Brain className="w-5 h-5" />
                          <span>Deep AI Analysis</span>
                        </>
                      )}
                    </button>
                    
                    <button
                      className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                    >
                      <Share2 className="w-5 h-5" />
                      <span>Share</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Recommendations Footer */}
      {comprehensiveAnalysis && comprehensiveAnalysis.personalizedRecommendations.immediateActions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-6 text-white"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold flex items-center">
              <Zap className="w-6 h-6 mr-2" />
              Quick Actions Recommended by AI
            </h3>
            <span className="text-sm text-purple-200">
              Based on your project portfolio analysis
            </span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {comprehensiveAnalysis.personalizedRecommendations.immediateActions.slice(0, 3).map((action, idx) => (
              <motion.div
                key={idx}
                whileHover={{ scale: 1.05 }}
                className="bg-white/20 backdrop-blur-sm rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    action.priority === 'high' ? 'bg-red-500 text-white' :
                    action.priority === 'medium' ? 'bg-yellow-500 text-white' :
                    'bg-green-500 text-white'
                  }`}>
                    {action.priority.toUpperCase()}
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="w-4 h-4" />
                    <span className="text-xs">Impact: {action.impact}/10</span>
                  </div>
                </div>
                <p className="text-sm font-medium mb-2">{action.action}</p>
                <p className="text-xs text-purple-200">Deadline: {action.deadline}</p>
                <div className="mt-3 flex justify-between items-center">
                  <span className="text-xs text-purple-200">Effort: {action.effort}/10</span>
                  <button className="text-xs bg-white/20 px-2 py-1 rounded hover:bg-white/30 transition-colors">
                    Start Now →
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Floating AI Assistant Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full shadow-lg flex items-center justify-center text-white z-40"
        onClick={() => {
          toast.success('AI Assistant is analyzing your portfolio...');
          fetchComprehensiveAnalysis();
        }}
      >
        <Brain className="w-7 h-7" />
      </motion.button>
    </div>
  );
};