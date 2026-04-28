import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, ArrowLeft, Zap, Clock, Star, RotateCcw } from 'lucide-react';

interface ConceptClashProps {
  subject: string;
  difficulty: string;
  onComplete: (data: { correct: number; total: number; score: number; subject: string; quizType: string; timeSpent: number }) => void;
  onBack: () => void;
}

interface Pair { term: string; definition: string; }

const FALLBACK_PAIRS: Record<string, Pair[]> = {
  "Operating Systems": [
    { term: "Deadlock", definition: "Circular wait where processes block each other indefinitely" },
    { term: "Semaphore", definition: "Synchronization primitive using signal and wait operations" },
    { term: "Thrashing", definition: "Excessive paging causing severe performance degradation" },
    { term: "Mutex", definition: "Mutual exclusion lock for critical section protection" },
    { term: "Virtual Memory", definition: "Technique that uses disk to extend physical RAM capacity" },
    { term: "Page Fault", definition: "Interrupt when accessed page is not in physical memory" },
    { term: "Context Switch", definition: "Saving and restoring CPU state when switching processes" },
    { term: "Starvation", definition: "Process indefinitely denied resources despite being ready" },
  ],
  "Database Management Systems": [
    { term: "Normalization", definition: "Process of organizing data to minimize redundancy" },
    { term: "ACID", definition: "Atomicity, Consistency, Isolation, Durability properties" },
    { term: "Foreign Key", definition: "Attribute referencing the primary key of another table" },
    { term: "JOIN", definition: "Operation combining rows from two or more tables" },
    { term: "Index", definition: "Data structure improving speed of data retrieval operations" },
    { term: "Transaction", definition: "Logical unit of work that must be completed entirely" },
    { term: "View", definition: "Virtual table based on the result of a SELECT query" },
    { term: "Trigger", definition: "Stored procedure automatically executed on data events" },
  ],
  "Data Structures and Algorithms": [
    { term: "Stack", definition: "LIFO data structure with push and pop operations" },
    { term: "Binary Search", definition: "O(log n) search on sorted array by halving search space" },
    { term: "Hash Table", definition: "Key-value store using hash function for O(1) average lookup" },
    { term: "BFS", definition: "Graph traversal exploring all neighbors before going deeper" },
    { term: "Recursion", definition: "Function that calls itself to solve smaller subproblems" },
    { term: "Heap", definition: "Complete binary tree satisfying the heap ordering property" },
    { term: "DFS", definition: "Graph traversal exploring as far as possible before backtracking" },
    { term: "Queue", definition: "FIFO data structure with enqueue and dequeue operations" },
  ],
  "Computer Networks": [
    { term: "TCP", definition: "Connection-oriented protocol ensuring reliable data delivery" },
    { term: "DNS", definition: "System translating domain names to IP addresses" },
    { term: "Subnet Mask", definition: "Determines network and host portions of an IP address" },
    { term: "ARP", definition: "Protocol mapping IP addresses to MAC addresses" },
    { term: "Firewall", definition: "Security system monitoring and filtering network traffic" },
    { term: "DHCP", definition: "Protocol automatically assigning IP addresses to devices" },
    { term: "HTTP", definition: "Application layer protocol for transferring hypertext" },
    { term: "SMTP", definition: "Protocol used for sending email messages between servers" },
  ],
  "Software Engineering": [
    { term: "Agile", definition: "Iterative development methodology with frequent feedback" },
    { term: "Unit Test", definition: "Testing individual components in isolation" },
    { term: "CI/CD", definition: "Automated building, testing and deployment pipeline" },
    { term: "Refactoring", definition: "Restructuring code without changing external behavior" },
    { term: "Design Pattern", definition: "Reusable solution to a commonly occurring problem" },
    { term: "UML", definition: "Unified Modeling Language for visualizing system design" },
  ],
};

const DEFAULT_PAIRS: Pair[] = [
  { term: "Algorithm", definition: "Step-by-step procedure for solving a problem" },
  { term: "Variable", definition: "Named storage location in memory holding a value" },
  { term: "Function", definition: "Reusable block of code performing a specific task" },
  { term: "Loop", definition: "Control structure that repeats a block of code" },
  { term: "Array", definition: "Collection of elements stored in contiguous memory" },
  { term: "Compiler", definition: "Program that translates source code to machine code" },
];

const LANE_GRADIENT = 'from-indigo-600 via-blue-600 to-cyan-500';

const ConceptClash: React.FC<ConceptClashProps> = ({ subject, difficulty, onComplete, onBack }) => {
  const [pairs, setPairs] = useState<Pair[]>([]);
  const [shuffledDefs, setShuffledDefs] = useState<string[]>([]);
  const [selectedTerm, setSelectedTerm] = useState<number | null>(null);
  const [matches, setMatches] = useState<Record<number, number>>({});
  const [wrong, setWrong] = useState<{ term: number; def: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [startTime] = useState(Date.now());
  const [correctCount, setCorrectCount] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);
  const [timer, setTimer] = useState(0);
  const [combo, setCombo] = useState(0);
  const [maxCombo, setMaxCombo] = useState(0);
  const [showSuccess, setShowSuccess] = useState<number | null>(null);

  useEffect(() => {
    const subjectPairs = FALLBACK_PAIRS[subject] || DEFAULT_PAIRS;
    const count = difficulty === 'easy' ? 4 : difficulty === 'medium' ? 5 : 6;
    const shuffled = [...subjectPairs].sort(() => Math.random() - 0.5).slice(0, count);
    setPairs(shuffled);
    setShuffledDefs([...shuffled.map(p => p.definition)].sort(() => Math.random() - 0.5));
    setLoading(false);
  }, [subject, difficulty]);

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const handleDefClick = useCallback((defIdx: number) => {
    if (selectedTerm === null || defIdx in Object.values(matches)) return;
    const defText = shuffledDefs[defIdx];
    const correctDef = pairs[selectedTerm].definition;

    if (defText === correctDef) {
      const newCombo = combo + 1;
      setCombo(newCombo);
      setMaxCombo(m => Math.max(m, newCombo));
      setMatches(prev => ({ ...prev, [selectedTerm]: defIdx }));
      setCorrectCount(c => c + 1);
      setShowSuccess(selectedTerm);
      setTimeout(() => setShowSuccess(null), 600);
      setSelectedTerm(null);

      if (Object.keys(matches).length + 1 === pairs.length) {
        const timeSpent = Math.floor((Date.now() - startTime) / 1000);
        const score = Math.round(((correctCount + 1) / pairs.length) * 100);
        setTimeout(() => onComplete({ correct: correctCount + 1, total: pairs.length, score, subject, quizType: 'concept_match', timeSpent }), 800);
      }
    } else {
      setCombo(0);
      setWrongCount(w => w + 1);
      setWrong({ term: selectedTerm, def: defIdx });
      setTimeout(() => { setWrong(null); setSelectedTerm(null); }, 700);
    }
  }, [selectedTerm, matches, pairs, shuffledDefs, combo, correctCount, startTime, subject, onComplete]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-200 dark:border-indigo-900" />
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-500 animate-pulse">Loading concept pairs...</p>
      </div>
    );
  }

  const allMatched = Object.keys(matches).length === pairs.length;
  const matchedCount = Object.keys(matches).length;
  const progressPct = (matchedCount / pairs.length) * 100;

  if (allMatched) {
    const pct = Math.round((correctCount / pairs.length) * 100);
    const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
    return (
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md mx-auto text-center py-8">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }} className="relative mx-auto mb-6">
          <div className={`w-28 h-28 rounded-full bg-gradient-to-br ${LANE_GRADIENT} mx-auto flex items-center justify-center shadow-lg shadow-indigo-500/30`}>
            <div className="text-5xl">🏆</div>
          </div>
          <motion.div initial={{ scale: 0 }} animate={{ scale: [0, 1.3, 1] }} transition={{ delay: 0.5 }}
            className="absolute -top-2 -right-2 w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center shadow-md">
            <Star className="w-5 h-5 text-yellow-800 fill-yellow-800" />
          </motion.div>
        </motion.div>
        <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-1">All Matched!</h3>
        <p className="text-gray-500 text-sm mb-6">You connected all {pairs.length} concept pairs</p>
        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Accuracy</p><p className="text-lg font-bold text-green-600">{pct}%</p></div>
          <div><p className="text-xs text-gray-400">Max Combo</p><p className="text-lg font-bold text-amber-600">🔥 {maxCombo}x</p></div>
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back to Hub
          </button>
          <button onClick={() => window.location.reload()} className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all">
            <RotateCcw className="w-4 h-4 inline mr-1" /> Play Again
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 via-blue-500 to-cyan-500 rounded-2xl p-5 text-white shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm text-xl">🔗</div>
            <div>
              <h2 className="font-bold text-lg">Concept Clash</h2>
              <p className="text-xs text-white/70">{subject} • {difficulty}</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 bg-white/15 rounded-lg px-3 py-1.5 backdrop-blur-sm">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-mono">{Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}</span>
            </div>
            {combo > 1 && (
              <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex items-center gap-1 bg-amber-400/30 rounded-lg px-3 py-1.5 backdrop-blur-sm">
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                <span className="font-bold text-amber-200">{combo}x</span>
              </motion.div>
            )}
          </div>
        </div>
        {/* Progress bar */}
        <div className="h-2.5 bg-white/15 rounded-full overflow-hidden">
          <motion.div animate={{ width: `${progressPct}%` }} transition={{ type: 'spring' }}
            className="h-full bg-gradient-to-r from-green-400 to-emerald-300 rounded-full" />
        </div>
        <div className="flex justify-between text-xs text-white/60 mt-1.5">
          <span>Match terms with definitions</span>
          <span>{matchedCount}/{pairs.length} matched</span>
        </div>
      </div>

      {/* Game area */}
      <div className="grid grid-cols-2 gap-5">
        {/* Terms column */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 px-1 mb-1">
            <div className="w-2 h-2 rounded-full bg-indigo-500" />
            <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest">Terms</h3>
          </div>
          <AnimatePresence>
            {pairs.map((p, i) => {
              const isMatched = i in matches;
              const isSelected = selectedTerm === i;
              const isWrongTerm = wrong?.term === i;
              const isJustMatched = showSuccess === i;
              return (
                <motion.button key={i} layout disabled={isMatched}
                  onClick={() => setSelectedTerm(isSelected ? null : i)}
                  whileHover={!isMatched ? { scale: 1.02, y: -1 } : {}}
                  whileTap={!isMatched ? { scale: 0.98 } : {}}
                  animate={isJustMatched ? { scale: [1, 1.1, 1] } : {}}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 font-medium text-sm relative overflow-hidden ${
                    isMatched ? 'border-green-400/60 bg-green-50 dark:bg-green-900/15 text-green-600 dark:text-green-400' :
                    isWrongTerm ? 'border-red-400 bg-red-50 dark:bg-red-900/20 animate-[shake_0.3s_ease-in-out]' :
                    isSelected ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 shadow-lg shadow-indigo-500/10 ring-2 ring-indigo-500/20' :
                    'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-indigo-300 hover:shadow-md'
                  }`}>
                  {isMatched && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="absolute right-3 top-1/2 -translate-y-1/2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    </motion.div>
                  )}
                  <span className={isMatched ? 'line-through opacity-60' : ''}>{p.term}</span>
                </motion.button>
              );
            })}
          </AnimatePresence>
        </div>

        {/* Definitions column */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 px-1 mb-1">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest">Definitions</h3>
          </div>
          {shuffledDefs.map((def, i) => {
            const isMatched = Object.values(matches).includes(i);
            const isWrongDef = wrong?.def === i;
            return (
              <motion.button key={i} layout disabled={isMatched || selectedTerm === null}
                onClick={() => handleDefClick(i)}
                whileHover={!isMatched && selectedTerm !== null ? { scale: 1.02, y: -1 } : {}}
                whileTap={!isMatched && selectedTerm !== null ? { scale: 0.98 } : {}}
                className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 text-sm ${
                  isMatched ? 'border-green-400/60 bg-green-50 dark:bg-green-900/15 text-green-600 dark:text-green-400' :
                  isWrongDef ? 'border-red-400 bg-red-50 dark:bg-red-900/20 animate-[shake_0.3s_ease-in-out]' :
                  selectedTerm !== null ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-purple-400 hover:bg-purple-50/50 dark:hover:bg-purple-900/10 cursor-pointer hover:shadow-md' :
                  'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-50 cursor-not-allowed'
                }`}>
                <span className={isMatched ? 'line-through opacity-60' : ''}>{def}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {selectedTerm === null && !allMatched && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center text-sm text-gray-400 dark:text-gray-500 py-2">
          👆 Select a term on the left to start matching
        </motion.p>
      )}
    </div>
  );
};

export default ConceptClash;
