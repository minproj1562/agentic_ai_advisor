// modules/agent1/student-analysis/hooks/useStudentAnalysis.ts
import { useState, useEffect, useCallback } from 'react';
import { getStudentAnalysisService } from '../../../../services/student_analysis.service';
import { StudentAnalysisData } from '../types/student-analysis.types';

// Adapter function to convert service types to hook types
const adaptStudentData = (serviceData: any[]): StudentAnalysisData[] => {
  return serviceData.map(student => ({
    studentId: student.student_id,
    name: student.name,
    email: `${student.student_id}@university.edu`, // Generate email or get from actual data
    department: student.department,
    semester: student.current_semester,
    cgpa: student.cgpa,
    lastSgpa: student.latest_sgpa,
    trend: student.improvement_trend,
    riskLevel: student.risk_level,
    weaknesses: student.weaknesses?.map((weakness: any) => ({
      subject: weakness.subject,
      topic: weakness.topic ? [weakness.topic] : ['General'],
      weakness_score: weakness.gap || 0,
      confidence: 0.8, // Default value
      recommended_resources: []
    })) || [],
    lastUpdated: student.last_updated
  }));
};

export const useStudentAnalysis = (facultyId: string) => {
  const [students, setStudents] = useState<StudentAnalysisData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const service = getStudentAnalysisService();
      
      // Use existing getStudentsList method with facultyId as department filter
      const data = await service.getStudentsList({ 
        department: facultyId,
        limit: 100 // Adjust based on your needs
      });
      
      const adaptedData = adaptStudentData(data);
      setStudents(adaptedData);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [facultyId]);

  useEffect(() => {
    if (facultyId) {
      fetchData();
    }
  }, [facultyId, fetchData]);

  return {
    students,
    loading,
    error,
    refetch: fetchData
  };
};