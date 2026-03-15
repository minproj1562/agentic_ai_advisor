// src/components/dashboard/cards/StudentDashboardViewModal.tsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  X, TrendingUp, TrendingDown, AlertTriangle, Eye,
  BarChart3, Target, Brain, Shield, Award, Activity,
  Loader2, AlertCircle, CheckCircle, Code, GraduationCap,
  Heart, Lightbulb, ChevronRight, Lock
} from 'lucide-react';
import apiClient from '../../../services/api.service';

interface Props {
  studentId: string;
  studentName: string;
  onClose: () => void;
}

const StudentDashboardViewModal: React.FC<Props> = ({ studentId, studentName, onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'weaknesses' | 'predictions'>('overview');

  useEffect(() => {
    let cancelled = false;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Try the dashboard-view endpoint first, fall back to standard detail
        let res;
        try {
          res = await apiClient.get(`/student-analysis/${studentId}/dashboard-view`);
        } catch {
          res = await apiClient.get(`/student-analysis/${studentId}`);
        }
        if (!cancelled) setData(res.data);
      } catch (err: any) {
        console.error('Failed to load student dashboard view:', err);
        if (!cancelled) setError(err?.response?.data?.detail || 'Failed to load student data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchData();
    return () => { cancelled = true; };
  }, [studentId]);

  const riskColor = (level: string) => {
    if (level === 'high') return 'text-red-600 bg-red-100';
    if (level === 'medium') return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const severityColor = (sev: string) => {
    switch (sev) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      default: return 'bg-blue-100 text-blue-700';
    }
  };

  const sgpaChartData = data?.performance_data?.sgpa_trend || data?.sgpa_trend || [];
  const weaknesses = data?.weaknesses || [];
  const predictions = data?.predictions || {};
  const recommendations = data?.recommendations || [];
  const projects = data?.projects || [];

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: BarChart3 },
    { id: 'performance' as const, label: 'Performance', icon: Activity },
    { id: 'weaknesses' as const, label: 'Weaknesses', icon: AlertTriangle },
    { id: 'predictions' as const, label: 'Predictions', icon: Brain },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0, y: 30 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.92, opacity: 0, y: 30 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 flex-shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg">
              {studentName.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                {studentName}
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700 uppercase">
                  <Lock className="w-3 h-3" /> Read-only
                </span>
              </h2>
              {data && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {data.roll_number && `${data.roll_number} · `}
                  {data.department} · Semester {data.current_semester}
                  {data.batch ? ` · Batch ${data.batch}` : ''}
                </p>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 px-6 flex-shrink-0 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  active
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-500">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              <p className="text-sm font-medium">Loading student dashboard…</p>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <AlertCircle className="w-10 h-10 text-red-400" />
              <p className="text-red-600 font-medium">{error}</p>
              <button onClick={onClose} className="mt-2 px-4 py-2 bg-gray-100 rounded-lg text-sm">Close</button>
            </div>
          ) : data ? (
            <>
              {/* ── OVERVIEW ── */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  {/* Stat Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                    {[
                      { label: 'CGPA', value: data.cgpa?.toFixed(2) || '—', icon: GraduationCap, color: 'text-indigo-500' },
                      { label: 'Latest SGPA', value: data.latest_sgpa?.toFixed(2) || '—', icon: TrendingUp, color: 'text-blue-500' },
                      { label: 'Credits', value: `${data.total_credits_earned || data.metadata?.total_credits || 0}`, icon: Award, color: 'text-purple-500' },
                      { label: 'Weaknesses', value: (data.weakness_count || 0).toString(), icon: AlertTriangle, color: 'text-orange-500' },
                      { label: 'Projects', value: (data.projects_count || projects.length || 0).toString(), icon: Code, color: 'text-green-500' },
                    ].map((s) => {
                      const Icon = s.icon;
                      return (
                        <div key={s.label} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 text-center">
                          <Icon className={`w-5 h-5 mx-auto mb-2 ${s.color}`} />
                          <p className="text-2xl font-bold text-gray-900 dark:text-white">{s.value}</p>
                          <p className="text-xs text-gray-500 mt-1">{s.label}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Risk / Trend / Profile */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 flex items-center gap-3">
                      <Shield className="w-6 h-6 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Risk Level</p>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${riskColor(data.risk_level)}`}>
                          {data.risk_level?.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 flex items-center gap-3">
                      {data.improvement_trend === 'improving'
                        ? <TrendingUp className="w-6 h-6 text-green-500" />
                        : data.improvement_trend === 'declining'
                        ? <TrendingDown className="w-6 h-6 text-red-500" />
                        : <Activity className="w-6 h-6 text-gray-400" />}
                      <div>
                        <p className="text-xs text-gray-500">Trend</p>
                        <p className="font-semibold text-gray-900 dark:text-white capitalize">{data.improvement_trend}</p>
                      </div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 flex items-center gap-3">
                      <Target className="w-6 h-6 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Profile</p>
                        <p className="font-semibold text-gray-900 dark:text-white">{data.profile_completeness}% complete</p>
                      </div>
                    </div>
                  </div>

                  {/* SGPA Trend - Simple Bar Display */}
                  {(Array.isArray(sgpaChartData) ? sgpaChartData : []).length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" /> SGPA Trend
                      </h4>
                      <div className="flex items-end gap-2 h-40">
                        {(Array.isArray(sgpaChartData) ? sgpaChartData : []).map((item: any, idx: number) => {
                          const sgpa = typeof item === 'number' ? item : item?.sgpa || 0;
                          const sem = typeof item === 'number' ? idx + 1 : item?.semester || idx + 1;
                          const heightPercent = (sgpa / 10) * 100;
                          return (
                            <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                              <span className="text-xs font-bold text-gray-700 dark:text-gray-300">{sgpa.toFixed(1)}</span>
                              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-t-lg relative" style={{ height: '120px' }}>
                                <div
                                  className="absolute bottom-0 w-full bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t-lg transition-all duration-500"
                                  style={{ height: `${heightPercent}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-gray-500">S{sem}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Interests & Skills */}
                  {((data.interests?.length > 0) || (data.skills?.length > 0)) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {data.interests?.length > 0 && (
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1.5">
                            <Heart className="w-4 h-4 text-pink-500" /> Interests
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {data.interests.map((i: string) => (
                              <span key={i} className="px-2 py-0.5 bg-pink-100 text-pink-700 rounded-full text-xs">{i}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {data.skills?.length > 0 && (
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1.5">
                            <Code className="w-4 h-4 text-green-500" /> Skills
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {data.skills.map((s: string) => (
                              <span key={s} className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">{s}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ── PERFORMANCE ── */}
              {activeTab === 'performance' && (
                <div className="space-y-6">
                  {/* Semester Subject Breakdown */}
                  {data.subjects_by_semester?.length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        <GraduationCap className="w-5 h-5 text-indigo-500" />
                        Semester-wise Performance
                      </h3>
                      {data.subjects_by_semester.map((sem: any) => (
                        <div key={sem.semester} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-3">
                            <p className="font-medium text-gray-900 dark:text-white">
                              Semester {sem.semester}
                              {sem.academic_year && <span className="text-gray-400 ml-2 text-xs">({sem.academic_year})</span>}
                            </p>
                            <span className="text-sm font-bold text-indigo-600">SGPA: {sem.sgpa?.toFixed(2)}</span>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {sem.subjects?.map((subj: any, si: number) => (
                              <div key={si} className="flex items-center justify-between text-xs bg-white dark:bg-gray-600 px-3 py-2 rounded-lg">
                                <span className="text-gray-700 dark:text-gray-300 truncate mr-2">{subj.name}</span>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  <span className="text-gray-500">{subj.total_marks?.toFixed(0)}%</span>
                                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                    subj.grade === 'F' ? 'bg-red-100 text-red-700' :
                                    subj.grade === 'O' ? 'bg-green-100 text-green-700' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>{subj.grade}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    /* Fallback: show SGPA trend as performance data */
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900 dark:text-white">Performance Data</h3>
                      {data.performance_data?.sgpa_trend?.length > 0 ? (
                        <div className="space-y-2">
                          {data.performance_data.sgpa_trend.map((s: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                              <span className="text-sm text-gray-700 dark:text-gray-300">Semester {s.semester}</span>
                              <div className="flex items-center gap-4">
                                <span className="text-sm text-gray-500">Credits: {s.credits}</span>
                                <span className="text-lg font-bold text-indigo-600">{s.sgpa?.toFixed(2)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-center text-gray-400 py-12">No performance data available.</p>
                      )}
                    </div>
                  )}

                  {/* Statistics */}
                  {data.performance_data?.statistics && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      {[
                        { label: 'Mean SGPA', value: data.performance_data.statistics.mean_sgpa?.toFixed(2) },
                        { label: 'Min SGPA', value: data.performance_data.statistics.min_sgpa?.toFixed(2) },
                        { label: 'Max SGPA', value: data.performance_data.statistics.max_sgpa?.toFixed(2) },
                        { label: 'Trend', value: data.performance_data.statistics.trend_direction },
                      ].map((st) => (
                        <div key={st.label} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-3 text-center">
                          <p className="text-xs text-gray-500 mb-1">{st.label}</p>
                          <p className="text-lg font-bold text-gray-900 dark:text-white capitalize">{st.value || '—'}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── WEAKNESSES ── */}
              {activeTab === 'weaknesses' && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-orange-500" />
                    Identified Weaknesses ({data.weakness_count || weaknesses.length || 0})
                  </h3>
                  {weaknesses.length > 0 ? (
                    <div className="space-y-3">
                      {weaknesses.map((w: any, idx: number) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="flex items-center justify-between p-4 bg-white dark:bg-gray-700 rounded-xl shadow-sm border border-gray-100 dark:border-gray-600"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 dark:text-white">{w.subject}</p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {w.subject_code && `${w.subject_code} · `}
                              Semester {w.semester} · Score: {w.current_score?.toFixed(0)}%
                              {w.grade && ` · Grade: ${w.grade}`}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${severityColor(w.severity)}`}>
                              {w.severity}
                            </span>
                            <span className="text-xs text-gray-400">Gap: {w.gap}%</span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                      <CheckCircle className="w-12 h-12 mb-3 text-green-400" />
                      <p className="font-medium text-gray-600">No weaknesses identified</p>
                      <p className="text-sm">This student is performing well across all subjects.</p>
                    </div>
                  )}
                </div>
              )}

              {/* ── PREDICTIONS ── */}
              {activeTab === 'predictions' && (
                <div className="space-y-6">
                  {/* Prediction Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 text-center border border-blue-200">
                      <Brain className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                      <p className="text-3xl font-bold text-blue-700">{predictions.next_semester_sgpa?.toFixed(2) || '—'}</p>
                      <p className="text-xs text-gray-600 mt-1">Predicted Next SGPA</p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-5 text-center border border-purple-200">
                      <GraduationCap className="w-6 h-6 text-purple-500 mx-auto mb-2" />
                      <p className="text-3xl font-bold text-purple-700">{predictions.expected_graduation_cgpa?.toFixed(2) || '—'}</p>
                      <p className="text-xs text-gray-600 mt-1">Expected Graduation CGPA</p>
                    </div>
                    <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-5 text-center border border-orange-200">
                      <Shield className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                      <p className={`text-2xl font-bold capitalize ${
                        predictions.failure_risk === 'high' ? 'text-red-600' :
                        predictions.failure_risk === 'medium' ? 'text-yellow-600' : 'text-green-600'
                      }`}>{predictions.failure_risk || '—'}</p>
                      <p className="text-xs text-gray-600 mt-1">Failure Risk</p>
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div className="bg-white dark:bg-gray-700 rounded-xl p-5 shadow-sm border dark:border-gray-600">
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-yellow-500" />
                      AI Recommendations
                    </h3>
                    {recommendations.length > 0 ? (
                      <div className="space-y-2.5">
                        {recommendations.map((rec: string, idx: number) => (
                          <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-600 rounded-lg">
                            <ChevronRight className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-gray-700 dark:text-gray-300">{rec}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400 text-center py-6">No recommendations generated yet.</p>
                    )}
                  </div>

                  {/* Projects */}
                  {projects.length > 0 && (
                    <div className="bg-white dark:bg-gray-700 rounded-xl p-5 shadow-sm border dark:border-gray-600">
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                        <Code className="w-5 h-5 text-green-500" />
                        Projects ({projects.length})
                      </h3>
                      <div className="space-y-3">
                        {projects.map((proj: any, idx: number) => (
                          <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-600 rounded-lg">
                            <p className="font-medium text-gray-900 dark:text-white text-sm">{proj.title}</p>
                            {proj.description && (
                              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{proj.description}</p>
                            )}
                            {proj.technologies?.length > 0 && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {proj.technologies.map((tech: string, ti: number) => (
                                  <span key={ti} className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[10px]">{tech}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex-shrink-0">
          <div className="flex items-center justify-between">
            <p className="text-[11px] text-gray-400 flex items-center gap-1">
              <Eye className="w-3 h-3" />
              Faculty read-only view · Data from MongoDB
              {data?.last_updated && ` · Updated: ${new Date(data.last_updated).toLocaleString()}`}
            </p>
            <button onClick={onClose} className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors">
              Close
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default StudentDashboardViewModal;