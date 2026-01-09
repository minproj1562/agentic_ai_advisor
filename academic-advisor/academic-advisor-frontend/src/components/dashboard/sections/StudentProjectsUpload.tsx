// src/components/dashboard/sections/StudentProjectsUpload.tsx
import React, { useState, useCallback, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  X,
  Github,
  Globe,
  Users,
  Code,
  Package,
  Wrench,
  Award,
  Target,
  BookOpen,
  Sparkles,
  FileText,
  File,
  CheckCircle,
  AlertCircle,
  Loader2,
  ChevronRight,
  Brain,
  Cloud,
  CheckCheck,
  XCircle
} from 'lucide-react';
import { studentProjectsService } from '../../../services/student_projects_cloudinary.service';
import { toast } from 'react-hot-toast';
import { ProjectAnalysisResults } from './ProjectAnalysisResults';
import { useAuth } from '../../../contexts/AuthContext';

// =============================================
// INTERFACES
// =============================================

interface ProjectFormData {
  title: string;
  description: string;
  detailedDescription: string;
  projectType: string;
  startDate: string;
  endDate: string;
  programmingLanguages: string[];
  frameworks: string[];
  tools: string[];
  githubUrl: string;
  demoUrl: string;
  isTeamProject: boolean;
  teamSize: number;
  teamMembers: Array<{
    name: string;
    role: string;
    contribution: string;
  }>;
  keyAchievements: string[];
  challengesFaced: string[];
  learnings: string[];
}

interface ProjectFile {
  file: File;
  preview?: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

// =============================================
// INITIAL FORM STATE
// =============================================

const INITIAL_FORM_DATA: ProjectFormData = {
  title: '',
  description: '',
  detailedDescription: '',
  projectType: 'personal',
  startDate: '',
  endDate: '',
  programmingLanguages: [],
  frameworks: [],
  tools: [],
  githubUrl: '',
  demoUrl: '',
  isTeamProject: false,
  teamSize: 1,
  teamMembers: [],
  keyAchievements: [],
  challengesFaced: [],
  learnings: []
};

// =============================================
// MAIN COMPONENT
// =============================================

export const StudentProjectsUpload: React.FC = () => {
  // =============================================
  // STATE
  // =============================================
  
  const [formData, setFormData] = useState<ProjectFormData>(INITIAL_FORM_DATA);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [interestProfile, setInterestProfile] = useState<any>(null);
  
  // Modal state
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisData, setAnalysisData] = useState<any>(null);
  
  const { user } = useAuth();

  // =============================================
  // HELPER FUNCTIONS
  // =============================================

  const getUserBranch = (): string => {
    return localStorage.getItem('userBranch') || 'IT';
  };

  const getUserSemester = (): number => {
    return parseInt(localStorage.getItem('userSemester') || '5');
  };

  // =============================================
  // FILE HANDLING - DROPZONE
  // =============================================

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      preview: file.type.startsWith('image/') 
        ? URL.createObjectURL(file) 
        : undefined,
      progress: 0,
      status: 'pending' as const
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/*': ['.txt', '.md'],
      'application/zip': ['.zip'],
      'application/x-tar': ['.tar'],
      'application/gzip': ['.gz']
    },
    maxSize: 10485760 // 10MB
  });

  // Cleanup file previews on unmount
  useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
    };
  }, [files]);

  const removeFile = (index: number): void => {
    setFiles(prev => {
      const newFiles = [...prev];
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview);
      }
      return newFiles.filter((_, i) => i !== index);
    });
  };

  // =============================================
  // TAG HANDLING (Languages, Frameworks, Tools)
  // =============================================

  const addTag = (
    field: 'programmingLanguages' | 'frameworks' | 'tools', 
    value: string
  ): void => {
    const trimmedValue = value.trim();
    if (trimmedValue && !formData[field].includes(trimmedValue)) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], trimmedValue]
      }));
    }
  };

  const removeTag = (
    field: 'programmingLanguages' | 'frameworks' | 'tools', 
    value: string
  ): void => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter(t => t !== value)
    }));
  };

  // =============================================
  // LIST ITEM HANDLING (Achievements, Challenges, Learnings)
  // =============================================

  const addListItem = (
    field: 'keyAchievements' | 'challengesFaced' | 'learnings', 
    value: string
  ): void => {
    const trimmedValue = value.trim();
    if (trimmedValue) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], trimmedValue]
      }));
    }
  };

  const removeListItem = (
    field: 'keyAchievements' | 'challengesFaced' | 'learnings', 
    index: number
  ): void => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  // =============================================
  // FORM RESET
  // =============================================

  const resetForm = useCallback(() => {
    setFormData(INITIAL_FORM_DATA);
    setFiles([]);
    setCurrentStep(1);
  }, []);

  // =============================================
  // MODAL CLOSE HANDLER
  // =============================================

  const handleCloseModal = useCallback(() => {
    console.log('User closing modal');
    setShowAnalysisModal(false);
    setAnalysisData(null);
    resetForm();
    
    // Dispatch event to refresh dashboard ONLY when user closes modal
    window.dispatchEvent(new Event('projectUploaded'));
  }, [resetForm]);

  // =============================================
  // FORM SUBMISSION
  // =============================================

  const handleSubmit = async (): Promise<void> => {
    console.log('Starting project submission...');
    setIsSubmitting(true);
    
    try {
      // Validate required fields
      if (!formData.title || !formData.description) {
        toast.error('Please fill in all required fields');
        setIsSubmitting(false);
        return;
      }

      // Update file status to uploading
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'uploading' as const, 
        progress: 0 
      })));

      // Prepare project data
      const projectData = {
        ...formData,
        startDate: new Date(formData.startDate).toISOString(),
        endDate: formData.endDate 
          ? new Date(formData.endDate).toISOString() 
          : null
      };

      // Step 1: Get comprehensive analysis
      let analysis = null;
      
      try {
        console.log('Fetching comprehensive analysis...');
        analysis = await studentProjectsService.analyzeProjectComprehensive(
          projectData,
          files.map(f => f.file)
        );
        console.log('Analysis received:', analysis);
      } catch (analysisError) {
        console.error('Analysis error:', analysisError);
        // Continue with upload even if analysis fails
      }

      // Step 2: Upload project to database
      console.log('Uploading project...');
      await studentProjectsService.createProject(
        projectData,
        files.map(f => f.file),
        (fileIndex, progress) => {
          setFiles(prev => prev.map((f, idx) => 
            idx === fileIndex 
              ? { 
                  ...f, 
                  progress, 
                  status: progress === 100 ? 'completed' as const : 'uploading' as const 
                }
              : f
          ));
        }
      );

      console.log('Project uploaded successfully');
      toast.success('Project uploaded successfully!');

      // Step 3: Show analysis modal if we have valid data
      if (analysis && analysis.inferred_interests && analysis.inferred_interests.length > 0) {
        console.log('Opening analysis modal...');
        setAnalysisData(analysis);
        setShowAnalysisModal(true);
        // DON'T reset form here - let modal close handler do it
      } else {
        // No analysis available, just reset and refresh
        console.log('No analysis data, resetting form');
        resetForm();
        window.dispatchEvent(new Event('projectUploaded'));
      }

    } catch (error: any) {
      console.error('Submission error:', error);
      toast.error(error.message || 'Failed to upload project');
      
      // Update file status to error
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'error' as const,
        error: error.message 
      })));
    } finally {
      setIsSubmitting(false);
    }
  };

  // =============================================
  // FETCH INTEREST PROFILE ON MOUNT
  // =============================================

  useEffect(() => {
    const fetchInterestProfile = async (): Promise<void> => {
      try {
        const profile = await studentProjectsService.getInterestProfile();
        setInterestProfile(profile);
      } catch (error) {
        console.error('Error fetching interest profile:', error);
      }
    };
    
    fetchInterestProfile();
  }, []);

  // =============================================
  // STEP VALIDATION
  // =============================================

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        if (!formData.title || !formData.description || !formData.startDate) {
          toast.error('Please fill in all required fields');
          return false;
        }
        break;
      case 2:
        if (formData.programmingLanguages.length === 0) {
          toast.error('Please add at least one programming language');
          return false;
        }
        break;
    }
    return true;
  };

  const goToNextStep = (): void => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    }
  };

  // =============================================
  // RENDER
  // =============================================

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      
      {/* ==================== HEADER ==================== */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Upload Your Projects</h1>
            <p className="text-purple-100">
              Share your projects and let AI discover your interests and career paths
            </p>
            <div className="flex items-center mt-3 text-sm text-purple-200">
              <Cloud className="w-4 h-4 mr-1" />
              <span>Powered by Cloudinary for secure file storage</span>
            </div>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
            <Brain className="w-12 h-12" />
          </div>
        </div>
      </div>

      {/* ==================== PROGRESS STEPS ==================== */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              className={`flex items-center ${step < 4 ? 'flex-1' : ''}`}
            >
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center 
                  font-semibold transition-all
                  ${currentStep >= step
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white scale-110'
                    : 'bg-gray-200 text-gray-500'
                  }
                `}
              >
                {currentStep > step ? <CheckCheck className="w-5 h-5" /> : step}
              </div>
              {step < 4 && (
                <div
                  className={`flex-1 h-1 mx-2 transition-all ${currentStep > step ? 'bg-purple-600' : 'bg-gray-200'}`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-4">
          <span className="text-sm font-medium">Basic Info</span>
          <span className="text-sm font-medium">Technical Details</span>
          <span className="text-sm font-medium">Outcomes</span>
          <span className="text-sm font-medium">Files & Submit</span>
        </div>
      </div>

      {/* ==================== FORM CONTENT ==================== */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <AnimatePresence mode="wait">
          
          {/* ==================== STEP 1: Basic Info ==================== */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
              
              {/* Project Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="e.g., AI-Powered Task Management System"
                />
              </div>

              {/* Project Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Type *
                </label>
                <select
                  value={formData.projectType}
                  onChange={(e) => setFormData(prev => ({ ...prev, projectType: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="academic">Academic Project</option>
                  <option value="personal">Personal Project</option>
                  <option value="hackathon">Hackathon</option>
                  <option value="internship">Internship</option>
                  <option value="competition">Competition</option>
                  <option value="research">Research</option>
                  <option value="open_source">Open Source</option>
                  <option value="freelance">Freelance</option>
                </select>
              </div>

              {/* Short Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Short Description *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={3}
                  placeholder="Brief overview of your project (2-3 sentences)"
                />
              </div>

              {/* Detailed Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Detailed Description
                </label>
                <textarea
                  value={formData.detailedDescription}
                  onChange={(e) => setFormData(prev => ({ ...prev, detailedDescription: e.target.value }))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  rows={6}
                  placeholder="Detailed explanation of your project, its features, and technical implementation"
                />
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, startDate: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, endDate: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Team Project Toggle */}
              <div className="flex items-center space-x-6">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.isTeamProject}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      isTeamProject: e.target.checked,
                      teamSize: e.target.checked ? 2 : 1
                    }))}
                    className="mr-2 rounded text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm font-medium">Team Project</span>
                </label>
                
                {formData.isTeamProject && (
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4 text-gray-500" />
                    <input
                      type="number"
                      min="2"
                      max="10"
                      value={formData.teamSize}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        teamSize: parseInt(e.target.value) || 2
                      }))}
                      className="w-20 px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-purple-500"
                    />
                    <span className="text-sm text-gray-600">members</span>
                  </div>
                )}
              </div>

              {/* Navigation */}
              <div className="flex justify-end">
                <button
                  onClick={goToNextStep}
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ==================== STEP 2: Technical Details ==================== */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <h2 className="text-xl font-semibold mb-4">Technical Details</h2>

              {/* Programming Languages */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Code className="inline w-4 h-4 mr-1" />
                  Programming Languages *
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.programmingLanguages.map((lang, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm flex items-center"
                    >
                      {lang}
                      <button
                        onClick={() => removeTag('programmingLanguages', lang)}
                        className="ml-2 hover:text-purple-900"
                        type="button"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add language (e.g., Python, JavaScript) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag('programmingLanguages', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                {/* Quick Add Buttons */}
                <div className="mt-2 flex flex-wrap gap-2">
                  {['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'React', 'Node.js'].map(lang => (
                    <button
                      key={lang}
                      onClick={() => addTag('programmingLanguages', lang)}
                      type="button"
                      className="text-xs px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
                    >
                      + {lang}
                    </button>
                  ))}
                </div>
              </div>

              {/* Frameworks & Libraries */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Package className="inline w-4 h-4 mr-1" />
                  Frameworks & Libraries
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.frameworks.map((framework, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm flex items-center"
                    >
                      {framework}
                      <button
                        onClick={() => removeTag('frameworks', framework)}
                        className="ml-2 hover:text-indigo-900"
                        type="button"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add framework (e.g., React, TensorFlow) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag('frameworks', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Tools & Technologies */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Wrench className="inline w-4 h-4 mr-1" />
                  Tools & Technologies
                </label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.tools.map((tool, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm flex items-center"
                    >
                      {tool}
                      <button
                        onClick={() => removeTag('tools', tool)}
                        className="ml-2 hover:text-green-900"
                        type="button"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add tool (e.g., Docker, AWS, Git) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addTag('tools', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Project Links */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Github className="inline w-4 h-4 mr-1" />
                    GitHub Repository URL
                  </label>
                  <input
                    type="url"
                    value={formData.githubUrl}
                    onChange={(e) => setFormData(prev => ({ ...prev, githubUrl: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="https://github.com/username/repository"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Globe className="inline w-4 h-4 mr-1" />
                    Live Demo URL
                  </label>
                  <input
                    type="url"
                    value={formData.demoUrl}
                    onChange={(e) => setFormData(prev => ({ ...prev, demoUrl: e.target.value }))}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="https://your-project-demo.com"
                  />
                </div>
              </div>

              {/* Navigation */}
              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep(1)}
                  type="button"
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentStep(3)}
                  type="button"
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ==================== STEP 3: Outcomes ==================== */}
          {currentStep === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <h2 className="text-xl font-semibold mb-4">Project Outcomes & Learnings</h2>

              {/* Key Achievements */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Award className="inline w-4 h-4 mr-1" />
                  Key Achievements
                </label>
                <div className="space-y-2 mb-2">
                  {formData.keyAchievements.map((achievement, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      <span className="flex-1 px-3 py-2 bg-green-50 rounded-lg text-sm">
                        {achievement}
                      </span>
                      <button
                        onClick={() => removeListItem('keyAchievements', index)}
                        type="button"
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add achievement (e.g., Reduced processing time by 50%) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addListItem('keyAchievements', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Challenges Faced */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <AlertCircle className="inline w-4 h-4 mr-1" />
                  Challenges Faced
                </label>
                <div className="space-y-2 mb-2">
                  {formData.challengesFaced.map((challenge, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <Target className="w-4 h-4 text-orange-500 flex-shrink-0" />
                      <span className="flex-1 px-3 py-2 bg-orange-50 rounded-lg text-sm">
                        {challenge}
                      </span>
                      <button
                        onClick={() => removeListItem('challengesFaced', index)}
                        type="button"
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add challenge (e.g., Optimizing database queries) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addListItem('challengesFaced', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Key Learnings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <BookOpen className="inline w-4 h-4 mr-1" />
                  Key Learnings
                </label>
                <div className="space-y-2 mb-2">
                  {formData.learnings.map((learning, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0" />
                      <span className="flex-1 px-3 py-2 bg-purple-50 rounded-lg text-sm">
                        {learning}
                      </span>
                      <button
                        onClick={() => removeListItem('learnings', index)}
                        type="button"
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="Add learning (e.g., Importance of code documentation) and press Enter"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addListItem('learnings', e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Navigation */}
              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep(2)}
                  type="button"
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentStep(4)}
                  type="button"
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:shadow-lg transition-shadow flex items-center space-x-2"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ==================== STEP 4: Files & Submit ==================== */}
          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <h2 className="text-xl font-semibold mb-4">Upload Project Files</h2>

              {/* Cloud Storage Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start space-x-3">
                <Cloud className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-blue-800 font-medium">Secure Cloud Storage</p>
                  <p className="text-xs text-blue-600 mt-1">
                    Your files will be securely uploaded to Cloudinary's cloud storage. 
                    Maximum file size: 10MB per file.
                  </p>
                </div>
              </div>

              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                  ${isDragActive 
                    ? 'border-purple-500 bg-purple-50' 
                    : 'border-gray-300 hover:border-purple-400'
                  }
                `}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                {isDragActive ? (
                  <p className="text-purple-600 font-medium">Drop the files here...</p>
                ) : (
                  <>
                    <p className="text-gray-600 font-medium mb-2">
                      Drag & drop project files here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports images, PDFs, documents, and code archives (Max 10MB per file)
                    </p>
                  </>
                )}
              </div>

              {/* File List */}
              {files.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">Files to Upload</h3>
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className={`
                        p-3 rounded-lg transition-all
                        ${file.status === 'error' 
                          ? 'bg-red-50 border border-red-200' 
                          : 'bg-gray-50'
                        }
                      `}
                    >
                      <div className="flex items-center space-x-3">
                        {/* File Preview/Icon */}
                        {file.preview ? (
                          <img
                            src={file.preview}
                            alt={file.file.name}
                            className="w-10 h-10 rounded object-cover"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center">
                            {file.file.type.includes('pdf') ? (
                              <FileText className="w-5 h-5 text-gray-600" />
                            ) : (
                              <File className="w-5 h-5 text-gray-600" />
                            )}
                          </div>
                        )}
                        
                        {/* File Info */}
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{file.file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        
                        {/* Status Indicators */}
                        {file.status === 'pending' && (
                          <button
                            onClick={() => removeFile(index)}
                            type="button"
                            className="text-red-500 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        
                        {file.status === 'uploading' && (
                          <div className="flex items-center space-x-2">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                            <span className="text-xs text-blue-600">{file.progress}%</span>
                          </div>
                        )}
                        
                        {file.status === 'completed' && (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        )}
                        
                        {file.status === 'error' && (
                          <div className="flex items-center space-x-2">
                            <XCircle className="w-5 h-5 text-red-500" />
                            <span className="text-xs text-red-600">Failed</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Progress Bar */}
                      {file.status === 'uploading' && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* Error Message */}
                      {file.status === 'error' && file.error && (
                        <p className="text-xs text-red-600 mt-1">{file.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Submit Section */}
              <div className="border-t pt-6">
                <div className="flex justify-between">
                  <button
                    onClick={() => setCurrentStep(3)}
                    disabled={isSubmitting}
                    type="button"
                    className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !formData.title || !formData.description}
                    type="button"
                    className={`
                      px-8 py-3 rounded-lg font-medium flex items-center space-x-2 transition-all
                      ${isSubmitting || !formData.title || !formData.description
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:shadow-lg'
                      }
                    `}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Uploading to Cloud...</span>
                      </>
                    ) : (
                      <>
                        <Cloud className="w-5 h-5" />
                        <span>Upload Project</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ==================== ANALYSIS MODAL (Portal) ==================== */}
      {showAnalysisModal && analysisData && ReactDOM.createPortal(
        <ProjectAnalysisResults
          analysis={analysisData}
          onClose={handleCloseModal}
          studentBranch={getUserBranch()}
          studentSemester={getUserSemester()}
        />,
        document.body
      )}

      {/* ==================== INTEREST PROFILE SUMMARY ==================== */}
      {interestProfile && 
       interestProfile.topDomains && 
       interestProfile.topDomains.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Your Interest Profile</h2>
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {interestProfile.topDomains.map((domain: any, index: number) => (
              <div
                key={index}
                className="p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-800">{domain.name}</span>
                  <span className="text-sm text-purple-600">{domain.strength}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${domain.strength}%` }}
                  />
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  {domain.projectCount} projects
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};