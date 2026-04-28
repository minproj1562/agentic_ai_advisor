import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, ArrowRight, ArrowLeft, Loader2, Clock, Award, RotateCcw, Zap, Brain, Code, BookOpen } from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

interface Question {
  question: string;
  options: string[];
  correct: number;
  explanation: string;
}

interface QuizGameProps {
  subject: string;
  quizType: string;
  difficulty: string;
  onComplete: (data: { correct: number; total: number; score: number; subject: string; quizType: string; timeSpent: number }) => void;
  onBack: () => void;
}

const QUIZ_META: Record<string, { icon: string; label: string; gradient: string; emoji: string }> = {
  mcq: { icon: '📝', label: 'Theory Quiz', gradient: 'from-indigo-500 via-blue-500 to-cyan-500', emoji: '📝' },
  code_debug: { icon: '🐛', label: 'Bug Hunter', gradient: 'from-red-500 via-rose-500 to-pink-500', emoji: '🐛' },
  fill_blank: { icon: '✏️', label: 'Fill the Gap', gradient: 'from-amber-500 via-orange-500 to-red-500', emoji: '✏️' },
};

const QuizGame: React.FC<QuizGameProps> = ({ subject, quizType, difficulty, onComplete, onBack }) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);
  const [startTime] = useState(Date.now());
  const [timer, setTimer] = useState(0);
  const [streak, setStreak] = useState(0);

  const meta = QUIZ_META[quizType] || QUIZ_META.mcq;

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const res = await apiClient.post('/improvement/generate-quiz', {
          subject, topic: '', difficulty, count: 5, quiz_type: quizType,
        });
        setQuestions(res.data.questions || []);
      } catch {
        toast.error('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [subject, quizType, difficulty]);

  const handleSelect = (idx: number) => {
    if (showAnswer) return;
    setSelected(idx);
    setShowAnswer(true);
    if (idx === questions[currentQ].correct) {
      setCorrectCount(c => c + 1);
      setStreak(s => s + 1);
    } else {
      setStreak(0);
    }
  };

  const handleNext = () => {
    if (currentQ + 1 >= questions.length) {
      setFinished(true);
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      onComplete({ correct: correctCount, total: questions.length, score: Math.round((correctCount / questions.length) * 100), subject, quizType, timeSpent });
    } else {
      setCurrentQ(c => c + 1);
      setSelected(null);
      setShowAnswer(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-200 dark:border-indigo-900" />
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
        </div>
        <div className="text-center">
          <p className="text-gray-700 dark:text-gray-300 font-medium">Generating questions...</p>
          <p className="text-sm text-gray-400 mt-1">{subject} • {difficulty}</p>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">😕</div>
        <p className="text-gray-500 mb-4 font-medium">No questions available for {subject}</p>
        <button onClick={onBack} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700">Go Back</button>
      </div>
    );
  }

  if (finished) {
    const pct = Math.round((correctCount / questions.length) * 100);
    const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
    const emoji = pct >= 80 ? '🎉' : pct >= 50 ? '👍' : '📚';
    const title = pct >= 80 ? 'Excellent!' : pct >= 50 ? 'Good Effort!' : 'Keep Practicing!';
    return (
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md mx-auto text-center py-8">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}
          className={`w-28 h-28 rounded-full mx-auto mb-6 flex items-center justify-center shadow-lg ${
            pct >= 80 ? 'bg-gradient-to-br from-green-400 to-emerald-600 shadow-green-500/30' :
            pct >= 50 ? 'bg-gradient-to-br from-amber-400 to-orange-600 shadow-amber-500/30' :
            'bg-gradient-to-br from-red-400 to-rose-600 shadow-red-500/30'
          }`}>
          <span className="text-5xl">{emoji}</span>
        </motion.div>
        <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-1">{title}</h3>
        <p className="text-gray-500 text-sm mb-6">{correctCount}/{questions.length} correct in {subject}</p>
        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Score</p><p className={`text-lg font-bold ${pct >= 80 ? 'text-green-600' : pct >= 50 ? 'text-amber-600' : 'text-red-600'}`}>{pct}%</p></div>
          <div><p className="text-xs text-gray-400">XP Earned</p><p className="text-lg font-bold text-amber-600">+{correctCount * 25}</p></div>
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back to Hub
          </button>
          <button onClick={() => window.location.reload()} className={`px-5 py-2.5 bg-gradient-to-r ${meta.gradient} text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all`}>
            <RotateCcw className="w-4 h-4 inline mr-1" /> Play Again
          </button>
        </div>
      </motion.div>
    );
  }

  const q = questions[currentQ];
  const isCorrect = selected === q.correct;
  const progressPct = ((currentQ + (showAnswer ? 1 : 0)) / questions.length) * 100;

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {/* Header */}
      <div className={`bg-gradient-to-r ${meta.gradient} rounded-2xl p-5 text-white shadow-lg`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm text-xl">{meta.emoji}</div>
            <div>
              <h2 className="font-bold text-lg">{meta.label}</h2>
              <p className="text-xs text-white/70">{subject} • {difficulty}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {streak > 1 && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}
                className="flex items-center gap-1 bg-amber-400/30 rounded-lg px-3 py-1.5 backdrop-blur-sm">
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                <span className="font-bold text-amber-200">{streak}🔥</span>
              </motion.div>
            )}
            <div className="flex items-center gap-1.5 bg-white/15 rounded-lg px-3 py-1.5 backdrop-blur-sm">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-mono">{Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}</span>
            </div>
            <div className="bg-white/15 rounded-lg px-3 py-1.5 backdrop-blur-sm font-medium">
              {currentQ + 1}/{questions.length}
            </div>
          </div>
        </div>
        <div className="h-2.5 bg-white/15 rounded-full overflow-hidden">
          <motion.div animate={{ width: `${progressPct}%` }} transition={{ type: 'spring' }}
            className="h-full bg-gradient-to-r from-white/60 to-white/40 rounded-full" />
        </div>
        <div className="flex justify-between text-xs text-white/60 mt-1.5">
          <span>✅ {correctCount} correct</span>
          <span>{Math.round(progressPct)}% complete</span>
        </div>
      </div>

      {/* Question */}
      <AnimatePresence mode="wait">
        <motion.div key={currentQ} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }}
          className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="p-6">
            <p className="text-base font-semibold text-gray-900 dark:text-white mb-6 whitespace-pre-wrap leading-relaxed">{q.question}</p>
            <div className="space-y-2.5">
              {q.options.map((opt, i) => {
                let cls = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/10';
                if (showAnswer && i === q.correct) cls = 'border-green-500 bg-green-50 dark:bg-green-900/20 ring-2 ring-green-500/20';
                else if (showAnswer && i === selected && !isCorrect) cls = 'border-red-500 bg-red-50 dark:bg-red-900/20';
                else if (showAnswer) cls = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30 opacity-50';

                return (
                  <motion.button key={i} onClick={() => handleSelect(i)} disabled={showAnswer}
                    whileHover={!showAnswer ? { scale: 1.01 } : {}}
                    whileTap={!showAnswer ? { scale: 0.99 } : {}}
                    className={`w-full text-left p-3.5 rounded-xl border-2 transition-all flex items-center gap-3 ${cls}`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                      showAnswer && i === q.correct ? 'bg-green-500 text-white' :
                      showAnswer && i === selected && !isCorrect ? 'bg-red-500 text-white' :
                      'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                    }`}>
                      {showAnswer && i === q.correct ? <CheckCircle className="w-4 h-4" /> :
                       showAnswer && i === selected && !isCorrect ? <XCircle className="w-4 h-4" /> :
                       String.fromCharCode(65 + i)}
                    </div>
                    <span className="text-gray-800 dark:text-gray-200 text-sm flex-1">{opt}</span>
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Explanation */}
          <AnimatePresence>
            {showAnswer && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                className="border-t border-gray-200 dark:border-gray-700">
                <div className={`p-5 ${isCorrect ? 'bg-green-50/50 dark:bg-green-900/10' : 'bg-amber-50/50 dark:bg-amber-900/10'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {isCorrect ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-red-500" />}
                    <span className="font-semibold text-sm text-gray-900 dark:text-white">{isCorrect ? 'Correct! 🎉' : 'Not quite right'}</span>
                    {isCorrect && <span className="ml-auto text-xs font-bold text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full">+25 XP</span>}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{q.explanation}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </AnimatePresence>

      {/* Next button */}
      <AnimatePresence>
        {showAnswer && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
            <button onClick={handleNext}
              className={`flex items-center gap-2 px-6 py-3 bg-gradient-to-r ${meta.gradient} text-white rounded-xl font-medium text-sm hover:shadow-lg transition-all`}>
              {currentQ + 1 >= questions.length ? 'See Results' : 'Next Question'} <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default QuizGame;
