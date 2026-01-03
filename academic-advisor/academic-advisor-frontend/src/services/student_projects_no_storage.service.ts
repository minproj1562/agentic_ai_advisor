// src/services/student_projects_no_storage.service.ts
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

class StudentProjectsNoStorageService {
  private readonly COLLECTION = 'student_projects';

  // Convert file to base64 (for small files only)
  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  }

  // Create project without Firebase Storage
  async createProject(projectData: any, files?: File[]) {
    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }

      console.log('Creating project for user:', user.uid);

      // Handle files locally or with free alternatives
      let fileData: any[] = [];
      
      if (files && files.length > 0) {
        // Option 1: Store small files as base64 (max 1MB recommended)
        for (const file of files) {
          if (file.size < 1048576) { // 1MB limit for base64
            try {
              const base64 = await this.fileToBase64(file);
              fileData.push({
                name: file.name,
                type: file.type,
                size: file.size,
                data: base64, // Store as base64
                uploadedAt: new Date().toISOString()
              });
            } catch (error) {
              console.error('Error converting file:', error);
            }
          } else {
            // For larger files, just store metadata
            fileData.push({
              name: file.name,
              type: file.type,
              size: file.size,
              data: null, // Don't store actual file
              note: 'File too large for free storage',
              uploadedAt: new Date().toISOString()
            });
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
        files: fileData, // Store file data directly in document
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
        status: 'active'
      };

      console.log('Project document to create:', projectDoc);

      // Save to Firestore
      await setDoc(doc(db, this.COLLECTION, projectId), projectDoc);

      console.log('Project created successfully:', projectId);

      // Generate mock AI interests (since we can't afford AI APIs)
      const inferredInterests = this.generateMockInterests(projectData);

      return {
        success: true,
        projectId,
        inferredInterests
      };

    } catch (error: any) {
      console.error('Detailed error creating project:', error);
      throw new Error(`Failed to create project: ${error.message}`);
    }
  }

  // Generate mock interests based on project data
  private generateMockInterests(projectData: any) {
    const interests = [];
    
    // Analyze programming languages
    if (projectData.programmingLanguages?.includes('Python')) {
      interests.push({
        domain: 'Data Science & AI',
        confidence: 0.85,
        keywords: ['Machine Learning', 'Data Analysis', 'AI', 'Neural Networks', 'Python'],
        relatedSkills: ['TensorFlow', 'Pandas', 'NumPy', 'Scikit-learn'],
        careerPaths: ['Data Scientist', 'ML Engineer', 'AI Researcher'],
        industryRelevance: 0.92
      });
    }

    if (projectData.programmingLanguages?.includes('JavaScript') || 
        projectData.frameworks?.includes('React')) {
      interests.push({
        domain: 'Web Development',
        confidence: 0.88,
        keywords: ['Frontend', 'React', 'Web Apps', 'UI/UX', 'JavaScript'],
        relatedSkills: ['Node.js', 'TypeScript', 'Next.js', 'Tailwind CSS'],
        careerPaths: ['Frontend Developer', 'Full Stack Developer', 'Web Developer'],
        industryRelevance: 0.89
      });
    }

    if (projectData.tools?.includes('Docker') || 
        projectData.tools?.includes('Kubernetes')) {
      interests.push({
        domain: 'DevOps & Cloud',
        confidence: 0.75,
        keywords: ['Cloud', 'DevOps', 'CI/CD', 'Infrastructure', 'Automation'],
        relatedSkills: ['AWS', 'Docker', 'Kubernetes', 'Jenkins'],
        careerPaths: ['DevOps Engineer', 'Cloud Architect', 'SRE'],
        industryRelevance: 0.87
      });
    }

    // Default interest if none matched
    if (interests.length === 0) {
      interests.push({
        domain: 'Software Development',
        confidence: 0.70,
        keywords: ['Programming', 'Software', 'Development', 'Technology', 'Innovation'],
        relatedSkills: ['Problem Solving', 'Algorithm Design', 'System Design', 'Testing'],
        careerPaths: ['Software Engineer', 'Developer', 'Tech Lead'],
        industryRelevance: 0.85
      });
    }

    return interests;
  }

  // Get user's projects
  async getUserProjects() {
    try {
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }

      const q = query(
        collection(db, this.COLLECTION),
        where('userId', '==', user.uid),
        orderBy('createdAt', 'desc')
      );

      const snapshot = await getDocs(q);
      const projects = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      return projects;
    } catch (error: any) {
      console.error('Error fetching projects:', error);
      throw error;
    }
  }

  // Get interest profile
  async getInterestProfile() {
    try {
      const projects = await this.getUserProjects();
      
      // Analyze all projects to build profile
      const domainCounts: any = {};
      
      projects.forEach((project: any) => {
        // Count programming languages
        project.programmingLanguages?.forEach((lang: string) => {
          domainCounts[lang] = (domainCounts[lang] || 0) + 1;
        });
      });

      // Convert to profile format
      const topDomains = Object.entries(domainCounts)
        .map(([name, count]) => ({
          name,
          strength: Math.min((count as number) * 20, 100),
          projectCount: count
        }))
        .sort((a, b) => b.strength - a.strength)
        .slice(0, 3);

      return { topDomains };
    } catch (error) {
      console.error('Error getting interest profile:', error);
      return { topDomains: [] };
    }
  }
}

export const studentProjectsService = new StudentProjectsNoStorageService();