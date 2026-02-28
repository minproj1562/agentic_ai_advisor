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

// Enhanced interfaces for comprehensive analysis
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
  match_score: number;
  reasons: string[];
  skills_to_gain: string[];
  career_relevance: string;
  difficulty_level: string;
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
}

export interface SkillGapAnalysis {
  current_skills: string[];
  required_skills: string[];
  skill_gaps: string[];
  priority_skills: string[];
  learning_resources: Record<string, string[]>;
  estimated_learning_time: string;
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

class StudentProjectsCloudinaryService {
  private readonly COLLECTION = 'student_projects';
  private readonly API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  private axiosInstance = axios.create({
    baseURL: this.API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  constructor() {
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

      // Create project document
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

      // Save to Firestore
      await setDoc(doc(db, this.COLLECTION, projectId), projectDoc);

      // Generate AI interests
      const inferredInterests = this.analyzeProjectInterests(projectData);

      // Update user's interest profile
      await this.updateUserInterestProfile(user.uid, inferredInterests);

      // Dispatch event for dashboard refresh
      //window.dispatchEvent(new Event('projectUploaded'));

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

async analyzeProjectComprehensive(
    projectData: any,
    files?: File[]
  ): Promise<ComprehensiveAnalysis> {
    try {
      const formData = new FormData();
      
      const studentBranch = localStorage.getItem('userBranch') || 'IT';
      const studentSemester = parseInt(localStorage.getItem('userSemester') || '5');
      
      formData.append('project_data', JSON.stringify(projectData));
      formData.append('student_branch', studentBranch);
      formData.append('student_semester', studentSemester.toString());
      
      if (files && files.length > 0) {
        files.forEach(file => {
          formData.append('files', file);
        });
      }
      
      const response = await fetch(`${this.API_BASE_URL}/student-projects/analyze-comprehensive`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${await this.getAuthToken()}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Analysis failed' }));
        throw new Error(error.detail || 'Analysis failed');
      }
      
      const result = await response.json();
      
      // ═══════════════════════════════════════════════════════════
      //  ROBUST RESPONSE PARSING
      //  The backend can return:
      //    A) Legacy format (top-level fields)
      //    B) Nested under result.analysis
      //    C) New format with cumulative_recommendations
      // ═══════════════════════════════════════════════════════════
      
      const source = result.analysis || result;
      
      // Parse inferred interests (handle both formats)
      const inferredInterests: InferredInterest[] = (source.inferred_interests || []).map((i: any) => ({
        domain: i.domain || '',
        confidence: i.confidence || 0,
        keywords: i.keywords || i.matched_keywords || [],
        relatedSkills: i.relatedSkills || i.related_skills || [],
        careerPaths: i.careerPaths || i.career_paths || [],
        industryRelevance: i.industryRelevance || i.industry_relevance || (i.confidence * 0.9),
        reasoning: i.reasoning || `Detected from project analysis`,
        evidence: i.evidence || i.keywords || [],
      }));
      
      // Parse elective recommendations (handle both legacy and cumulative)
      let electiveRecs: ElectiveRecommendation[] = [];
      if (source.elective_recommendations && source.elective_recommendations.length > 0) {
        // Legacy format from backend
        electiveRecs = source.elective_recommendations.map((e: any) => ({
          elective: e.elective || e.elective_name || '',
          code: e.code || e.elective_code || '',
          match_score: e.match_score || 0,
          reasons: e.reasons || [e.match_explanation || 'Based on your profile'],
          skills_to_gain: e.skills_to_gain || e.skill_alignment || [],
          career_relevance: e.career_relevance || '',
          difficulty_level: e.difficulty_level || 'Intermediate',
        }));
      } else if (source.cumulative_recommendations?.electives) {
        // New cumulative format
        electiveRecs = source.cumulative_recommendations.electives.map((e: any) => ({
          elective: e.elective_name || '',
          code: e.elective_code || '',
          match_score: e.match_score || 0,
          reasons: [e.match_explanation || 'Based on cumulative analysis'],
          skills_to_gain: e.skill_alignment || [],
          career_relevance: (e.career_relevance || []).join(', '),
          difficulty_level: 'Intermediate',
        }));
      }
      
      // Parse honours recommendations
      let honoursRecs: HonoursRecommendation[] = [];
      if (source.honours_minor_recommendations && source.honours_minor_recommendations.length > 0) {
        honoursRecs = source.honours_minor_recommendations;
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
        }));
      }
      
      // Parse career paths
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
      
      // Parse skill gap analysis
      const skillGap: SkillGapAnalysis = source.skill_gap_analysis || {
        current_skills: source.cumulative_recommendations?.electives?.[0]?.skill_alignment || [],
        required_skills: [],
        skill_gaps: [],
        priority_skills: [],
        learning_resources: {},
        estimated_learning_time: '2-3 months',
      };
      
      // Parse next steps
      const nextSteps: NextStep[] = (source.next_steps || []).map((s: any) => ({
        category: s.category || 'General',
        action: s.action || '',
        deadline: s.deadline || 'This semester',
        priority: s.priority || 'medium',
        details: s.details || '',
      }));
      
      const validatedAnalysis: ComprehensiveAnalysis = {
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
        },
      };
      
      // Store for quick access
      localStorage.setItem('latestAnalysis', JSON.stringify(validatedAnalysis));
      localStorage.setItem('analysisDate', new Date().toISOString());
      
      console.log('✅ Analysis parsed successfully:', {
        interests: validatedAnalysis.inferred_interests.length,
        electives: validatedAnalysis.elective_recommendations.length,
        honours: validatedAnalysis.honours_minor_recommendations.length,
        careers: validatedAnalysis.career_paths.length,
        nextSteps: validatedAnalysis.next_steps.length,
      });
      
      return validatedAnalysis;
      
    } catch (error: any) {
      console.error('Comprehensive analysis error:', error);
      return this.fallbackFrontendAnalysis(projectData, files || []);
    }
  }

  private fallbackFrontendAnalysis(
    projectData: any,
    files: File[]
  ): ComprehensiveAnalysis {
    try {
      const studentBranch = localStorage.getItem('userBranch') || 'IT';
      const studentSemester = parseInt(localStorage.getItem('userSemester') || '5');
      
      // Generate comprehensive analysis using frontend logic
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
          confidence_score: 0.7, // Lower confidence for frontend analysis
          error: 'Backend analysis failed, using frontend fallback'
        }
      };

    } catch (error: any) {
      console.error('Error in frontend fallback analysis:', error);
      
      // Return empty analysis structure on error
      return {
        inferred_interests: [],
        elective_recommendations: [],
        honours_minor_recommendations: [],
        career_paths: [],
        skill_gap_analysis: {
          current_skills: projectData.programmingLanguages || [],
          required_skills: [],
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

  // Existing methods remain the same...
  private recommendElectives(projectData: any, branch: string, semester: number): ElectiveRecommendation[] {
    const recommendations: ElectiveRecommendation[] = [];
    
    // IT Branch Semester 5 Electives
    if (branch === 'IT' && semester === 5) {
      // Data Warehousing
      if (projectData.tools?.some((t: string) => 
        ['SQL', 'Database', 'ETL', 'BI'].some(keyword => t.toLowerCase().includes(keyword.toLowerCase()))
      )) {
        recommendations.push({
          elective: 'Data Warehousing',
          match_score: 92,
          reasons: [
            'Your experience with databases aligns perfectly',
            'Critical for data-driven career paths',
            'Builds on your existing SQL knowledge'
          ],
          skills_to_gain: ['ETL', 'OLAP', 'Data Modeling', 'Business Intelligence'],
          career_relevance: 'Essential for Data Analyst and BI Developer roles',
          difficulty_level: 'Moderate - Well prepared'
        });
      }

      // Cloud Computing
      if (projectData.tools?.some((t: string) => 
        ['Docker', 'AWS', 'Cloud', 'Kubernetes'].some(keyword => t.toLowerCase().includes(keyword.toLowerCase()))
      )) {
        recommendations.push({
          elective: 'Cloud Computing',
          match_score: 88,
          reasons: [
            'Your DevOps tools experience is valuable',
            'High industry demand for cloud skills',
            'Natural progression from your current skills'
          ],
          skills_to_gain: ['AWS', 'Azure', 'Docker', 'Microservices', 'Serverless'],
          career_relevance: 'Critical for modern tech careers',
          difficulty_level: 'Moderate - Some preparation needed'
        });
      }
    }

    // Default recommendation if no specific matches
    if (recommendations.length === 0) {
      recommendations.push({
        elective: 'Cloud Computing',
        match_score: 75,
        reasons: [
          'Universal relevance in modern tech',
          'High industry demand',
          'Complements any tech stack'
        ],
        skills_to_gain: ['Cloud Architecture', 'DevOps', 'Scalability'],
        career_relevance: 'Essential for most tech careers',
        difficulty_level: 'Challenging - Preparation required'
      });
    }

    return recommendations;
  }

private recommendHonoursPrograms(
  projectData: any, 
  branch: string,
  interests: InferredInterest[]
): HonoursRecommendation[] {
  const recommendations: HonoursRecommendation[] = [];
  
  // IT Department specific programmes
  const IT_HONOURS = ['Cybersecurity', 'AI & Machine Learning', 'AIML'];
  const IT_MINORS = ['Data Science', 'Cloud Computing', 'Blockchain', 'Full Stack Development', 'IoT', 'DevOps'];
  
  // Helper function to determine type for IT branch
  const getProgrammeTypeForIT = (programName: string): 'Honours' | 'Minor' => {
    const nameLower = programName.toLowerCase();
    if (IT_HONOURS.some(h => nameLower.includes(h.toLowerCase()))) {
      return 'Honours';
    }
    return 'Minor';
  };
  
  // AI & ML - Honours for IT
  if (interests.some(i => i.domain.includes('AI') || i.domain.includes('Machine Learning'))) {
    if (['IT', 'COMP', 'EXTC'].includes(branch)) {
      recommendations.push({
        program: 'AI & Machine Learning',
        type: branch === 'IT' ? 'Honours' : (branch === 'COMP' ? 'Honours' : 'Minor'),
        match_score: 90,
        reasons: [
          'Strong alignment with your AI/ML interests',
          'Your programming skills provide solid foundation',
          'Excellent career prospects in AI field'
        ],
        courses: ['Knowledge Engineering', 'Foundation ML', 'Deep Learning', 'Advanced AI'],
        career_paths: ['ML Engineer', 'AI Researcher', 'Data Scientist'],
        skills_to_develop: ['TensorFlow', 'PyTorch', 'Neural Networks', 'NLP'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true
      });
    }
  }

  // Cybersecurity - Honours for IT
  if (interests.some(i => 
    i.domain.includes('Security') || 
    i.domain.includes('Cyber') ||
    i.domain.includes('Network')
  ) || projectData.tools?.some((t: string) => 
    ['Security', 'Crypto', 'Firewall', 'Penetration'].some(kw => 
      t.toLowerCase().includes(kw.toLowerCase())
    )
  )) {
    recommendations.push({
      program: 'Cybersecurity',
      type: branch === 'IT' ? 'Honours' : 'Minor',  // ✅ FIXED: Honours for IT only
      match_score: 85,
      reasons: [
        'Strong alignment with security interests',
        'High industry demand for cybersecurity professionals',
        'Critical for modern tech careers'
      ],
      courses: ['Network Security', 'Cryptography', 'Ethical Hacking', 'Security Operations'],
      career_paths: ['Security Analyst', 'Penetration Tester', 'Security Architect'],
      skills_to_develop: ['Ethical Hacking', 'SIEM', 'Incident Response', 'Compliance'],
      semester_commitment: '4 semesters (Sem V-VIII)',
      credits: 18,
      eligibility_met: true
    });
  }

  // Data Science - Minor for IT
  if (interests.some(i => i.domain.includes('Data'))) {
    recommendations.push({
      program: 'Data Science',
      type: branch === 'IT' ? 'Minor' : (branch === 'COMP' ? 'Honours' : 'Minor'),  // ✅ FIXED: Minor for IT
      match_score: 85,
      reasons: [
        'Aligns with data-focused projects',
        'High industry demand',
        'Complements programming skills'
      ],
      courses: ['Statistical Methods', 'Big Data', 'Machine Learning', 'Visualization'],
      career_paths: ['Data Scientist', 'Data Analyst', 'Business Intelligence Analyst'],
      skills_to_develop: ['Python', 'R', 'SQL', 'Tableau'],
      semester_commitment: '4 semesters (Sem V-VIII)',
      credits: 18,
      eligibility_met: true
    });
  }

  // Cloud Computing - Minor for IT
  if (projectData.tools?.some((t: string) => 
    ['Docker', 'AWS', 'Cloud', 'Kubernetes', 'Azure', 'GCP'].some(keyword => 
      t.toLowerCase().includes(keyword.toLowerCase())
    )
  )) {
    recommendations.push({
      program: 'Cloud Computing',
      type: 'Minor',  // ✅ Always Minor for IT
      match_score: 80,
      reasons: [
        'Your DevOps tools experience is valuable',
        'High industry demand for cloud skills',
        'Natural progression from your current skills'
      ],
      courses: ['Cloud Architecture', 'AWS Services', 'Azure', 'Kubernetes'],
      career_paths: ['Cloud Architect', 'DevOps Engineer', 'SRE'],
      skills_to_develop: ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Terraform'],
      semester_commitment: '4 semesters (Sem V-VIII)',
      credits: 18,
      eligibility_met: true
    });
  }

  // Blockchain - Minor for IT
  if (projectData.programmingLanguages?.includes('Solidity') ||
      interests.some(i => i.domain.toLowerCase().includes('blockchain'))) {
    recommendations.push({
      program: 'Blockchain Technology',
      type: 'Minor',  // ✅ Always Minor for IT
      match_score: 78,
      reasons: [
        'Emerging field with high potential',
        'Unique skill combination',
        'Growing industry demand'
      ],
      courses: ['Intro Blockchain', 'Smart Contracts', 'DApp Development', 'Web3'],
      career_paths: ['Blockchain Developer', 'Smart Contract Engineer', 'Web3 Developer'],
      skills_to_develop: ['Solidity', 'Web3.js', 'Ethereum', 'Hyperledger'],
      semester_commitment: '4 semesters (Sem V-VIII)',
      credits: 18,
      eligibility_met: true
    });
  }

  // Research option
  if (projectData.projectType === 'research' || projectData.keyAchievements?.some((a: string) => 
    a.toLowerCase().includes('publish') || a.toLowerCase().includes('paper')
  )) {
    recommendations.push({
      program: 'Honours in Research',
      type: 'Research',
      match_score: 88,
      reasons: [
        'Research experience demonstrated',
        'Path to publication/patent',
        'IIT/TIFR collaboration opportunity'
      ],
      courses: ['Research Methodology', 'Literature Review', 'Research Project'],
      career_paths: ['Research Scientist', 'PhD Candidate', 'R&D Engineer'],
      skills_to_develop: ['Research Methods', 'Academic Writing', 'Data Analysis'],
      semester_commitment: '4 semesters (Sem V-VIII)',
      credits: 18,
      eligibility_met: true
    });
  }

  return recommendations;
}

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
        
        paths.push({
          title: career,
          match_score: Math.round(interest.confidence * 100),
          source_domains: [interest.domain],
          required_skills: interest.relatedSkills,
          honours_program: relevantHonours?.program,
          market_demand: this.getMarketDemand(career),
          salary_range: this.getSalaryRange(career),
          growth_potential: this.getGrowthPotential(career),
          preparation_path: this.getPreparationPath(career)
        });
      });
    });

    // Sort and deduplicate
    const uniquePaths = paths.reduce((acc: CareerPath[], current) => {
      const exists = acc.find(item => item.title === current.title);
      if (!exists) {
        acc.push(current);
      }
      return acc;
    }, []);

    return uniquePaths.sort((a, b) => b.match_score - a.match_score).slice(0, 5);
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

    const prioritySkills = skillGaps.slice(0, 5);

    const learningResources: Record<string, string[]> = {};
    prioritySkills.forEach(skill => {
      learningResources[skill] = this.getLearningResources(skill);
    });

    return {
      current_skills: currentSkills,
      required_skills: Array.from(requiredSkills),
      skill_gaps: skillGaps,
      priority_skills: prioritySkills,
      learning_resources: learningResources,
      estimated_learning_time: `${prioritySkills.length * 2} weeks`
    };
  }

  private generateNextSteps(semester: number, honoursPrograms: HonoursRecommendation[]): NextStep[] {
    const steps: NextStep[] = [];

    if (semester === 4) {
      steps.push({
        category: 'Academic',
        action: 'Apply for Honours/Minor Program',
        deadline: 'Before Semester 5 registration',
        priority: 'High',
        details: honoursPrograms.length > 0 
          ? `Consider ${honoursPrograms[0].program} (${honoursPrograms[0].match_score}% match)`
          : 'Review available Honours/Minor options'
      });
    }

    if (semester >= 5) {
      steps.push({
        category: 'Academic',
        action: 'Select Next Semester Electives',
        deadline: 'Registration period',
        priority: 'High',
        details: 'Choose electives aligned with your career goals'
      });
    }

    steps.push({
      category: 'Skills',
      action: 'Start Online Certification',
      deadline: 'Next 2 months',
      priority: 'Medium',
      details: 'Focus on cloud computing or data science certifications'
    });

    steps.push({
      category: 'Portfolio',
      action: 'Build Advanced Project',
      deadline: 'This semester',
      priority: 'Medium',
      details: 'Create a project showcasing your specialized skills'
    });

    return steps;
  }

  private getMarketDemand(career: string): string {
    const highDemand = ['ML Engineer', 'Data Scientist', 'Cloud Architect', 'DevOps Engineer'];
    if (highDemand.some(hd => career.includes(hd))) return 'Very High';
    if (career.includes('Developer')) return 'High';
    return 'Moderate';
  }

  private getSalaryRange(career: string): string {
    const salaryMap: Record<string, string> = {
      'ML Engineer': '8-25 LPA',
      'Data Scientist': '7-22 LPA',
      'Full Stack Developer': '5-18 LPA',
      'Cloud Architect': '12-30 LPA',
      'DevOps Engineer': '6-20 LPA'
    };
    
    for (const [key, value] of Object.entries(salaryMap)) {
      if (career.includes(key)) return value;
    }
    return '5-15 LPA';
  }

  private getGrowthPotential(career: string): string {
    if (career.includes('AI') || career.includes('ML') || career.includes('Cloud')) {
      return 'Excellent';
    }
    if (career.includes('Developer') || career.includes('Engineer')) {
      return 'Good';
    }
    return 'Moderate';
  }

  private getPreparationPath(career: string): string[] {
    const basePath = [
      'Complete relevant electives',
      'Choose appropriate Honours/Minor program',
      'Build portfolio projects'
    ];

    if (career.includes('ML') || career.includes('Data')) {
      return [
        ...basePath,
        'Master Python and ML libraries',
        'Participate in Kaggle competitions',
        'Get cloud ML certifications'
      ];
    }

    if (career.includes('Cloud') || career.includes('DevOps')) {
      return [
        ...basePath,
        'Get AWS/Azure certifications',
        'Learn containerization (Docker/Kubernetes)',
        'Practice CI/CD pipelines'
      ];
    }

    return [...basePath, 'Gain internship experience', 'Network with professionals'];
  }

  private getLearningResources(skill: string): string[] {
    const resourceMap: Record<string, string[]> = {
      'Python': ['Python for Everybody (Coursera)', 'Real Python', 'Python Crash Course'],
      'Machine Learning': ['Andrew Ng ML Course', 'Fast.ai', 'Kaggle Learn'],
      'Cloud': ['AWS Training', 'Google Cloud Skills', 'Azure Learn'],
      'Docker': ['Docker Official Docs', 'Docker Mastery Course', 'Play with Docker'],
      'React': ['React Official Tutorial', 'Scrimba React', 'FreeCodeCamp React']
    };

    for (const [key, resources] of Object.entries(resourceMap)) {
      if (skill.toLowerCase().includes(key.toLowerCase())) {
        return resources;
      }
    }

    return ['YouTube Tutorials', 'Official Documentation', 'Udemy Courses'];
  }

  private analyzeProjectInterests(projectData: any): InferredInterest[] {
    const interests: InferredInterest[] = [];
    const { programmingLanguages = [], frameworks = [], tools = [] } = projectData;

    // Enhanced AI/ML Interest Detection
    if (programmingLanguages.includes('Python') || 
        frameworks.some((f: string) => ['TensorFlow', 'PyTorch', 'Scikit-learn'].includes(f))) {
      interests.push({
        domain: 'Artificial Intelligence & Machine Learning',
        confidence: 0.90,
        keywords: ['Machine Learning', 'Deep Learning', 'Neural Networks', 'Data Science', 'AI'],
        relatedSkills: ['TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Jupyter'],
        careerPaths: ['ML Engineer', 'Data Scientist', 'AI Researcher'],
        industryRelevance: 0.95,
        reasoning: 'Strong alignment with AI/ML based on technology stack',
        evidence: ['Uses Python', 'ML frameworks detected']
      });
    }

    // Web Development Interest
    if (programmingLanguages.some((lang: string) => 
      ['JavaScript', 'TypeScript', 'HTML', 'CSS'].includes(lang)) ||
      frameworks.some((f: string) => 
      ['React', 'Angular', 'Vue', 'Node.js', 'Express'].includes(f))) {
      interests.push({
        domain: 'Web Development',
        confidence: 0.85,
        keywords: ['Web Development', 'Frontend', 'Backend', 'Full Stack'],
        relatedSkills: ['JavaScript', 'React', 'Node.js', 'CSS', 'APIs'],
        careerPaths: ['Frontend Developer', 'Backend Developer', 'Full Stack Developer'],
        industryRelevance: 0.90,
        reasoning: 'Web technologies detected in project stack',
        evidence: ['Web frameworks/languages used']
      });
    }

    // Data Engineering Interest
    if (tools.some((t: string) => 
      ['SQL', 'Database', 'PostgreSQL', 'MongoDB', 'ETL'].some(keyword => t.includes(keyword)))) {
      interests.push({
        domain: 'Data Engineering',
        confidence: 0.80,
        keywords: ['Data Engineering', 'Databases', 'ETL', 'Data Pipelines'],
        relatedSkills: ['SQL', 'Database Design', 'ETL', 'Data Modeling'],
        careerPaths: ['Data Engineer', 'Database Administrator', 'ETL Developer'],
        industryRelevance: 0.88,
        reasoning: 'Database and data processing tools detected',
        evidence: ['Database technologies used']
      });
    }

    return interests;
  }

  // Keep all other existing methods...
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

      await deleteDoc(doc(db, this.COLLECTION, projectId));
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
      const domains = Object.entries(profile.domains)
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

  private async updateUserInterestProfile(userId: string, newInterests: any[]) {
    try {
      const userDocRef = doc(db, 'users', userId);
      const userDoc = await getDoc(userDocRef);
      
      if (userDoc.exists()) {
        const currentProfile = userDoc.data().interestProfile || { domains: {} };
        
        newInterests.forEach(interest => {
          const domain = interest.domain;
          if (!currentProfile.domains[domain]) {
            currentProfile.domains[domain] = {
              score: 0,
              count: 0,
              keywords: [],
              lastUpdated: null
            };
          }
          
          currentProfile.domains[domain].score = 
            (currentProfile.domains[domain].score * currentProfile.domains[domain].count + interest.confidence) / 
            (currentProfile.domains[domain].count + 1);
          currentProfile.domains[domain].count += 1;
          currentProfile.domains[domain].keywords = [
            ...new Set([...currentProfile.domains[domain].keywords, ...interest.keywords])
          ].slice(0, 10);
          currentProfile.domains[domain].lastUpdated = new Date().toISOString();
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

  async getEligibleHonoursPrograms(branch: string): Promise<HonoursRecommendation[]> {
    // This would normally call your backend
    // For now, returning static data based on FCRIT handbook
    const programs: HonoursRecommendation[] = [];
    
    if (['IT', 'COMP', 'EXTC'].includes(branch)) {
      programs.push({
        program: 'AI & Machine Learning',
        type: 'Honours',
        match_score: 0,
        reasons: [],
        courses: ['Knowledge Engineering', 'Foundation ML', 'Deep Learning', 'Advanced AI'],
        career_paths: ['ML Engineer', 'AI Researcher', 'Data Scientist'],
        skills_to_develop: ['Python', 'TensorFlow', 'Neural Networks'],
        semester_commitment: '4 semesters (Sem V-VIII)',
        credits: 18,
        eligibility_met: true
      });
    }
    
    return programs;
  }

  async getAvailableElectives(branch: string, semester: number): Promise<any> {
    // Return electives based on branch and semester
    if (branch === 'IT' && semester === 5) {
      return {
        'Data Warehousing': {
          credits: 3,
          description: 'Learn ETL, OLAP, dimensional modeling',
          prerequisites: ['Database Management Systems']
        },
        'Cloud Computing': {
          credits: 3,
          description: 'Master cloud platforms, Docker, Kubernetes',
          prerequisites: ['Computer Networks']
        }
      };
    }
    
    return {};
  }

  // Utility method to get latest analysis from localStorage
  getLatestAnalysis(): ComprehensiveAnalysis | null {
    try {
      const stored = localStorage.getItem('latestAnalysis');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  // Utility method to clear stored analysis
  clearStoredAnalysis(): void {
    localStorage.removeItem('latestAnalysis');
    localStorage.removeItem('analysisDate');
  }
}

export const studentProjectsService = new StudentProjectsCloudinaryService();