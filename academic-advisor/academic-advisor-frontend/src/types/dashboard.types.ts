// types/dashboard.types.ts
export interface Faculty {
  id: string;
  name: string;
  email: string;
  department: string;
  profilePhoto: string;
  role: 'Professor' | 'Associate Professor' | 'Assistant Professor';
  expertise: string[];
  joinedDate: Date;
  totalMentees: number;
  badges?: Badge[];
}

export interface Student {
  id: string;
  name: string;
  email: string;
  rollNumber: string;
  currentSGPI: number;
  sgpiTrend: number[]; // Last 4 semesters
  weakSubjects: Subject[];
  strongSubjects: Subject[];
  lastInteraction: Date;
  status: 'Active' | 'At Risk' | 'Improving';
}

export interface Subject {
  name: string;
  grade: string;
  confidenceLevel: number; // 0-100
}

export interface CVMetadata {
  uploadedAt: Date;
  fileName: string;
  extractedSkills: Skill[];
  researchAreas: string[];
  publications: number;
  experience: string;
  lastAnalyzed: Date;
}

export interface Skill {
  name: string;
  category: 'Technical' | 'Research' | 'Soft Skill';
  confidence: number; // 0-100
}

export interface MentorshipSlot {
  id: string;
  date: Date;
  startTime: string;
  endTime: string;
  isBooked: boolean;
  studentId?: string;
  type: 'Regular' | 'Emergency' | 'Group';
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  timestamp: Date;
  isRead: boolean;
  actionUrl?: string;
}

export interface Badge {
  id: string;
  name: string;
  icon: string;
  description: string;
  earnedDate: Date;
}

export interface DashboardStats {
  totalMentees: number;
  atRiskStudents: number;
  improvingStudents: number;
  upcomingSlots: number;
  unreadNotifications: number;
}

export interface DashboardData {
  faculty: Faculty;
  mentees: Student[];
  cvMetadata: CVMetadata | null;
  mentorshipSlots: MentorshipSlot[];
  notifications: Notification[];
  stats: DashboardStats;
}