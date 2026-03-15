// src/components/dashboard/AcademicChatbot.tsx
// GAMIFIED VERSION - XP, Streaks, Achievements, Animations
// FIXED: No hooks inside renderStructured, all renderers restored
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Bot, User, Loader2, RefreshCw, X,
  Minimize2, Maximize2, Wifi, WifiOff, AlertCircle,
  BookOpen, GraduationCap, Users, Briefcase, Sparkles,
  Calendar, ThumbsUp, ThumbsDown, ChevronRight, ChevronDown, ChevronLeft,
  TrendingUp, TrendingDown,
  MapPin, DollarSign,
  MessageSquare, Mail, ArrowRight, Zap, ExternalLink,
  Star, Award, Target, Brain, CheckCircle2,
  XCircle, BarChart3, Play, FileText, Video,
  Lightbulb, Rocket, Heart, Shield,
  Code, Hash, Search, ArrowUpRight,
  Flame, Trophy, Crown, Gift, Lock, Medal,
  Gem, Moon, Sun,
} from 'lucide-react';
import { useChatbot } from '../../hooks/useChatbot';
import type {
  ChatMessage,
  ChatResponseContent,
  AdvisorSuggestion,
} from '../../types/chatbot.types';
import { motion, AnimatePresence } from 'framer-motion';

/* ═══════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════ */
interface Props {
  isFloating?: boolean;
  defaultOpen?: boolean;
  className?: string;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string | React.ReactNode;  // Can be string ID or ReactNode
  xp: number;
  unlocked: boolean;
  unlockedAt?: Date;
  progress?: number;
  maxProgress?: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

interface GamificationState {
  xp: number;
  level: number;
  streak: number;
  lastActiveDate: string;
  totalQuestions: number;
  quizzesCompleted: number;
  perfectQuizzes: number;
  topicsExplored: string[];
  achievements: Achievement[];
  dailyXpEarned: number;
  weeklyXpEarned: number;
}

/* ═══════════════════════════════════════════════════════
   GAMIFICATION CONSTANTS
   ═══════════════════════════════════════════════════════ */
const XP_VALUES = {
  ASK_QUESTION: 5, EXPLORE_TOPIC: 10, COMPLETE_QUIZ: 25,
  PERFECT_QUIZ: 50, DAILY_STREAK: 15, FIRST_QUESTION: 20,
  GIVE_FEEDBACK: 5, EXPLORE_CAREER: 15, VIEW_RESOURCES: 8,
};

const LEVEL_THRESHOLDS = [0,50,120,220,350,520,730,1000,1350,1800,2400,3200,4200,5500,7000];

const LEVEL_TITLES = [
  'Freshman','Curious Mind','Knowledge Seeker','Quick Learner','Scholar',
  'Academic Star','Brainiac','Prodigy','Mastermind','Genius',
  'Sage','Oracle','Enlightened','Transcendent','Legend'
];


const RARITY_COLORS = {
  common: { bg: 'from-gray-400 to-gray-500', text: 'text-gray-600', border: 'border-gray-300' },
  rare: { bg: 'from-blue-400 to-blue-600', text: 'text-blue-600', border: 'border-blue-400' },
  epic: { bg: 'from-purple-400 to-purple-600', text: 'text-purple-600', border: 'border-purple-400' },
  legendary: { bg: 'from-amber-400 to-orange-500', text: 'text-amber-600', border: 'border-amber-400' },
};

/* Icon lookup - maps string IDs to actual React components */
const ACHIEVEMENT_ICONS: Record<string, React.ReactNode> = {
  first_question: <MessageSquare className="w-4 h-4" />,
  streak_3: <Flame className="w-4 h-4" />,
  streak_7: <Flame className="w-4 h-4" />,
  streak_30: <Crown className="w-4 h-4" />,
  quiz_1: <Brain className="w-4 h-4" />,
  quiz_perfect: <Trophy className="w-4 h-4" />,
  quiz_10: <Medal className="w-4 h-4" />,
  topics_5: <Target className="w-4 h-4" />,
  topics_20: <Gem className="w-4 h-4" />,
  career_explorer: <Briefcase className="w-4 h-4" />,
  level_5: <Star className="w-4 h-4" />,
  level_10: <Award className="w-4 h-4" />,
  night_owl: <Moon className="w-4 h-4" />,
  early_bird: <Sun className="w-4 h-4" />,
  helper: <Heart className="w-4 h-4" />,
};

const getAchievementIcon = (id: string): React.ReactNode => {
  return ACHIEVEMENT_ICONS[id] || <Star className="w-4 h-4" />;
};

const DEFAULT_ACHIEVEMENTS: Achievement[] = [
  { id: 'first_question', title: 'Curious Cat', description: 'Ask your first question', icon: 'first_question' as any, xp: 20, unlocked: false, rarity: 'common' },
  { id: 'streak_3', title: 'Consistent Learner', description: '3-day learning streak', icon: 'streak_3' as any, xp: 30, unlocked: false, rarity: 'common' },
  { id: 'streak_7', title: 'Week Warrior', description: '7-day learning streak', icon: 'streak_7' as any, xp: 75, unlocked: false, rarity: 'rare' },
  { id: 'streak_30', title: 'Monthly Master', description: '30-day learning streak', icon: 'streak_30' as any, xp: 300, unlocked: false, rarity: 'legendary' },
  { id: 'quiz_1', title: 'Quiz Taker', description: 'Complete your first quiz', icon: 'quiz_1' as any, xp: 25, unlocked: false, rarity: 'common' },
  { id: 'quiz_perfect', title: 'Perfect Score', description: 'Get 100% on a quiz', icon: 'quiz_perfect' as any, xp: 50, unlocked: false, rarity: 'rare' },
  { id: 'quiz_10', title: 'Quiz Champion', description: 'Complete 10 quizzes', icon: 'quiz_10' as any, xp: 100, unlocked: false, progress: 0, maxProgress: 10, rarity: 'epic' },
  { id: 'topics_5', title: 'Explorer', description: 'Explore 5 different topics', icon: 'topics_5' as any, xp: 40, unlocked: false, progress: 0, maxProgress: 5, rarity: 'common' },
  { id: 'topics_20', title: 'Knowledge Hunter', description: 'Explore 20 different topics', icon: 'topics_20' as any, xp: 150, unlocked: false, progress: 0, maxProgress: 20, rarity: 'epic' },
  { id: 'career_explorer', title: 'Future Planner', description: 'Explore 3 career paths', icon: 'career_explorer' as any, xp: 35, unlocked: false, progress: 0, maxProgress: 3, rarity: 'rare' },
  { id: 'level_5', title: 'Rising Star', description: 'Reach Level 5', icon: 'level_5' as any, xp: 100, unlocked: false, rarity: 'rare' },
  { id: 'level_10', title: 'Academic Excellence', description: 'Reach Level 10', icon: 'level_10' as any, xp: 250, unlocked: false, rarity: 'legendary' },
  { id: 'night_owl', title: 'Night Owl', description: 'Study after 10 PM', icon: 'night_owl' as any, xp: 15, unlocked: false, rarity: 'common' },
  { id: 'early_bird', title: 'Early Bird', description: 'Study before 7 AM', icon: 'early_bird' as any, xp: 15, unlocked: false, rarity: 'common' },
  { id: 'helper', title: 'Feedback Friend', description: 'Give feedback 5 times', icon: 'helper' as any, xp: 25, unlocked: false, progress: 0, maxProgress: 5, rarity: 'common' },
];

/* ═══════════════════════════════════════════════════════
   LOCAL STORAGE HELPERS
   ═══════════════════════════════════════════════════════ */
const STORAGE_KEY = 'academic_advisor_gamification';

const loadGamificationState = (): GamificationState => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const state = JSON.parse(saved);
      
      // Fix: Ensure achievements have correct structure (icons may be corrupted from old saves)
      if (state.achievements) {
        state.achievements = state.achievements.map((a: any) => {
          const defaultAch = DEFAULT_ACHIEVEMENTS.find(d => d.id === a.id);
          return {
            ...defaultAch,  // Get defaults (including proper icon string)
            ...a,            // Override with saved progress/unlocked state
            icon: a.id,      // Always use ID string, never serialized JSX
          };
        });
        // Add any new achievements that weren't in the save
        DEFAULT_ACHIEVEMENTS.forEach(d => {
          if (!state.achievements.find((a: any) => a.id === d.id)) {
            state.achievements.push(d);
          }
        });
      }
      
      const today = new Date().toDateString();
      if (state.lastActiveDate !== today) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        if (state.lastActiveDate !== yesterday.toDateString()) state.streak = 0;
        state.dailyXpEarned = 0;
      }
      return state;
    }
  } catch (e) { console.error('Failed to load gamification state:', e); }
  return { xp:0, level:1, streak:0, lastActiveDate:'', totalQuestions:0,
    quizzesCompleted:0, perfectQuizzes:0, topicsExplored:[], achievements:DEFAULT_ACHIEVEMENTS,
    dailyXpEarned:0, weeklyXpEarned:0 };
};

const saveGamificationState = (state: GamificationState) => {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) { /* */ }
};

const calculateLevel = (xp: number): number => {
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) if (xp >= LEVEL_THRESHOLDS[i]) return i + 1;
  return 1;
};
const getXpForNextLevel = (level: number): number =>
  level >= LEVEL_THRESHOLDS.length ? LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1] : LEVEL_THRESHOLDS[level];
const getXpForCurrentLevel = (level: number): number =>
  level <= 1 ? 0 : LEVEL_THRESHOLDS[level - 1];

/* ═══════════════════════════════════════════════════════
   MARKDOWN → HTML
   ═══════════════════════════════════════════════════════ */
const formatMarkdown = (text: string): string => {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*\*(.*?)\*\*\*/g,'<strong class="font-bold text-gray-900 dark:text-white"><em>$1</em></strong>')
    .replace(/\*\*(.*?)\*\*/g,'<strong class="font-bold text-gray-900 dark:text-white">$1</strong>')
    .replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g,'<em class="italic">$1</em>')
    .replace(/`([^`]+)`/g,'<code class="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-300 px-1.5 py-0.5 rounded text-[10px] font-mono border border-indigo-100 dark:border-indigo-800/50">$1</code>')
    .replace(/^[\-•\*]\s+(.+)/gm,'<div class="flex items-start gap-2 my-1"><span class="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 mt-1.5 shrink-0"></span><span class="flex-1">$1</span></div>')
    .replace(/^(\d+)[.)]\s+(.+)/gm,'<div class="flex items-start gap-2 my-1"><span class="w-5 h-5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5">$1</span><span class="flex-1">$2</span></div>')
    .replace(/^###\s+(.+)/gm,'<p class="font-bold text-xs text-gray-800 dark:text-gray-200 mt-3 mb-1">$1</p>')
    .replace(/^##\s+(.+)/gm,'<p class="font-bold text-sm text-gray-800 dark:text-gray-200 mt-3 mb-1.5">$1</p>')
    .replace(/^(📚|📊|💡|🎯|📈|📉|✅|⚠️|💪|💼|🔗|📝|✓|→|🏆|🎓|🔬|🛠️|🌟|📖|🧠|🔥|💻|🚀|⭐|📌|➡️)\s+(.+)/gm,'<div class="flex items-start gap-2 my-1"><span class="text-sm shrink-0">$1</span><span class="flex-1">$2</span></div>')
    .replace(/\n\n/g,'<div class="h-2.5"></div>')
    .replace(/\n/g,'<br/>');
};

const Markdown: React.FC<{text:string;className?:string}> = ({text,className=''}) => (
  <div className={`leading-relaxed ${className}`} dangerouslySetInnerHTML={{__html:formatMarkdown(text)}} />
);

/* ═══════════════════════════════════════════════════════
   MICRO COMPONENTS
   ═══════════════════════════════════════════════════════ */
const Pill: React.FC<{children:React.ReactNode;color?:string;glow?:boolean}> = ({children,color='gray',glow=false}) => {
  const map: Record<string,string> = {
    green:'bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 border-emerald-500/20',
    amber:'bg-amber-500/10 text-amber-500 dark:text-amber-400 border-amber-500/20',
    red:'bg-rose-500/10 text-rose-500 dark:text-rose-400 border-rose-500/20',
    blue:'bg-blue-500/10 text-blue-500 dark:text-blue-400 border-blue-500/20',
    violet:'bg-violet-500/10 text-violet-500 dark:text-violet-400 border-violet-500/20',
    cyan:'bg-cyan-500/10 text-cyan-500 dark:text-cyan-400 border-cyan-500/20',
    pink:'bg-pink-500/10 text-pink-500 dark:text-pink-400 border-pink-500/20',
    gray:'bg-gray-500/10 text-gray-500 dark:text-gray-400 border-gray-500/20',
    indigo:'bg-indigo-500/10 text-indigo-500 dark:text-indigo-400 border-indigo-500/20',
  };
  return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${map[color]||map.gray} ${glow?'shadow-sm shadow-current/10':''}`}>{children}</span>;
};

const ConfBadge: React.FC<{c:string}> = ({c}) => {
  const m: Record<string,{color:string;icon:React.ReactNode}> = {
    High:{color:'green',icon:<CheckCircle2 className="w-2.5 h-2.5"/>},
    Medium:{color:'amber',icon:<span>~</span>},
    Low:{color:'red',icon:<AlertCircle className="w-2.5 h-2.5"/>},
  };
  const {color,icon} = m[c]||m.Medium;
  return <Pill color={color}><span className="flex items-center gap-0.5">{icon} {c}</span></Pill>;
};

const MiniSparkline: React.FC<{data:number[];color?:string;height?:number}> = ({data,color='#818cf8',height=28}) => {
  if (data.length<2) return null;
  const min=Math.min(...data), max=Math.max(...data), range=max-min||1, w=90;
  const pts = data.map((v,i)=>`${(i/(data.length-1))*w},${height-((v-min)/range)*(height-6)-3}`).join(' ');
  const lp = pts.split(' ').pop()!.split(',');
  return (
    <svg width={w} height={height} className="inline-block">
      <defs><linearGradient id="sparkGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor={color} stopOpacity="0.3"/><stop offset="100%" stopColor={color} stopOpacity="1"/></linearGradient></defs>
      <polyline fill="none" stroke="url(#sparkGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points={pts}/>
      <circle cx={parseFloat(lp[0])} cy={parseFloat(lp[1])} r="3.5" fill={color} stroke="white" strokeWidth="1.5"/>
    </svg>
  );
};

const ProgressRing: React.FC<{value:number;max?:number;size?:number;color?:string;label?:string}> = ({value,max=10,size=56,color='#818cf8',label}) => {
  const pct=Math.min(value/max,1), r=(size-8)/2, circ=2*Math.PI*r, offset=circ*(1-pct);
  return (
    <div className="relative inline-flex items-center justify-center" style={{width:size,height:size}}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="currentColor" className="text-gray-200 dark:text-gray-700" strokeWidth="4"/>
        <motion.circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={circ} initial={{strokeDashoffset:circ}} animate={{strokeDashoffset:offset}} transition={{duration:1.2,ease:'easeOut'}}/>
      </svg>
      <div className="absolute text-center"><p className="text-xs font-bold" style={{color}}>{label||value}</p></div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════
   XP POPUP / ACHIEVEMENT POPUP / LEVEL UP / CONFETTI
   ═══════════════════════════════════════════════════════ */
const XPPopup: React.FC<{xp:number;onComplete:()=>void}> = ({xp,onComplete}) => {
  useEffect(()=>{const t=setTimeout(onComplete,1500);return()=>clearTimeout(t);},[onComplete]);
  return (
    <motion.div initial={{opacity:0,y:20,scale:0.8}} animate={{opacity:1,y:-30,scale:1}} exit={{opacity:0,y:-60,scale:0.5}} className="absolute top-0 left-1/2 -translate-x-1/2 z-50 pointer-events-none">
      <div className="flex items-center gap-1 bg-gradient-to-r from-amber-400 to-orange-500 text-white px-3 py-1.5 rounded-full shadow-lg shadow-amber-500/30 font-bold text-sm"><Zap className="w-4 h-4"/>+{xp} XP</div>
    </motion.div>
  );
};

const AchievementPopup: React.FC<{achievement:Achievement;onClose:()=>void}> = ({achievement,onClose}) => {
  useEffect(()=>{const t=setTimeout(onClose,4000);return()=>clearTimeout(t);},[onClose]);
  const rs = RARITY_COLORS[achievement.rarity];
  const icon = getAchievementIcon(achievement.id);  // ← ADD THIS
  return (
    <motion.div initial={{opacity:0,y:50,scale:0.8}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,y:-20,scale:0.9}} className="fixed bottom-24 right-6 z-[100] max-w-xs">
      <div className={`relative overflow-hidden rounded-2xl bg-white dark:bg-gray-800 shadow-2xl border-2 ${rs.border}`}>
        <div className={`absolute inset-0 bg-gradient-to-br ${rs.bg} opacity-10`}/>
        <motion.div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent" animate={{x:['-100%','200%']}} transition={{duration:1.5,repeat:2}}/>
        <div className="relative p-4">
          <div className="flex items-center gap-3">
            <motion.div animate={{rotate:[0,10,-10,0],scale:[1,1.1,1]}} transition={{duration:0.5,repeat:2}} className={`w-12 h-12 rounded-xl bg-gradient-to-br ${rs.bg} flex items-center justify-center shadow-lg text-white`}>
              {icon}  {/* ← CHANGED from achievement.icon */}
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};


const Confetti: React.FC = () => {
  const colors = ['#818cf8','#f472b6','#34d399','#fbbf24','#60a5fa','#c084fc','#fb7185'];
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
      {Array.from({length:50}).map((_,i)=>(
        <motion.div key={i} className="absolute" style={{width:Math.random()*8+4,height:Math.random()*8+4,background:colors[i%colors.length],borderRadius:Math.random()>0.5?'50%':'2px',left:`${Math.random()*100}%`,top:'-20px'}}
          initial={{y:-20,opacity:1,rotate:0}} animate={{y:400,x:(Math.random()-0.5)*300,opacity:0,rotate:Math.random()*720}} transition={{duration:2+Math.random(),ease:'easeOut',delay:Math.random()*0.5}}/>
      ))}
    </div>
  );
};

const LevelUpCelebration: React.FC<{level:number;onClose:()=>void}> = ({level,onClose}) => {
  useEffect(()=>{const t=setTimeout(onClose,3500);return()=>clearTimeout(t);},[onClose]);
  return (
    <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <motion.div initial={{scale:0,rotate:-180}} animate={{scale:1,rotate:0}} exit={{scale:0,rotate:180}} transition={{type:'spring',damping:15}} className="relative" onClick={e=>e.stopPropagation()}>
        <Confetti/>
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-3xl p-8 shadow-2xl text-center text-white">
          <motion.div animate={{y:[0,-10,0],scale:[1,1.1,1]}} transition={{duration:1,repeat:Infinity}} className="text-6xl mb-4">🎉</motion.div>
          <h2 className="text-2xl font-bold mb-2">Level Up!</h2>
          <span className="text-4xl font-black">{level}</span>
          <p className="text-white/80 text-sm mt-2">{LEVEL_TITLES[level-1]||'Legend'}</p>
          <div className="mt-4 flex justify-center"><Crown className="w-12 h-12 text-amber-300"/></div>
        </div>
      </motion.div>
    </motion.div>
  );
};

/* ═══════════════════════════════════════════════════════
   GAMIFICATION BAR / ACHIEVEMENTS PANEL
   ═══════════════════════════════════════════════════════ */
const GamificationBar: React.FC<{state:GamificationState;onShowAchievements:()=>void}> = ({state,onShowAchievements}) => {
  const curXp=getXpForCurrentLevel(state.level), nxtXp=getXpForNextLevel(state.level);
  const prog=state.xp-curXp, need=nxtXp-curXp, pct=Math.min((prog/need)*100,100);
  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-gradient-to-r from-indigo-500/5 to-purple-500/5 border-b border-indigo-100/50 dark:border-indigo-900/30">
      <div className="relative">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-indigo-500/30">{state.level}</div>
        {state.streak>=3 && <motion.div animate={{scale:[1,1.2,1]}} transition={{duration:1,repeat:Infinity}} className="absolute -top-1 -right-1 w-5 h-5 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center text-white shadow-md"><Flame className="w-3 h-3"/></motion.div>}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between text-[9px] mb-0.5">
          <span className="font-bold text-gray-700 dark:text-gray-300">{LEVEL_TITLES[state.level-1]||'Legend'}</span>
          <span className="text-gray-400">{prog}/{need} XP</span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <motion.div className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full" initial={{width:0}} animate={{width:`${pct}%`}} transition={{duration:0.5}}/>
        </div>
      </div>
      <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-orange-500/10 border border-orange-200/50 dark:border-orange-800/30">
        <Flame className={`w-3.5 h-3.5 ${state.streak>0?'text-orange-500':'text-gray-400'}`}/>
        <span className={`text-xs font-bold ${state.streak>0?'text-orange-600':'text-gray-400'}`}>{state.streak}</span>
      </div>
      <button onClick={onShowAchievements} className="relative p-2 rounded-lg bg-amber-500/10 border border-amber-200/50 dark:border-amber-800/30 hover:bg-amber-500/20 transition-colors">
        <Trophy className="w-4 h-4 text-amber-500"/>
        {state.achievements.filter(a=>a.unlocked).length>0 && <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">{state.achievements.filter(a=>a.unlocked).length}</span>}
      </button>
    </div>
  );
};

const AchievementCard: React.FC<{achievement:Achievement}> = ({achievement}) => {
  const rs=RARITY_COLORS[achievement.rarity];
  const hasProg=achievement.maxProgress&&achievement.maxProgress>0;
  const pPct=hasProg?((achievement.progress||0)/achievement.maxProgress!)*100:0;
  const icon = getAchievementIcon(achievement.id);  // ← ADD THIS
  return (
    <div className={`relative rounded-xl p-3 border transition-all ${achievement.unlocked?`bg-white/80 dark:bg-gray-800/80 ${rs.border}`:'bg-gray-50/50 dark:bg-gray-800/50 border-gray-200/50 dark:border-gray-700/50 opacity-60'}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${achievement.unlocked?`bg-gradient-to-br ${rs.bg} text-white shadow-md`:'bg-gray-200 dark:bg-gray-700 text-gray-400'}`}>
          {achievement.unlocked ? icon : <Lock className="w-4 h-4"/>}  {/* ← CHANGED */}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={`text-xs font-bold ${achievement.unlocked?'text-gray-800 dark:text-white':'text-gray-500'}`}>{achievement.title}</p>
            <span className={`text-[8px] font-bold uppercase ${rs.text}`}>{achievement.rarity}</span>
          </div>
          <p className="text-[10px] text-gray-500">{achievement.description}</p>
          {hasProg&&!achievement.unlocked&&(
            <div className="mt-1.5">
              <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><div className={`h-full bg-gradient-to-r ${rs.bg} rounded-full transition-all`} style={{width:`${pPct}%`}}/></div>
              <p className="text-[8px] text-gray-400 mt-0.5">{achievement.progress}/{achievement.maxProgress}</p>
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 text-amber-500 font-bold text-xs shrink-0"><Zap className="w-3 h-3"/>{achievement.xp}</div>
      </div>
    </div>
  );
};

const AchievementsPanel: React.FC<{achievements:Achievement[];onClose:()=>void}> = ({achievements,onClose}) => {
  const unlocked=achievements.filter(a=>a.unlocked), locked=achievements.filter(a=>!a.unlocked);
  return (
    <motion.div initial={{opacity:0,x:300}} animate={{opacity:1,x:0}} exit={{opacity:0,x:300}} className="absolute inset-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl overflow-y-auto">
      <div className="sticky top-0 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm border-b border-gray-200/50 dark:border-gray-700/50 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2"><Trophy className="w-5 h-5 text-amber-500"/><h3 className="font-bold text-gray-800 dark:text-white">Achievements</h3><span className="text-xs text-gray-400">{unlocked.length}/{achievements.length}</span></div>
        <button onClick={onClose} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"><X className="w-4 h-4 text-gray-500"/></button>
      </div>
      <div className="p-4 space-y-4">
        {unlocked.length>0&&<div><p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider mb-2 flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> Unlocked ({unlocked.length})</p><div className="space-y-2">{unlocked.map(a=><AchievementCard key={a.id} achievement={a}/>)}</div></div>}
        <div><p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1"><Lock className="w-3 h-3"/> Locked ({locked.length})</p><div className="space-y-2">{locked.map(a=><AchievementCard key={a.id} achievement={a}/>)}</div></div>
      </div>
    </motion.div>
  );
};

/* ═══════════════════════════════════════════════════════
   TYPING / SUGGESTION / QUICK ACTION / ADVISOR
   ═══════════════════════════════════════════════════════ */
const TypingWave: React.FC = () => (
  <div className="flex items-center gap-3 py-2.5 px-1">
    <div className="flex items-end gap-[3px] h-5">{[0,1,2,3,4].map(i=><motion.div key={i} className="w-[3px] rounded-full bg-gradient-to-t from-indigo-500 to-purple-400" animate={{height:['4px','18px','6px','14px','4px']}} transition={{duration:1.2,repeat:Infinity,delay:i*0.12,ease:'easeInOut'}}/>)}</div>
    <span className="text-[11px] text-gray-400 italic animate-pulse">thinking...</span>
  </div>
);

const SuggestionChip: React.FC<{text:string;icon?:React.ReactNode;onClick:()=>void}> = ({text,icon,onClick}) => (
  <motion.button whileHover={{scale:1.04,y:-1}} whileTap={{scale:0.96}} onClick={onClick}
    className="text-[11px] bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-full border border-gray-200/60 dark:border-gray-700/60 hover:border-indigo-400/60 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 dark:hover:from-indigo-900/20 dark:hover:to-purple-900/20 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all shadow-sm hover:shadow-md whitespace-nowrap flex items-center gap-1.5 cursor-pointer">
    {icon}{text}<ArrowUpRight className="w-2.5 h-2.5 opacity-60"/>
  </motion.button>
);

const QuickAction: React.FC<{icon:React.ReactNode;label:string;sub:string;gradient:string;xpReward:number;onClick:()=>void;delay?:number}> = ({icon,label,sub,gradient,xpReward,onClick,delay=0}) => (
  <motion.button initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} transition={{delay:0.1+delay*0.08,duration:0.4}} whileHover={{scale:1.03,y:-2}} whileTap={{scale:0.97}} onClick={onClick}
    className="relative flex items-start gap-3 p-3.5 rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-white/50 dark:border-gray-700/50 hover:border-indigo-200/80 shadow-sm hover:shadow-xl transition-all text-left group overflow-hidden">
    <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} shrink-0 shadow-lg group-hover:scale-110 transition-all duration-300`}>{icon}</div>
    <div className="min-w-0 flex-1">
      <p className="text-xs font-bold text-gray-800 dark:text-gray-200 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors">{label}</p>
      <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">{sub}</p>
    </div>
    <div className="flex flex-col items-end gap-1 shrink-0">
      <ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-indigo-500 transition-all group-hover:translate-x-1"/>
      <span className="text-[8px] text-amber-500 font-bold flex items-center gap-0.5"><Zap className="w-2 h-2"/>+{xpReward}</span>
    </div>
  </motion.button>
);

const AdvisorCard: React.FC<{suggestion:AdvisorSuggestion}> = ({suggestion}) => (
  <motion.div initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} className="mt-3 p-3.5 rounded-2xl bg-gradient-to-r from-amber-500/5 to-orange-500/5 border border-amber-300/30 dark:border-amber-700/30">
    <div className="flex items-start gap-2.5">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shrink-0 shadow-md"><Lightbulb className="w-4 h-4 text-white"/></div>
      <div className="flex-1">
        <p className="text-[11px] text-amber-800 dark:text-amber-200 leading-relaxed">{suggestion.message}</p>
        <button onClick={()=>window.open('/faculty-portal','_blank')} className="mt-2.5 text-[10px] font-bold bg-gradient-to-r from-amber-500 to-orange-500 text-white px-4 py-1.5 rounded-full shadow-md flex items-center gap-1">{suggestion.action} <ArrowRight className="w-3 h-3"/></button>
      </div>
    </div>
  </motion.div>
);

/* ═══════════════════════════════════════════════════════
   QUIZ CARD (with XP)
   ═══════════════════════════════════════════════════════ */
const QuizCard: React.FC<{topic:string;subject?:string;questions:Array<{q:string;options:string[];correct:number;explanation:string}>;onSend:(msg:string)=>void;onQuizComplete:(score:number,total:number)=>void}> = ({topic,subject,questions,onSend,onQuizComplete}) => {
  const [cur,setCur]=useState(0);const [sel,setSel]=useState<number|null>(null);const [score,setScore]=useState(0);
  const [answered,setAnswered]=useState<boolean[]>(new Array(questions.length).fill(false));
  const [showExp,setShowExp]=useState(false);const [done,setDone]=useState(false);const [showConf,setShowConf]=useState(false);
  const q=questions[cur]; if(!q) return null;
  const handleAnswer=(idx:number)=>{if(answered[cur])return;setSel(idx);setShowExp(true);const na=[...answered];na[cur]=true;setAnswered(na);if(idx===q.correct)setScore(s=>s+1);};
  const next=()=>{if(cur+1<questions.length){setCur(c=>c+1);setSel(null);setShowExp(false);}else{const fs=score+(sel===q.correct?1:0);setDone(true);if(Math.round((fs/questions.length)*100)>=70)setShowConf(true);onQuizComplete(fs,questions.length);}};
  if(done){
    const fs=score,pct=Math.round((fs/questions.length)*100);
    const grade=pct>=90?{emoji:'🏆',text:'Outstanding!'}:pct>=70?{emoji:'🎉',text:'Great job!'}:pct>=50?{emoji:'👍',text:'Good effort!'}:{emoji:'💪',text:'Keep practicing!'};
    return (
      <motion.div initial={{scale:0.9,opacity:0}} animate={{scale:1,opacity:1}} className="relative rounded-2xl p-6 bg-gradient-to-br from-gray-50 to-white dark:from-gray-800/80 dark:to-gray-900/80 border border-gray-200/50 dark:border-gray-700/50 shadow-lg overflow-hidden">
        {showConf&&<Confetti/>}
        <div className="text-center relative z-10 space-y-3">
          <motion.p className="text-5xl" animate={{scale:[1,1.3,1],rotate:[0,10,-10,0]}} transition={{duration:0.6}}>{grade.emoji}</motion.p>
          <p className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">{grade.text}</p>
          <p className="text-[10px] text-gray-400">{topic}</p>
          <div className="flex justify-center items-center gap-2"><span className="text-3xl font-black text-indigo-600">{pct}%</span><span className="text-gray-400">({fs}/{questions.length})</span></div>
          {pct===100&&<div className="flex items-center justify-center gap-1 text-amber-500 font-bold"><Trophy className="w-5 h-5"/>Perfect Score! +50 XP</div>}
          <div className="flex gap-2 justify-center pt-2">
            <button onClick={()=>{setCur(0);setSel(null);setScore(0);setAnswered(new Array(questions.length).fill(false));setShowExp(false);setDone(false);setShowConf(false);}} className="text-[11px] px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-1"><RefreshCw className="w-3 h-3"/> Retry</button>
            <button onClick={()=>onSend(`Explain ${topic}`)} className="text-[11px] px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md flex items-center gap-1"><BookOpen className="w-3 h-3"/> Learn More</button>
          </div>
        </div>
      </motion.div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2"><div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg"><Brain className="w-4 h-4 text-white"/></div><div><p className="text-xs font-bold text-gray-800 dark:text-gray-200">Quiz: {topic}</p>{subject&&<p className="text-[9px] text-gray-400">{subject}</p>}</div></div>
        <div className="flex items-center gap-2"><Pill color="violet" glow>{cur+1}/{questions.length}</Pill><span className="text-[9px] text-amber-500 font-bold flex items-center gap-0.5"><Zap className="w-2.5 h-2.5"/>+25</span></div>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"><motion.div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full" animate={{width:`${((cur+(answered[cur]?1:0))/questions.length)*100}%`}} transition={{duration:0.5}}/></div>
      <motion.div key={cur} initial={{opacity:0,x:20}} animate={{opacity:1,x:0}} className="rounded-xl p-3 bg-violet-50/50 dark:bg-violet-900/10 border border-violet-100 dark:border-violet-800/30"><p className="text-xs font-semibold leading-relaxed text-gray-800 dark:text-gray-200">{q.q}</p></motion.div>
      <div className="space-y-2">{q.options.map((opt,i)=>{const isC=i===q.correct,isS=i===sel,wa=answered[cur];let cls='border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 hover:border-indigo-300 hover:shadow-sm';if(wa){if(isC)cls='border-emerald-400 bg-emerald-50/80 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 shadow-sm shadow-emerald-500/10';else if(isS)cls='border-rose-400 bg-rose-50/80 dark:bg-rose-900/20 text-rose-700 dark:text-rose-400';else cls='border-gray-200 dark:border-gray-700 opacity-40';}return(
        <motion.button key={i} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}} transition={{delay:i*0.08}} whileHover={!wa?{scale:1.01,x:4}:{}} whileTap={!wa?{scale:0.98}:{}} onClick={()=>handleAnswer(i)} disabled={wa} className={`w-full text-left p-3 rounded-xl border text-xs transition-all flex items-center gap-3 ${cls}`}>
          <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0 ${wa&&isC?'bg-emerald-500 text-white shadow-md':wa&&isS?'bg-rose-500 text-white shadow-md':'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>{wa&&isC?<CheckCircle2 className="w-3.5 h-3.5"/>:wa&&isS?<XCircle className="w-3.5 h-3.5"/>:String.fromCharCode(65+i)}</span>
          <span className="flex-1">{opt}</span>
        </motion.button>);})}</div>
      <AnimatePresence>{showExp&&<motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}} className="rounded-xl p-3.5 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 dark:from-blue-900/10 dark:to-indigo-900/10 border-l-[3px] border-blue-400"><p className="text-[11px] text-gray-700 dark:text-gray-300"><Lightbulb className="w-3 h-3 inline text-blue-500 mr-1"/>{q.explanation}</p></motion.div>}</AnimatePresence>
      {answered[cur]&&<motion.button initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} onClick={next} className="w-full py-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white text-xs font-bold shadow-lg shadow-violet-500/25 flex items-center justify-center gap-2">{cur+1<questions.length?<>Next Question <ArrowRight className="w-3.5 h-3.5"/></>:<>See Results <Sparkles className="w-3.5 h-3.5"/></>}</motion.button>}
    </div>
  );
};

/* ═══════════════════════════════════════════════════════
   FLASHCARD DECK — Progressive complexity swipe cards
   ═══════════════════════════════════════════════════════ */
const CARD_LEVEL_STYLES: Record<string,{gradient:string;bg:string;border:string;text:string;badge:string}> = {
  beginner: {
    gradient: 'from-emerald-500 to-teal-600',
    bg: 'from-emerald-50/80 to-teal-50/80 dark:from-emerald-900/10 dark:to-teal-900/10',
    border: 'border-emerald-200/50 dark:border-emerald-800/30',
    text: 'text-emerald-600 dark:text-emerald-400',
    badge: 'Basics',
  },
  intermediate: {
    gradient: 'from-blue-500 to-indigo-600',
    bg: 'from-blue-50/80 to-indigo-50/80 dark:from-blue-900/10 dark:to-indigo-900/10',
    border: 'border-blue-200/50 dark:border-blue-800/30',
    text: 'text-blue-600 dark:text-blue-400',
    badge: 'Core',
  },
  advanced: {
    gradient: 'from-orange-500 to-rose-600',
    bg: 'from-orange-50/80 to-rose-50/80 dark:from-orange-900/10 dark:to-rose-900/10',
    border: 'border-orange-200/50 dark:border-orange-800/30',
    text: 'text-orange-600 dark:text-orange-400',
    badge: 'Advanced',
  },
};

const FlashcardDeck: React.FC<{
  cards: Array<{title:string;icon:string;points:string[];level:string}>;
  topic: string;
  subject?: string;
  resources?: any[];
  onSend: (msg:string)=>void;
}> = ({cards, topic, subject, resources, onSend}) => {
  const [current, setCurrent] = useState(0);

  if (!cards || cards.length === 0) return null;
  const card = cards[current];
  const style = CARD_LEVEL_STYLES[card.level] || CARD_LEVEL_STYLES.beginner;
  const isFirst = current === 0;
  const isLast = current === cards.length - 1;

  const goTo = (idx: number) => setCurrent(Math.max(0, Math.min(idx, cards.length - 1)));

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
            <Brain className="w-4 h-4 text-white"/>
          </div>
          <div>
            <span className="font-bold text-sm text-gray-800 dark:text-gray-200">{topic}</span>
            {subject && <div className="mt-0.5"><Pill color="blue">{subject}</Pill></div>}
          </div>
        </div>
        <Pill color="violet" glow>{current+1}/{cards.length}</Pill>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-400 via-blue-500 to-orange-500 rounded-full"
          animate={{width:`${((current+1)/cards.length)*100}%`}}
          transition={{duration:0.3}}
        />
      </div>

      {/* Card */}
      <div className="relative min-h-[160px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={current}
            initial={{opacity:0,y:12,scale:0.97}}
            animate={{opacity:1,y:0,scale:1}}
            exit={{opacity:0,y:-12,scale:0.97}}
            transition={{duration:0.22,ease:'easeInOut'}}
            className={`rounded-2xl p-4 bg-gradient-to-br ${style.bg} border ${style.border}`}
          >
            {/* Card header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">{card.icon}</span>
                <span className={`text-xs font-bold ${style.text}`}>{card.title}</span>
              </div>
              <span className={`text-[8px] font-bold uppercase px-2 py-0.5 rounded-full bg-gradient-to-r ${style.gradient} text-white shadow-sm`}>
                {style.badge}
              </span>
            </div>

            {/* Card points */}
            <div className="space-y-2">
              {card.points.map((point:string, i:number) => (
                <motion.div
                  key={i}
                  initial={{opacity:0,x:-8}}
                  animate={{opacity:1,x:0}}
                  transition={{delay:i*0.07}}
                  className="flex items-start gap-2 text-[11px] text-gray-700 dark:text-gray-300"
                >
                  <span className={`w-5 h-5 rounded-md bg-gradient-to-br ${style.gradient} text-white flex items-center justify-center text-[8px] font-bold shrink-0 mt-0.5 shadow-sm`}>
                    {i+1}
                  </span>
                  <Markdown text={point} className="flex-1"/>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between px-1">
        <button
          onClick={()=>goTo(current-1)}
          disabled={isFirst}
          className={`p-2 rounded-xl border transition-all ${isFirst?'opacity-25 cursor-not-allowed border-gray-200 dark:border-gray-700':'border-gray-300 dark:border-gray-600 hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 active:scale-95'}`}
        >
          <ChevronLeft className="w-4 h-4 text-gray-500"/>
        </button>

        {/* Dots */}
        <div className="flex items-center gap-1.5">
          {cards.map((_:any, i:number) => (
            <button
              key={i}
              onClick={()=>goTo(i)}
              className={`transition-all duration-300 rounded-full ${
                i===current
                  ? `w-6 h-2 bg-gradient-to-r ${style.gradient} shadow-sm`
                  : i<current
                    ? 'w-2 h-2 bg-emerald-400/60'
                    : 'w-2 h-2 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400'
              }`}
            />
          ))}
        </div>

        <button
          onClick={()=>goTo(current+1)}
          disabled={isLast}
          className={`p-2 rounded-xl border transition-all ${isLast?'opacity-25 cursor-not-allowed border-gray-200 dark:border-gray-700':'border-gray-300 dark:border-gray-600 hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 active:scale-95'}`}
        >
          <ChevronRight className="w-4 h-4 text-gray-500"/>
        </button>
      </div>

      {/* Swipe hint on first card */}
      {current===0&&cards.length>1&&(
        <motion.p initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.5}} className="text-[9px] text-gray-400 text-center italic flex items-center justify-center gap-1">
          <ArrowRight className="w-2.5 h-2.5"/> Navigate through {cards.length} cards — basics to advanced
        </motion.p>
      )}

      {/* Resources (shown on last card) */}
      {isLast && resources && resources.length>0 && (
        <motion.div initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} className="space-y-1.5">
          <p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
            <FileText className="w-3 h-3 text-orange-400"/> Recommended Resources
          </p>
          {resources.map((r:any, i:number) => (
            <motion.a key={i} href={r.url} target="_blank" rel="noopener noreferrer"
              initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}}
              className="flex items-center justify-between p-2.5 rounded-xl bg-white/60 dark:bg-gray-800/60 hover:bg-gradient-to-r hover:from-orange-50/80 hover:to-rose-50/80 border border-gray-100/60 dark:border-gray-700/30 hover:border-orange-200/60 transition-all group cursor-pointer hover:shadow-md">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                  {platformIcon(r.platform)}
                </div>
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold truncate group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">{r.title}</p>
                  <span className="text-[8px] text-gray-400">{r.platform}{r.difficulty?` · ${r.difficulty}`:''}</span>
                </div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-orange-500 transition-colors shrink-0"/>
            </motion.a>
          ))}
        </motion.div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button onClick={()=>onSend(`Quiz me on ${topic}`)}
          className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-300/30 text-[11px] font-semibold text-violet-600 dark:text-violet-400 hover:from-violet-500/20 hover:to-purple-500/20 transition-all flex items-center justify-center gap-1.5">
          <Brain className="w-3.5 h-3.5"/> Quiz me
        </button>
        <button onClick={()=>onSend(`Resources for ${subject||topic}`)}
          className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-orange-500/10 to-rose-500/10 border border-orange-300/30 text-[11px] font-semibold text-orange-600 dark:text-orange-400 hover:from-orange-500/20 hover:to-rose-500/20 transition-all flex items-center justify-center gap-1.5">
          <FileText className="w-3.5 h-3.5"/> Resources
        </button>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════════════════════
   INTENT/PLATFORM ICONS
   ═══════════════════════════════════════════════════════ */
const intentIcon = (intent?:string) => {
  const m:Record<string,React.ReactNode>={SYLLABUS_QUERY:<BookOpen className="w-3.5 h-3.5 text-blue-400"/>,FACULTY_QUERY:<Users className="w-3.5 h-3.5 text-emerald-400"/>,PERFORMANCE_QUERY:<BarChart3 className="w-3.5 h-3.5 text-violet-400"/>,ELECTIVE_QUERY:<Sparkles className="w-3.5 h-3.5 text-amber-400"/>,CAREER_QUERY:<Briefcase className="w-3.5 h-3.5 text-indigo-400"/>,STUDY_PLAN_QUERY:<Calendar className="w-3.5 h-3.5 text-teal-400"/>,MENTOR_QUERY:<GraduationCap className="w-3.5 h-3.5 text-amber-400"/>,RESOURCE_QUERY:<FileText className="w-3.5 h-3.5 text-orange-400"/>,GREETING:<Heart className="w-3.5 h-3.5 text-pink-400"/>};
  return m[intent||'']||<Bot className="w-3.5 h-3.5 text-indigo-400"/>;
};
const platformIcon = (p:string) => {const pl=p?.toLowerCase()||'';if(pl.includes('youtube'))return<Play className="w-3.5 h-3.5 text-red-500"/>;if(pl.includes('coursera')||pl.includes('udemy'))return<Video className="w-3.5 h-3.5 text-blue-500"/>;if(pl.includes('leetcode')||pl.includes('neetcode'))return<Target className="w-3.5 h-3.5 text-amber-500"/>;if(pl.includes('gfg')||pl.includes('geeksforgeeks'))return<Code className="w-3.5 h-3.5 text-green-500"/>;return<FileText className="w-3.5 h-3.5 text-gray-400"/>;};

/* ═══════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════ */
const AcademicChatbot: React.FC<Props> = ({isFloating=true,defaultOpen=false,className=''}) => {
  const {messages,isLoading,suggestions,sessionToken,isOnline,sendMessage,clearSession,submitFeedback,retryConnection} = useChatbot();
  const [input,setInput]=useState('');
  const [isOpen,setIsOpen]=useState(defaultOpen);
  const [isMinimized,setIsMinimized]=useState(false);
  const [feedback,setFeedback]=useState<Record<string,number>>({});
  const [showAchievements,setShowAchievements]=useState(false);
  const [gamification,setGamification]=useState<GamificationState>(()=>loadGamificationState());
  const [xpPopups,setXpPopups]=useState<Array<{id:number;xp:number}>>([]);
  const [achievementPopup,setAchievementPopup]=useState<Achievement|null>(null);
  const [levelUpPopup,setLevelUpPopup]=useState<number|null>(null);
  const endRef=useRef<HTMLDivElement>(null);
  const inputRef=useRef<HTMLInputElement>(null);
  const popupIdRef=useRef(0);
  const messageCount=messages.filter(m=>m.role==='user').length;

  useEffect(()=>{saveGamificationState(gamification);},[gamification]);

  useEffect(()=>{
    const today=new Date().toDateString();
    if(gamification.lastActiveDate!==today){
      const yesterday=new Date();yesterday.setDate(yesterday.getDate()-1);
      setGamification(prev=>{
        const ns=prev.lastActiveDate===yesterday.toDateString()?prev.streak+1:prev.lastActiveDate===today?prev.streak:1;
        return {...prev,streak:ns,lastActiveDate:today,dailyXpEarned:prev.lastActiveDate===today?prev.dailyXpEarned:0};
      });
    }
  },[]);

  const awardXP=useCallback((amount:number)=>{
    const id=++popupIdRef.current;
    setXpPopups(prev=>[...prev,{id,xp:amount}]);
    setGamification(prev=>{
      const newXp=prev.xp+amount,newLevel=calculateLevel(newXp);
      if(newLevel>prev.level)setTimeout(()=>setLevelUpPopup(newLevel),500);
      return {...prev,xp:newXp,level:newLevel,dailyXpEarned:prev.dailyXpEarned+amount,weeklyXpEarned:prev.weeklyXpEarned+amount};
    });
  },[]);

  const awardAchievement=useCallback((achievementId:string)=>{
    setGamification(prev=>{
      const ach=prev.achievements.find(a=>a.id===achievementId);
      if(!ach||ach.unlocked)return prev;
      const updated={...ach,unlocked:true,unlockedAt:new Date()};
      setAchievementPopup(updated);
      return {...prev,achievements:prev.achievements.map(a=>a.id===achievementId?updated:a),xp:prev.xp+ach.xp};
    });
  },[]);

  const updateAchievementProgress=useCallback((achievementId:string,increment:number=1)=>{
    setGamification(prev=>{
      const achievements=prev.achievements.map(a=>{
        if(a.id===achievementId&&a.maxProgress&&!a.unlocked){
          const np=(a.progress||0)+increment;
          if(np>=a.maxProgress)setTimeout(()=>awardAchievement(achievementId),300);
          return {...a,progress:np};
        }
        return a;
      });
      return {...prev,achievements};
    });
  },[awardAchievement]);

  const handleTopicExplored=useCallback((topic:string)=>{
    if(!gamification.topicsExplored.includes(topic)){
      setGamification(prev=>({...prev,topicsExplored:[...prev.topicsExplored,topic]}));
      awardXP(XP_VALUES.EXPLORE_TOPIC);
      updateAchievementProgress('topics_5');
      updateAchievementProgress('topics_20');
    }
  },[gamification.topicsExplored,awardXP,updateAchievementProgress]);

  const handleQuizComplete=useCallback((score:number,total:number)=>{
    awardXP(XP_VALUES.COMPLETE_QUIZ);
    setGamification(prev=>({...prev,quizzesCompleted:prev.quizzesCompleted+1,perfectQuizzes:score===total?prev.perfectQuizzes+1:prev.perfectQuizzes}));
    if(gamification.quizzesCompleted===0)awardAchievement('quiz_1');
    if(score===total){awardXP(XP_VALUES.PERFECT_QUIZ-XP_VALUES.COMPLETE_QUIZ);awardAchievement('quiz_perfect');}
    updateAchievementProgress('quiz_10');
  },[awardXP,awardAchievement,updateAchievementProgress,gamification]);

  // ═══ FIXED: Track topics/careers at component level, NOT inside renderStructured ═══
  useEffect(()=>{
    if(messages.length===0)return;
    const lastMsg=messages[messages.length-1];
    if(lastMsg.role!=='assistant'||typeof lastMsg.content==='string')return;
    const resp=lastMsg.content as ChatResponseContent;
    if(!resp||!resp.type)return;
    if(resp.type==='concept_explanation'&&resp.content?.topic)handleTopicExplored(resp.content.topic);
    if(resp.type==='career_guidance'&&resp.content?.career?.title)updateAchievementProgress('career_explorer');
  },[messages.length]);

  const scroll=useCallback(()=>{setTimeout(()=>endRef.current?.scrollIntoView({behavior:'smooth'}),120);},[]);
  useEffect(scroll,[messages,scroll]);
  useEffect(()=>{if(isOpen&&!isMinimized)inputRef.current?.focus();},[isOpen,isMinimized]);

  const send=async(msg:string=input)=>{
    const text=msg.trim();if(!text||isLoading)return;setInput('');
    awardXP(XP_VALUES.ASK_QUESTION);
    if(gamification.totalQuestions===0)awardAchievement('first_question');
    setGamification(prev=>({...prev,totalQuestions:prev.totalQuestions+1}));
    const hour=new Date().getHours();
    if((hour>=22||hour<5)&&!gamification.achievements.find(a=>a.id==='night_owl')?.unlocked)awardAchievement('night_owl');
    if(hour>=5&&hour<7&&!gamification.achievements.find(a=>a.id==='early_bird')?.unlocked)awardAchievement('early_bird');
    await sendMessage(text);
  };

  const onFeedback=async(id:string,rating:number)=>{
    setFeedback(p=>({...p,[id]:rating}));awardXP(XP_VALUES.GIVE_FEEDBACK);updateAchievementProgress('helper');
    await submitFeedback({session_id:sessionToken||'',message_id:id,rating,was_helpful:rating>=4});
  };

  const FeedbackRow: React.FC<{id:string}>=({id})=>{
    if(feedback[id])return<motion.span initial={{scale:0}} animate={{scale:1}} className="text-[10px] text-emerald-400 flex items-center gap-0.5"><CheckCircle2 className="w-2.5 h-2.5"/> Thanks!</motion.span>;
    return(<div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
      <button onClick={()=>onFeedback(id,5)} className="p-1.5 rounded-lg hover:bg-emerald-500/10" title="Helpful"><ThumbsUp className="w-3 h-3 text-gray-400 hover:text-emerald-400 transition-colors"/></button>
      <button onClick={()=>onFeedback(id,2)} className="p-1.5 rounded-lg hover:bg-rose-500/10" title="Not helpful"><ThumbsDown className="w-3 h-3 text-gray-400 hover:text-rose-400 transition-colors"/></button>
    </div>);
  };

  const ResponseFooter: React.FC<{resp:ChatResponseContent;msgId:string}>=({resp,msgId})=>(
    <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-gray-100/50 dark:border-gray-700/30">
      <div className="flex items-center gap-1.5 flex-wrap">
        <ConfBadge c={resp.confidence}/>{resp.from_cache&&<Pill color="cyan">⚡ Cached</Pill>}{(resp.llm_enhanced||resp.llm_generated)&&<Pill color="pink" glow><span className="flex items-center gap-0.5"><Sparkles className="w-2.5 h-2.5"/> AI</span></Pill>}
      </div>
      <FeedbackRow id={msgId}/>
    </div>
  );

  /* ═══════════════════════════════════════════════════════
     ALL STRUCTURED RENDERERS (NO hooks inside!)
     ═══════════════════════════════════════════════════════ */
  const renderStructured = (resp: ChatResponseContent, msgId: string) => {
    const { type, content, confidence } = resp;

    // ── Quiz ──
    if (type === 'quiz') return <QuizCard topic={content.topic} subject={content.subject} questions={content.questions||[]} onSend={send} onQuizComplete={handleQuizComplete}/>;

    // ── Semester Subjects ──
    if (type === 'semester_subjects') {
      const subjects = content.subjects || [];
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5 flex-wrap"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg"><BookOpen className="w-4 h-4 text-white"/></div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">Semester {content.semester}</span><div className="flex gap-1.5 mt-0.5"><Pill color="blue">{content.count} subjects</Pill><Pill color="cyan">{content.total_credits} credits</Pill></div></div></div>
        <div className="space-y-1.5">{subjects.map((s:any,i:number)=>(
          <motion.button key={i} initial={{opacity:0,x:-12}} animate={{opacity:1,x:0}} transition={{delay:i*0.04}} onClick={()=>send(`Tell me about ${s.name}`)}
            className="w-full flex items-center justify-between p-3 rounded-xl group bg-white/60 dark:bg-gray-800/60 hover:bg-gradient-to-r hover:from-indigo-50/80 hover:to-blue-50/80 dark:hover:from-indigo-900/10 border border-transparent hover:border-indigo-200/60 transition-all text-left hover:shadow-md">
            <div className="flex items-center gap-3 min-w-0"><span className="text-[9px] font-mono text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-lg w-[70px] text-center shrink-0">{s.code}</span><span className="text-[11px] font-medium truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{s.name}</span></div>
            <div className="flex items-center gap-2 shrink-0 ml-2"><Pill color={s.subject_type==='core'?'green':'violet'}>{s.subject_type==='core'?'Core':'Elective'}</Pill><span className="text-[9px] text-gray-400">{s.credits}cr</span><ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-indigo-500 transition-all"/></div>
          </motion.button>))}</div>
        <p className="text-[9px] text-gray-400 text-center italic flex items-center justify-center gap-1"><Search className="w-2.5 h-2.5"/> Tap any subject to see full syllabus</p>
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Syllabus Breakdown ──
    if (type === 'syllabus_breakdown') {
      const units = content.units || [];
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5 flex-wrap"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg"><BookOpen className="w-4 h-4 text-white"/></div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">{content.name}</span><div className="flex flex-wrap gap-1.5 mt-0.5">{content.code&&<Pill color="blue">{content.code}</Pill>}{content.semester&&<Pill color="cyan">Sem {content.semester}</Pill>}{content.credits>0&&<Pill color="green">{content.credits} credits</Pill>}</div></div></div>
        {content.description&&<p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed bg-gray-50/50 dark:bg-gray-800/30 rounded-xl p-3 border border-gray-100/50 dark:border-gray-700/30">{content.description}</p>}
        {units.length>0&&<div className="space-y-2"><p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1"><Hash className="w-3 h-3"/> Units & Topics</p>
          {units.map((u:any,i:number)=>(<motion.div key={i} initial={{opacity:0}} animate={{opacity:1}} transition={{delay:i*0.06}} className="rounded-xl p-3.5 bg-white/60 dark:bg-gray-800/60 border border-gray-100/60 dark:border-gray-700/30 hover:shadow-sm transition-shadow">
            <p className="text-[11px] font-bold text-gray-700 dark:text-gray-300 flex items-center gap-2"><span className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 text-white flex items-center justify-center text-[9px] font-bold shrink-0 shadow-md">{u.unit_number||i+1}</span>{u.title}</p>
            {u.topics?.length>0&&<div className="flex flex-wrap gap-1.5 mt-2.5">{u.topics.slice(0,10).map((t:any,j:number)=>{const name=typeof t==='string'?t:t.name||t.title||String(t);return(<button key={j} onClick={()=>send(`Explain ${name}`)} className="text-[9px] bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 px-2.5 py-1 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-all border border-indigo-200/40 dark:border-indigo-700/40 hover:shadow-sm hover:scale-105 active:scale-95">{name}</button>);})}{u.topics.length>10&&<span className="text-[9px] text-gray-400 px-1 self-center">+{u.topics.length-10} more</span>}</div>}
          </motion.div>))}</div>}
        {content.faculty?.length>0&&<div className="rounded-xl p-3 bg-emerald-50/50 dark:bg-emerald-900/10 border border-emerald-200/30 dark:border-emerald-800/30"><p className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 mb-1 flex items-center gap-1"><Users className="w-3 h-3"/> Faculty</p>{content.faculty.map((f:any,i:number)=><p key={i} className="text-[10px] text-gray-600 dark:text-gray-400">{f.name} — {f.designation}</p>)}</div>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Concept Explanation (Flashcard mode + legacy mode) ──
    if (type === 'concept_explanation') {
      // ── Flashcard mode: when backend returns cards array ──
      if (content.cards && content.cards.length > 0) {
        return (<div className="space-y-3">
          <FlashcardDeck
            cards={content.cards}
            topic={content.topic || ''}
            subject={content.subject}
            resources={content.resources}
            onSend={send}
          />
          {content.suggestions?.length>0&&<div className="flex flex-wrap gap-1.5">{content.suggestions.map((s:string,i:number)=>(<SuggestionChip key={i} text={s} onClick={()=>send(s)}/>))}</div>}
          <ResponseFooter resp={resp} msgId={msgId}/>
        </div>);
      }

      // ── Legacy mode: definition + key_points (first-time explains, built-in KB) ──
      return (<div className="space-y-3">
        {(content.topic||content.subject)&&<div className="flex items-center gap-2.5 flex-wrap"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg"><Brain className="w-4 h-4 text-white"/></div><div>{content.topic&&<span className="font-bold text-sm text-gray-800 dark:text-gray-200">{content.topic}</span>}{content.subject&&<div className="mt-0.5"><Pill color="blue">{content.subject}</Pill></div>}</div></div>}
        
        {content.definition&&<div className="rounded-xl p-4 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 dark:from-blue-900/10 dark:to-indigo-900/10 border-l-[3px] border-blue-400"><Markdown text={content.definition} className="text-[11px] text-gray-700 dark:text-gray-300"/></div>}
        
        {content.explanation&&<Markdown text={content.explanation} className="text-[11px] text-gray-600 dark:text-gray-400"/>}
        
        {content.key_points?.length>0&&<div className="space-y-1.5"><p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1"><Lightbulb className="w-3 h-3 text-amber-400"/> Key Points</p>{content.key_points.map((p:string,i:number)=>(<motion.div key={i} initial={{opacity:0,x:-6}} animate={{opacity:1,x:0}} transition={{delay:i*0.06}} className="flex items-start gap-2.5 text-[11px] text-gray-700 dark:text-gray-300 bg-white/40 dark:bg-gray-800/40 rounded-lg p-2.5 border border-gray-100/50 dark:border-gray-700/30"><span className="w-5 h-5 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 text-white flex items-center justify-center text-[8px] font-bold shrink-0 mt-0.5 shadow-sm">{i+1}</span><Markdown text={p} className="flex-1"/></motion.div>))}</div>}
        
        {content.examples?.length>0&&<div className="rounded-xl p-3 bg-amber-50/50 dark:bg-amber-900/5 border border-amber-200/30 dark:border-amber-800/20"><p className="text-[9px] font-bold text-amber-600 dark:text-amber-400 mb-1.5 flex items-center gap-1"><Lightbulb className="w-3 h-3"/> Examples</p>{content.examples.map((e:string,i:number)=>(<div key={i} className="text-[10px] text-gray-600 dark:text-gray-400 flex items-start gap-1.5 my-0.5"><span className="text-amber-400 shrink-0">→</span><Markdown text={e} className="flex-1"/></div>))}</div>}
        
        {content.common_mistakes?.length>0&&<div className="rounded-xl p-3 bg-rose-50/50 dark:bg-rose-900/5 border border-rose-200/30 dark:border-rose-800/20"><p className="text-[9px] font-bold text-rose-600 dark:text-rose-400 mb-1.5 flex items-center gap-1"><AlertCircle className="w-3 h-3"/> Common Mistakes</p>{content.common_mistakes.map((m:string,i:number)=>(<div key={i} className="text-[10px] text-gray-600 dark:text-gray-400 flex items-start gap-1.5 my-0.5"><span className="text-rose-400 shrink-0">✗</span><Markdown text={m} className="flex-1"/></div>))}</div>}
        
        {content.related_topics?.length>0&&<div><p className="text-[9px] text-gray-400 mb-1.5 font-medium">Related:</p><div className="flex flex-wrap gap-1.5">{content.related_topics.map((t:string,i:number)=>(<button key={i} onClick={()=>send(`Explain ${t}`)} className="text-[9px] bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 px-2.5 py-1 rounded-lg hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-900/20 dark:hover:text-indigo-400 transition-all border border-gray-200/50 dark:border-gray-700/50 hover:shadow-sm flex items-center gap-1">{t}<ArrowUpRight className="w-2.5 h-2.5 opacity-60"/></button>))}</div></div>}
        
        {content.exam_relevance&&<div className="rounded-lg p-2.5 text-[10px] bg-violet-50/50 dark:bg-violet-900/10 border border-violet-200/30 dark:border-violet-800/30 flex items-center gap-2"><Award className="w-4 h-4 text-violet-500 shrink-0"/><span><span className="font-semibold text-violet-600 dark:text-violet-400">Exam Relevance: </span><Markdown text={content.exam_relevance} className="inline"/></span></div>}
        
        {content.resources?.length>0&&<div className="space-y-1.5"><p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1"><FileText className="w-3 h-3 text-orange-400"/> Recommended Resources</p>{content.resources.map((r:any,i:number)=>(<motion.a key={i} href={r.url} target="_blank" rel="noopener noreferrer" initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}} className="flex items-center justify-between p-2.5 rounded-xl bg-white/60 dark:bg-gray-800/60 hover:bg-gradient-to-r hover:from-orange-50/80 hover:to-rose-50/80 border border-gray-100/60 dark:border-gray-700/30 hover:border-orange-200/60 transition-all group cursor-pointer hover:shadow-md"><div className="flex items-center gap-2.5 min-w-0"><div className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">{platformIcon(r.platform)}</div><div className="min-w-0"><p className="text-[10px] font-semibold truncate group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">{r.title}</p><span className="text-[8px] text-gray-400">{r.platform}{r.difficulty?` · ${r.difficulty}`:''}</span></div></div><ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-orange-500 transition-colors shrink-0"/></motion.a>))}</div>}
        
        {content.topic&&<div className="flex gap-2"><button onClick={()=>send(`Quiz me on ${content.topic}`)} className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-300/30 text-[11px] font-semibold text-violet-600 dark:text-violet-400 hover:from-violet-500/20 hover:to-purple-500/20 transition-all flex items-center justify-center gap-1.5"><Brain className="w-3.5 h-3.5"/> Quiz me</button><button onClick={()=>send(`Resources for ${content.subject||content.topic}`)} className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-orange-500/10 to-rose-500/10 border border-orange-300/30 text-[11px] font-semibold text-orange-600 dark:text-orange-400 hover:from-orange-500/20 hover:to-rose-500/20 transition-all flex items-center justify-center gap-1.5"><FileText className="w-3.5 h-3.5"/> Resources</button></div>}
        
        {content.suggestions?.length>0&&<div className="flex flex-wrap gap-1.5">{content.suggestions.map((s:string,i:number)=>(<SuggestionChip key={i} text={s} onClick={()=>send(s)}/>))}</div>}
        
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Faculty / Mentor ──
    if (['faculty_list','faculty_recommendation','mentor_recommendation'].includes(type)) {
      const list=content.faculty||content.recommendations||[];const isMentor=type==='mentor_recommendation';
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5"><div className={`w-9 h-9 rounded-xl bg-gradient-to-br shadow-lg flex items-center justify-center ${isMentor?'from-amber-500 to-orange-500':'from-emerald-500 to-teal-500'}`}>{isMentor?<GraduationCap className="w-4 h-4 text-white"/>:<Users className="w-4 h-4 text-white"/>}</div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">{isMentor?'Recommended Mentors':'Faculty'}</span><div className="mt-0.5"><Pill color={isMentor?'amber':'green'}>{content.count||list.length} found</Pill></div></div></div>
        {content.message&&<p className="text-[11px] text-gray-500">{content.message}</p>}
        {list.map((f:any,i:number)=>(<motion.div key={i} initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}} className="rounded-xl p-3.5 bg-white/60 dark:bg-gray-800/60 border border-gray-100/60 dark:border-gray-700/30 hover:shadow-md transition-shadow">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-lg">{f.name?.split(' ').map((w:string)=>w[0]).join('').slice(0,2)}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2"><div><p className="text-[12px] font-bold text-gray-800 dark:text-gray-200">{f.name}</p><p className="text-[9px] text-gray-400">{f.designation} · {f.department}</p></div>
                {f.email&&<a href={`mailto:${f.email}`} className="text-[9px] bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors flex items-center gap-1 shrink-0 border border-indigo-200/40 dark:border-indigo-700/40"><Mail className="w-2.5 h-2.5"/> Email</a>}</div>
              {f.match_reason&&<p className="text-[9px] text-emerald-500 mt-1.5 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> {f.match_reason}</p>}
              {(f.subjects_taught?.length>0||f.subjects?.length>0)&&<div className="flex flex-wrap gap-1 mt-2">{(f.subjects_taught||f.subjects||[]).slice(0,4).map((s:string,j:number)=>(<span key={j} className="text-[8px] bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-0.5 rounded-full">{s}</span>))}</div>}
            </div>
          </div>
        </motion.div>))}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Performance Analysis ──
    if (type === 'performance_analysis') {
      const trend=content.trend_direction;const sgpaData=(content.sgpa_trend||[]).map((s:any)=>s.sgpa);
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg"><BarChart3 className="w-4 h-4 text-white"/></div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">Academic Performance</span><div className="mt-0.5">{trend==='improving'?<Pill color="green" glow><span className="flex items-center gap-0.5"><TrendingUp className="w-2.5 h-2.5"/> Improving</span></Pill>:trend==='declining'?<Pill color="red" glow><span className="flex items-center gap-0.5"><TrendingDown className="w-2.5 h-2.5"/> Declining</span></Pill>:<Pill color="amber">→ Stable</Pill>}</div></div></div>
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-xl p-3 bg-gradient-to-br from-violet-500/5 to-purple-500/5 border border-violet-200/30 text-center"><ProgressRing value={content.current_cgpa||0} max={10} size={52} color="#8b5cf6" label={content.current_cgpa?.toFixed(1)||'–'}/><p className="text-[8px] text-gray-400 mt-1 font-medium">CGPA</p></div>
          <div className="rounded-xl p-3 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 border border-blue-200/30 text-center"><p className="text-xl font-bold text-blue-500">{content.latest_sgpa?.toFixed(1)||'–'}</p><p className="text-[8px] text-gray-400 font-medium">Latest SGPA</p>{sgpaData.length>1&&<div className="mt-1.5 flex justify-center"><MiniSparkline data={sgpaData} color="#3b82f6"/></div>}</div>
          <div className="rounded-xl p-3 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 border border-emerald-200/30 text-center"><p className="text-lg font-bold text-emerald-500">{content.strong_subjects?.length||0}</p><p className="text-[8px] text-gray-400 font-medium">Strong</p><p className="text-sm font-bold text-rose-400 mt-0.5">{content.weak_subjects?.length||0}<span className="text-[8px] text-gray-400 font-normal"> Weak</span></p></div>
        </div>
        {content.subject_analysis?.length>0&&<div className="space-y-2"><p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider">Subject Breakdown</p>{content.subject_analysis.slice(0,6).map((s:any,i:number)=>(<div key={i} className="flex items-center gap-2.5 text-[10px]"><span className="truncate w-28 text-gray-600 dark:text-gray-400 shrink-0">{s.subject}</span><div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2.5"><motion.div initial={{width:0}} animate={{width:`${Math.min(s.score,100)}%`}} transition={{duration:0.8,delay:i*0.1}} className={`h-2.5 rounded-full ${s.status==='strong'?'bg-gradient-to-r from-emerald-400 to-teal-500':s.status==='weak'?'bg-gradient-to-r from-rose-400 to-red-500':'bg-gradient-to-r from-amber-400 to-orange-500'}`}/></div><span className={`w-7 text-right font-bold ${s.status==='strong'?'text-emerald-500':s.status==='weak'?'text-rose-500':'text-amber-500'}`}>{s.score}</span></div>))}</div>}
        {content.recommendations?.length>0&&<div className="rounded-xl p-3.5 bg-gradient-to-r from-indigo-50/50 to-purple-50/50 dark:from-indigo-900/5 dark:to-purple-900/5 border border-indigo-200/30"><p className="text-[9px] font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 mb-2"><Rocket className="w-3 h-3"/> Improvement Roadmap</p>{content.recommendations.map((r:string,i:number)=>(<Markdown key={i} text={r} className="text-[10px] text-gray-600 dark:text-gray-400 py-0.5"/>))}</div>}
        {content.ai_insights&&<div className="rounded-xl p-3 text-[10px] bg-gradient-to-r from-violet-50/50 to-pink-50/50 dark:from-violet-900/10 dark:to-pink-900/10 border border-violet-200/30"><div className="flex items-center gap-1.5 mb-1"><Sparkles className="w-3 h-3 text-violet-500"/><span className="text-[9px] font-bold text-violet-600 dark:text-violet-400">AI Insights</span></div><Markdown text={content.ai_insights} className="text-gray-600 dark:text-gray-400"/></div>}
        {content.suggestions?.length>0&&<div className="flex flex-wrap gap-1.5">{content.suggestions.map((s:string,i:number)=>(<SuggestionChip key={i} text={s} onClick={()=>send(s)}/>))}</div>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Career Guidance ──
    if (type === 'career_guidance') {
      const career=content.career||{};const roadmap=content.roadmap||[];
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5 flex-wrap"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg"><Briefcase className="w-4 h-4 text-white"/></div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">{career.title}</span>{career.market_demand&&<div className="mt-0.5"><Pill color="green" glow>{career.market_demand} Demand</Pill></div>}</div></div>
        {career.description&&<p className="text-[11px] text-gray-500 leading-relaxed">{career.description}</p>}
        {career.salary_range&&<div className="rounded-xl p-3.5 bg-gradient-to-r from-emerald-50/80 to-teal-50/80 dark:from-emerald-900/10 dark:to-teal-900/10 border border-emerald-200/30"><p className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mb-2"><DollarSign className="w-3 h-3"/> Salary Range (India)</p><div className="grid grid-cols-3 gap-2 text-[10px]">{['entry_level','mid_level','senior_level'].map(k=>career.salary_range[k]?<div key={k} className="text-center"><p className="text-[8px] text-gray-400 uppercase">{k.replace('_',' ')}</p><p className="font-bold text-emerald-600 dark:text-emerald-400 text-sm">{career.salary_range[k]}</p></div>:null)}</div></div>}
        {career.required_skills?.length>0&&<div><p className="text-[9px] text-gray-400 mb-1.5 font-medium">Required Skills:</p><div className="flex flex-wrap gap-1.5">{career.required_skills.map((s:string,i:number)=>(<Pill key={i} color="blue">{s}</Pill>))}</div></div>}
        {content.gap_analysis&&<div className="rounded-xl p-3.5 bg-orange-50/50 dark:bg-orange-900/5 border border-orange-200/30"><p className="text-[9px] font-bold text-orange-600 dark:text-orange-400 mb-2 flex items-center gap-1"><Target className="w-3 h-3"/> Your Skill Match</p><div className="flex items-center gap-3"><div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3"><motion.div initial={{width:0}} animate={{width:`${content.gap_analysis.skill_match_pct}%`}} transition={{duration:1}} className="bg-gradient-to-r from-emerald-400 to-teal-500 h-3 rounded-full"/></div><span className="text-sm font-bold text-emerald-600">{content.gap_analysis.skill_match_pct}%</span></div>{content.gap_analysis.missing_skills?.length>0&&<p className="text-[9px] text-orange-500 mt-2">📚 Skills to develop: {content.gap_analysis.missing_skills.slice(0,4).join(', ')}</p>}</div>}
        {roadmap.length>0&&<div><p className="text-[9px] font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1"><MapPin className="w-3 h-3"/> Career Roadmap</p>{roadmap.map((s:any)=>(<div key={s.step} className="flex items-start gap-3 mb-3 last:mb-0"><div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-[9px] font-bold text-white shrink-0 mt-0.5 shadow-lg">{s.step}</div><div className="text-[10px] border-l-2 border-indigo-200 dark:border-indigo-800 pl-3 pb-2 flex-1"><span className="font-bold text-gray-800 dark:text-gray-200">{s.title}</span><span className="text-gray-400 ml-1">· {s.duration}</span><p className="text-gray-500 mt-0.5">{s.description}</p></div></div>))}</div>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Career List ──
    if (type === 'career_list') {
      return (<div className="space-y-2.5">
        {content.message&&<p className="text-[11px] text-gray-500 font-medium">{content.message}</p>}
        {(content.careers||[]).map((c:any,i:number)=>(<motion.button key={i} onClick={()=>send(`Tell me about ${c.title} career`)} initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{delay:i*0.05}} className="w-full text-left p-3.5 rounded-xl bg-white/60 dark:bg-gray-800/60 hover:bg-gradient-to-r hover:from-indigo-50/80 hover:to-blue-50/80 border border-gray-100/60 dark:border-gray-700/30 hover:border-indigo-200/60 transition-all text-xs group hover:shadow-md"><div className="flex justify-between items-center"><span className="font-bold text-gray-800 dark:text-gray-200 group-hover:text-indigo-600 transition-colors">{c.title}</span><div className="flex items-center gap-1.5">{c.demand&&<Pill color="green">{c.demand}</Pill>}<ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-indigo-500 transition-all"/></div></div>{c.description&&<p className="text-[10px] text-gray-400 mt-1">{c.description}</p>}</motion.button>))}
        {content.hint&&<p className="text-[9px] text-gray-400 italic text-center">{content.hint}</p>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Resource List ──
    if (type === 'resource_list') {
      const resources=content.resources||[];
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-rose-500 flex items-center justify-center shadow-lg"><FileText className="w-4 h-4 text-white"/></div><Markdown text={content.message||''} className="text-sm font-bold text-gray-800 dark:text-gray-200"/></div>
        {resources.map((r:any,i:number)=>(<motion.a key={i} href={r.url} target="_blank" rel="noopener noreferrer" initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}} className="flex items-center justify-between p-3.5 rounded-xl bg-white/60 dark:bg-gray-800/60 hover:bg-gradient-to-r hover:from-orange-50/80 hover:to-rose-50/80 border border-gray-100/60 dark:border-gray-700/30 hover:border-orange-200/60 transition-all group cursor-pointer hover:shadow-md">
          <div className="flex items-center gap-3 min-w-0"><div className="w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">{platformIcon(r.platform)}</div><div className="min-w-0"><p className="text-[11px] font-semibold truncate group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">{r.title}</p><div className="flex items-center gap-2 mt-0.5 flex-wrap"><span className="text-[9px] text-gray-400">{r.platform}</span><Pill color={r.difficulty==='Beginner'?'green':r.difficulty==='Advanced'?'red':'amber'}>{r.difficulty||r.type}</Pill></div></div></div>
          <div className="flex items-center gap-2 shrink-0 ml-2">{r.rating>0&&<span className="text-[9px] text-amber-500 flex items-center gap-0.5"><Star className="w-3 h-3 fill-amber-400"/>{r.rating}</span>}<ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-orange-500 transition-colors"/></div>
        </motion.a>))}
        {content.cta&&<a href={content.cta.url} className="text-[10px] text-indigo-600 hover:text-indigo-700 font-bold flex items-center gap-1 justify-center py-2 rounded-xl bg-indigo-50/50 dark:bg-indigo-900/10 border border-indigo-200/30 hover:border-indigo-300/50 transition-all hover:shadow-sm">{content.cta.text} <ExternalLink className="w-3 h-3"/></a>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Study Plan ──
    if (type === 'study_plan') {
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 flex items-center justify-center shadow-lg"><Calendar className="w-4 h-4 text-white"/></div><div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">Study Plan</span>{content.total_daily_hours&&<div className="mt-0.5"><Pill color="cyan">{content.total_daily_hours}h/day</Pill></div>}</div></div>
        {content.daily_schedule?.map((s:any,i:number)=>(<div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/60 dark:bg-gray-800/60 text-[10px] border border-gray-100/60 dark:border-gray-700/30"><div className="flex items-center gap-2.5"><span className={`w-3 h-3 rounded-full ${s.priority==='high'?'bg-gradient-to-br from-rose-400 to-red-500 shadow-sm shadow-rose-500/30':'bg-gradient-to-br from-blue-400 to-indigo-500 shadow-sm shadow-blue-500/30'}`}/><span className="font-medium text-gray-700 dark:text-gray-300">{s.subject}</span>{s.priority==='high'&&<Pill color="red">Priority</Pill>}</div><span className="text-gray-500 font-bold text-sm">{s.suggested_hours}h</span></div>))}
        {content.exam_tips?.length>0&&<div className="rounded-xl p-3 bg-amber-50/50 dark:bg-amber-900/5 border border-amber-200/30"><p className="text-[9px] font-bold text-amber-600 dark:text-amber-400 mb-1.5 flex items-center gap-1"><Lightbulb className="w-3 h-3"/> Exam Tips</p>{content.exam_tips.map((t:string,i:number)=>(<p key={i} className="text-[10px] text-gray-600 dark:text-gray-400 py-0.5 flex items-start gap-1.5"><span className="text-amber-400 shrink-0">→</span> {t}</p>))}</div>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Elective Recommendation ──
    if (type === 'elective_recommendation') {
      return (<div className="space-y-3">
        <div className="flex items-center gap-2.5"><div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg"><Sparkles className="w-4 h-4 text-white"/></div><span className="font-bold text-sm text-gray-800 dark:text-gray-200">Recommended Electives</span></div>
        {(content.recommendations||[]).map((r:any,i:number)=>(<motion.div key={i} initial={{opacity:0,y:4}} animate={{opacity:1,y:0}} transition={{delay:i*0.06}} className="rounded-xl p-3.5 bg-white/60 dark:bg-gray-800/60 border border-gray-100/60 dark:border-gray-700/30"><div className="flex justify-between items-start"><span className="text-[11px] font-bold text-gray-800 dark:text-gray-200">{r.name}</span>{r.category&&<Pill color="violet">{r.category}</Pill>}</div>{r.reasons?.[0]&&<p className="text-[9px] text-emerald-500 mt-1.5 font-medium flex items-center gap-1"><CheckCircle2 className="w-3 h-3"/> {r.reasons[0]}</p>}{r.career_paths?.length>0&&<div className="flex flex-wrap gap-1 mt-2">{r.career_paths.map((p:string,j:number)=>(<button key={j} onClick={()=>send(`Career in ${p}`)} className="text-[8px] bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full border border-blue-200/40 hover:bg-blue-100 transition-colors">→ {p}</button>))}</div>}</motion.div>))}
        {content.advice&&<p className="text-[9px] text-gray-400 italic text-center">💡 {content.advice}</p>}
        <ResponseFooter resp={resp} msgId={msgId}/>
      </div>);
    }

    // ── Default / Text ──
    return (<div className="space-y-2.5">
      <Markdown text={content.message||JSON.stringify(content)} className="text-[11px] text-gray-700 dark:text-gray-300"/>
      {content.scope?.length>0&&<div className="grid grid-cols-2 gap-1.5 mt-2">{content.scope.map((s:string,i:number)=>(<div key={i} className="text-[10px] text-gray-600 dark:text-gray-400 bg-white/50 dark:bg-gray-800/50 rounded-xl px-3 py-2 border border-gray-100/60 dark:border-gray-700/40 flex items-center gap-1.5">{s}</div>))}</div>}
      {content.suggestions?.length>0&&<div className="flex flex-wrap gap-1.5 mt-2">{content.suggestions.map((s:string,i:number)=>(<SuggestionChip key={i} text={s} onClick={()=>send(s)}/>))}</div>}
      <div className="flex items-center justify-between mt-1.5"><div className="flex items-center gap-1.5">{confidence&&<ConfBadge c={confidence}/>}{resp.from_cache&&<Pill color="cyan">⚡ Cached</Pill>}{(resp.llm_enhanced||resp.llm_generated)&&<Pill color="pink"><span className="flex items-center gap-0.5"><Sparkles className="w-2.5 h-2.5"/> AI</span></Pill>}</div><FeedbackRow id={msgId}/></div>
    </div>);
  };

  const renderMsg = (msg: ChatMessage) => {
    if (msg.isLoading) return <TypingWave/>;
    if (typeof msg.content === 'string') return (<div><Markdown text={msg.content} className="text-[11px]"/>{msg.advisorSuggestion&&<AdvisorCard suggestion={msg.advisorSuggestion}/>}</div>);
    const resp = msg.content as ChatResponseContent;
    return (<div>{renderStructured(resp, msg.id)}{(resp.advisor_suggestion||msg.advisorSuggestion)&&<AdvisorCard suggestion={resp.advisor_suggestion||msg.advisorSuggestion!}/>}</div>);
  };

  /* ═══════════════════════════════════════════════════════
     LAYOUT
     ═══════════════════════════════════════════════════════ */
  if (isFloating && !isOpen) {
    return (
      <motion.button initial={{scale:0}} animate={{scale:1}} whileHover={{scale:1.08}} whileTap={{scale:0.92}} onClick={()=>setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white shadow-2xl shadow-purple-500/30 flex items-center justify-center hover:shadow-purple-500/50 transition-shadow">
        <Bot className="w-6 h-6"/>
        {gamification.streak>0&&<motion.div initial={{scale:0}} animate={{scale:1}} className="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center text-white text-[10px] font-bold shadow-md"><Flame className="w-3 h-3"/></motion.div>}
        <span className="absolute -bottom-0.5 -left-0.5 w-4 h-4 bg-emerald-400 rounded-full border-2 border-white animate-pulse"/>
        <motion.span className="absolute inset-0 rounded-2xl border-2 border-purple-400/50" animate={{scale:[1,1.3,1.3],opacity:[0.5,0,0]}} transition={{duration:2,repeat:Infinity}}/>
      </motion.button>
    );
  }

  const containerClass = isFloating
    ? `fixed bottom-6 right-6 w-[420px] ${isMinimized?'h-14':'h-[700px]'} bg-gray-50/95 dark:bg-gray-900/95 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/15 flex flex-col z-50 transition-all duration-300 border border-white/20 dark:border-gray-700/50 overflow-hidden`
    : `w-full h-full bg-gray-50/95 dark:bg-gray-900/95 backdrop-blur-xl rounded-3xl shadow-lg flex flex-col overflow-hidden ${className}`;

  return (
    <div className={containerClass}>
      <AnimatePresence>{xpPopups.map(p=><XPPopup key={p.id} xp={p.xp} onComplete={()=>setXpPopups(prev=>prev.filter(x=>x.id!==p.id))}/>)}</AnimatePresence>
      <AnimatePresence>{achievementPopup&&<AchievementPopup achievement={achievementPopup} onClose={()=>setAchievementPopup(null)}/>}</AnimatePresence>
      <AnimatePresence>{levelUpPopup&&<LevelUpCelebration level={levelUpPopup} onClose={()=>setLevelUpPopup(null)}/>}</AnimatePresence>

      {/* Header */}
      <div className="relative flex items-center justify-between px-4 py-3.5 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 text-white shrink-0 overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full blur-2xl"/>
        <div className="absolute bottom-0 left-10 w-16 h-16 bg-pink-400/20 rounded-full blur-xl"/>
        <div className="flex items-center gap-3 relative z-10">
          <div className="relative">
            <motion.div animate={{rotate:[0,5,-5,0]}} transition={{duration:4,repeat:Infinity,ease:'easeInOut'}} className="w-10 h-10 bg-white/15 rounded-2xl flex items-center justify-center backdrop-blur-sm border border-white/20 shadow-lg"><Bot className="w-5 h-5"/></motion.div>
            <span className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-purple-600 ${isOnline?'bg-emerald-400':'bg-amber-400'}`}/>
          </div>
          <div>
            <h3 className="font-bold text-sm tracking-tight">Academic Advisor</h3>
            {!isMinimized&&<div className="flex items-center gap-2"><p className="text-[10px] text-white/60 flex items-center gap-1">{isOnline?<><Wifi className="w-2.5 h-2.5"/> Online</>:<><WifiOff className="w-2.5 h-2.5"/> Offline</>}</p><div className="flex items-center gap-1 text-[9px] text-white/50 bg-white/10 px-1.5 py-0.5 rounded-full"><Zap className="w-2.5 h-2.5 text-amber-300"/> {gamification.xp} XP</div></div>}
          </div>
        </div>
        <div className="flex items-center gap-0.5 relative z-10">
          <button onClick={clearSession} className="p-1.5 hover:bg-white/10 rounded-xl transition-colors" title="New conversation"><RefreshCw className="w-3.5 h-3.5"/></button>
          {isFloating&&<><button onClick={()=>setIsMinimized(!isMinimized)} className="p-1.5 hover:bg-white/10 rounded-xl transition-colors">{isMinimized?<Maximize2 className="w-3.5 h-3.5"/>:<Minimize2 className="w-3.5 h-3.5"/>}</button><button onClick={()=>setIsOpen(false)} className="p-1.5 hover:bg-white/10 rounded-xl transition-colors"><X className="w-3.5 h-3.5"/></button></>}
        </div>
      </div>

      {!isMinimized&&<>
        <GamificationBar state={gamification} onShowAchievements={()=>setShowAchievements(true)}/>
        <AnimatePresence>{showAchievements&&<AchievementsPanel achievements={gamification.achievements} onClose={()=>setShowAchievements(false)}/>}</AnimatePresence>

        {!isOnline&&<div className="px-4 py-2.5 bg-amber-50/80 dark:bg-amber-900/10 border-b border-amber-200/50"><p className="text-[10px] text-amber-600 flex items-center gap-1.5"><AlertCircle className="w-3.5 h-3.5"/>Offline mode<button onClick={retryConnection} className="ml-auto text-[9px] font-bold text-amber-700">Retry →</button></p></div>}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scroll-smooth scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-700 scrollbar-track-transparent">
          {messages.length===0&&(
            <motion.div initial={{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:0.5}} className="space-y-5 pt-2">
              <div className="text-center">
                <motion.div animate={{y:[0,-8,0]}} transition={{duration:3,repeat:Infinity,ease:'easeInOut'}} className="mx-auto bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-purple-500/30 mb-4 w-[72px] h-[72px]"><Bot className="w-9 h-9 text-white"/></motion.div>
                <h4 className="font-bold text-lg bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Hey there! 👋</h4>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 max-w-[300px] mx-auto leading-relaxed">Earn XP, unlock achievements, and level up while learning! 🎮</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <QuickAction icon={<BookOpen className="w-4 h-4 text-white"/>} label="Explore Syllabus" sub="Topics, units & concepts" gradient="from-blue-500 to-cyan-500" xpReward={10} onClick={()=>send('Syllabus for semester 3')} delay={0}/>
                <QuickAction icon={<Users className="w-4 h-4 text-white"/>} label="Find Faculty" sub="Who teaches what" gradient="from-emerald-500 to-teal-500" xpReward={5} onClick={()=>send('Who teaches Operating Systems?')} delay={1}/>
                <QuickAction icon={<Briefcase className="w-4 h-4 text-white"/>} label="Career Paths" sub="Roadmaps & salaries" gradient="from-indigo-500 to-blue-500" xpReward={15} onClick={()=>send('Career in data science')} delay={2}/>
                <QuickAction icon={<BarChart3 className="w-4 h-4 text-white"/>} label="My Performance" sub="Grades & analysis" gradient="from-violet-500 to-purple-500" xpReward={5} onClick={()=>send('Show my academic performance')} delay={3}/>
                <QuickAction icon={<Brain className="w-4 h-4 text-white"/>} label="Take a Quiz" sub="Test & earn XP!" gradient="from-pink-500 to-rose-500" xpReward={25} onClick={()=>send('Quiz me on deadlock')} delay={4}/>
                <QuickAction icon={<FileText className="w-4 h-4 text-white"/>} label="Study Resources" sub="Videos, notes & practice" gradient="from-orange-500 to-amber-500" xpReward={8} onClick={()=>send('Resources for machine learning')} delay={5}/>
              </div>
              {gamification.dailyXpEarned<100&&<motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.8}} className="rounded-xl p-3 bg-gradient-to-r from-amber-50/80 to-orange-50/80 dark:from-amber-900/10 dark:to-orange-900/10 border border-amber-200/50"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center"><Gift className="w-4 h-4 text-white"/></div><div className="flex-1"><p className="text-[10px] font-bold text-amber-700">Daily Goal</p><p className="text-[9px] text-amber-600">Earn 100 XP today!</p></div><p className="text-xs font-bold text-amber-600">{gamification.dailyXpEarned}/100</p></div><div className="mt-2 h-1.5 bg-amber-200 rounded-full overflow-hidden"><motion.div className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full" initial={{width:0}} animate={{width:`${Math.min(gamification.dailyXpEarned,100)}%`}}/></div></motion.div>}
              <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.6}} className="text-center"><p className="text-[9px] text-gray-400 bg-gray-100/50 dark:bg-gray-800/30 rounded-full px-4 py-1.5 inline-flex items-center gap-1"><Zap className="w-2.5 h-2.5 text-amber-400"/>I understand shortcuts: OS, ML, DBMS, DSA, CN, AI...</p></motion.div>
            </motion.div>
          )}

          <AnimatePresence>
            {messages.map(msg=>(
              <motion.div key={msg.id} initial={{opacity:0,y:8,scale:0.98}} animate={{opacity:1,y:0,scale:1}} exit={{opacity:0,scale:0.95}} transition={{duration:0.3}} className={`flex ${msg.role==='user'?'justify-end':'justify-start'}`}>
                <div className={`max-w-[92%] group ${msg.role==='user'?'rounded-2xl rounded-br-md px-4 py-2.5 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white shadow-lg shadow-purple-500/15':msg.isError?'rounded-2xl rounded-bl-md px-4 py-3 bg-rose-50/80 dark:bg-rose-900/10 text-rose-800 dark:text-rose-300 border border-rose-200/50':'rounded-2xl rounded-bl-md px-4 py-3.5 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-800 dark:text-gray-200 border border-white/60 dark:border-gray-700/40 shadow-sm hover:shadow-md transition-shadow'}`}>
                  <div className="flex items-start gap-2.5">
                    {msg.role==='assistant'&&!msg.isLoading&&<div className="mt-0.5 shrink-0">{msg.isError?<div className="w-5 h-5 rounded-lg bg-rose-100 dark:bg-rose-900/20 flex items-center justify-center"><AlertCircle className="w-3 h-3 text-rose-500"/></div>:<div className="w-5 h-5 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center">{intentIcon(msg.intent)}</div>}</div>}
                    <div className="flex-1 min-w-0">{renderMsg(msg)}</div>
                    {msg.role==='user'&&<User className="w-3.5 h-3.5 mt-0.5 text-white/40 shrink-0"/>}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={endRef}/>
        </div>

        {messages.length>0&&suggestions.length>0&&!isLoading&&<div className="px-3 py-2.5 border-t border-gray-200/50 dark:border-gray-800/50 overflow-x-auto flex gap-1.5 scrollbar-none bg-white/30 dark:bg-gray-900/30 backdrop-blur-sm">{suggestions.slice(0,4).map((s,i)=>(<SuggestionChip key={i} text={s} onClick={()=>send(s)}/>))}</div>}

        {/* Input */}
        <div className="px-4 py-3.5 border-t border-gray-200/50 dark:border-gray-800/50 bg-white/60 dark:bg-gray-900/60 backdrop-blur-sm shrink-0">
          <form onSubmit={e=>{e.preventDefault();send();}} className="flex items-center gap-2.5">
            <div className="flex-1 relative">
              <input ref={inputRef} type="text" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask anything academic..." disabled={isLoading}
                className="w-full px-4 py-3 bg-white/90 dark:bg-gray-800/90 border border-gray-200/70 dark:border-gray-700/70 rounded-2xl text-xs placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:border-purple-400/50 dark:text-white transition-all disabled:opacity-50 backdrop-blur-sm shadow-sm focus:shadow-lg pr-10"/>
              {input.trim()&&!isLoading&&<motion.div initial={{scale:0}} animate={{scale:1}} className="absolute right-3 top-1/2 -translate-y-1/2"><span className="text-[9px] text-amber-500 font-bold flex items-center gap-0.5"><Zap className="w-2.5 h-2.5"/>+5</span></motion.div>}
            </div>
            <motion.button type="submit" disabled={isLoading||!input.trim()} whileHover={{scale:1.05}} whileTap={{scale:0.95}}
              className="p-3 rounded-2xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-600 disabled:from-gray-300 disabled:to-gray-400 dark:disabled:from-gray-600 dark:disabled:to-gray-700 text-white transition-all shadow-lg shadow-purple-500/25 disabled:shadow-none">
              {isLoading?<Loader2 className="w-4 h-4 animate-spin"/>:<Send className="w-4 h-4"/>}
            </motion.button>
          </form>
          <div className="flex items-center justify-center gap-2 mt-2">
            <p className="text-[8px] text-gray-400 flex items-center gap-1"><Sparkles className="w-2.5 h-2.5 text-purple-400"/> Powered by AI</p>
            <span className="text-[8px] text-gray-300 dark:text-gray-600">·</span>
            <p className="text-[8px] text-gray-400">Level {gamification.level} · {LEVEL_TITLES[gamification.level-1]}</p>
          </div>
        </div>
      </>}
    </div>
  );
};

export default AcademicChatbot;