// academic-advisor-frontend/src/components/dashboard/games/TheoryEngine.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, ArrowLeft, Loader2, MessageCircle, Send,
  CheckCircle, XCircle, Clock, Zap, RefreshCw, Video, ChevronDown
} from 'lucide-react';
import apiClient from '../../../services/api.service';
import toast from 'react-hot-toast';

interface TheoryEngineProps {
  subject: string;
  topic?: string;
  difficulty: string;
  onComplete: (data: { correct: number; total: number; score: number; subject: string; quizType: string; timeSpent: number }) => void;
  onBack: () => void;
}

interface ChatMessage {
  role: 'ai' | 'user';
  content: string;
}

const VIDEO_RESOURCES: Record<string, { title: string; channel: string; url: string }[]> = {
  'Data Structures': [
    { title: 'Arrays & Linked Lists', channel: 'MIT OCW', url: 'https://youtube.com' },
    { title: 'Trees & Graphs', channel: 'Abdul Bari', url: 'https://youtube.com' },
  ],
  'Machine Learning': [
    { title: 'Neural Networks', channel: '3Blue1Brown', url: 'https://youtube.com' },
    { title: 'Gradient Descent', channel: 'StatQuest', url: 'https://youtube.com' },
  ],
};

const TheoryEngine: React.FC<TheoryEngineProps> = ({ subject, topic, difficulty, onComplete, onBack }) => {
  const [phase, setPhase] = useState<'lesson' | 'check' | 'chat' | 'complete'>('lesson');
  const [lesson, setLesson] = useState('');
  const [loading, setLoading] = useState(true);
  const [checkQ, setCheckQ] = useState<{ question: string; options: string[]; correct: number; explanation: string } | null>(null);
  const [checkAnswer, setCheckAnswer] = useState<number | null>(null);
  const [showCheckResult, setShowCheckResult] = useState(false);
  const [attempts, setAttempts] = useState(0);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [timer, setTimer] = useState(0);
  const [startTime] = useState(Date.now());
  const [showVideos, setShowVideos] = useState(false);
  const [reExplainCount, setReExplainCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setTimer(t => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  // Generate lesson
  useEffect(() => {
    const fetchLesson = async () => {
      try {
        const res = await apiClient.post('/improvement/generate-quiz', {
          subject, topic: topic || '', difficulty, count: 1, quiz_type: 'theory_lesson',
        });
        const q = res.data.questions?.[0];
        if (q) {
          setLesson(q.explanation || q.question || `Understanding ${topic || subject}`);
          setCheckQ({ question: q.question, options: q.options || [], correct: q.correct || 0, explanation: q.explanation || '' });
        } else {
          setLesson(`## ${topic || subject}\n\nThis is an adaptive lesson on ${topic || subject}. The AI will generate personalized content based on your level.`);
        }
      } catch {
        setLesson(`Understanding ${topic || subject} — content loading failed.`);
      } finally {
        setLoading(false);
      }
    };
    fetchLesson();
  }, [subject, topic, difficulty]);

  const handleReExplain = async () => {
    if (reExplainCount >= 3) {
      toast('Maximum re-explanations reached. Flagged for faculty help.', { icon: '🏫' });
      return;
    }
    setLoading(true);
    setReExplainCount(c => c + 1);
    try {
      const styles = ['Use a real-world analogy', 'Explain like I am 5 years old', 'Use a step-by-step visual breakdown'];
      const res = await apiClient.post('/improvement/generate-quiz', {
        subject, topic: `${styles[reExplainCount]}: ${topic || subject}`, difficulty: 'easy', count: 1, quiz_type: 'theory_lesson',
      });
      const q = res.data.questions?.[0];
      if (q) setLesson(q.explanation || q.question || lesson);
    } catch { /* keep existing */ }
    setLoading(false);
  };

  const handleCheckAnswer = (idx: number) => {
    if (showCheckResult) return;
    setCheckAnswer(idx);
    setShowCheckResult(true);
    setAttempts(a => a + 1);
  };

  const handleAskAI = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);
    try {
      const res = await apiClient.post('/improvement/generate-quiz', {
        subject, topic: `Student asks about ${topic || subject}: "${userMsg}"`, difficulty, count: 1, quiz_type: 'theory_lesson',
      });
      const q = res.data.questions?.[0];
      setChatMessages(prev => [...prev, { role: 'ai', content: q?.explanation || q?.question || 'Let me explain that differently...' }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I could not process that question right now.' }]);
    }
    setChatLoading(false);
  };

  const handleComplete = () => {
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);
    const correct = checkAnswer === checkQ?.correct ? 1 : 0;
    const score = correct * 100;
    setPhase('complete');
    onComplete({ correct, total: 1, score, subject, quizType: 'theory_engine', timeSpent });
  };

  const timeStr = `${Math.floor(timer / 60)}:${(timer % 60).toString().padStart(2, '0')}`;
  const videos = VIDEO_RESOURCES[subject] || [];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-200 dark:border-indigo-900" />
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin" />
        </div>
        <p className="text-gray-700 dark:text-gray-300 font-medium">Generating adaptive lesson...</p>
        <p className="text-sm text-gray-400">{subject} • {topic || 'General'}</p>
      </div>
    );
  }

  if (phase === 'complete') {
    const xp = 30 + (checkAnswer === checkQ?.correct ? 20 : 0);
    return (
      <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="max-w-md mx-auto text-center py-8">
        <div className="text-5xl mb-4">📖</div>
        <h3 className="text-2xl font-black text-gray-900 dark:text-white mb-1">Lesson Complete!</h3>
        <p className="text-gray-500 text-sm mb-6">{topic || subject} studied in {timeStr}</p>
        <div className="grid grid-cols-3 gap-4 mb-6 bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
          <div><p className="text-xs text-gray-400">Time</p><p className="text-lg font-bold text-gray-900 dark:text-white">{timeStr}</p></div>
          <div><p className="text-xs text-gray-400">Comprehension</p><p className={`text-lg font-bold ${checkAnswer === checkQ?.correct ? 'text-green-600' : 'text-amber-600'}`}>{checkAnswer === checkQ?.correct ? '✅' : '🔄'}</p></div>
          <div><p className="text-xs text-gray-400">XP</p><p className="text-lg font-bold text-amber-600">+{xp}</p></div>
        </div>
        <button onClick={onBack} className="px-5 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium">
          <ArrowLeft className="w-4 h-4 inline mr-1" /> Back to Hub
        </button>
      </motion.div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 via-blue-500 to-cyan-500 rounded-2xl p-4 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-lg">Theory Engine</h2>
              <p className="text-xs text-white/70">{topic || subject} • {difficulty}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="bg-white/15 rounded-lg px-3 py-1.5 backdrop-blur-sm flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /><span className="font-mono">{timeStr}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Phase tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
        {[
          { id: 'lesson', label: '📖 Lesson' },
          { id: 'check', label: '✅ Check' },
          { id: 'chat', label: '💬 Ask AI' },
        ].map(t => (
          <button key={t.id} onClick={() => setPhase(t.id as any)}
            className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              phase === t.id ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500'
            }`}>{t.label}</button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* Lesson Phase */}
        {phase === 'lesson' && (
          <motion.div key="lesson" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-sm">
              <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed whitespace-pre-wrap">
                {lesson}
              </div>
            </div>

            {/* Re-explain button */}
            <div className="flex items-center gap-3">
              <button onClick={handleReExplain} disabled={reExplainCount >= 3}
                className="flex items-center gap-2 px-4 py-2 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 rounded-xl text-sm font-medium hover:bg-amber-100 disabled:opacity-50">
                <RefreshCw className="w-4 h-4" /> Explain differently ({3 - reExplainCount} left)
              </button>
              <button onClick={() => setPhase('check')}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700">
                <CheckCircle className="w-4 h-4" /> Check understanding
              </button>
            </div>

            {/* Video resources */}
            {videos.length > 0 && (
              <div>
                <button onClick={() => setShowVideos(!showVideos)} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
                  <Video className="w-4 h-4" /> Video Resources <ChevronDown className={`w-3 h-3 transition-transform ${showVideos ? 'rotate-180' : ''}`} />
                </button>
                {showVideos && (
                  <div className="mt-2 space-y-2">
                    {videos.map((v, i) => (
                      <a key={i} href={v.url} target="_blank" rel="noreferrer"
                        className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-lg hover:bg-red-100 transition-colors">
                        <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center"><Video className="w-4 h-4 text-white" /></div>
                        <div><p className="text-sm font-medium text-gray-900 dark:text-white">{v.title}</p><p className="text-xs text-gray-500">{v.channel}</p></div>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}

        {/* Comprehension Check */}
        {phase === 'check' && checkQ && (
          <motion.div key="check" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-5">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">{checkQ.question}</h3>
              <div className="space-y-2">
                {checkQ.options.map((opt, i) => {
                  let cls = 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 hover:border-indigo-400';
                  if (showCheckResult && i === checkQ.correct) cls = 'border-green-500 bg-green-50 dark:bg-green-900/20 ring-2 ring-green-500/20';
                  else if (showCheckResult && i === checkAnswer && checkAnswer !== checkQ.correct) cls = 'border-red-500 bg-red-50 dark:bg-red-900/20';
                  else if (showCheckResult) cls = 'opacity-50';
                  return (
                    <button key={i} onClick={() => handleCheckAnswer(i)} disabled={showCheckResult}
                      className={`w-full text-left p-3 rounded-xl border-2 transition-all flex items-center gap-3 ${cls}`}>
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                        showCheckResult && i === checkQ.correct ? 'bg-green-500 text-white' :
                        showCheckResult && i === checkAnswer ? 'bg-red-500 text-white' :
                        'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                      }`}>{String.fromCharCode(65 + i)}</div>
                      <span className="text-sm text-gray-800 dark:text-gray-200">{opt}</span>
                    </button>
                  );
                })}
              </div>
            </div>
            {showCheckResult && (
              <div className={`p-4 border-t ${checkAnswer === checkQ.correct ? 'bg-green-50/50 dark:bg-green-900/10' : 'bg-amber-50/50 dark:bg-amber-900/10'}`}>
                <p className="text-sm text-gray-600 dark:text-gray-400">{checkQ.explanation}</p>
                <div className="flex gap-2 mt-3">
                  {checkAnswer !== checkQ.correct && (
                    <button onClick={() => { setPhase('lesson'); handleReExplain(); }}
                      className="px-3 py-1.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 rounded-lg text-xs font-medium">
                      🔄 Re-learn
                    </button>
                  )}
                  <button onClick={handleComplete}
                    className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium">
                    ✅ Complete lesson
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Ask AI Chat */}
        {phase === 'chat' && (
          <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <MessageCircle className="w-4 h-4 text-indigo-500" /> Ask about {topic || subject}
              </h3>
            </div>
            <div className="h-64 overflow-y-auto p-4 space-y-3">
              {chatMessages.length === 0 && (
                <p className="text-center text-gray-400 text-sm py-8">Ask any question about {topic || subject}!</p>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] px-3 py-2 rounded-xl text-sm ${
                    msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded-xl">
                    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                  </div>
                </div>
              )}
            </div>
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
              <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAskAI()}
                placeholder="Type your question..."
                className="flex-1 px-3 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:border-indigo-500" />
              <button onClick={handleAskAI} disabled={chatLoading || !chatInput.trim()}
                className="px-3 py-2 bg-indigo-600 text-white rounded-lg disabled:opacity-50">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TheoryEngine;
