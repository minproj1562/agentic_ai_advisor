// utils/mockData.ts
import { DashboardData } from '../types/dashboard.types'; // ✅ FIXED: Changed from '@/types/dashboard.types' to relative path

export const getMockDashboardData = (facultyId: string): DashboardData => {
  return {
    faculty: {
      id: facultyId,
      name: 'Dr. Sarah Johnson',
      email: 'sarah.johnson@university.edu',
      department: 'Computer Science',
      profilePhoto: '/api/placeholder/100/100',
      role: 'Associate Professor',
      expertise: ['Machine Learning', 'Data Structures', 'AI', 'Cloud Computing'],
      joinedDate: new Date('2018-08-15'),
      totalMentees: 12,
      badges: [
        {
          id: 'badge-1',
          name: 'Mentor Champion',
          icon: '🏆',
          description: 'Mentored 50+ students',
          earnedDate: new Date('2023-06-15')
        },
        {
          id: 'badge-2',
          name: 'Research Star',
          icon: '⭐',
          description: '10+ publications',
          earnedDate: new Date('2023-01-20')
        }
      ]
    },
    mentees: [
      {
        id: 'student-1',
        name: 'Alex Chen',
        email: 'alex.chen@student.edu',
        rollNumber: 'CS2021001',
        currentSGPI: 8.5,
        sgpiTrend: [7.8, 8.0, 8.2, 8.5],
        weakSubjects: [
          { name: 'Operating Systems', grade: 'B', confidenceLevel: 65 },
          { name: 'Compiler Design', grade: 'B-', confidenceLevel: 60 }
        ],
        strongSubjects: [
          { name: 'Data Structures', grade: 'A', confidenceLevel: 90 },
          { name: 'Algorithms', grade: 'A+', confidenceLevel: 95 }
        ],
        lastInteraction: new Date('2024-01-15'),
        status: 'Improving'
      },
      {
        id: 'student-2',
        name: 'Emily Rodriguez',
        email: 'emily.r@student.edu',
        rollNumber: 'CS2021002',
        currentSGPI: 7.2,
        sgpiTrend: [7.5, 7.3, 7.0, 7.2],
        weakSubjects: [
          { name: 'Mathematics III', grade: 'C+', confidenceLevel: 55 },
          { name: 'Database Systems', grade: 'B-', confidenceLevel: 60 }
        ],
        strongSubjects: [
          { name: 'Web Development', grade: 'A', confidenceLevel: 88 },
          { name: 'UI/UX Design', grade: 'A', confidenceLevel: 92 }
        ],
        lastInteraction: new Date('2024-01-18'),
        status: 'At Risk'
      },
      {
        id: 'student-3',
        name: 'Marcus Williams',
        email: 'marcus.w@student.edu',
        rollNumber: 'CS2021003',
        currentSGPI: 9.1,
        sgpiTrend: [8.8, 8.9, 9.0, 9.1],
        weakSubjects: [],
        strongSubjects: [
          { name: 'Machine Learning', grade: 'A+', confidenceLevel: 96 },
          { name: 'Deep Learning', grade: 'A+', confidenceLevel: 94 },
          { name: 'Computer Vision', grade: 'A', confidenceLevel: 90 }
        ],
        lastInteraction: new Date('2024-01-10'),
        status: 'Active'
      }
    ],
    cvMetadata: {
      uploadedAt: new Date('2024-01-01'),
      fileName: 'sarah_johnson_cv_2024.pdf',
      extractedSkills: [
        { name: 'Python', category: 'Technical', confidence: 95 },
        { name: 'TensorFlow', category: 'Technical', confidence: 88 },
        { name: 'Machine Learning', category: 'Research', confidence: 92 },
        { name: 'Research Methodology', category: 'Research', confidence: 85 },
        { name: 'Team Leadership', category: 'Soft Skill', confidence: 80 }
      ],
      researchAreas: ['AI in Education', 'Neural Networks', 'NLP', 'Computer Vision'],
      publications: 24,
      experience: '12 years in academia, 5 years in industry',
      lastAnalyzed: new Date('2024-01-15')
    },
    mentorshipSlots: [
      {
        id: 'slot-1',
        date: new Date('2024-01-22'),
        startTime: '10:00',
        endTime: '11:00',
        isBooked: true,
        studentId: 'student-1',
        type: 'Regular'
      },
      {
        id: 'slot-2',
        date: new Date('2024-01-23'),
        startTime: '14:00',
        endTime: '15:00',
        isBooked: false,
        type: 'Regular'
      },
      {
        id: 'slot-3',
        date: new Date('2024-01-24'),
        startTime: '11:00',
        endTime: '12:00',
        isBooked: true,
        studentId: 'student-2',
        type: 'Emergency'
      }
    ],
    notifications: [
      {
        id: 'notif-1',
        title: 'New Mentee Assigned',
        message: 'John Doe has been assigned to you as a new mentee.',
        type: 'info',
        timestamp: new Date('2024-01-20T09:00:00'),
        isRead: false
      },
      {
        id: 'notif-2',
        title: 'Student At Risk',
        message: 'Emily Rodriguez SGPI dropped below 7.5',
        type: 'warning',
        timestamp: new Date('2024-01-19T14:30:00'),
        isRead: false
      },
      {
        id: 'notif-3',
        title: 'CV Analysis Complete',
        message: 'Your CV has been analyzed successfully',
        type: 'success',
        timestamp: new Date('2024-01-15T11:00:00'),
        isRead: true
      }
    ],
    stats: {
      totalMentees: 12,
      atRiskStudents: 2,
      improvingStudents: 5,
      upcomingSlots: 6,
      unreadNotifications: 2
    }
  };
};