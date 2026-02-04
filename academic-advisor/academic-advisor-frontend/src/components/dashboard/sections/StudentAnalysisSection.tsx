// src/components/dashboard/sections/StudentAnalysisSection.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { 
  Users, Search, Filter, Eye, TrendingUp, 
  TrendingDown, AlertTriangle, ChevronDown, FileText 
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import { format } from 'date-fns';

interface StudentAnalysisSectionProps {
  facultyId: string;
  facultyData: any;
}

const StudentAnalysisSection: React.FC<StudentAnalysisSectionProps> = ({
  facultyId,
  facultyData
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [selectedStudent, setSelectedStudent] = useState<any>(null);

  // Fetch students assigned to faculty
  const { data: studentsData, isLoading } = useQuery({
    queryKey: ['faculty-students', facultyId, filterRisk],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterRisk !== 'all') params.append('risk_level', filterRisk);
      
      const response = await apiClient.get(`/faculty/students?${params}`);
      return response.data;
    },
    enabled: !!facultyId,
  });

  const students = studentsData?.students || [];

  // Filter by search term
  const filteredStudents = students.filter((student: any) =>
    student.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.roll_number?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'low':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 bg-gray-300 rounded-full" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Student Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            View and monitor student performance (Read-only)
          </p>
        </div>
        
        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search students..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Students</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {students.length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Students</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {students.filter((s: any) => s.risk_level === 'high').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">At Risk</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {students.filter((s: any) => s.improvement_trend === 'improving').length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Improving</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {students.reduce((acc: number, s: any) => acc + (s.projects_count || 0), 0)}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Total Projects</p>
            </div>
          </div>
        </div>
      </div>

      {/* Students Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Student
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  CGPA
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Trend
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Risk Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Weaknesses
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Projects
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center gap-2 text-gray-500">
                      <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                      Loading students...
                    </div>
                  </td>
                </tr>
              ) : filteredStudents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                    No students found
                  </td>
                </tr>
              ) : (
                filteredStudents.map((student: any, index: number) => (
                  <motion.tr
                    key={student.id || index}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                          {student.name?.charAt(0) || 'S'}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {student.name}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {student.roll_number}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-lg font-bold ${
                        student.cgpa >= 8 ? 'text-green-600' :
                        student.cgpa >= 6 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {student.cgpa?.toFixed(2) || '-'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getTrendIcon(student.improvement_trend)}
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                          {student.improvement_trend || 'Stable'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        getRiskBadgeColor(student.risk_level)
                      }`}>
                        {student.risk_level?.toUpperCase() || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {student.weakness_count || 0} identified
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {student.projects_count || 0} projects
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => setSelectedStudent(student)}
                        className="p-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <Eye className="w-5 h-5" />
                      </button>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </div>
  );
};

// Student Detail Modal (Read-Only)
const StudentDetailModal: React.FC<{
  student: any;
  onClose: () => void;
}> = ({ student, onClose }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-2xl">
              {student.name?.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {student.name}
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                {student.roll_number} • {student.department} • Semester {student.semester}
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Performance Summary */}
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
              Performance Summary
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {student.cgpa?.toFixed(2) || '-'}
                </p>
                <p className="text-xs text-gray-500">CGPA</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {student.attendance || '-'}%
                </p>
                <p className="text-xs text-gray-500">Attendance</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {student.projects_count || 0}
                </p>
                <p className="text-xs text-gray-500">Projects</p>
              </div>
            </div>
          </div>

          {/* Weaknesses */}
          {student.weaknesses?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                Identified Weaknesses
              </h3>
              <div className="space-y-2">
                {student.weaknesses.map((weakness: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                  >
                    <span className="text-gray-900 dark:text-white">
                      {weakness.subject}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      weakness.severity === 'high' ? 'bg-red-100 text-red-700' :
                      weakness.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {weakness.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projects */}
          {student.projects?.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                Projects
              </h3>
              <div className="space-y-2">
                {student.projects.map((project: any, index: number) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <p className="font-medium text-gray-900 dark:text-white">
                      {project.title}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {project.description}
                    </p>
                    {project.technologies && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {project.technologies.map((tech: string, i: number) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded text-xs"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
            This is a read-only view. Student data is managed by students/admins.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default StudentAnalysisSection;