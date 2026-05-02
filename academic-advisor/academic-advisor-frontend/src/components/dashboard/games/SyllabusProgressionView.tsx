// SyllabusProgressionView.tsx — Syllabus-driven learning path with 5 engines per unit
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft, BookOpen, Code, Award, Lock, CheckCircle,
  Loader2, ChevronDown, ChevronRight, Zap, Trophy
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

interface Props {
  subject: string;
  overallPct: number;
  subjectMastery: any;
  onBack: () => void;
  onTheory: (topic: string, diff: string) => void;
  onQuiz: (type: string, diff: string) => void;
  onGame: (game: string, diff: string) => void;
  onCode: (diff: string) => void;
  onBoss: (topic: string, diff: string) => void;
  onComplete: (r: any) => void;
}

const SyllabusProgressionView: React.FC<Props> = ({
  subject, overallPct, subjectMastery, onBack,
  onTheory, onQuiz, onGame, onCode, onBoss, onComplete,
}) => {
  const qc = useQueryClient();
  const [expandedUnit, setExpandedUnit] = useState<number | null>(null);
  const [grandFinaleActive, setGrandFinaleActive] = useState(false);

  const { data: syllabusData, isLoading } = useQuery({
    queryKey: ['syllabus-progress', subject],
    queryFn: async () => (await apiClient.get(`/improvement/syllabus-progress/${encodeURIComponent(subject)}`)).data,
  });

  const grandFinaleMutation = useMutation({
    mutationFn: async (d: any) => (await apiClient.post('/improvement/grand-finale-complete', d)).data,
    onSuccess: (d) => {
      if (d.passed) {
        toast.success(`👑 Grand Finale PASSED! +${d.xp_earned} XP — Recommendations updated!`, { duration: 5000 });
      } else {
        toast(`Keep practicing! You scored ${d.percentage}%. Need 80% to pass.`, { icon: '💪' });
      }
      qc.invalidateQueries({ queryKey: ['improvement-progress'] });
      qc.invalidateQueries({ queryKey: ['syllabus-progress'] });
      qc.invalidateQueries({ queryKey: ['mastery-summary'] });
      qc.invalidateQueries({ queryKey: ['weak-subjects'] });
      setGrandFinaleActive(false);
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-200 dark:border-indigo-900" />
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-600 dark:text-gray-300 font-medium">Loading syllabus for {subject}...</p>
      </div>
    );
  }

  const units: any[] = syllabusData?.units || [];
  const hasCoding = syllabusData?.has_coding || false;
  const totalUnits = syllabusData?.total_units || 0;
  const completedUnits = syllabusData?.completed_units || 0;
  const progress = syllabusData?.overall_progress || 0;
  const grandFinaleUnlocked = syllabusData?.grand_finale_unlocked || false;

  return (
    <div className="space-y-5 p-1">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
        <ArrowLeft className="w-4 h-4" /> Back to subjects
      </button>

      {/* Subject Header with Progress */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-6 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-black">{subject}</h2>
            <p className="text-white/70 text-sm mt-1">
              {completedUnits}/{totalUnits} units completed • Progress through the syllabus
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-black">{Math.round(progress)}%</p>
            <p className="text-xs text-white/60">Syllabus Progress</p>
          </div>
        </div>
        <div className="mt-3 h-3 bg-white/20 rounded-full overflow-hidden">
          <motion.div initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 1 }}
            className="h-full bg-white/50 rounded-full" />
        </div>
        {!hasCoding && (
          <p className="text-xs text-white/50 mt-2 italic">💡 Code Studio is not shown for this subject (non-programming)</p>
        )}
      </div>

      {/* Syllabus Unit Roadmap */}
      <div className="space-y-3">
        {units.map((unit: any, idx: number) => {
          const isLocked = unit.locked;
          const isCompleted = unit.completed;
          const isExpanded = expandedUnit === idx;
          const topicsList: string[] = unit.topics || [];

          return (
            <motion.div key={idx} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`rounded-xl border-2 overflow-hidden transition-all ${
                isCompleted ? 'border-green-400 dark:border-green-700 bg-green-50/50 dark:bg-green-900/10' :
                isLocked ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-60' :
                'border-indigo-300 dark:border-indigo-700 bg-white dark:bg-gray-800 shadow-md'
              }`}>
              {/* Unit Header */}
              <button onClick={() => !isLocked && setExpandedUnit(isExpanded ? null : idx)}
                disabled={isLocked}
                className="w-full flex items-center gap-3 p-4 text-left">
                {/* Step indicator */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                  isCompleted ? 'bg-green-500 text-white' :
                  isLocked ? 'bg-gray-300 dark:bg-gray-600 text-gray-500' :
                  'bg-indigo-500 text-white'
                }`}>
                  {isCompleted ? <CheckCircle className="w-5 h-5" /> :
                   isLocked ? <Lock className="w-4 h-4" /> :
                   unit.unit_number}
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className={`font-semibold text-sm ${isLocked ? 'text-gray-400' : 'text-gray-900 dark:text-white'}`}>
                    Unit {unit.unit_number}: {unit.title}
                  </h3>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {topicsList.slice(0, 4).map((t: string, ti: number) => (
                      <span key={ti} className="text-[10px] px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400">
                        {typeof t === 'string' ? t.slice(0, 25) : ''}
                      </span>
                    ))}
                    {topicsList.length > 4 && <span className="text-[10px] text-gray-400">+{topicsList.length - 4}</span>}
                  </div>
                </div>

                {/* Mastery badge */}
                {unit.mastery_pct > 0 && (
                  <span className={`text-xs font-bold px-2 py-1 rounded-lg ${
                    unit.mastery_pct >= 80 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    unit.mastery_pct >= 60 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>{unit.mastery_pct}%</span>
                )}

                {!isLocked && (isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />)}
              </button>

              {/* Expanded: 5 Engines for this unit */}
              <AnimatePresence>
                {isExpanded && !isLocked && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="px-4 pb-4 space-y-3">
                      <div className="border-t border-gray-200 dark:border-gray-700 pt-3" />
                      <p className="text-xs text-gray-500 mb-2">Complete activities to master this unit (need 60%+)</p>

                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {/* Theory */}
                        <button onClick={() => onTheory(topicsList.join(', ') || unit.title, 'medium')}
                          className="flex items-center gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors text-left">
                          <span className="text-lg">🧠</span>
                          <div><p className="text-xs font-semibold text-indigo-700 dark:text-indigo-300">Theory Engine</p>
                          <p className="text-[10px] text-gray-500">AI lesson on {unit.title}</p></div>
                        </button>

                        {/* Quiz */}
                        <button onClick={() => onQuiz('mcq', 'medium')}
                          className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors text-left">
                          <span className="text-lg">⚔️</span>
                          <div><p className="text-xs font-semibold text-amber-700 dark:text-amber-300">Quiz Arena</p>
                          <p className="text-[10px] text-gray-500">MCQ on unit topics</p></div>
                        </button>

                        {/* Practical */}
                        <button onClick={() => onGame('output_predict', 'medium')}
                          className="flex items-center gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors text-left">
                          <span className="text-lg">🔬</span>
                          <div><p className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Practical Lab</p>
                          <p className="text-[10px] text-gray-500">Output prediction</p></div>
                        </button>

                        {/* Concept Clash */}
                        <button onClick={() => onGame('concept_match', 'medium')}
                          className="flex items-center gap-2 p-3 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-xl hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors text-left">
                          <span className="text-lg">🔗</span>
                          <div><p className="text-xs font-semibold text-purple-700 dark:text-purple-300">Concept Clash</p>
                          <p className="text-[10px] text-gray-500">Match terms & definitions</p></div>
                        </button>

                        {/* Code Studio (only for coding subjects) */}
                        {hasCoding && (
                          <button onClick={() => onCode('medium')}
                            className="flex items-center gap-2 p-3 bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-800 rounded-xl hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors text-left">
                            <span className="text-lg">💻</span>
                            <div><p className="text-xs font-semibold text-violet-700 dark:text-violet-300">Code Studio</p>
                            <p className="text-[10px] text-gray-500">Editor + tests</p></div>
                          </button>
                        )}

                        {/* Boss Battle */}
                        <button onClick={() => onBoss(topicsList[0] || unit.title, 'medium')}
                          className="flex items-center gap-2 p-3 bg-gray-900 dark:bg-gray-800 border border-red-800/40 rounded-xl hover:bg-gray-800 dark:hover:bg-gray-700 transition-colors text-left">
                          <span className="text-lg">👹</span>
                          <div><p className="text-xs font-semibold text-red-400">Boss Battle</p>
                          <p className="text-[10px] text-gray-500">Defeat the unit boss</p></div>
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}

        {/* Grand Finale */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className={`rounded-2xl border-2 overflow-hidden ${
            grandFinaleUnlocked
              ? 'border-yellow-400 dark:border-yellow-600 bg-gradient-to-br from-yellow-50 via-amber-50 to-orange-50 dark:from-yellow-900/20 dark:via-amber-900/20 dark:to-orange-900/20 shadow-lg'
              : 'border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800/50 opacity-50'
          }`}>
          <div className="p-5">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl ${
                grandFinaleUnlocked ? 'bg-yellow-400 dark:bg-yellow-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}>
                {grandFinaleUnlocked ? '👑' : <Lock className="w-5 h-5 text-gray-500" />}
              </div>
              <div className="flex-1">
                <h3 className="font-black text-lg text-gray-900 dark:text-white">🏆 Grand Finale</h3>
                <p className="text-xs text-gray-500">
                  {grandFinaleUnlocked
                    ? 'All units mastered! Take the cumulative exam to prove your mastery and update your recommendations.'
                    : `Complete all ${totalUnits} units to unlock the Grand Finale (${completedUnits}/${totalUnits} done)`}
                </p>
              </div>
              {grandFinaleUnlocked && (
                <div className="flex items-center gap-1 text-amber-600">
                  <Zap className="w-4 h-4" /><span className="text-xs font-bold">3× XP</span>
                </div>
              )}
            </div>
            {grandFinaleUnlocked && (
              <button onClick={() => {
                toast.loading('Generating Grand Finale exam...', { id: 'gf' });
                apiClient.post('/improvement/grand-finale', { subject, count: 10, difficulty: 'hard', quiz_type: 'mcq', topic: '' })
                  .then(r => {
                    toast.dismiss('gf');
                    setGrandFinaleActive(true);
                    // Store questions in localStorage for the quiz component
                    localStorage.setItem('grandFinaleQuestions', JSON.stringify(r.data));
                    onQuiz('mcq', 'hard');
                  })
                  .catch(() => { toast.dismiss('gf'); toast.error('Failed to generate Grand Finale'); });
              }}
                className="mt-4 w-full py-3 bg-gradient-to-r from-yellow-500 to-amber-500 hover:from-yellow-600 hover:to-amber-600 text-white rounded-xl font-bold text-sm shadow-lg transition-colors flex items-center justify-center gap-2">
                <Trophy className="w-5 h-5" /> Begin Grand Finale Exam
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default SyllabusProgressionView;
