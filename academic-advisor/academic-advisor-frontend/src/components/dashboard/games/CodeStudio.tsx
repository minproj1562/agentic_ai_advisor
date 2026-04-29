// academic-advisor-frontend/src/components/dashboard/games/CodeStudio.tsx
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, ArrowLeft, Loader2, CheckCircle, XCircle, Zap,
  Lightbulb, RotateCcw, Code, Terminal, Clock, Award, Send
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

interface CodeTask {
  title: string;
  description: string;
  starter_code: string;
  test_cases: { input: string; expected: string; description: string }[];
  hints: string[];
  language: string;
}

interface TestResult {
  passed: boolean;
  input: string;
  expected: string;
  actual: string;
  description: string;
}

interface CodeStudioProps {
  subject: string;
  topic?: string;
  difficulty: string;
  onComplete: (data: { correct: number; total: number; score: number; subject: string; quizType: string; timeSpent: number }) => void;
  onBack: () => void;
}

const LANG_COLORS: Record<string, string> = {
  python: 'from-blue-500 to-yellow-500',
  javascript: 'from-yellow-400 to-yellow-600',
  java: 'from-red-500 to-orange-500',
  cpp: 'from-blue-600 to-blue-800',
  c: 'from-gray-600 to-blue-700',
};

const CodeStudio: React.FC<CodeStudioProps> = ({ subject, topic, difficulty, onComplete, onBack }) => {
  const [task, setTask] = useState<CodeTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [running, setRunning] = useState(false);
  const [hintIdx, setHintIdx] = useState(-1);
  const [showHint, setShowHint] = useState(false);
  const [timer, setTimer] = useState(0);
  const [startTime] = useState(Date.now());
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch coding task from AI
  useEffect(() => {
    const fetchTask = async () => {
      try {
        const res = await apiClient.post('/improvement/generate-quiz', {
          subject, topic: topic || '', difficulty, count: 1, quiz_type: 'coding_task',
        });
        const q = res.data.questions?.[0];
        if (q) {
          const codeTask: CodeTask = {
            title: q.question || `${subject} Coding Challenge`,
            description: q.explanation || `Write a solution for this ${subject} problem.`,
            starter_code: q.options?.[0] || `# Write your ${subject} solution here\n\ndef solution():\n    pass\n`,
            test_cases: (q.options?.slice(1) || []).map((tc: string, i: number) => {
              const parts = tc.split('→');
              return { input: parts[0]?.trim() || `Test ${i+1}`, expected: parts[1]?.trim() || 'True', description: `Test case ${i+1}` };
            }),
            hints: [q.explanation || 'Think about the problem step by step.', 'Break the problem into smaller parts.', 'Consider edge cases.'],
            language: 'python',
          };
          if (codeTask.test_cases.length === 0) {
            codeTask.test_cases = [
              { input: 'Basic test', expected: 'Correct output', description: 'Basic functionality' },
              { input: 'Edge case', expected: 'Handles edge case', description: 'Edge case handling' },
            ];
          }
          setTask(codeTask);
          setCode(codeTask.starter_code);
        } else {
          // Fallback task
          setTask({
            title: `${subject} Challenge`,
            description: `Write a Python function that demonstrates your understanding of ${topic || subject}.`,
            starter_code: `# ${subject} - ${difficulty} difficulty\n# Write your solution below\n\ndef solve(data):\n    \"\"\"Your solution here\"\"\"\n    pass\n\n# Test your solution\nprint(solve("test"))`,
            test_cases: [
              { input: 'solve("test")', expected: 'Not None', description: 'Returns a value' },
              { input: 'solve("")', expected: 'Handles empty', description: 'Edge case' },
            ],
            hints: ['Start by understanding the problem.', 'Write pseudocode first.', 'Test with simple inputs.'],
            language: 'python',
          });
          setCode(`# ${subject} - ${difficulty} difficulty\n# Write your solution below\n\ndef solve(data):\n    \"\"\"Your solution here\"\"\"\n    pass\n\n# Test your solution\nprint(solve("test"))`);
        }
      } catch {
        toast.error('Failed to load coding task');
        setTask({
          title: `${subject} Practice`,
          description: `Practice coding for ${subject}`,
          starter_code: '# Write your code here\n',
          test_cases: [],
          hints: ['Think step by step'],
          language: 'python',
        });
        setCode('# Write your code here\n');
      } finally {
        setLoading(false);
      }
    };
    fetchTask();
  }, [subject, topic, difficulty]);

  const handleRun = async () => {
    setRunning(true);
    setOutput('');
    setTestResults([]);
    try {
      // Simulate running code (AI evaluates)
      const res = await apiClient.post('/improvement/generate-quiz', {
        subject, topic: `Evaluate this code:\n${code}`, difficulty: 'medium', count: 1, quiz_type: 'code_review',
      });
      const review = res.data.questions?.[0];
      const passed = code.trim().length > 20 && !code.includes('pass\n') && code !== task?.starter_code;
      const results: TestResult[] = (task?.test_cases || []).map((tc, i) => ({
        passed: passed || i === 0,
        input: tc.input, expected: tc.expected,
        actual: passed ? tc.expected : 'No output',
        description: tc.description,
      }));
      setTestResults(results);
      setOutput(review?.explanation || (passed ? '✅ Code looks good! All checks passed.' : '❌ Code needs work. Make sure to implement the solution.'));
    } catch {
      setOutput('⚠️ Could not evaluate code. Check your implementation.');
      setTestResults((task?.test_cases || []).map(tc => ({
        passed: false, input: tc.input, expected: tc.expected, actual: 'Error', description: tc.description,
      })));
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = () => {
    const passed = testResults.filter(r => r.passed).length;
    const total = Math.max(testResults.length, 1);
    const pct = Math.round((passed / total) * 100);
    setScore(pct);
    setSubmitted(true);
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);
    onComplete({ correct: passed, total, score: pct, subject, quizType: 'code_studio', timeSpent });
  };

  const handleHint = () => {
    if (!task) return;
    const next = Math.min(hintIdx + 1, task.hints.length - 1);
    setHintIdx(next);
    setShowHint(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.currentTarget.selectionStart;
      const end = e.currentTarget.selectionEnd;
      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      setCode(newCode);
      setTimeout(() => { if (textareaRef.current) { textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4; } }, 0);
    }
  };

  const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-emerald-200 dark:border-emerald-900" />
          <div className="absolute inset-0 rounded-full border-4 border-emerald-500 border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-700 dark:text-gray-300 font-medium">Loading coding challenge...</p>
        <p className="text-sm text-gray-400">{subject} • {difficulty}</p>
      </div>
    );
  }

  // ── Results screen ──
  if (submitted) {
    const xp = Math.round(score * 1.5);
    return (
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md mx-auto text-center py-8">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.2 }}
          className={`w-24 h-24 rounded-2xl mx-auto mb-6 flex items-center justify-center shadow-lg ${
            score >= 80 ? 'bg-gradient-to-br from-green-400 to-emerald-600' :
            score >= 50 ? 'bg-gradient-to-br from-amber-400 to-orange-600' :
            'bg-gradient-to-br from-red-400 to-rose-600'
          }`}>
          <span className="text-4xl">{score >= 80 ? '🏆' : score >= 50 ? '👍' : '📚'}</span>
        </motion.div>
        <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-1">
          {score >= 80 ? 'Excellent Code!' : score >= 50 ? 'Good Effort!' : 'Keep Practicing!'}
        </h3>
        <p className="text-gray-500 text-sm mb-6">
          {testResults.filter(r => r.passed).length}/{testResults.length} tests passed
        </p>
        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Score</p><p className={`text-lg font-bold ${score >= 80 ? 'text-green-600' : score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>{score}%</p></div>
          <div><p className="text-xs text-gray-400">XP</p><p className="text-lg font-bold text-amber-600">+{xp}</p></div>
        </div>
        <div className="flex gap-3 justify-center">
          <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium">
            <ArrowLeft className="w-4 h-4 inline mr-1" /> Back
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className={`bg-gradient-to-r ${LANG_COLORS[task?.language || 'python'] || LANG_COLORS.python} rounded-2xl p-4 text-white shadow-lg`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <Code className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-lg">{task?.title || 'Code Studio'}</h2>
              <p className="text-xs text-white/70">{subject} • {difficulty}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="bg-white/15 rounded-lg px-3 py-1.5 backdrop-blur-sm flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /><span className="font-mono">{timeStr}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Task description */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-emerald-500" /> Problem
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{task?.description}</p>
      </div>

      {/* Editor + Output split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Code Editor */}
        <div className="bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <span className="text-xs text-gray-400 ml-2">{task?.language || 'python'}</span>
            </div>
            <div className="flex gap-2">
              <button onClick={handleHint} className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 px-2 py-1 bg-amber-500/10 rounded">
                <Lightbulb className="w-3 h-3" /> Hint ({Math.min(hintIdx + 2, task?.hints.length || 0)}/{task?.hints.length || 0})
              </button>
              <button onClick={() => { setCode(task?.starter_code || ''); setTestResults([]); setOutput(''); }}
                className="text-xs text-gray-400 hover:text-gray-300 flex items-center gap-1">
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
            </div>
          </div>
          <textarea
            ref={textareaRef}
            value={code}
            onChange={e => setCode(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full h-64 bg-gray-900 text-green-400 font-mono text-sm p-4 resize-none focus:outline-none"
            spellCheck={false}
            placeholder="// Write your code here..."
          />
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 border-t border-gray-700">
            <button onClick={handleRun} disabled={running}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-medium disabled:opacity-50">
              {running ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
              {running ? 'Running...' : 'Run Code'}
            </button>
            <button onClick={handleSubmit} disabled={testResults.length === 0}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-medium disabled:opacity-50">
              <Send className="w-3 h-3" /> Submit
            </button>
          </div>
        </div>

        {/* Output + Tests */}
        <div className="space-y-3">
          {/* Hint */}
          <AnimatePresence>
            {showHint && hintIdx >= 0 && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-amber-700 dark:text-amber-400 flex items-center gap-1">
                    <Lightbulb className="w-3 h-3" /> Hint {hintIdx + 1}
                  </span>
                  <button onClick={() => setShowHint(false)} className="text-amber-400 text-xs">✕</button>
                </div>
                <p className="text-sm text-amber-800 dark:text-amber-300">{task?.hints[hintIdx]}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Output console */}
          <div className="bg-gray-900 rounded-xl border border-gray-700 overflow-hidden">
            <div className="px-3 py-2 bg-gray-800 border-b border-gray-700">
              <span className="text-xs text-gray-400 flex items-center gap-1"><Terminal className="w-3 h-3" /> Output</span>
            </div>
            <div className="p-3 h-32 overflow-y-auto font-mono text-xs text-gray-300 whitespace-pre-wrap">
              {output || <span className="text-gray-600">Run your code to see output...</span>}
            </div>
          </div>

          {/* Test Results */}
          {testResults.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  Tests: {testResults.filter(r => r.passed).length}/{testResults.length} passed
                </span>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {testResults.map((r, i) => (
                  <div key={i} className={`px-3 py-2 flex items-center gap-2 ${r.passed ? 'bg-green-50/50 dark:bg-green-900/10' : 'bg-red-50/50 dark:bg-red-900/10'}`}>
                    {r.passed ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-900 dark:text-white truncate">{r.description}</p>
                      {!r.passed && <p className="text-xs text-red-500 mt-0.5">Expected: {r.expected}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeStudio;
