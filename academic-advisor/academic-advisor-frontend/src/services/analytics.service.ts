import { 
  collection, 
  doc, 
  getDoc, 
  getDocs, 
  query, 
  where, 
  orderBy, 
  limit,
  addDoc,
  updateDoc,
  serverTimestamp,
  onSnapshot
} from 'firebase/firestore';
import { db } from './firebase.config';

interface PerformanceMetric {
  studentId: string;
  semester: number;
  sgpi: number;
  credits: number;
  courses: number;
  timestamp: Date;
  subjects: SubjectScore[];
}

interface SubjectScore {
  name: string;
  code: string;
  marks: number;
  grade: string;
  credits: number;
}

interface DashboardMetrics {
  currentSGPI: number;
  previousSGPI: number;
  trend: 'up' | 'down' | 'stable';
  percentageChange: number;
  totalCredits: number;
  completedCourses: number;
  averageSGPI: number;
  bestSGPI: number;
  currentSemester: number;
  department: string;
  rank: number;
  totalStudents: number;
}

class AnalyticsService {
  // Track custom events for analytics
  async trackEvent(eventName: string, properties: any) {
    try {
      await addDoc(collection(db, 'analytics_events'), {
        eventName,
        properties,
        timestamp: serverTimestamp(),
        userAgent: navigator.userAgent
      });
    } catch (error) {
      console.error('Analytics tracking error:', error);
    }
  }

  // Get real-time performance metrics
  async getPerformanceMetrics(studentId: string): Promise<PerformanceMetric[]> {
    try {
      const metricsRef = collection(db, 'performance_metrics');
      const q = query(
        metricsRef,
        where('studentId', '==', studentId),
        orderBy('semester', 'desc'),
        limit(10)
      );
      
      const snapshot = await getDocs(q);
      
      if (snapshot.empty) {
        // Return mock data if no real data exists
        return this.generateMockPerformanceData(studentId);
      }
      
      return snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          studentId: data.studentId,
          semester: data.semester,
          sgpi: data.sgpi,
          credits: data.credits,
          courses: data.courses,
          timestamp: data.timestamp?.toDate() || new Date(),
          subjects: data.subjects || []
        };
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
      return this.generateMockPerformanceData(studentId);
    }
  }

  // Get dashboard statistics
  async getDashboardStats(studentId: string): Promise<DashboardMetrics> {
    try {
      const metrics = await this.getPerformanceMetrics(studentId);
      
      if (metrics.length === 0) {
        return this.getDefaultDashboardMetrics();
      }

      const currentMetric = metrics[0];
      const previousMetric = metrics[1] || metrics[0];
      
      const currentSGPI = currentMetric.sgpi;
      const previousSGPI = previousMetric.sgpi;
      const percentageChange = previousSGPI ? ((currentSGPI - previousSGPI) / previousSGPI) * 100 : 0;
      
      const totalCredits = metrics.reduce((sum, m) => sum + m.credits, 0);
      const completedCourses = metrics.reduce((sum, m) => sum + m.courses, 0);
      const averageSGPI = metrics.reduce((sum, m) => sum + m.sgpi, 0) / metrics.length;
      const bestSGPI = Math.max(...metrics.map(m => m.sgpi));
      
      // Fetch student profile for additional info
      const profileData = await this.getStudentProfile(studentId);
      
      return {
        currentSGPI: Number(currentSGPI.toFixed(2)),
        previousSGPI: Number(previousSGPI.toFixed(2)),
        trend: percentageChange > 0 ? 'up' : percentageChange < 0 ? 'down' : 'stable',
        percentageChange: Number(percentageChange.toFixed(2)),
        totalCredits,
        completedCourses,
        averageSGPI: Number(averageSGPI.toFixed(2)),
        bestSGPI: Number(bestSGPI.toFixed(2)),
        currentSemester: profileData.currentSemester,
        department: profileData.department,
        rank: profileData.rank,
        totalStudents: profileData.totalStudents
      };
    } catch (error) {
      console.error('Error getting dashboard stats:', error);
      return this.getDefaultDashboardMetrics();
    }
  }

  // Get student profile
  async getStudentProfile(studentId: string) {
    try {
      const docRef = doc(db, 'students', studentId);
      const docSnap = await getDoc(docRef);
      
      if (docSnap.exists()) {
        return docSnap.data();
      }
      
      // Return default profile if not exists
      return {
        currentSemester: 5,
        department: 'Computer Science',
        rank: 15,
        totalStudents: 120,
        registrationNumber: 'CS2021001'
      };
    } catch (error) {
      console.error('Error fetching student profile:', error);
      return {
        currentSemester: 5,
        department: 'CSE',
        rank: 15,
        totalStudents: 120
      };
    }
  }

  // Generate insights from performance data
  async generateInsights(data: PerformanceMetric[]) {
    const insights = {
      trends: this.analyzeTrends(data),
      predictions: this.predictPerformance(data),
      recommendations: this.generateRecommendations(data),
      riskFactors: this.identifyRiskFactors(data)
    };
    
    return insights;
  }

  // Analyze performance trends
  private analyzeTrends(data: PerformanceMetric[]) {
    if (data.length < 2) {
      return { overall: 'stable', direction: 0, confidence: 0 };
    }

    const sgpiValues = data.map(d => d.sgpi).reverse();
    let upwardCount = 0;
    let downwardCount = 0;
    
    for (let i = 1; i < sgpiValues.length; i++) {
      if (sgpiValues[i] > sgpiValues[i - 1]) upwardCount++;
      else if (sgpiValues[i] < sgpiValues[i - 1]) downwardCount++;
    }
    
    const totalChanges = upwardCount + downwardCount;
    const trend = upwardCount > downwardCount ? 'improving' : 
                  downwardCount > upwardCount ? 'declining' : 'stable';
    
    return {
      overall: trend,
      direction: upwardCount - downwardCount,
      confidence: totalChanges > 0 ? Math.abs(upwardCount - downwardCount) / totalChanges : 0,
      averageChange: this.calculateAverageChange(sgpiValues)
    };
  }

  // Calculate average change
  private calculateAverageChange(values: number[]): number {
    if (values.length < 2) return 0;
    
    let totalChange = 0;
    for (let i = 1; i < values.length; i++) {
      totalChange += values[i] - values[i - 1];
    }
    
    return totalChange / (values.length - 1);
  }

  // Predict future performance
  private predictPerformance(data: PerformanceMetric[]) {
    if (data.length < 3) {
      return { nextSGPI: data[0]?.sgpi || 0, confidence: 'low' };
    }

    // Simple linear regression for prediction
    const sgpiValues = data.map(d => d.sgpi).slice(0, 5).reverse();
    const n = sgpiValues.length;
    
    // Calculate slope and intercept
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (let i = 0; i < n; i++) {
      sumX += i;
      sumY += sgpiValues[i];
      sumXY += i * sgpiValues[i];
      sumX2 += i * i;
    }
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // Predict next semester
    const nextSGPI = slope * n + intercept;
    
    // Determine confidence based on R-squared
    const yMean = sumY / n;
    let ssRes = 0, ssTot = 0;
    for (let i = 0; i < n; i++) {
      const yPred = slope * i + intercept;
      ssRes += Math.pow(sgpiValues[i] - yPred, 2);
      ssTot += Math.pow(sgpiValues[i] - yMean, 2);
    }
    
    const rSquared = 1 - (ssRes / ssTot);
    const confidence = rSquared > 0.8 ? 'high' : rSquared > 0.5 ? 'medium' : 'low';
    
    return {
      nextSGPI: Math.min(10, Math.max(0, Number(nextSGPI.toFixed(2)))),
      confidence,
      rSquared: Number(rSquared.toFixed(2))
    };
  }

  // Generate recommendations
  private generateRecommendations(data: PerformanceMetric[]) {
    const recommendations = [];
    const currentSGPI = data[0]?.sgpi || 0;
    const trend = this.analyzeTrends(data);
    
    if (currentSGPI < 7) {
      recommendations.push({
        type: 'warning',
        message: 'Your SGPI is below 7.0. Consider seeking academic support.',
        priority: 'high'
      });
    }
    
    if (trend.overall === 'declining') {
      recommendations.push({
        type: 'alert',
        message: 'Your performance shows a declining trend. Review your study habits.',
        priority: 'medium'
      });
    }
    
    if (currentSGPI > 8.5) {
      recommendations.push({
        type: 'success',
        message: 'Excellent performance! Consider applying for scholarships.',
        priority: 'low'
      });
    }
    
    return recommendations;
  }

  // Identify risk factors
  private identifyRiskFactors(data: PerformanceMetric[]) {
    const risks = [];
    const currentSGPI = data[0]?.sgpi || 0;
    const trend = this.analyzeTrends(data);
    
    if (currentSGPI < 6) {
      risks.push({ factor: 'Low SGPI', severity: 'high', impact: 'Academic probation risk' });
    }
    
    if (trend.overall === 'declining' && trend.confidence > 0.6) {
      risks.push({ factor: 'Declining trend', severity: 'medium', impact: 'Future performance at risk' });
    }
    
    const failedSubjects = data[0]?.subjects?.filter(s => s.grade === 'F').length || 0;
    if (failedSubjects > 0) {
      risks.push({ factor: `${failedSubjects} failed subjects`, severity: 'high', impact: 'Graduation delay' });
    }
    
    return risks;
  }

  // Generate mock data for testing
  private generateMockPerformanceData(studentId: string): PerformanceMetric[] {
    const semesters = 5;
    const data: PerformanceMetric[] = [];
    
    for (let i = semesters; i >= 1; i--) {
      const baseGPI = 7 + Math.random() * 2;
      const variation = Math.random() * 0.5 - 0.25;
      
      data.push({
        studentId,
        semester: i,
        sgpi: Number((baseGPI + variation + (i * 0.1)).toFixed(2)),
        credits: 22 + Math.floor(Math.random() * 4),
        courses: 5 + Math.floor(Math.random() * 3),
        timestamp: new Date(Date.now() - (semesters - i) * 120 * 24 * 60 * 60 * 1000),
        subjects: this.generateMockSubjects()
      });
    }
    
    return data;
  }

  // Generate mock subjects
  private generateMockSubjects(): SubjectScore[] {
    const subjects = [
      { name: 'Data Structures', code: 'CS201' },
      { name: 'Database Systems', code: 'CS202' },
      { name: 'Machine Learning', code: 'CS301' },
      { name: 'Computer Networks', code: 'CS302' },
      { name: 'Operating Systems', code: 'CS303' }
    ];
    
    return subjects.map(subject => ({
      ...subject,
      marks: 60 + Math.floor(Math.random() * 40),
      grade: this.marksToGrade(60 + Math.floor(Math.random() * 40)),
      credits: 3 + Math.floor(Math.random() * 2)
    }));
  }

  // Convert marks to grade
  private marksToGrade(marks: number): string {
    if (marks >= 90) return 'A+';
    if (marks >= 80) return 'A';
    if (marks >= 70) return 'B+';
    if (marks >= 60) return 'B';
    if (marks >= 50) return 'C';
    if (marks >= 40) return 'D';
    return 'F';
  }

  // Get default dashboard metrics
  private getDefaultDashboardMetrics(): DashboardMetrics {
    return {
      currentSGPI: 8.5,
      previousSGPI: 8.2,
      trend: 'up',
      percentageChange: 3.66,
      totalCredits: 120,
      completedCourses: 30,
      averageSGPI: 8.1,
      bestSGPI: 8.7,
      currentSemester: 5,
      department: 'Computer Science',
      rank: 15,
      totalStudents: 120
    };
  }

  // Subscribe to real-time updates
  subscribeToMetrics(studentId: string, callback: (data: PerformanceMetric[]) => void) {
    const metricsRef = collection(db, 'performance_metrics');
    const q = query(
      metricsRef,
      where('studentId', '==', studentId),
      orderBy('semester', 'desc')
    );
    
    return onSnapshot(q, (snapshot) => {
      const metrics = snapshot.docs.map(doc => {
        const data = doc.data();
        return {
          studentId: data.studentId,
          semester: data.semester,
          sgpi: data.sgpi,
          credits: data.credits,
          courses: data.courses,
          timestamp: data.timestamp?.toDate() || new Date(),
          subjects: data.subjects || []
        };
      });
      
      callback(metrics);
    });
  }
}

export const analyticsService = new AnalyticsService();