// src/services/student_projects_cloudinary.service.ts
import {
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  query,
  where,
  orderBy,
  serverTimestamp,
  updateDoc,
  deleteDoc
} from 'firebase/firestore';
import { auth, db } from './firebase.config';
import { cloudinaryService } from './cloudinary.service';
import axios from 'axios';

// =============================================
// INTERFACES
// =============================================

export interface InferredInterest {
  domain: string;
  confidence: number;
  keywords: string[];
  relatedSkills: string[];
  careerPaths: string[];
  industryRelevance: number;
  reasoning?: string;
  evidence?: string[];
}

export interface ElectiveRecommendation {
  elective: string;
  code?: string;
  match_score: number;
  reasons: string[];
  skills_to_gain: string[];
  career_relevance: string;
  difficulty_level: string;
  score_breakdown?: any;
  ranking_explanation?: any;
  confidence?: any;
}

export interface HonoursRecommendation {
  program: string;
  type: 'Honours' | 'Minor' | 'Research';
  match_score: number;
  reasons: string[];
  courses: string[];
  career_paths: string[];
  skills_to_develop: string[];
  semester_commitment: string;
  credits: number;
  eligibility_met: boolean;
  score_breakdown?: any;
}

export interface CareerPath {
  title: string;
  match_score: number;
  source_domains: string[];
  required_skills: string[];
  honours_program?: string;
  market_demand: string;
  salary_range: string;
  growth_potential: string;
  preparation_path: string[];
  companies_hiring?: string[];
}

export interface SkillGapAnalysis {
  current_skills: string[];
  required_skills?: string[];
  skill_gaps: string[];
  priority_skills: string[];
  learning_resources: Record<string, string[]>;
  estimated_learning_time: string;
  completeness_percentage?: number;
}

export interface NextStep {
  category: string;
  action: string;
  deadline: string;
  priority: string;
  details: string;
}

export interface ComprehensiveAnalysis {
  inferred_interests: InferredInterest[];
  elective_recommendations: ElectiveRecommendation[];
  honours_minor_recommendations: HonoursRecommendation[];
  career_paths: CareerPath[];
  skill_gap_analysis: SkillGapAnalysis;
  next_steps: NextStep[];
  metadata?: {
    analysis_date: string;
    student_branch: string;
    student_semester: number;
    confidence_score: number;
    error?: string;
    ml_model_used?: boolean;
    files_parsed?: number;
  };
  data_summary?: {
    total_marks_subjects: number;
    total_interests: number;
    total_projects: number;
    cgpa: number;
  };
}

interface ProjectFile {
  name: string;
  url: string;
  publicId: string;
  thumbnailUrl?: string;
  size: number;
  type: string;
  uploadedAt: string;
}

// =============================================
// SERVICE CLASS
// =============================================

class StudentProjectsCloudinaryService {
  private readonly COLLECTION = 'student_projects';
  
   private readonly API_BASE_URL: string;
  private axiosInstance;

  constructor() {
    const rawUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
    
    // If VITE_API_URL already has /api/v1, use it; otherwise add it
    if (rawUrl.endsWith('/api/v1')) {
      this.API_BASE_URL = rawUrl;
    } else {
      this.API_BASE_URL = `${rawUrl}/api/v1`;
    }

    console.log('🔧 StudentProjects API URL:', this.API_BASE_URL);

    this.axiosInstance = axios.create({
      baseURL: this.API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000,
    });

    // Add auth interceptor
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        const user = auth.currentUser;
        if (user) {
          const token = await user.getIdToken();
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  private async getAuthToken(): Promise<string> {
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }
    return await user.getIdToken();
  }


  // =============================================
  // CREATE PROJECT (saves to Firestore + triggers backend MongoDB save)
  // =============================================

  async createProject(
    projectData: any,
    files?: File[],
    onUploadProgress?: (fileIndex: number, progress: number) => void
  ) {
    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }

      // Upload files to Cloudinary
      let uploadedFiles: ProjectFile[] = [];

      if (files && files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];

          const validation = cloudinaryService.validateFile(file);
          if (!validation.valid) {
            console.error(`File ${file.name} validation failed:`, validation.error);
            continue;
          }

          try {
            const uploadResult = await cloudinaryService.uploadFile(
              file,
              `student_projects/${user.uid}`,
              (progress) => onUploadProgress?.(i, progress)
            );

            uploadedFiles.push({
              name: file.name,
              url: uploadResult.secure_url,
              publicId: uploadResult.public_id,
              thumbnailUrl: uploadResult.thumbnail_url ||
                cloudinaryService.getThumbnailUrl(uploadResult.public_id),
              size: file.size,
              type: file.type,
              uploadedAt: new Date().toISOString()
            });
          } catch (error) {
            console.error(`Failed to upload file ${file.name}:`, error);
          }
        }
      }

      // Create project document for Firestore
      const projectId = `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const projectDoc = {
        ...projectData,
        id: projectId,
        userId: user.uid,
        userEmail: user.email,
        files: uploadedFiles,
        fileCount: uploadedFiles.length,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'active'
      };

      // Save to Firestore (for frontend listing)
      await setDoc(doc(db, this.COLLECTION, projectId), projectDoc);
      console.log('✅ Project saved to Firestore:', projectId);

      // Also save to MongoDB via backend (for ML recommendations)
      try {
        await this.saveProjectToBackend(projectData, uploadedFiles);
        console.log('✅ Project also saved to MongoDB via backend');
      } catch (backendError) {
        console.warn('⚠️ Backend MongoDB save failed (analysis will still work):', backendError);
      }

      // Generate local interests for Firestore profile
      const inferredInterests = this.analyzeProjectInterests(projectData);
      await this.updateUserInterestProfile(user.uid, inferredInterests);

      return {
        success: true,
        projectId,
        uploadedFiles,
        inferredInterests
      };
    } catch (error: any) {
      console.error('Error in createProject:', error);
      throw new Error(`Failed to create project: ${error.message}`);
    }
  }

  // =============================================
  // SAVE PROJECT TO BACKEND (MongoDB)
  // =============================================

  private async saveProjectToBackend(projectData: any, uploadedFiles: ProjectFile[]) {
    try {
      const payload = {
        title: projectData.title,
        description: projectData.description,
        detailed_description: projectData.detailedDescription || '',
        project_type: projectData.projectType || 'personal',
        start_date: projectData.startDate,
        end_date: projectData.endDate,
        programming_languages: projectData.programmingLanguages || [],
        frameworks: projectData.frameworks || [],
        tools: projectData.tools || [],
        technologies: projectData.technologies || [],
        github_url: projectData.githubUrl || '',
        demo_url: projectData.demoUrl || '',
        is_team_project: projectData.isTeamProject || false,
        team_size: projectData.teamSize || 1,
        key_achievements: projectData.keyAchievements || [],
        challenges_faced: projectData.challengesFaced || [],
        learnings: projectData.learnings || [],
        files: uploadedFiles.map(f => ({
          name: f.name,
          url: f.url,
          size: f.size,
          type: f.type,
        })),
      };

      await this.axiosInstance.post('/student-projects/save-project', payload);
    } catch (error) {
      // Non-critical - the analyze-comprehensive endpoint also saves
      console.warn('Direct project save to backend failed:', error);
    }
  }

  // =============================================
  // COMPREHENSIVE ANALYSIS (the main AI analysis)
  // =============================================

  async analyzeProjectComprehensive(
    projectData: any,
    files?: File[]
  ): Promise<ComprehensiveAnalysis> {
    try {
      const formData = new FormData();

      const studentBranch = localStorage.getItem('userBranch') || 'IT';
      const studentSemester = parseInt(localStorage.getItem('userSemester') || '5');

      // Send project data as JSON string
      formData.append('project_data', JSON.stringify({
        title: projectData.title,
        description: projectData.description,
        detailedDescription: projectData.detailedDescription || '',
        projectType: projectData.projectType || 'personal',
        startDate: projectData.startDate,
        endDate: projectData.endDate,
        programmingLanguages: projectData.programmingLanguages || [],
        frameworks: projectData.frameworks || [],
        tools: projectData.tools || [],
        technologies: projectData.technologies || [],
        githubUrl: projectData.githubUrl || '',
        demoUrl: projectData.demoUrl || '',
        isTeamProject: projectData.isTeamProject || false,
        teamSize: projectData.teamSize || 1,
        keyAchievements: projectData.keyAchievements || [],
        challengesFaced: projectData.challengesFaced || [],
        learnings: projectData.learnings || [],
      }));

      formData.append('student_branch', studentBranch);
      formData.append('student_semester', studentSemester.toString());

      if (files && files.length > 0) {
        files.forEach(file => {
          formData.append('files', file);
        });
      }

      console.log('🔄 Sending analysis request to backend...');
      console.log('   Branch:', studentBranch, 'Semester:', studentSemester);
      console.log('   Skills:', projectData.programmingLanguages);
      console.log('   Frameworks:', projectData.frameworks);
      console.log('   Tools:', projectData.tools);

      const token = await this.getAuthToken();

      const response = await fetch(`${this.API_BASE_URL}/student-projects/analyze-comprehensive`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Backend analysis failed:', response.status, errorText);

        let errorDetail = 'Analysis failed';
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorDetail;
        } catch {
          // not JSON
        }
        throw new Error(errorDetail);
      }

      const result = await response.json();
      console.log('✅ Raw backend response received:', Object.keys(result));

      // Parse the response into our frontend format
      const analysis = this.parseBackendResponse(result, studentBranch, studentSemester);

      // Store for quick access
      localStorage.setItem('latestAnalysis', JSON.stringify(analysis));
      localStorage.setItem('analysisDate', new Date().toISOString());

      console.log('✅ Analysis parsed successfully:', {
        interests: analysis.inferred_interests.length,
        electives: analysis.elective_recommendations.length,
        honours: analysis.honours_minor_recommendations.length,
        careers: analysis.career_paths.length,
        nextSteps: analysis.next_steps.length,
      });

      return analysis;

    } catch (error: any) {
      console.error('❌ Comprehensive analysis error:', error);
      console.log('🔄 Falling back to frontend analysis...');
      return this.fallbackFrontendAnalysis(projectData, files || []);
    }
  }

  // =============================================
  // PARSE BACKEND RESPONSE (handles all formats)
  // =============================================

  private parseBackendResponse(
    result: any,
    studentBranch: string,
    studentSemester: number
  ): ComprehensiveAnalysis {
    // The backend can return data at top level OR nested under result.analysis
    const source = result.analysis || result;

    // --- Parse inferred interests ---
    const inferredInterests: InferredInterest[] = (source.inferred_interests || []).map((i: any) => ({
      domain: i.domain || '',
      confidence: i.confidence || 0,
      keywords: i.keywords || i.matched_keywords || [],
      relatedSkills: i.relatedSkills || i.related_skills || [],
      careerPaths: i.careerPaths || i.career_paths || [],
      industryRelevance: i.industryRelevance || i.industry_relevance || (i.confidence * 0.9),
      reasoning: i.reasoning || 'Detected from project analysis',
      evidence: i.evidence || i.keywords || i.matched_keywords || [],
    }));

    // --- Parse elective recommendations ---
    let electiveRecs: ElectiveRecommendation[] = [];

    // Try top-level elective_recommendations first
    if (source.elective_recommendations && source.elective_recommendations.length > 0) {
      electiveRecs = source.elective_recommendations.map((e: any) => ({
        elective: e.elective || e.elective_name || '',
        code: e.code || e.elective_code || '',
        match_score: e.match_score || 0,
        reasons: e.reasons || [e.match_explanation || 'Based on your profile'],
        skills_to_gain: e.skills_to_gain || e.skill_alignment || [],
        career_relevance: Array.isArray(e.career_relevance)
          ? e.career_relevance.join(', ')
          : e.career_relevance || '',
        difficulty_level: e.difficulty_level || 'Intermediate',
        score_breakdown: e.score_breakdown || null,
        ranking_explanation: e.ranking_explanation || null,
        confidence: e.confidence || null,
      }));
    }
    // Try cumulative_recommendations.electives
    else if (source.cumulative_recommendations?.electives) {
      electiveRecs = source.cumulative_recommendations.electives.map((e: any) => ({
        elective: e.elective_name || e.elective || '',
        code: e.elective_code || '',
        match_score: e.match_score || 0,
        reasons: [e.match_explanation || 'Based on cumulative analysis'],
        skills_to_gain: e.skill_alignment || [],
        career_relevance: Array.isArray(e.career_relevance)
          ? e.career_relevance.join(', ')
          : e.career_relevance || '',
        difficulty_level: 'Intermediate',
        score_breakdown: e.score_breakdown || null,
        ranking_explanation: e.ranking_explanation || null,
        confidence: e.confidence || null,
      }));
    }

    // --- Parse honours recommendations ---
    let honoursRecs: HonoursRecommendation[] = [];

    if (source.honours_minor_recommendations && source.honours_minor_recommendations.length > 0) {
      honoursRecs = source.honours_minor_recommendations.map((h: any) => ({
        program: h.program || '',
        type: h.type || 'Honours',
        match_score: h.match_score || 0,
        reasons: h.reasons || [h.explanation || 'Based on your profile'],
        courses: h.courses || h.skills_gained || [],
        career_paths: h.career_paths || [],
        skills_to_develop: h.skills_to_develop || h.skills_gained || [],
        semester_commitment: h.semester_commitment || '4 semesters (Sem V-VIII)',
        credits: h.credits || 18,
        eligibility_met: h.eligibility_met !== undefined ? h.eligibility_met : (h.eligibility !== false),
        score_breakdown: h.score_breakdown || null,
      }));
    } else if (source.cumulative_recommendations?.honours) {
      honoursRecs = source.cumulative_recommendations.honours.map((h: any) => ({
        program: h.program || '',
        type: h.type || 'Honours',
        match_score: h.match_score || 0,
        reasons: [h.explanation || 'Based on your profile'],
        courses: h.skills_gained || h.courses || [],
        career_paths: h.career_paths || [],
        skills_to_develop: h.skills_gained || [],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: h.eligibility !== false,
        score_breakdown: h.score_breakdown || null,
      }));
    }

    // --- Parse career paths ---
    let careerPaths: CareerPath[] = [];

    if (source.career_paths && source.career_paths.length > 0) {
      careerPaths = source.career_paths.map((c: any) => ({
        title: c.title || c.career || '',
        match_score: c.match_score || 0,
        source_domains: c.source_domains || [],
        required_skills: c.required_skills || c.missing_skills || [],
        honours_program: c.honours_program,
        market_demand: c.market_demand || c.growth_potential || 'High',
        salary_range: c.salary_range || '',
        growth_potential: c.growth_potential || 'High',
        preparation_path: c.preparation_path || [],
        companies_hiring: c.companies_hiring || c.top_companies || [],
      }));
    } else if (source.cumulative_recommendations?.careers) {
      careerPaths = source.cumulative_recommendations.careers.map((c: any) => ({
        title: c.career || '',
        match_score: c.match_score || 0,
        source_domains: [],
        required_skills: c.missing_skills || [],
        market_demand: c.growth_potential === 'Very High' ? 'Very High' : 'High',
        salary_range: c.salary_range || '',
        growth_potential: c.growth_potential || 'High',
        preparation_path: c.preparation_path || [],
        companies_hiring: c.top_companies || [],
      }));
    }

    // --- Parse skill gap analysis ---
    const rawSkillGap = source.skill_gap_analysis || {};
    const skillGap: SkillGapAnalysis = {
      current_skills: rawSkillGap.current_skills || [],
      required_skills: rawSkillGap.required_skills || [],
      skill_gaps: rawSkillGap.skill_gaps || [],
      priority_skills: rawSkillGap.priority_skills || [],
      learning_resources: rawSkillGap.learning_resources || {},
      estimated_learning_time: rawSkillGap.estimated_learning_time || '2-3 months',
      completeness_percentage: rawSkillGap.completeness_percentage || 0,
    };

    // --- Parse next steps ---
    const nextSteps: NextStep[] = (source.next_steps || []).map((s: any) => ({
      category: s.category || 'General',
      action: s.action || '',
      deadline: s.deadline || 'This semester',
      priority: s.priority || 'medium',
      details: s.details || '',
    }));

    return {
      inferred_interests: inferredInterests,
      elective_recommendations: electiveRecs,
      honours_minor_recommendations: honoursRecs,
      career_paths: careerPaths,
      skill_gap_analysis: skillGap,
      next_steps: nextSteps,
      metadata: {
        analysis_date: source.metadata?.analysis_date || result.generated_at || new Date().toISOString(),
        student_branch: result.student_info?.branch || studentBranch,
        student_semester: result.student_info?.semester || studentSemester,
        confidence_score: source.metadata?.confidence_score || 0.8,
        ml_model_used: source.metadata?.ml_model_used || false,
        files_parsed: source.metadata?.files_parsed || 0,
      },
      data_summary: result.data_summary || undefined,
    };
  }

  // =============================================
  // FALLBACK FRONTEND ANALYSIS
  // =============================================

  private fallbackFrontendAnalysis(
    projectData: any,
    files: File[]
  ): ComprehensiveAnalysis {
    try {
      const studentBranch = localStorage.getItem('userBranch') || 'IT';
      const studentSemester = parseInt(localStorage.getItem('userSemester') || '5');

      const inferredInterests = this.analyzeProjectInterests(projectData);
      const electiveRecommendations = this.recommendElectives(projectData, studentBranch, studentSemester);
      const honoursRecommendations = this.recommendHonoursPrograms(projectData, studentBranch, inferredInterests);
      const careerPaths = this.generateCareerPaths(inferredInterests, honoursRecommendations);
      const skillGapAnalysis = this.analyzeSkillGaps(projectData, careerPaths);
      const nextSteps = this.generateNextSteps(studentSemester, honoursRecommendations);

      return {
        inferred_interests: inferredInterests,
        elective_recommendations: electiveRecommendations,
        honours_minor_recommendations: honoursRecommendations,
        career_paths: careerPaths,
        skill_gap_analysis: skillGapAnalysis,
        next_steps: nextSteps,
        metadata: {
          analysis_date: new Date().toISOString(),
          student_branch: studentBranch,
          student_semester: studentSemester,
          confidence_score: 0.6,
          error: 'Backend unavailable - using frontend fallback analysis'
        }
      };
    } catch (error: any) {
      console.error('Frontend fallback analysis also failed:', error);
      return {
        inferred_interests: [],
        elective_recommendations: [],
        honours_minor_recommendations: [],
        career_paths: [],
        skill_gap_analysis: {
          current_skills: projectData.programmingLanguages || [],
          skill_gaps: [],
          priority_skills: [],
          learning_resources: {},
          estimated_learning_time: '3-6 months'
        },
        next_steps: [],
        metadata: {
          analysis_date: new Date().toISOString(),
          student_branch: localStorage.getItem('userBranch') || 'IT',
          student_semester: parseInt(localStorage.getItem('userSemester') || '5'),
          confidence_score: 0,
          error: error.message
        }
      };
    }
  }

  // =============================================
  // LOCAL INTEREST ANALYSIS (for fallback + Firestore)
  // =============================================

  private analyzeProjectInterests(projectData: any): InferredInterest[] {
    const interests: InferredInterest[] = [];
    const languages = projectData.programmingLanguages || [];
    const frameworks = projectData.frameworks || [];
    const tools = projectData.tools || [];
    const allTech = [...languages, ...frameworks, ...tools].map(s => s.toLowerCase());
    const textBlob = [
      projectData.title || '',
      projectData.description || '',
      projectData.detailedDescription || '',
      ...allTech,
      ...(projectData.keyAchievements || []),
      ...(projectData.learnings || []),
    ].join(' ').toLowerCase();

    // AI/ML Detection
    const aiKeywords = ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'sklearn',
      'machine learning', 'deep learning', 'neural', 'nlp', 'ai',
      'keras', 'pandas', 'numpy', 'data science', 'model', 'prediction',
      'classification', 'regression', 'computer vision', 'opencv'];
    const aiMatches = aiKeywords.filter(kw => textBlob.includes(kw));
    if (aiMatches.length > 0) {
      interests.push({
        domain: 'Artificial Intelligence & Machine Learning',
        confidence: Math.min(aiMatches.length / 4, 1.0),
        keywords: aiMatches,
        relatedSkills: ['TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn'],
        careerPaths: ['ML Engineer', 'Data Scientist', 'AI Researcher'],
        industryRelevance: 0.95,
        reasoning: 'AI/ML technologies detected in project',
        evidence: aiMatches.slice(0, 5),
      });
    }

    // Web Development Detection
    const webKeywords = ['javascript', 'typescript', 'react', 'angular', 'vue',
      'node', 'express', 'html', 'css', 'frontend', 'backend', 'fullstack',
      'web', 'django', 'flask', 'fastapi', 'next.js', 'rest api'];
    const webMatches = webKeywords.filter(kw => textBlob.includes(kw));
    if (webMatches.length > 0) {
      interests.push({
        domain: 'Web Development',
        confidence: Math.min(webMatches.length / 4, 1.0),
        keywords: webMatches,
        relatedSkills: ['JavaScript', 'React', 'Node.js', 'HTML/CSS', 'TypeScript'],
        careerPaths: ['Full Stack Developer', 'Frontend Developer', 'Backend Developer'],
        industryRelevance: 0.90,
        reasoning: 'Web technologies detected in project',
        evidence: webMatches.slice(0, 5),
      });
    }

    // Cloud & DevOps Detection
    const cloudKeywords = ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'cloud',
      'devops', 'terraform', 'ci/cd', 'jenkins', 'serverless', 'microservices',
      'container', 'deploy', 'hosting'];
    const cloudMatches = cloudKeywords.filter(kw => textBlob.includes(kw));
    if (cloudMatches.length > 0) {
      interests.push({
        domain: 'Cloud & Distributed Systems',
        confidence: Math.min(cloudMatches.length / 4, 1.0),
        keywords: cloudMatches,
        relatedSkills: ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'Linux'],
        careerPaths: ['Cloud Architect', 'DevOps Engineer', 'SRE'],
        industryRelevance: 0.92,
        reasoning: 'Cloud/DevOps tools detected in project',
        evidence: cloudMatches.slice(0, 5),
      });
    }

    // Data Science & Analytics Detection
    const dataKeywords = ['sql', 'database', 'mongodb', 'postgresql', 'data',
      'analytics', 'visualization', 'tableau', 'power bi', 'etl',
      'data warehouse', 'dashboard', 'report', 'bi'];
    const dataMatches = dataKeywords.filter(kw => textBlob.includes(kw));
    if (dataMatches.length > 0) {
      interests.push({
        domain: 'Data Science & Analytics',
        confidence: Math.min(dataMatches.length / 4, 1.0),
        keywords: dataMatches,
        relatedSkills: ['SQL', 'Python', 'Tableau', 'Pandas', 'R'],
        careerPaths: ['Data Analyst', 'BI Developer', 'Data Engineer'],
        industryRelevance: 0.88,
        reasoning: 'Data technologies detected in project',
        evidence: dataMatches.slice(0, 5),
      });
    }

    // IoT & Embedded Detection
    const iotKeywords = ['arduino', 'raspberry pi', 'iot', 'embedded', 'sensor',
      'mqtt', 'bluetooth', 'zigbee', 'microcontroller', 'esp32',
      'smart home', 'wearable', 'gpio'];
    const iotMatches = iotKeywords.filter(kw => textBlob.includes(kw));
    if (iotMatches.length > 0) {
      interests.push({
        domain: 'Mobile & IoT Development',
        confidence: Math.min(iotMatches.length / 3, 1.0),
        keywords: iotMatches,
        relatedSkills: ['Arduino', 'Raspberry Pi', 'C/C++', 'MQTT', 'Sensors'],
        careerPaths: ['IoT Engineer', 'Embedded Developer'],
        industryRelevance: 0.85,
        reasoning: 'IoT/Embedded technologies detected in project',
        evidence: iotMatches.slice(0, 5),
      });
    }

    // Sort by confidence
    interests.sort((a, b) => b.confidence - a.confidence);
    return interests.slice(0, 4);
  }

  // =============================================
  // LOCAL ELECTIVE RECOMMENDATIONS (fallback)
  // =============================================

  private recommendElectives(projectData: any, branch: string, semester: number): ElectiveRecommendation[] {
    const recommendations: ElectiveRecommendation[] = [];
    const allTech = [
      ...(projectData.programmingLanguages || []),
      ...(projectData.frameworks || []),
      ...(projectData.tools || []),
    ].map(s => s.toLowerCase());
    const textBlob = [
      projectData.title || '',
      projectData.description || '',
      ...allTech,
    ].join(' ').toLowerCase();

    // ML
    const mlKeywords = ['python', 'tensorflow', 'pytorch', 'machine learning', 'ai', 'data science', 'neural'];
    const mlHits = mlKeywords.filter(kw => textBlob.includes(kw)).length;
    if (mlHits > 0) {
      recommendations.push({
        elective: 'Machine Learning',
        match_score: Math.min(mlHits * 15 + 30, 95),
        reasons: ['Your Python/AI skills align perfectly', 'High industry demand for ML engineers'],
        skills_to_gain: ['TensorFlow', 'PyTorch', 'Neural Networks', 'NLP'],
        career_relevance: 'Essential for Data Science and AI careers',
        difficulty_level: mlHits >= 3 ? 'Well Prepared' : 'Moderate',
      });
    }

    // Cloud Computing
    const cloudKeywords = ['docker', 'aws', 'cloud', 'kubernetes', 'devops', 'deploy', 'web', 'react', 'node'];
    const cloudHits = cloudKeywords.filter(kw => textBlob.includes(kw)).length;
    if (cloudHits > 0) {
      recommendations.push({
        elective: 'Cloud Computing Services',
        match_score: Math.min(cloudHits * 12 + 30, 92),
        reasons: ['Your DevOps/web experience aligns well', 'Critical for modern deployment'],
        skills_to_gain: ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Serverless'],
        career_relevance: 'Essential for Cloud Architect and DevOps roles',
        difficulty_level: cloudHits >= 3 ? 'Well Prepared' : 'Moderate',
      });
    }

    // DWM
    const dwmKeywords = ['sql', 'database', 'mongodb', 'data', 'analytics', 'etl'];
    const dwmHits = dwmKeywords.filter(kw => textBlob.includes(kw)).length;
    if (dwmHits > 0) {
      recommendations.push({
        elective: 'Data Warehouse and Mining',
        match_score: Math.min(dwmHits * 14 + 25, 90),
        reasons: ['Database skills provide solid foundation', 'Critical for data careers'],
        skills_to_gain: ['ETL', 'OLAP', 'Data Modeling', 'Business Intelligence'],
        career_relevance: 'Essential for Data Analyst and BI Developer roles',
        difficulty_level: 'Moderate',
      });
    }

    // WT
    const wtKeywords = ['iot', 'arduino', 'embedded', 'sensor', 'wireless', 'network', 'microcontroller'];
    const wtHits = wtKeywords.filter(kw => textBlob.includes(kw)).length;
    if (wtHits > 0) {
      recommendations.push({
        elective: 'Wireless Technology',
        match_score: Math.min(wtHits * 14 + 25, 90),
        reasons: ['IoT/embedded experience aligns well', 'Growing IoT market demand'],
        skills_to_gain: ['IoT Protocols', 'Wireless Networks', 'Sensor Integration'],
        career_relevance: 'Essential for IoT Engineer and Network roles',
        difficulty_level: 'Moderate',
      });
    }

    // Default if no matches
    if (recommendations.length === 0) {
      recommendations.push({
        elective: 'Machine Learning',
        match_score: 65,
        reasons: ['Universal relevance in modern tech', 'High industry demand'],
        skills_to_gain: ['Python', 'TensorFlow', 'Data Analysis'],
        career_relevance: 'Applicable across many tech careers',
        difficulty_level: 'Challenging - Preparation needed',
      });
    }

    recommendations.sort((a, b) => b.match_score - a.match_score);
    return recommendations;
  }

  // =============================================
  // LOCAL HONOURS RECOMMENDATIONS (fallback)
  // =============================================

  private recommendHonoursPrograms(
    projectData: any,
    branch: string,
    interests: InferredInterest[]
  ): HonoursRecommendation[] {
    const recommendations: HonoursRecommendation[] = [];
    const interestDomains = interests.map(i => i.domain.toLowerCase());

    if (interestDomains.some(d => d.includes('ai') || d.includes('machine learning'))) {
      recommendations.push({
        program: 'AI & Machine Learning',
        type: branch === 'IT' ? 'Honours' : 'Minor',
        match_score: 90,
        reasons: ['Strong alignment with your AI/ML interests', 'Excellent career prospects'],
        courses: ['Knowledge Engineering', 'Foundation ML', 'Deep Learning', 'Advanced AI'],
        career_paths: ['ML Engineer', 'AI Researcher', 'Data Scientist'],
        skills_to_develop: ['TensorFlow', 'PyTorch', 'Neural Networks', 'NLP'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true,
      });
    }

    if (interestDomains.some(d => d.includes('cloud') || d.includes('web'))) {
      recommendations.push({
        program: 'Cloud Computing',
        type: 'Minor',
        match_score: 80,
        reasons: ['DevOps/cloud tools experience is valuable', 'High industry demand'],
        courses: ['Cloud Architecture', 'AWS Services', 'Kubernetes', 'Serverless'],
        career_paths: ['Cloud Architect', 'DevOps Engineer', 'SRE'],
        skills_to_develop: ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Terraform'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true,
      });
    }

    if (interestDomains.some(d => d.includes('data'))) {
      recommendations.push({
        program: 'Data Science',
        type: branch === 'IT' ? 'Minor' : 'Honours',
        match_score: 85,
        reasons: ['Data-focused project experience', 'High industry demand'],
        courses: ['Statistical Methods', 'Big Data', 'Machine Learning', 'Visualization'],
        career_paths: ['Data Scientist', 'Data Analyst', 'BI Analyst'],
        skills_to_develop: ['Python', 'R', 'SQL', 'Tableau'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true,
      });
    }

    if (recommendations.length === 0) {
      recommendations.push({
        program: 'AI & Machine Learning',
        type: 'Honours',
        match_score: 70,
        reasons: ['Universal relevance', 'Strong career prospects in AI'],
        courses: ['Foundation ML', 'Deep Learning'],
        career_paths: ['ML Engineer', 'Data Scientist'],
        skills_to_develop: ['Python', 'TensorFlow'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true,
      });
    }

    return recommendations;
  }

  // =============================================
  // LOCAL CAREER PATH GENERATION (fallback)
  // =============================================

  private generateCareerPaths(
    interests: InferredInterest[],
    honoursPrograms: HonoursRecommendation[]
  ): CareerPath[] {
    const paths: CareerPath[] = [];

    interests.forEach(interest => {
      interest.careerPaths.forEach(career => {
        const relevantHonours = honoursPrograms.find(h =>
          h.career_paths.includes(career)
        );

        if (!paths.find(p => p.title === career)) {
          paths.push({
            title: career,
            match_score: Math.round(interest.confidence * 100),
            source_domains: [interest.domain],
            required_skills: interest.relatedSkills,
            honours_program: relevantHonours?.program,
            market_demand: this.getMarketDemand(career),
            salary_range: this.getSalaryRange(career),
            growth_potential: this.getGrowthPotential(career),
            preparation_path: this.getPreparationPath(career),
            companies_hiring: [],
          });
        }
      });
    });

    return paths.sort((a, b) => b.match_score - a.match_score).slice(0, 5);
  }

  private analyzeSkillGaps(projectData: any, careerPaths: CareerPath[]): SkillGapAnalysis {
    const currentSkills = [
      ...(projectData.programmingLanguages || []),
      ...(projectData.frameworks || []),
      ...(projectData.tools || [])
    ];

    const requiredSkills = new Set<string>();
    careerPaths.forEach(path => {
      path.required_skills.forEach(skill => requiredSkills.add(skill));
    });

    const skillGaps = Array.from(requiredSkills).filter(skill =>
      !currentSkills.some((cs: string) => cs.toLowerCase() === skill.toLowerCase())
    );

    return {
      current_skills: currentSkills,
      required_skills: Array.from(requiredSkills),
      skill_gaps: skillGaps,
      priority_skills: skillGaps.slice(0, 5),
      learning_resources: {},
      estimated_learning_time: `${Math.max(skillGaps.length * 2, 4)} weeks`
    };
  }

  private generateNextSteps(semester: number, honoursPrograms: HonoursRecommendation[]): NextStep[] {
    const steps: NextStep[] = [];

    if (semester <= 5) {
      steps.push({
        category: 'Academic',
        action: 'Select Next Semester Electives',
        deadline: 'Registration period',
        priority: 'High',
        details: honoursPrograms.length > 0
          ? `Consider electives aligned with ${honoursPrograms[0].program}`
          : 'Choose electives aligned with career goals',
      });
    }

    steps.push({
      category: 'Skills',
      action: 'Start Online Certification',
      deadline: 'Next 2 months',
      priority: 'Medium',
      details: 'Focus on certifications that strengthen your profile',
    });

    steps.push({
      category: 'Portfolio',
      action: 'Upload More Projects',
      deadline: 'Ongoing',
      priority: 'Medium',
      details: 'Each project improves AI recommendation accuracy by 10-15%',
    });

    return steps;
  }

  // =============================================
  // HELPER METHODS
  // =============================================

  private getMarketDemand(career: string): string {
    const highDemand = ['ML Engineer', 'Data Scientist', 'Cloud Architect', 'DevOps Engineer'];
    if (highDemand.some(hd => career.includes(hd))) return 'Very High';
    if (career.includes('Developer')) return 'High';
    return 'Moderate';
  }

  private getSalaryRange(career: string): string {
    const map: Record<string, string> = {
      'ML Engineer': '₹8-25 LPA', 'Data Scientist': '₹7-22 LPA',
      'Full Stack Developer': '₹5-18 LPA', 'Cloud Architect': '₹12-30 LPA',
      'DevOps Engineer': '₹6-20 LPA', 'Frontend Developer': '₹5-15 LPA',
      'Backend Developer': '₹6-18 LPA', 'AI Researcher': '₹10-30 LPA',
      'IoT Engineer': '₹5-14 LPA', 'Data Analyst': '₹4-12 LPA',
    };
    for (const [key, value] of Object.entries(map)) {
      if (career.includes(key)) return value;
    }
    return '₹5-15 LPA';
  }

  private getGrowthPotential(career: string): string {
    if (career.includes('AI') || career.includes('ML') || career.includes('Cloud')) return 'Excellent';
    if (career.includes('Developer') || career.includes('Engineer')) return 'Good';
    return 'Moderate';
  }

  private getPreparationPath(career: string): string[] {
    const base = ['Complete relevant electives', 'Build portfolio projects'];
    if (career.includes('ML') || career.includes('Data')) {
      return [...base, 'Master Python and ML libraries', 'Participate in Kaggle'];
    }
    if (career.includes('Cloud') || career.includes('DevOps')) {
      return [...base, 'Get AWS/Azure certifications', 'Learn Docker/Kubernetes'];
    }
    return [...base, 'Gain internship experience'];
  }

  // =============================================
  // CRUD OPERATIONS
  // =============================================

  async getUserProjects() {
    try {
      const user = auth.currentUser;
      if (!user) return [];

      const projectsRef = collection(db, this.COLLECTION);
      const q = query(projectsRef, where('userId', '==', user.uid));
      const snapshot = await getDocs(q);

      return snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
    } catch (error) {
      console.error('Error fetching projects:', error);
      return [];
    }
  }

  async deleteProject(projectId: string) {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error('User not authenticated');

      // Delete from Firestore
      await deleteDoc(doc(db, this.COLLECTION, projectId));

      // Also delete from MongoDB
      try {
        await this.axiosInstance.delete(`/student-projects/project/${projectId}`);
        console.log('✅ Project deleted from MongoDB');
      } catch (backendErr) {
        console.warn('MongoDB delete failed (non-critical):', backendErr);
      }

      // Invalidate recommendation cache
      try {
        await this.axiosInstance.post('/recommendations/invalidate-cache');
      } catch (cacheErr) {
        console.warn('Cache invalidation failed (non-critical):', cacheErr);
      }

      return { success: true };
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  }

  async getInterestProfile() {
    try {
      const user = auth.currentUser;
      if (!user) return { topDomains: [] };

      const userDoc = await getDoc(doc(db, 'users', user.uid));

      if (!userDoc.exists() || !userDoc.data().interestProfile) {
        return { topDomains: [] };
      }

      const profile = userDoc.data().interestProfile;
      const domains = Object.entries(profile.domains || {})
        .map(([name, data]: any) => ({
          name,
          strength: Math.round(data.score * 100),
          projectCount: data.count,
          keywords: data.keywords
        }))
        .sort((a, b) => b.strength - a.strength)
        .slice(0, 5);

      return { topDomains: domains };
    } catch (error) {
      console.error('Error getting interest profile:', error);
      return { topDomains: [] };
    }
  }

  private async updateUserInterestProfile(userId: string, newInterests: InferredInterest[]) {
    try {
      const userDocRef = doc(db, 'users', userId);
      const userDocSnap = await getDoc(userDocRef);

      if (userDocSnap.exists()) {
        const currentProfile = userDocSnap.data().interestProfile || { domains: {} };

        newInterests.forEach(interest => {
          const domain = interest.domain;
          if (!currentProfile.domains[domain]) {
            currentProfile.domains[domain] = {
              score: 0, count: 0, keywords: [], lastUpdated: null
            };
          }
          const d = currentProfile.domains[domain];
          d.score = (d.score * d.count + interest.confidence) / (d.count + 1);
          d.count += 1;
          d.keywords = [...new Set([...d.keywords, ...interest.keywords])].slice(0, 10);
          d.lastUpdated = new Date().toISOString();
        });

        await updateDoc(userDocRef, {
          interestProfile: currentProfile,
          lastProjectUpload: serverTimestamp()
        });
      }
    } catch (error) {
      console.error('Error updating interest profile:', error);
    }
  }

  // =============================================
  // UTILITY METHODS
  // =============================================

  getLatestAnalysis(): ComprehensiveAnalysis | null {
    try {
      const stored = localStorage.getItem('latestAnalysis');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  clearStoredAnalysis(): void {
    localStorage.removeItem('latestAnalysis');
    localStorage.removeItem('analysisDate');
  }
}

export const studentProjectsService = new StudentProjectsCloudinaryService();