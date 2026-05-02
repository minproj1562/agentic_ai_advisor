// academic-advisor-frontend/src/components/dashboard/ImprovementHub.tsx
import React, { useState, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Zap, Trophy, Target, Flame, Gamepad2,
  CheckCircle, Clock, Award, Brain, Code, BookOpen,
  ChevronRight, Play, ArrowLeft, Loader2, AlertTriangle
} from 'lucide-react';
import apiClient from '../../services/api.service';
import toast from 'react-hot-toast';
const QuizGame = lazy(() => import('./games/QuizGame'));
const ConceptClash = lazy(() => import('./games/ConceptClash'));
const OutputPredictor = lazy(() => import('./games/OutputPredictor'));
const BossBattle = lazy(() => import('./games/BossBattle'));
const CodeStudio = lazy(() => import('./games/CodeStudio'));
const TheoryEngine = lazy(() => import('./games/TheoryEngine'));
import SyllabusProgressionView from './games/SyllabusProgressionView';

const LEVEL_TITLES = ['Freshman','Learner','Explorer','Scholar','Specialist','Expert','Master','Grandmaster','Legend','Titan'];
const getLevelTitle = (l: number) => LEVEL_TITLES[Math.min(l - 1, 9)];
const LEVEL_COLORS = [
  'from-gray-400 to-gray-500','from-green-400 to-emerald-500','from-blue-400 to-cyan-500',
  'from-purple-400 to-violet-500','from-amber-400 to-orange-500','from-rose-400 to-pink-500',
  'from-red-500 to-rose-600','from-indigo-500 to-purple-600','from-yellow-400 to-amber-500','from-cyan-400 to-teal-500',
];

const QUIZ_TYPES = [
  { id: 'mcq', name: 'Theory Quiz', icon: '📝', desc: 'MCQ questions testing concepts & theory', color: 'from-indigo-500 to-blue-600' },
  { id: 'code_debug', name: 'Bug Hunter', icon: '🐛', desc: 'Find & fix bugs in code snippets', color: 'from-red-500 to-rose-600' },
  { id: 'fill_blank', name: 'Fill the Gap', icon: '✏️', desc: 'Complete sentences with correct terms', color: 'from-emerald-500 to-teal-600' },
];

const DIFFICULTIES = [
  { id: 'easy', label: 'Easy', emoji: '🟢', desc: 'Recall & definitions' },
  { id: 'medium', label: 'Medium', emoji: '🟡', desc: 'Application level' },
  { id: 'hard', label: 'Hard', emoji: '🔴', desc: 'Analysis & problem-solving' },
];

const ImprovementHub: React.FC = () => {
  const qc = useQueryClient();
  const [tab, setTab] = useState<'overview'|'practice'|'roadmaps'|'badges'|'leaderboard'>('overview');
  const [activeQuiz, setActiveQuiz] = useState<{subject:string;type:string;diff:string}|null>(null);
  const [activeGame, setActiveGame] = useState<{subject:string;game:string;diff:string}|null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string|null>(null);
  const [showRoadmapModal, setShowRoadmapModal] = useState(false);
  const [activeBoss, setActiveBoss] = useState<{subject:string;topic:string;diff:string}|null>(null);
  const [activeCode, setActiveCode] = useState<{subject:string;diff:string}|null>(null);
  const [activeTheory, setActiveTheory] = useState<{subject:string;topic:string;diff:string}|null>(null);

  const { data: progress } = useQuery({
    queryKey: ['improvement-progress'],
    queryFn: async () => (await apiClient.get('/improvement/progress')).data,
  });

  const { data: weakData } = useQuery({
    queryKey: ['weak-subjects'],
    queryFn: async () => (await apiClient.get('/improvement/weak-subjects')).data,
  });

  const { data: masteryData } = useQuery({
    queryKey: ['mastery-summary'],
    queryFn: async () => (await apiClient.get('/improvement/mastery-summary')).data,
  });

  const { data: syllabusData } = useQuery({
    queryKey: ['syllabus-subjects'],
    queryFn: async () => {
      try {
        const semester = localStorage.getItem('userSemester') || '5';
        const res = await apiClient.get(`/academic/subjects?semester=${semester}`);
        return res.data;
      } catch { return null; }
    },
    staleTime: 10 * 60 * 1000,
  });

  const createRoadmap = useMutation({
    mutationFn: async (d: {target_type:string;target_name:string}) => (await apiClient.post('/improvement/roadmap', d)).data,
    onSuccess: () => { toast.success('🗺️ Roadmap created!'); qc.invalidateQueries({queryKey:['improvement-progress']}); setShowRoadmapModal(false); },
    onError: () => toast.error('Failed to create roadmap'),
  });

  const submitQuiz = useMutation({
    mutationFn: async (d: any) => (await apiClient.post('/improvement/submit-quiz', d)).data,
    onSuccess: (d) => { toast.success(`⚡ +${d.xp_earned} XP! ${d.percentage}% correct`); qc.invalidateQueries({queryKey:['improvement-progress']}); },
  });

  const updateMastery = useMutation({
    mutationFn: async (d: any) => (await apiClient.post('/improvement/update-mastery', d)).data,
    onSuccess: () => { qc.invalidateQueries({queryKey:['mastery-summary']}); },
  });

  const handleGameComplete = (r: any) => {
    // Submit quiz score for XP
    submitQuiz.mutate({ subject: r.subject, quiz_type: r.quizType, total_questions: r.total, correct_answers: r.correct, time_spent_seconds: r.timeSpent });
    // Update mastery
    const lane = ['mcq','fill_blank','concept_match'].includes(r.quizType) ? 'theory' : ['output_predict','step_sequence'].includes(r.quizType) ? 'practical' : 'coding';
    updateMastery.mutate({ subject: r.subject, lane, score: r.score, total_questions: r.total, correct_answers: r.correct });
  };

  const level = progress?.level || 1;
  const weakSubjects: any[] = weakData?.weak_subjects || [];

  // Build subject list from backend syllabus + weak subjects, with fallback
  const DEFAULT_SUBJECTS = ['Operating Systems','Database Management Systems','Data Structures and Algorithms','Computer Networks','Software Engineering','Machine Learning','Discrete Mathematics','Object Oriented Programming'];
  const backendSubjects: string[] = syllabusData?.subjects?.map((s: any) => s.name || s.subject_name || s) || syllabusData?.map?.((s: any) => s.name || s.subject_name || s) || [];
  const weakNames = weakSubjects.map((w: any) => w.name);
  const syllabusSubjects = [...new Set([...weakNames, ...(backendSubjects.length > 0 ? backendSubjects : DEFAULT_SUBJECTS)])];

  // Active theory engine
  if (activeTheory) {
    return (
      <div className="space-y-4 p-1">
        <button onClick={() => setActiveTheory(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" /> Back to Hub
        </button>
        <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>}>
          <TheoryEngine subject={activeTheory.subject} topic={activeTheory.topic} difficulty={activeTheory.diff} onComplete={(r) => { handleGameComplete({...r, quizType:'theory_engine'}); }} onBack={() => setActiveTheory(null)} />
        </Suspense>
      </div>
    );
  }

  // Active code studio
  if (activeCode) {
    return (
      <div className="space-y-4 p-1">
        <button onClick={() => setActiveCode(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" /> Back to Hub
        </button>
        <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-emerald-500" /></div>}>
          <CodeStudio subject={activeCode.subject} difficulty={activeCode.diff} onComplete={(r) => { handleGameComplete({...r, quizType:'code_studio'}); }} onBack={() => setActiveCode(null)} />
        </Suspense>
      </div>
    );
  }

  // Active boss battle rendering
  if (activeBoss) {
    return (
      <div className="space-y-4 p-1">
        <button onClick={() => setActiveBoss(null)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" /> Back to Hub
        </button>
        <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-red-500" /></div>}>
          <BossBattle subject={activeBoss.subject} topic={activeBoss.topic} difficulty={activeBoss.diff} onComplete={(r) => { handleGameComplete({...r, quizType:'boss_battle'}); }} onBack={() => setActiveBoss(null)} />
        </Suspense>
      </div>
    );
  }

  // Active game rendering
  if (activeQuiz || activeGame) {
    const game = activeGame || activeQuiz;
    const gameType = activeGame?.game || activeQuiz?.type || 'mcq';
    return (
      <div className="space-y-4 p-1">
        <button onClick={() => { setActiveQuiz(null); setActiveGame(null); }} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <ArrowLeft className="w-4 h-4" /> Back to Hub
        </button>
        <Suspense fallback={<div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-indigo-500" /></div>}>
          {gameType === 'concept_match' ? (
            <ConceptClash subject={game!.subject} difficulty={game!.diff} onComplete={handleGameComplete} onBack={() => { setActiveGame(null); setActiveQuiz(null); }} />
          ) : gameType === 'output_predict' ? (
            <OutputPredictor subject={game!.subject} difficulty={game!.diff} onComplete={handleGameComplete} onBack={() => { setActiveGame(null); setActiveQuiz(null); }} />
          ) : (
            <QuizGame subject={game!.subject} quizType={gameType} difficulty={game!.diff} onComplete={handleGameComplete} onBack={() => { setActiveGame(null); setActiveQuiz(null); }} />
          )}
        </Suspense>
      </div>
    );
  }

  // Subject selection → Syllabus Progression View
  if (selectedSubject) {
    const subjectMastery = masteryData?.subjects?.find((s: any) => s.subject === selectedSubject);
    const overallPct = subjectMastery?.overall_mastery || 0;

    return <SyllabusProgressionView
      subject={selectedSubject}
      overallPct={overallPct}
      subjectMastery={subjectMastery}
      onBack={() => setSelectedSubject(null)}
      onTheory={(topic: string, diff: string) => setActiveTheory({subject: selectedSubject, topic, diff})}
      onQuiz={(type: string, diff: string) => setActiveQuiz({subject: selectedSubject, type, diff})}
      onGame={(game: string, diff: string) => setActiveGame({subject: selectedSubject, game, diff})}
      onCode={(diff: string) => setActiveCode({subject: selectedSubject, diff})}
      onBoss={(topic: string, diff: string) => setActiveBoss({subject: selectedSubject, topic, diff})}
      onComplete={handleGameComplete}
    />;
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Zap },
    { id: 'practice', label: 'Practice', icon: Brain },
    { id: 'roadmaps', label: 'Roadmaps', icon: Target },
    { id: 'badges', label: 'Badges', icon: Trophy },
    { id: 'leaderboard', label: 'Ranks', icon: Trophy },
  ] as const;

  return (
    <div className="space-y-6 p-1">
      {/* Hero XP Card */}
      <motion.div initial={{opacity:0,y:-20}} animate={{opacity:1,y:0}}
        className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${LEVEL_COLORS[Math.min(level-1,9)]} p-6 text-white shadow-2xl`}>
        <div className="absolute inset-0 bg-black/10" />
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-5">
            <motion.div animate={{rotate:[0,5,-5,0],scale:[1,1.05,1]}} transition={{duration:3,repeat:Infinity}}
              className="flex h-20 w-20 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 text-3xl font-black">{level}</motion.div>
            <div>
              <p className="text-sm text-white/70">Level {level}</p>
              <h2 className="text-2xl font-black">{getLevelTitle(level)}</h2>
              <p className="text-sm text-white/80 mt-1">{progress?.total_xp?.toLocaleString() || 0} XP total</p>
            </div>
          </div>
          <div className="text-right space-y-1">
            <div className="flex items-center gap-2 text-white/80"><Flame className="w-4 h-4" /><span className="text-sm">{progress?.current_streak||0} day streak</span></div>
            <div className="flex items-center gap-2 text-white/80"><Trophy className="w-4 h-4" /><span className="text-sm">{progress?.badge_count||0} badges</span></div>
            <div className="flex items-center gap-2 text-white/80"><Gamepad2 className="w-4 h-4" /><span className="text-sm">{progress?.games_played||0} quizzes</span></div>
          </div>
        </div>
        <div className="relative z-10 mt-4">
          <div className="flex justify-between text-xs text-white/70 mb-1">
            <span>Level {level}</span><span>{progress?.xp_to_next_level||500} XP to Level {level+1}</span>
          </div>
          <div className="h-3 rounded-full bg-black/20 overflow-hidden">
            <motion.div initial={{width:0}} animate={{width:`${progress?.level_progress_pct||0}%`}} transition={{duration:1}} className="h-full rounded-full bg-white/40 backdrop-blur-sm" />
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-1 justify-center ${
              tab===t.id ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* Overview */}
        {tab === 'overview' && (
          <motion.div key="ov" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                {label:'Total XP', value: progress?.total_xp?.toLocaleString()||'0', icon:Zap, color:'text-amber-500', bg:'bg-amber-50 dark:bg-amber-900/20'},
                {label:'Study Time', value:`${progress?.total_study_minutes||0}m`, icon:Clock, color:'text-blue-500', bg:'bg-blue-50 dark:bg-blue-900/20'},
                {label:'Quizzes Passed', value:`${progress?.quizzes_passed||0}/${progress?.quizzes_taken||0}`, icon:CheckCircle, color:'text-green-500', bg:'bg-green-50 dark:bg-green-900/20'},
                {label:'Longest Streak', value:`${progress?.longest_streak||0} days`, icon:Flame, color:'text-red-500', bg:'bg-red-50 dark:bg-red-900/20'},
              ].map((s,i) => (
                <motion.div key={s.label} initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} transition={{delay:i*0.1}}
                  className={`${s.bg} rounded-xl p-5 border border-gray-200/50 dark:border-gray-700/50`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${s.bg}`}><s.icon className={`w-5 h-5 ${s.color}`} /></div>
                    <div><p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p><p className="text-xl font-bold text-gray-900 dark:text-white">{s.value}</p></div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Weak Subjects Alert */}
            {weakSubjects.length > 0 && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <h3 className="font-semibold text-amber-800 dark:text-amber-300">Weak Subjects Detected</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {weakSubjects.map((ws: any, i: number) => (
                    <button key={i} onClick={() => setSelectedSubject(ws.name)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        ws.severity === 'critical' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 hover:bg-amber-200'
                      }`}>
                      {ws.name} ({ws.marks}/100)
                    </button>
                  ))}
                </div>
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">Click a subject to start practicing!</p>
              </div>
            )}

            {/* Active Roadmaps */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Active Roadmaps</h3>
                <button onClick={() => setShowRoadmapModal(true)} className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">
                  <Target className="w-3.5 h-3.5" /> New Roadmap
                </button>
              </div>
              {progress?.active_plans?.length > 0 ? progress.active_plans.map((p: any, i: number) => (
                <motion.div key={p.id} initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:i*0.1}}
                  className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <div><h4 className="font-semibold text-gray-900 dark:text-white">{p.target}</h4><p className="text-xs text-gray-500 capitalize">{p.type} prep</p></div>
                    <span className="text-sm font-bold text-indigo-600">{p.progress.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    <motion.div initial={{width:0}} animate={{width:`${p.progress}%`}} className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{p.steps_done}/{p.steps_total} steps</p>
                </motion.div>
              )) : (
                <div className="text-center py-8 text-gray-500"><Target className="w-12 h-12 mx-auto mb-2 opacity-30" /><p>No active roadmaps. Create one to start earning XP!</p></div>
              )}
            </div>
          </motion.div>
        )}

        {/* Practice Tab */}
        {tab === 'practice' && (
          <motion.div key="pr" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} className="space-y-6">
            {weakSubjects.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-500" /> Your Weak Subjects
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {weakSubjects.map((ws: any, i: number) => (
                    <motion.button key={i} initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{delay:i*0.05}}
                      onClick={() => setSelectedSubject(ws.name)}
                      className={`text-left p-4 rounded-xl border-2 transition-all hover:shadow-lg ${
                        ws.severity === 'critical' ? 'border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-900/10' : 'border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10'
                      }`}>
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-gray-900 dark:text-white">{ws.name}</h4>
                        <span className={`text-sm font-bold ${ws.severity==='critical'?'text-red-600':'text-amber-600'}`}>{ws.marks}/100</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Sem {ws.semester} • Click to practice</p>
                    </motion.button>
                  ))}
                </div>
              </div>
            )}
            {/* Boss Battle Section */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-5 border border-red-900/30">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">⚔️</span>
                <h3 className="text-lg font-bold text-white">Boss Battles</h3>
                <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full ml-auto">Bonus XP</span>
              </div>
              <p className="text-xs text-gray-400 mb-4">Defeat concept bosses to prove mastery! Each boss guards a prerequisite topic.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {(weakSubjects.length > 0 ? weakSubjects.slice(0, 4) : syllabusSubjects.slice(0, 4).map(n => ({name: n}))).map((ws: any, i: number) => (
                  <motion.button key={i} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.05}}
                    onClick={() => setActiveBoss({subject:ws.name, topic: ws.name, diff:'medium'})}
                    whileHover={{scale:1.02}}
                    className="flex items-center gap-3 p-3 bg-gray-800/50 hover:bg-red-900/20 border border-gray-700 hover:border-red-700 rounded-xl transition-all text-left">
                    <span className="text-2xl">{['💀','🐉','👻','😈','🧟','🕷️','🦇','🤖'][i % 8]}</span>
                    <div>
                      <p className="text-sm font-medium text-white">{ws.name}</p>
                      <p className="text-xs text-gray-500">Click to challenge</p>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-500" /> Syllabus Subjects
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {syllabusSubjects.map((subj: string, i: number) => (
                  <motion.button key={subj} initial={{opacity:0,scale:0.95}} animate={{opacity:1,scale:1}} transition={{delay:i*0.03}}
                    onClick={() => setSelectedSubject(subj)} whileHover={{scale:1.03}}
                    className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-indigo-400 hover:shadow-md transition-all text-left">
                    <h4 className="font-medium text-gray-900 dark:text-white text-sm">{subj}</h4>
                    <p className="text-xs text-indigo-500 mt-1 flex items-center gap-1"><Play className="w-3 h-3" /> 5 Engines</p>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Roadmaps Tab */}
        {tab === 'roadmaps' && (
          <motion.div key="rm" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} className="space-y-4">
            <div className="flex justify-end">
              <button onClick={() => setShowRoadmapModal(true)} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700">
                <Target className="w-4 h-4" /> Create New Roadmap
              </button>
            </div>
            {progress?.active_plans?.map((plan: any) => (
              <div key={plan.id} className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div><h3 className="text-lg font-bold text-gray-900 dark:text-white">{plan.target}</h3><p className="text-sm text-gray-500 capitalize">{plan.type} • {plan.steps_done}/{plan.steps_total} steps</p></div>
                  <span className="text-2xl font-black text-indigo-600">{plan.progress.toFixed(0)}%</span>
                </div>
                <div className="h-3 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden mb-3">
                  <motion.div initial={{width:0}} animate={{width:`${plan.progress}%`}} className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500" />
                </div>
              </div>
            ))}
          </motion.div>
        )}

        {/* Badges Tab */}
        {tab === 'badges' && (
          <motion.div key="bd" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {progress?.badges?.length > 0 ? progress.badges.map((b: any, i: number) => (
              <motion.div key={b.badge_id} initial={{opacity:0,rotateY:90}} animate={{opacity:1,rotateY:0}} transition={{delay:i*0.1}}
                className="bg-white dark:bg-gray-800 rounded-xl p-4 text-center border border-gray-200 dark:border-gray-700 shadow-sm">
                <motion.div animate={{y:[0,-5,0]}} transition={{duration:2,repeat:Infinity,delay:i*0.3}} className="text-4xl mb-2">{b.icon}</motion.div>
                <h4 className="font-semibold text-sm text-gray-900 dark:text-white">{b.name}</h4>
                <p className="text-xs text-gray-500 mt-1">{b.description}</p>
                <span className="inline-block mt-2 text-xs font-medium text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-2 py-0.5 rounded">+{b.xp_bonus} XP</span>
              </motion.div>
            )) : (
              <div className="col-span-full text-center py-12 text-gray-500">
                <Trophy className="w-16 h-16 mx-auto mb-3 opacity-20" /><p className="text-lg font-medium">No badges yet</p><p className="text-sm">Complete quizzes and roadmaps to earn badges!</p>
              </div>
            )}
          </motion.div>
        )}

        {/* Leaderboard Tab */}
        {tab === 'leaderboard' && (
          <motion.div key="lb" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-10}}>
            <Suspense fallback={<div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-amber-500" /></div>}>
              {React.createElement(lazy(() => import('./games/Leaderboard')), { currentUserXP: progress?.total_xp || 0 })}
            </Suspense>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Roadmap Modal */}
      <AnimatePresence>
        {showRoadmapModal && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowRoadmapModal(false)}>
            <motion.div initial={{scale:0.9,y:20}} animate={{scale:1,y:0}} exit={{scale:0.9,y:20}} onClick={e => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full shadow-2xl">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">🗺️ Create Personalized Roadmap</h3>
              <p className="text-sm text-gray-500 mb-6">Based on your performance and goals, here are recommended roadmaps. We'll build a step-by-step plan with XP rewards.</p>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {/* Personalized weak subject roadmaps */}
                {weakSubjects.slice(0, 3).map((ws: any) => (
                  <button key={`weak-${ws.name}`} onClick={() => createRoadmap.mutate({target_type:'subject',target_name:ws.name})} disabled={createRoadmap.isPending}
                    className="w-full flex items-center gap-3 p-3 rounded-xl border border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left">
                    <span className="text-2xl">{ws.severity === 'critical' ? '🚨' : '⚠️'}</span>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white text-sm">{ws.name}</p>
                      <p className="text-xs text-red-600 dark:text-red-400">Score: {ws.marks}/100 • {ws.severity} priority</p>
                    </div>
                    <ChevronRight className="w-4 h-4 ml-auto text-gray-400" />
                  </button>
                ))}
                {/* Career roadmaps from localStorage goals */}
                {(() => {
                  const savedGoals = JSON.parse(localStorage.getItem('careerGoals') || '[]');
                  const savedInterests = JSON.parse(localStorage.getItem('studentInterests') || '[]');
                  const careerOptions = savedGoals.length > 0 
                    ? savedGoals.slice(0, 2).map((g: string) => ({ type: 'career', name: g, icon: '🎯', desc: `Personalized path for ${g}` }))
                    : [
                        { type: 'career', name: 'Data Scientist', icon: '📊', desc: 'Prepare for data science career' },
                        { type: 'career', name: 'Software Developer', icon: '💻', desc: 'Build full-stack skills' },
                      ];
                  const electiveOptions = savedInterests.length > 0
                    ? savedInterests.slice(0, 2).map((i: string) => ({ type: 'elective', name: i, icon: '✨', desc: `Deep dive into ${i}` }))
                    : [
                        { type: 'elective', name: 'Machine Learning', icon: '🤖', desc: 'Get ready for ML elective' },
                        { type: 'elective', name: 'Cloud Computing', icon: '☁️', desc: 'Prepare for cloud computing' },
                      ];
                  return [...careerOptions, ...electiveOptions];
                })().map((o: any) => (
                  <button key={o.name} onClick={() => createRoadmap.mutate({target_type:o.type,target_name:o.name})} disabled={createRoadmap.isPending}
                    className="w-full flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left">
                    <span className="text-2xl">{o.icon}</span>
                    <div><p className="font-medium text-gray-900 dark:text-white text-sm">{o.name}</p><p className="text-xs text-gray-500">{o.desc}</p></div>
                    <ChevronRight className="w-4 h-4 ml-auto text-gray-400" />
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ImprovementHub;
