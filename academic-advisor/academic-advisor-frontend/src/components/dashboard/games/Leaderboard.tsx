// academic-advisor-frontend/src/components/dashboard/games/Leaderboard.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Flame, Zap, Medal, Crown, TrendingUp, Clock, Star } from 'lucide-react';

interface LeaderboardEntry {
  rank: number;
  name: string;
  avatar?: string;
  xp: number;
  level: number;
  streak: number;
  badges: number;
  isCurrentUser?: boolean;
}

interface LeaderboardProps {
  entries?: LeaderboardEntry[];
  currentUserXP?: number;
  currentUserRank?: number;
  className?: string;
}

const RANK_STYLES: Record<number, { bg: string; icon: React.ReactNode; ring: string }> = {
  1: { bg: 'bg-gradient-to-r from-amber-400 to-yellow-500', icon: <Crown className="w-5 h-5 text-white" />, ring: 'ring-2 ring-amber-400/50' },
  2: { bg: 'bg-gradient-to-r from-gray-300 to-gray-400', icon: <Medal className="w-5 h-5 text-white" />, ring: 'ring-2 ring-gray-300/50' },
  3: { bg: 'bg-gradient-to-r from-amber-600 to-orange-700', icon: <Medal className="w-5 h-5 text-white" />, ring: 'ring-2 ring-amber-600/50' },
};

// Generate sample data if none provided
const generateSampleData = (currentXP: number = 0): LeaderboardEntry[] => {
  const names = [
    'Arjun S.', 'Priya M.', 'Rahul K.', 'Sneha P.', 'Vikram D.',
    'Ananya R.', 'Karthik V.', 'Divya S.', 'Rohan T.', 'Meera J.',
    'Aditya B.', 'Neha G.', 'Siddharth L.', 'Pooja N.', 'Amit H.',
  ];
  const entries: LeaderboardEntry[] = names.map((name, i) => ({
    rank: i + 1,
    name,
    xp: Math.max(100, 3500 - i * 200 + Math.floor(Math.random() * 100)),
    level: Math.max(1, 8 - Math.floor(i / 2)),
    streak: Math.max(0, 14 - i + Math.floor(Math.random() * 5)),
    badges: Math.max(0, 12 - i + Math.floor(Math.random() * 3)),
    isCurrentUser: false,
  }));

  // Insert current user
  const userEntry: LeaderboardEntry = {
    rank: 0, name: 'You', xp: currentXP || 850,
    level: Math.floor((currentXP || 850) / 500) + 1,
    streak: 3, badges: 2, isCurrentUser: true,
  };
  entries.push(userEntry);
  entries.sort((a, b) => b.xp - a.xp);
  entries.forEach((e, i) => e.rank = i + 1);
  return entries.slice(0, 15);
};

const Leaderboard: React.FC<LeaderboardProps> = ({ entries, currentUserXP = 0, className = '' }) => {
  const [filter, setFilter] = useState<'xp' | 'streak' | 'badges'>('xp');
  const data = entries || generateSampleData(currentUserXP);

  const sorted = [...data].sort((a, b) => {
    if (filter === 'streak') return b.streak - a.streak;
    if (filter === 'badges') return b.badges - a.badges;
    return b.xp - a.xp;
  }).map((e, i) => ({ ...e, rank: i + 1 }));

  const currentUser = sorted.find(e => e.isCurrentUser);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 rounded-2xl p-5 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black flex items-center gap-2">
              <Trophy className="w-6 h-6" /> Leaderboard
            </h2>
            <p className="text-sm text-white/70 mt-1">Compete with your classmates</p>
          </div>
          {currentUser && (
            <div className="text-right">
              <p className="text-3xl font-black">#{currentUser.rank}</p>
              <p className="text-xs text-white/70">{currentUser.xp.toLocaleString()} XP</p>
            </div>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1">
        {[
          { id: 'xp' as const, label: '⚡ XP', icon: Zap },
          { id: 'streak' as const, label: '🔥 Streak', icon: Flame },
          { id: 'badges' as const, label: '🏅 Badges', icon: Star },
        ].map(t => (
          <button key={t.id} onClick={() => setFilter(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              filter === t.id ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-500'
            }`}>{t.label}</button>
        ))}
      </div>

      {/* Podium (Top 3) */}
      <div className="flex items-end justify-center gap-3 py-4">
        {[sorted[1], sorted[0], sorted[2]].filter(Boolean).map((entry, i) => {
          const heights = ['h-20', 'h-28', 'h-16'];
          const positions = [1, 0, 2]; // 2nd, 1st, 3rd
          const rank = positions[i] + 1;
          const style = RANK_STYLES[rank] || RANK_STYLES[3];
          return (
            <motion.div key={entry.rank} initial={{ y: 30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.15 }}
              className="flex flex-col items-center">
              <div className={`w-12 h-12 rounded-full ${style.bg} flex items-center justify-center mb-2 ${style.ring} shadow-lg ${entry.isCurrentUser ? 'border-2 border-white' : ''}`}>
                {style.icon}
              </div>
              <p className={`text-xs font-bold mb-1 ${entry.isCurrentUser ? 'text-amber-600' : 'text-gray-900 dark:text-white'}`}>
                {entry.name}
              </p>
              <p className="text-[10px] text-gray-500 mb-2">{entry.xp.toLocaleString()} XP</p>
              <div className={`${heights[i]} w-16 rounded-t-xl ${style.bg} flex items-center justify-center shadow-inner`}>
                <span className="text-white font-black text-lg">#{rank}</span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Full list */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {sorted.map((entry, i) => (
            <motion.div key={entry.rank} initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
              className={`flex items-center gap-3 px-4 py-3 transition-colors ${
                entry.isCurrentUser ? 'bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-500' : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}>
              {/* Rank */}
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black flex-shrink-0 ${
                entry.rank <= 3 ? `${RANK_STYLES[entry.rank]?.bg || 'bg-gray-200'} text-white` :
                'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}>
                {entry.rank}
              </div>

              {/* Name + Level */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate ${entry.isCurrentUser ? 'text-indigo-700 dark:text-indigo-300' : 'text-gray-900 dark:text-white'}`}>
                  {entry.name} {entry.isCurrentUser && '(You)'}
                </p>
                <p className="text-xs text-gray-500">Level {entry.level}</p>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-4 text-xs">
                <span className={`font-bold flex items-center gap-1 ${filter === 'xp' ? 'text-amber-600' : 'text-gray-400'}`}>
                  <Zap className="w-3 h-3" /> {entry.xp.toLocaleString()}
                </span>
                <span className={`font-medium flex items-center gap-1 ${filter === 'streak' ? 'text-orange-500' : 'text-gray-400'}`}>
                  <Flame className="w-3 h-3" /> {entry.streak}d
                </span>
                <span className={`font-medium flex items-center gap-1 ${filter === 'badges' ? 'text-purple-500' : 'text-gray-400'}`}>
                  <Star className="w-3 h-3" /> {entry.badges}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Leaderboard;
