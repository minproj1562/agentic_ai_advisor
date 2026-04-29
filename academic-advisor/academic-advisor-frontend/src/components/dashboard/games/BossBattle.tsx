// academic-advisor-frontend/src/components/dashboard/games/BossBattle.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Swords, Shield, Heart, Zap, Clock, ArrowLeft,
  CheckCircle, XCircle, Flame, Star, Trophy, RotateCcw, Skull
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

interface BossQuestion {
  question: string;
  options: string[];
  correct: number;
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
}

interface BossBattleProps {
  subject: string;
  topic: string;
  difficulty: string;
  onComplete: (data: {
    correct: number; total: number; score: number;
    subject: string; quizType: string; timeSpent: number;
    bossDefeated: boolean;
  }) => void;
  onBack: () => void;
}

// Boss definitions
const BOSS_POOL = [
  { name: 'The Void Compiler', emoji: '💀', color: 'from-gray-800 to-gray-900', attack: 'Syntax Storm' },
  { name: 'Infinite Loop Dragon', emoji: '🐉', color: 'from-red-700 to-red-900', attack: 'Endless Recursion' },
  { name: 'The Null Pointer', emoji: '👻', color: 'from-purple-700 to-purple-900', attack: 'Segmentation Fault' },
  { name: 'Memory Leaker', emoji: '🧟', color: 'from-green-700 to-green-900', attack: 'Heap Overflow' },
  { name: 'Deadlock Demon', emoji: '😈', color: 'from-orange-700 to-orange-900', attack: 'Thread Starvation' },
  { name: 'The Runtime Terror', emoji: '🕷️', color: 'from-indigo-700 to-indigo-900', attack: 'Uncaught Exception' },
  { name: 'Abstraction Phantom', emoji: '🦇', color: 'from-violet-700 to-violet-900', attack: 'Complexity Surge' },
  { name: 'Binary Beast', emoji: '🤖', color: 'from-cyan-700 to-cyan-900', attack: 'Data Corruption' },
];

const BossBattle: React.FC<BossBattleProps> = ({ subject, topic, difficulty, onComplete, onBack }) => {
  const [phase, setPhase] = useState<'intro' | 'battle' | 'victory' | 'defeat'>('intro');
  const [questions, setQuestions] = useState<BossQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [streak, setStreak] = useState(0);
  const [timer, setTimer] = useState(0);
  const [startTime] = useState(Date.now());

  // Boss state
  const [bossHP, setBossHP] = useState(100);
  const [playerHP, setPlayerHP] = useState(100);
  const [boss] = useState(() => BOSS_POOL[Math.floor(Math.random() * BOSS_POOL.length)]);
  const [shakeScreen, setShakeScreen] = useState(false);
  const [attackAnimation, setAttackAnimation] = useState<'player' | 'boss' | null>(null);
  const [comboCount, setComboCount] = useState(0);
  const [showDamageText, setShowDamageText] = useState<{ value: number; type: 'player' | 'boss' } | null>(null);

  const totalQuestions = 8;
  const damagePerCorrect = 100 / Math.ceil(totalQuestions * 0.6); // Need ~60% to win
  const damagePerWrong = 100 / Math.ceil(totalQuestions * 0.5);   // Can survive ~50% wrong

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const res = await apiClient.post('/improvement/generate-quiz', {
          subject, topic: topic || '', difficulty, count: totalQuestions, quiz_type: 'mcq',
        });
        setQuestions(res.data.questions || []);
      } catch {
        toast.error('Failed to summon the boss!');
      } finally {
        setLoading(false);
      }
    };
    fetchQuestions();
  }, [subject, topic, difficulty]);

  const dealDamage = useCallback((target: 'boss' | 'player', amount: number) => {
    setShowDamageText({ value: Math.round(amount), type: target });
    setTimeout(() => setShowDamageText(null), 1200);

    if (target === 'boss') {
      setAttackAnimation('player');
      setBossHP(prev => Math.max(0, prev - amount));
    } else {
      setAttackAnimation('boss');
      setShakeScreen(true);
      setPlayerHP(prev => Math.max(0, prev - amount));
      setTimeout(() => setShakeScreen(false), 500);
    }
    setTimeout(() => setAttackAnimation(null), 600);
  }, []);

  const handleSelect = (idx: number) => {
    if (showAnswer) return;
    setSelected(idx);
    setShowAnswer(true);

    const isCorrect = idx === questions[currentQ].correct;

    if (isCorrect) {
      setCorrectCount(c => c + 1);
      setStreak(s => s + 1);
      setComboCount(c => c + 1);
      const comboDmg = comboCount >= 3 ? damagePerCorrect * 1.5 : damagePerCorrect;
      setTimeout(() => dealDamage('boss', comboDmg), 300);
    } else {
      setStreak(0);
      setComboCount(0);
      setTimeout(() => dealDamage('player', damagePerWrong), 300);
    }
  };

  const handleNext = () => {
    if (bossHP <= 0) {
      setPhase('victory');
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      onComplete({
        correct: correctCount, total: questions.length, score: Math.round((correctCount / questions.length) * 100),
        subject, quizType: 'boss_battle', timeSpent, bossDefeated: true,
      });
      return;
    }
    if (playerHP <= 0 || currentQ + 1 >= questions.length) {
      setPhase('defeat');
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      onComplete({
        correct: correctCount, total: questions.length, score: Math.round((correctCount / questions.length) * 100),
        subject, quizType: 'boss_battle', timeSpent, bossDefeated: false,
      });
      return;
    }
    setCurrentQ(c => c + 1);
    setSelected(null);
    setShowAnswer(false);
  };

  // ── Intro Screen ──
  if (phase === 'intro') {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-lg mx-auto text-center py-8">
        <motion.div
          animate={{ y: [0, -10, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className={`w-32 h-32 mx-auto mb-6 rounded-2xl bg-gradient-to-br ${boss.color} flex items-center justify-center shadow-2xl border-2 border-white/10`}
        >
          <span className="text-6xl drop-shadow-lg">{boss.emoji}</span>
        </motion.div>

        <h2 className="text-3xl font-black text-gray-900 dark:text-white mb-2">
          ⚔️ BOSS BATTLE
        </h2>
        <h3 className={`text-xl font-bold bg-gradient-to-r ${boss.color} bg-clip-text text-transparent mb-1`}>
          {boss.name}
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
          Topic: {topic || subject} • {difficulty} difficulty
        </p>

        <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-6 text-left border border-gray-200 dark:border-gray-700">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <Skull className="w-4 h-4 text-red-500" /> Boss Powers
          </h4>
          <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <li>• Special Attack: <span className="font-medium text-red-500">{boss.attack}</span></li>
            <li>• {totalQuestions} questions to defeat the boss</li>
            <li>• Wrong answers damage <span className="text-red-500 font-medium">YOU</span></li>
            <li>• Build combos for <span className="text-amber-500 font-medium">1.5× damage</span></li>
          </ul>
        </div>

        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Retreat
          </button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setPhase('battle')}
            disabled={loading}
            className="px-8 py-3 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl font-bold text-sm shadow-lg shadow-red-500/30 disabled:opacity-50"
          >
            {loading ? '⏳ Summoning...' : '⚔️ FIGHT!'}
          </motion.button>
        </div>
      </motion.div>
    );
  }

  // ── Victory Screen ──
  if (phase === 'victory') {
    const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
    const xpEarned = correctCount * 30 + 100; // Bonus for defeating boss
    return (
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md mx-auto text-center py-8">
        <motion.div
          initial={{ rotate: -10 }}
          animate={{ rotate: [0, -5, 5, 0], scale: [1, 1.1, 1] }}
          transition={{ duration: 1, repeat: 2 }}
          className="text-7xl mb-4"
        >🏆</motion.div>

        <h2 className="text-3xl font-black text-gray-900 dark:text-white mb-1">BOSS DEFEATED!</h2>
        <p className="text-gray-500 mb-1">{boss.name} has been vanquished!</p>
        <p className="text-sm text-gray-400 mb-6">{correctCount}/{questions.length} correct in {timeStr}</p>

        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Accuracy</p><p className="text-lg font-bold text-green-600">{Math.round((correctCount / questions.length) * 100)}%</p></div>
          <div><p className="text-xs text-gray-400">XP Earned</p><p className="text-lg font-bold text-amber-600">+{xpEarned}</p></div>
        </div>

        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5, type: 'spring' }}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-100 to-yellow-100 dark:from-amber-900/30 dark:to-yellow-900/30 px-4 py-2 rounded-xl mb-6 border border-amber-200 dark:border-amber-800">
          <Trophy className="w-5 h-5 text-amber-600" />
          <span className="font-bold text-amber-700 dark:text-amber-400">Boss Slayer Badge Earned!</span>
        </motion.div>

        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back
          </button>
        </div>
      </motion.div>
    );
  }

  // ── Defeat Screen ──
  if (phase === 'defeat') {
    const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
    const xpEarned = correctCount * 15; // Partial XP
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-md mx-auto text-center py-8">
        <motion.div animate={{ y: [0, -3, 0] }} transition={{ duration: 2, repeat: Infinity }}
          className="text-6xl mb-4">💀</motion.div>

        <h2 className="text-2xl font-black text-gray-900 dark:text-white mb-1">DEFEATED...</h2>
        <p className="text-gray-500 mb-1">{boss.name} was too powerful!</p>
        <p className="text-sm text-gray-400 mb-6">{correctCount}/{questions.length} correct • +{xpEarned} XP</p>

        <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-4 mb-6 border border-amber-200 dark:border-amber-800">
          <p className="text-sm text-amber-700 dark:text-amber-400">
            💡 <strong>Tip:</strong> Review the explanations for wrong answers, then try again!
          </p>
        </div>

        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back
          </button>
          <button onClick={() => window.location.reload()}
            className="px-5 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl text-sm font-medium shadow-lg">
            <RotateCcw className="w-4 h-4 inline mr-1" /> Retry Boss
          </button>
        </div>
      </motion.div>
    );
  }

  // ── Battle Screen ──
  if (questions.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">😕</div>
        <p className="text-gray-500 mb-4">Failed to summon the boss.</p>
        <button onClick={onBack} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium">Go Back</button>
      </div>
    );
  }

  const q = questions[currentQ];
  const isCorrect = selected !== null && selected === q.correct;

  return (
    <motion.div animate={shakeScreen ? { x: [-5, 5, -3, 3, 0] } : {}} transition={{ duration: 0.4 }}
      className="max-w-2xl mx-auto space-y-4">

      {/* HP Bars */}
      <div className="bg-gray-900 rounded-2xl p-4 shadow-2xl border border-gray-700">
        {/* Boss HP */}
        <div className="flex items-center gap-3 mb-3">
          <motion.div
            animate={attackAnimation === 'player' ? { x: [0, -8, 8, -4, 0], scale: [1, 0.95, 1] } : {}}
            className={`w-12 h-12 rounded-xl bg-gradient-to-br ${boss.color} flex items-center justify-center border border-white/10 shadow-lg`}
          >
            <span className="text-2xl">{boss.emoji}</span>
          </motion.div>
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-bold text-white">{boss.name}</span>
              <span className="text-xs text-red-400 font-mono">{Math.max(0, Math.round(bossHP))}/100 HP</span>
            </div>
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                animate={{ width: `${Math.max(0, bossHP)}%` }}
                transition={{ type: 'spring', stiffness: 100 }}
                className={`h-full rounded-full ${
                  bossHP > 60 ? 'bg-gradient-to-r from-red-500 to-red-400' :
                  bossHP > 30 ? 'bg-gradient-to-r from-orange-500 to-amber-400' :
                  'bg-gradient-to-r from-yellow-500 to-yellow-300'
                }`}
              />
            </div>
          </div>
        </div>

        {/* Player HP */}
        <div className="flex items-center gap-3">
          <motion.div
            animate={attackAnimation === 'boss' ? { x: [0, 8, -8, 4, 0], scale: [1, 0.95, 1] } : {}}
            className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center border border-white/10 shadow-lg"
          >
            <Shield className="w-6 h-6 text-white" />
          </motion.div>
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-bold text-white">You</span>
              <span className="text-xs text-green-400 font-mono">{Math.max(0, Math.round(playerHP))}/100 HP</span>
            </div>
            <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
              <motion.div
                animate={{ width: `${Math.max(0, playerHP)}%` }}
                transition={{ type: 'spring', stiffness: 100 }}
                className={`h-full rounded-full ${
                  playerHP > 60 ? 'bg-gradient-to-r from-green-500 to-emerald-400' :
                  playerHP > 30 ? 'bg-gradient-to-r from-amber-500 to-yellow-400' :
                  'bg-gradient-to-r from-red-500 to-red-300'
                }`}
              />
            </div>
          </div>
        </div>

        {/* Battle info bar */}
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-700">
          <div className="flex items-center gap-3 text-xs">
            {comboCount >= 2 && (
              <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }}
                className="flex items-center gap-1 bg-amber-500/20 text-amber-400 px-2 py-1 rounded-lg font-bold">
                <Flame className="w-3 h-3" /> {comboCount}× COMBO
              </motion.span>
            )}
            <span className="text-gray-400 flex items-center gap-1">
              <Clock className="w-3 h-3" /> {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}
            </span>
          </div>
          <span className="text-xs text-gray-400 font-medium">
            Round {currentQ + 1}/{questions.length}
          </span>
        </div>

        {/* Floating damage text */}
        <AnimatePresence>
          {showDamageText && (
            <motion.div
              initial={{ opacity: 1, y: 0, scale: 1 }}
              animate={{ opacity: 0, y: -40, scale: 1.5 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1 }}
              className={`absolute top-1/2 ${showDamageText.type === 'boss' ? 'left-1/4' : 'right-1/4'}
                text-2xl font-black ${showDamageText.type === 'boss' ? 'text-red-400' : 'text-yellow-400'} pointer-events-none`}
            >
              -{showDamageText.value}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Question Card */}
      <AnimatePresence mode="wait">
        <motion.div key={currentQ} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }}
          className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <Swords className="w-4 h-4 text-red-500" />
              <span className="text-xs font-medium text-gray-500 uppercase">Attack Round {currentQ + 1}</span>
            </div>
            <p className="text-base font-semibold text-gray-900 dark:text-white mb-5 whitespace-pre-wrap leading-relaxed">
              {q.question}
            </p>
            <div className="space-y-2.5">
              {q.options.map((opt, i) => {
                let cls = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 hover:border-red-400 hover:bg-red-50/30 dark:hover:bg-red-900/10';
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
                <div className={`p-4 ${isCorrect ? 'bg-green-50/50 dark:bg-green-900/10' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {isCorrect ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="font-semibold text-sm text-green-700 dark:text-green-400">
                          ⚔️ Critical Hit! {comboCount >= 3 ? '(1.5× combo damage!)' : ''}
                        </span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-5 h-5 text-red-500" />
                        <span className="font-semibold text-sm text-red-700 dark:text-red-400">
                          💥 {boss.name} uses {boss.attack}!
                        </span>
                      </>
                    )}
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
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl font-medium text-sm shadow-lg shadow-red-500/20 hover:shadow-xl transition-all">
              {bossHP <= 0 ? '🏆 Claim Victory' :
               playerHP <= 0 || currentQ + 1 >= questions.length ? '💀 See Results' :
               '⚔️ Next Attack'}
              <Swords className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default BossBattle;
