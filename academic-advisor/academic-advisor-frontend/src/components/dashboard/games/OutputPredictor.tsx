import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, ArrowRight, ArrowLeft, Clock, Zap, Star, RotateCcw, Code } from 'lucide-react';

interface OutputPredictorProps {
  subject: string;
  difficulty: string;
  onComplete: (data: { correct: number; total: number; score: number; subject: string; quizType: string; timeSpent: number }) => void;
  onBack: () => void;
}

interface CodeQ { code: string; options: string[]; correct: number; explanation: string; title?: string; }

const QUESTIONS: Record<string, CodeQ[]> = {
  "Data Structures and Algorithms": [
    { title: "Fibonacci Recursion", code: `def mystery(n):\n    if n <= 1:\n        return n\n    return mystery(n-1) + mystery(n-2)\nprint(mystery(5))`, options: ["5", "8", "3", "13"], correct: 0, explanation: "This is the Fibonacci sequence. F(5) = F(4)+F(3) = 3+2 = 5" },
    { title: "Stack Operations", code: `stack = []\nstack.append(1)\nstack.append(2)\nstack.append(3)\nstack.pop()\nprint(stack[-1])`, options: ["1", "2", "3", "Error"], correct: 1, explanation: "After pushing 1,2,3 and popping 3, the top element is 2" },
    { title: "Sorting & Index", code: `arr = [3, 1, 4, 1, 5]\narr.sort()\nprint(arr[2])`, options: ["4", "1", "3", "5"], correct: 2, explanation: "After sorting: [1,1,3,4,5]. Index 2 is 3" },
    { title: "Binary Search", code: `def search(arr, x):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if arr[mid] == x: return mid\n        elif arr[mid] < x: lo = mid+1\n        else: hi = mid-1\n    return -1\nprint(search([2,4,6,8,10], 6))`, options: ["2", "3", "1", "0"], correct: 0, explanation: "Binary search finds 6 at index 2" },
    { title: "Queue Operations", code: `from collections import deque\nq = deque()\nq.append('A')\nq.append('B')\nq.append('C')\nq.popleft()\nq.popleft()\nprint(q[0])`, options: ["A", "B", "C", "Error"], correct: 2, explanation: "Queue FIFO: after removing A and B, C remains at front" },
    { title: "Linked List Length", code: `class Node:\n    def __init__(self, val):\n        self.val = val\n        self.next = None\n\ndef length(head):\n    count = 0\n    while head:\n        count += 1\n        head = head.next\n    return count\n\na = Node(1)\na.next = Node(2)\na.next.next = Node(3)\nprint(length(a))`, options: ["3", "2", "1", "0"], correct: 0, explanation: "The linked list has 3 nodes: 1→2→3, so length returns 3" },
    { title: "Dictionary Max", code: `scores = {'Alice': 85, 'Bob': 92, 'Carol': 78}\nwinner = max(scores, key=scores.get)\nprint(winner)`, options: ["Bob", "92", "Alice", "Carol"], correct: 0, explanation: "max() with key=scores.get returns the key with highest value: 'Bob' (92)" },
  ],
  "Operating Systems": [
    { title: "SJF Scheduling", code: `# Process scheduling (SJF)\n# Arrival: P1=0, P2=1, P3=2\n# Burst:   P1=6, P2=2, P3=4\n# Avg waiting time?`, options: ["3.0", "4.33", "2.33", "5.0"], correct: 2, explanation: "SJF: P1(0-6), P2 waits 5, P3 waits 4. Avg = (0+5+2)/3 ≈ 2.33" },
    { title: "FIFO Page Faults", code: `# Page Reference: 1,2,3,4,1,2,5\n# Frames = 3, FIFO replacement\n# Total page faults?`, options: ["5", "6", "7", "4"], correct: 2, explanation: "FIFO with 3 frames causes 7 page faults in this sequence" },
    { title: "Fork Process", code: `import os\npid = os.fork()\nif pid == 0:\n    print("Child")\nelse:\n    print("Parent")`, options: ["Child\\nParent", "Parent\\nChild", "Both are possible", "Only Parent"], correct: 2, explanation: "fork() creates a child. Output order depends on OS scheduling — both orders are possible" },
    { title: "Process Count", code: `# How many processes are created?\nfork()\nfork()\nfork()\n# Total processes = ?`, options: ["8", "6", "3", "4"], correct: 0, explanation: "Each fork() doubles processes: 1→2→4→8. Total = 2³ = 8 processes" },
    { title: "Banker's Algorithm", code: `# Available: [3, 3, 2]\n# Max Need: P0=[7,5,3] P1=[3,2,2]\n# Allocation: P0=[0,1,0] P1=[2,0,0]\n# Remaining need of P1?`, options: ["[1,2,2]", "[3,2,2]", "[2,0,0]", "[1,2,0]"], correct: 0, explanation: "Need = Max - Allocation. P1: [3,2,2] - [2,0,0] = [1,2,2]" },
  ],
  "Database Management Systems": [
    { title: "GROUP BY + HAVING", code: `-- Students(id, name, marks)\nSELECT COUNT(*) FROM Students\nWHERE marks > 60\nGROUP BY name\nHAVING COUNT(*) > 1;`, options: ["Students scoring >60", "Duplicate names with marks>60", "Error - invalid", "All names"], correct: 1, explanation: "GROUP BY name + HAVING COUNT(*)>1 finds duplicate names among students with marks > 60" },
    { title: "LEFT JOIN + NULL", code: `-- emp(id, name, dept_id)\n-- dept(id, name)\nSELECT e.name FROM emp e\nLEFT JOIN dept d ON e.dept_id = d.id\nWHERE d.id IS NULL;`, options: ["Employees with no dept", "All employees", "All departments", "Error"], correct: 0, explanation: "LEFT JOIN + WHERE d.id IS NULL returns employees whose dept_id doesn't match any department" },
    { title: "Subquery Result", code: `-- emp(id, name, salary, dept_id)\nSELECT name FROM emp\nWHERE salary > (\n  SELECT AVG(salary) FROM emp\n);`, options: ["Above-average earners", "All employees", "Highest salary only", "Error"], correct: 0, explanation: "The subquery computes avg salary; outer query selects employees earning more than that average" },
    { title: "Normal Form", code: `-- Table: Student(roll, name, phone)\n-- roll -> name (FD)\n-- roll ->> phone (MVD)\n-- One student has multiple phones\n-- Highest normal form?`, options: ["1NF", "2NF", "BCNF", "4NF"], correct: 0, explanation: "Multi-valued phone numbers violate 1NF if stored as comma-separated; the table is at most in 1NF" },
  ],
  "Computer Networks": [
    { title: "Subnet Calculation", code: `# Given IP: 192.168.1.130/26\n# What is the subnet mask?`, options: ["255.255.255.192", "255.255.255.128", "255.255.255.224", "255.255.255.0"], correct: 0, explanation: "/26 = 26 bits for network = 255.255.255.11000000 = 255.255.255.192" },
    { title: "TCP Handshake", code: `# TCP 3-way handshake\n# Client sends SYN (seq=100)\n# Server responds with?\n# Client sends?`, options: ["SYN-ACK(101), ACK(102)", "ACK(101), SYN(102)", "SYN-ACK(101,300), ACK(301)", "SYN(200), ACK(201)"], correct: 2, explanation: "Server: SYN-ACK with ack=101, seq=300. Client: ACK with ack=301" },
    { title: "Host Count", code: `# Network: 10.0.0.0/24\n# How many usable host addresses?`, options: ["254", "256", "255", "252"], correct: 0, explanation: "/24 = 256 addresses total, minus network (10.0.0.0) and broadcast (10.0.0.255) = 254 usable" },
    { title: "OSI Layer", code: `# Which layer handles:\n# - Routing between networks\n# - Logical addressing (IP)\n# - Path determination`, options: ["Network Layer (3)", "Transport Layer (4)", "Data Link Layer (2)", "Session Layer (5)"], correct: 0, explanation: "The Network Layer (Layer 3) handles routing, IP addressing, and path determination" },
  ],
};

const DEFAULT_QS: CodeQ[] = [
  { title: "Reference vs Value", code: `x = 10\ny = x\nx = 20\nprint(y)`, options: ["10", "20", "Error", "None"], correct: 0, explanation: "y gets the value 10 when assigned. Changing x later doesn't affect y." },
  { title: "List Mutability", code: `a = [1, 2, 3]\nb = a\nb.append(4)\nprint(len(a))`, options: ["3", "4", "Error", "1"], correct: 1, explanation: "Lists are mutable and b=a makes both point to the same list." },
  { title: "String Slicing", code: `s = "Hello World"\nprint(s[0:5])\nprint(s[-5:])`, options: ["Hello\\nWorld", "Hello\\norld", "H\\nW", "Error"], correct: 0, explanation: "s[0:5] gives 'Hello', s[-5:] gives 'World'" },
];

const OutputPredictor: React.FC<OutputPredictorProps> = ({ subject, difficulty, onComplete, onBack }) => {
  const allQ = (QUESTIONS[subject] || DEFAULT_QS);
  const questions = allQ.slice(0, difficulty === 'easy' ? 3 : difficulty === 'medium' ? 4 : 5);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);
  const [startTime] = useState(Date.now());
  const [timer, setTimer] = useState(0);
  const [streak, setStreak] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

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
      onComplete({ correct: correctCount, total: questions.length, score: Math.round((correctCount / questions.length) * 100), subject, quizType: 'output_predict', timeSpent });
    } else {
      setCurrentQ(c => c + 1);
      setSelected(null);
      setShowAnswer(false);
    }
  };

  if (finished) {
    const pct = Math.round((correctCount / questions.length) * 100);
    const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
    const emoji = pct >= 80 ? '🎯' : pct >= 50 ? '👍' : '📚';
    const title = pct >= 80 ? 'Sharp Eye!' : pct >= 50 ? 'Good Work!' : 'Keep Practicing!';
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
        <p className="text-gray-500 text-sm mb-6">{correctCount}/{questions.length} outputs predicted correctly</p>
        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Score</p><p className="text-lg font-bold text-emerald-600">{pct}%</p></div>
          <div><p className="text-xs text-gray-400">XP Earned</p><p className="text-lg font-bold text-amber-600">+{correctCount * 25}</p></div>
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back
          </button>
          <button onClick={() => window.location.reload()} className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all">
            <RotateCcw className="w-4 h-4 inline mr-1" /> Try Again
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
      <div className="bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 rounded-2xl p-5 text-white shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm text-xl">🔮</div>
            <div>
              <h2 className="font-bold text-lg">Output Predictor</h2>
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
            className="h-full bg-gradient-to-r from-green-300 to-emerald-200 rounded-full" />
        </div>
        <div className="flex justify-between text-xs text-white/60 mt-1.5">
          <span>✅ {correctCount} correct</span>
          <span>{Math.round(progressPct)}% complete</span>
        </div>
      </div>

      {/* Question card */}
      <motion.div key={currentQ} initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">

        {/* Question title */}
        {q.title && (
          <div className="px-6 pt-5 pb-2">
            <div className="flex items-center gap-2">
              <Code className="w-4 h-4 text-emerald-500" />
              <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{q.title}</span>
            </div>
          </div>
        )}

        {/* Code block */}
        <div className="px-6 pb-4">
          <div className="relative rounded-xl overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-8 bg-gray-800 flex items-center px-3 gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
              <span className="text-xs text-gray-500 ml-2 font-mono">output.py</span>
            </div>
            <pre className="bg-gray-900 text-green-400 p-4 pt-10 text-sm font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">{q.code}</pre>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3 font-medium">What will this output?</p>
        </div>

        {/* Options */}
        <div className="px-6 pb-6 space-y-2.5">
          {q.options.map((opt, i) => {
            let cls = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 hover:border-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/10';
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
                <code className="font-mono text-sm text-gray-800 dark:text-gray-200">{opt}</code>
              </motion.button>
            );
          })}
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

      {/* Next button */}
      <AnimatePresence>
        {showAnswer && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-end">
            <button onClick={handleNext}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-medium text-sm hover:shadow-lg hover:shadow-emerald-500/20 transition-all">
              {currentQ + 1 >= questions.length ? 'See Results' : 'Next Question'} <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default OutputPredictor;
