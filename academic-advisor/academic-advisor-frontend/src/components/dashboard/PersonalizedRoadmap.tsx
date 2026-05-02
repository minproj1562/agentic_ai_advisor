// academic-advisor-frontend/src/components/dashboard/PersonalizedRoadmap.tsx
// Interactive, AI-powered personalized learning roadmap

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Target, ChevronRight, Sparkles, Clock, BookOpen, Code,
  ExternalLink, Award, CheckCircle, Lock, Loader2, ArrowLeft,
  Rocket, Star, Zap, TrendingUp, Users, MapPin, AlertCircle,
} from 'lucide-react';
import apiClient from '../../services/api.service';
import toast from 'react-hot-toast';

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface DomainOption {
  name: string;
  icon: string;
  color: string;
  prereqs: string[];
  career_titles: string[];
  match_score: number;
  recommended: boolean;
}

interface RoadmapPhase {
  phase: number;
  title: string;
  description: string;
  weeks: number;
  status: 'current' | 'locked' | 'completed';
  objectives: string[];
  projects: { title: string; description: string; difficulty: string }[];
  skills: string[];
  completed: boolean;
}

interface AIRoadmap {
  domain: string;
  domain_icon: string;
  domain_color: string;
  goal: string;
  timeline_weeks: number;
  skill_level: string;
  student_context: {
    cgpa: number;
    semester: number;
    strong_subjects: string[];
    weak_subjects: string[];
  };
  phases: RoadmapPhase[];
  curated_resources: {
    courses: { title: string; url: string; platform: string; free: boolean }[];
    projects: { title: string; difficulty: string; skills: string[]; description: string }[];
    certifications: string[];
  };
  stats: {
    total_phases: number;
    total_objectives: number;
    total_projects: number;
    estimated_hours: number;
  };
}

// ═══════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════

const PersonalizedRoadmap: React.FC = () => {
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const [customGoal, setCustomGoal] = useState('');
  const [timeline, setTimeline] = useState(12);
  const [activePhase, setActivePhase] = useState(0);
  const [completedObjectives, setCompletedObjectives] = useState<Set<string>>(new Set());

  // Fetch personalized domains
  const { data: domainsData, isLoading: domainsLoading } = useQuery({
    queryKey: ['ai-roadmap-domains'],
    queryFn: async () => (await apiClient.get('/improvement/ai-roadmap/domains')).data,
    staleTime: 5 * 60 * 1000,
  });

  // Generate AI roadmap
  const generateMutation = useMutation({
    mutationFn: async (params: { domain: string; goal: string; timeline_weeks: number }) =>
      (await apiClient.post('/improvement/ai-roadmap', params)).data,
    onSuccess: () => toast.success('🗺️ Your personalized roadmap is ready!'),
    onError: () => toast.error('Failed to generate roadmap. Please try again.'),
  });

  const roadmap = generateMutation.data as AIRoadmap | undefined;
  const domains = (domainsData?.domains || []) as DomainOption[];
  const studentCtx = domainsData?.student_context;

  const handleGenerate = (domain: string) => {
    setSelectedDomain(domain);
    setActivePhase(0);
    setCompletedObjectives(new Set());
    generateMutation.mutate({ domain, goal: customGoal, timeline_weeks: timeline });
  };

  const toggleObjective = (key: string) => {
    setCompletedObjectives(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const progressPct = useMemo(() => {
    if (!roadmap) return 0;
    const total = roadmap.stats.total_objectives;
    return total > 0 ? Math.round((completedObjectives.size / total) * 100) : 0;
  }, [roadmap, completedObjectives]);

  // ─── Domain Selection View ───
  if (!roadmap && !generateMutation.isPending) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500/10 to-blue-500/10 rounded-full mb-4">
            <Sparkles className="w-4 h-4 text-violet-500" />
            <span className="text-sm font-semibold text-violet-700">AI-Powered</span>
          </motion.div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-violet-600 to-blue-600 bg-clip-text text-transparent">
            Your Personalized Learning Roadmap
          </h2>
          <p className="text-gray-500 mt-2 max-w-xl mx-auto">
            Choose a domain you're passionate about. We'll analyze your academic profile and create
            a step-by-step plan tailored to your strengths, weaknesses, and career goals.
          </p>
        </div>

        {/* Student Context Banner */}
        {studentCtx && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-gradient-to-r from-slate-50 to-blue-50 rounded-2xl p-5 border border-blue-100">
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-500" />
                <span className="text-gray-600">CGPA:</span>
                <span className="font-bold text-blue-700">{studentCtx.cgpa?.toFixed(2) || 'N/A'}</span>
              </div>
              {studentCtx.strong_subjects?.length > 0 && (
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-green-500" />
                  <span className="text-gray-600">Strong:</span>
                  <span className="font-medium text-green-700">{studentCtx.strong_subjects.slice(0, 3).join(', ')}</span>
                </div>
              )}
              {studentCtx.interests?.length > 0 && (
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-500" />
                  <span className="text-gray-600">Interests:</span>
                  <span className="font-medium text-amber-700">{studentCtx.interests.slice(0, 3).join(', ')}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Goal & Timeline */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">🎯 Your Goal (optional)</label>
            <input
              type="text"
              value={customGoal}
              onChange={e => setCustomGoal(e.target.value)}
              placeholder="e.g., Get placed at Google, Build a startup..."
              className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-violet-400 focus:ring-2 focus:ring-violet-100 transition-all text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">⏱️ Timeline</label>
            <div className="flex gap-2">
              {[8, 12, 16, 24].map(w => (
                <button
                  key={w}
                  onClick={() => setTimeline(w)}
                  className={`flex-1 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                    timeline === w
                      ? 'border-violet-500 bg-violet-50 text-violet-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-600'
                  }`}
                >
                  {w} weeks
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Domain Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {domainsLoading ? (
            <div className="col-span-4 flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
            </div>
          ) : (
            domains.map((domain, i) => (
              <motion.button
                key={domain.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => handleGenerate(domain.name)}
                whileHover={{ scale: 1.03, y: -4 }}
                whileTap={{ scale: 0.97 }}
                className="relative text-left p-5 rounded-2xl border-2 border-gray-100 bg-white hover:shadow-xl transition-all overflow-hidden group"
              >
                {domain.recommended && (
                  <div className="absolute top-2 right-2 bg-gradient-to-r from-green-400 to-emerald-500 text-white text-[10px] px-2 py-0.5 rounded-full font-bold">
                    ⭐ Recommended
                  </div>
                )}
                <div className="text-3xl mb-3">{domain.icon}</div>
                <h3 className="font-bold text-gray-900 text-sm">{domain.name}</h3>
                <div className="mt-2">
                  <div className="flex items-center gap-1 mb-1">
                    <div className="h-1.5 flex-1 rounded-full bg-gray-100 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${domain.match_score}%` }}
                        transition={{ delay: i * 0.05 + 0.3 }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: domain.color }}
                      />
                    </div>
                    <span className="text-xs font-bold" style={{ color: domain.color }}>{domain.match_score}%</span>
                  </div>
                  <p className="text-[11px] text-gray-400">match score</p>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {domain.career_titles.slice(0, 2).map(t => (
                    <span key={t} className="text-[10px] px-2 py-0.5 bg-gray-50 rounded-full text-gray-500">{t}</span>
                  ))}
                </div>
                <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </motion.button>
            ))
          )}
        </div>
      </div>
    );
  }

  // ─── Loading View ───
  if (generateMutation.isPending) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}>
          <Sparkles className="w-12 h-12 text-violet-500" />
        </motion.div>
        <h3 className="text-xl font-bold text-gray-900 mt-6">Crafting Your Roadmap...</h3>
        <p className="text-sm text-gray-500 mt-2">Analyzing your profile & building personalized phases</p>
        <div className="mt-6 flex gap-1">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
              className="w-2.5 h-2.5 rounded-full bg-violet-400"
            />
          ))}
        </div>
      </div>
    );
  }

  // ─── Roadmap View ───
  if (!roadmap) return null;
  const currentPhaseData = roadmap.phases[activePhase];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => { generateMutation.reset(); setSelectedDomain(null); }}
            className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-500" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{roadmap.domain_icon}</span>
              <h2 className="text-2xl font-bold text-gray-900">{roadmap.domain} Roadmap</h2>
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              {roadmap.goal} • {roadmap.timeline_weeks} weeks • Level: <span className="font-medium capitalize">{roadmap.skill_level}</span>
            </p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-3xl font-black" style={{ color: roadmap.domain_color }}>{progressPct}%</p>
          <p className="text-xs text-gray-400">completed</p>
        </div>
      </div>

      {/* Overall Progress Bar */}
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progressPct}%` }}
          className="h-full rounded-full bg-gradient-to-r"
          style={{ backgroundImage: `linear-gradient(to right, ${roadmap.domain_color}, ${roadmap.domain_color}88)` }}
        />
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { icon: MapPin, label: 'Phases', value: roadmap.stats.total_phases, color: 'text-violet-600 bg-violet-50' },
          { icon: Target, label: 'Objectives', value: roadmap.stats.total_objectives, color: 'text-blue-600 bg-blue-50' },
          { icon: Code, label: 'Projects', value: roadmap.stats.total_projects, color: 'text-green-600 bg-green-50' },
          { icon: Clock, label: 'Est. Hours', value: roadmap.stats.estimated_hours, color: 'text-amber-600 bg-amber-50' },
        ].map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
            className={`${stat.color} rounded-xl p-3 text-center`}>
            <stat.icon className="w-5 h-5 mx-auto mb-1" />
            <p className="text-xl font-black">{stat.value}</p>
            <p className="text-[11px] font-medium opacity-70">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Phase Navigation */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {roadmap.phases.map((phase, i) => {
          const phaseCompleted = phase.objectives.every((_, oi) => completedObjectives.has(`${i}-${oi}`));
          return (
            <button
              key={i}
              onClick={() => setActivePhase(i)}
              className={`flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activePhase === i
                  ? 'text-white shadow-lg'
                  : phaseCompleted
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
              style={activePhase === i ? { backgroundColor: roadmap.domain_color } : {}}
            >
              {phaseCompleted ? <CheckCircle className="w-4 h-4" /> : <span className="w-5 h-5 rounded-full border-2 border-current flex items-center justify-center text-xs font-bold">{i + 1}</span>}
              <span className="whitespace-nowrap">{phase.title.replace(/^[^\w]*/, '').substring(0, 20)}</span>
            </button>
          );
        })}
      </div>

      {/* Active Phase Detail */}
      <AnimatePresence mode="wait">
        {currentPhaseData && (
          <motion.div
            key={activePhase}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* Phase Content (2/3) */}
            <div className="lg:col-span-2 space-y-5">
              {/* Phase Header */}
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
                    style={{ backgroundColor: roadmap.domain_color }}>
                    {currentPhaseData.phase}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{currentPhaseData.title}</h3>
                    <p className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {currentPhaseData.weeks} weeks
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{currentPhaseData.description}</p>

                {/* Skills Tags */}
                <div className="flex flex-wrap gap-1.5 mt-4">
                  {currentPhaseData.skills.map(skill => (
                    <span key={skill} className="px-2.5 py-1 text-xs font-medium rounded-lg"
                      style={{ backgroundColor: `${roadmap.domain_color}15`, color: roadmap.domain_color }}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Objectives Checklist */}
              <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5" style={{ color: roadmap.domain_color }} />
                  Learning Objectives
                </h4>
                <div className="space-y-3">
                  {currentPhaseData.objectives.map((obj, oi) => {
                    const key = `${activePhase}-${oi}`;
                    const done = completedObjectives.has(key);
                    return (
                      <motion.button
                        key={oi}
                        onClick={() => toggleObjective(key)}
                        whileHover={{ x: 4 }}
                        className={`w-full flex items-start gap-3 p-3 rounded-xl text-left transition-all ${
                          done ? 'bg-green-50 border border-green-200' : 'bg-gray-50 hover:bg-gray-100 border border-transparent'
                        }`}
                      >
                        <div className={`w-6 h-6 rounded-lg flex-shrink-0 flex items-center justify-center mt-0.5 transition-all ${
                          done ? 'bg-green-500 text-white' : 'border-2 border-gray-300'
                        }`}>
                          {done && <CheckCircle className="w-4 h-4" />}
                        </div>
                        <span className={`text-sm ${done ? 'text-green-700 line-through' : 'text-gray-700'}`}>{obj}</span>
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              {/* Phase Projects */}
              {currentPhaseData.projects.length > 0 && (
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <h4 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                    <Rocket className="w-5 h-5" style={{ color: roadmap.domain_color }} />
                    Mini-Projects
                  </h4>
                  <div className="space-y-3">
                    {currentPhaseData.projects.map((proj, pi) => (
                      <div key={pi} className="p-4 rounded-xl border border-dashed border-gray-200 bg-gradient-to-r from-gray-50 to-white hover:border-gray-300 transition-all">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="font-semibold text-gray-900 text-sm">{proj.title}</h5>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                            proj.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                            proj.difficulty === 'intermediate' ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {proj.difficulty}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500">{proj.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar (1/3) */}
            <div className="space-y-5">
              {/* Curated Courses */}
              {roadmap.curated_resources.courses.length > 0 && (
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                  <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                    <BookOpen className="w-4 h-4" style={{ color: roadmap.domain_color }} />
                    Top Courses
                  </h4>
                  <div className="space-y-2">
                    {roadmap.curated_resources.courses.map((c, i) => (
                      <a key={i} href={c.url} target="_blank" rel="noopener noreferrer"
                        className="flex items-center justify-between p-3 rounded-xl bg-gray-50 hover:bg-blue-50 transition-all group">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{c.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-gray-400">{c.platform}</span>
                            {c.free && <span className="text-[10px] px-1.5 py-0.5 bg-green-100 text-green-700 rounded font-bold">FREE</span>}
                          </div>
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-500 flex-shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Portfolio Projects */}
              {roadmap.curated_resources.projects.length > 0 && (
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                  <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                    <Code className="w-4 h-4" style={{ color: roadmap.domain_color }} />
                    Portfolio Projects
                  </h4>
                  <div className="space-y-2">
                    {roadmap.curated_resources.projects.map((p, i) => (
                      <div key={i} className="p-3 rounded-xl bg-gray-50">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">{p.title}</p>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            p.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                            p.difficulty === 'intermediate' ? 'bg-amber-100 text-amber-700' :
                            'bg-red-100 text-red-700'
                          }`}>{p.difficulty}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{p.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {p.skills.map(s => (
                            <span key={s} className="text-[10px] px-1.5 py-0.5 bg-white border border-gray-200 rounded text-gray-500">{s}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications */}
              {roadmap.curated_resources.certifications.length > 0 && (
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                  <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
                    <Award className="w-4 h-4" style={{ color: roadmap.domain_color }} />
                    Certifications
                  </h4>
                  <div className="space-y-2">
                    {roadmap.curated_resources.certifications.map((cert, i) => (
                      <div key={i} className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-50">
                        <span className="text-amber-500">🏆</span>
                        <span className="text-sm text-amber-800 font-medium">{cert}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PersonalizedRoadmap;
