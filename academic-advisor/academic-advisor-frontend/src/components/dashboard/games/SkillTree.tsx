// academic-advisor-frontend/src/components/dashboard/games/SkillTree.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lock, CheckCircle, Star, Zap, ChevronRight,
  Brain, Code, BookOpen, Award, Target, Flame, Play
} from 'lucide-react';

interface SkillNode {
  id: string;
  name: string;
  type: 'prerequisite' | 'target' | 'elective';
  status: 'locked' | 'available' | 'in_progress' | 'completed' | 'mastered';
  mastery: number; // 0-100
  xp: number;
  dependencies: string[];
  semester?: number;
  grade?: string;
  children?: string[];
}

interface SkillTreeProps {
  nodes: SkillNode[];
  targetElective: string;
  onNodeClick: (node: SkillNode) => void;
  className?: string;
}

const NODE_STYLES: Record<string, { bg: string; border: string; glow: string; icon: React.ReactNode }> = {
  locked: {
    bg: 'bg-gray-200 dark:bg-gray-700',
    border: 'border-gray-300 dark:border-gray-600',
    glow: '',
    icon: <Lock className="w-5 h-5 text-gray-400" />,
  },
  available: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-400 dark:border-blue-500',
    glow: 'shadow-blue-500/20 shadow-lg',
    icon: <Play className="w-5 h-5 text-blue-500" />,
  },
  in_progress: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-400 dark:border-amber-500',
    glow: 'shadow-amber-500/20 shadow-lg animate-pulse',
    icon: <Flame className="w-5 h-5 text-amber-500" />,
  },
  completed: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-400 dark:border-green-500',
    glow: 'shadow-green-500/10 shadow-md',
    icon: <CheckCircle className="w-5 h-5 text-green-500" />,
  },
  mastered: {
    bg: 'bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20',
    border: 'border-purple-400 dark:border-purple-500',
    glow: 'shadow-purple-500/20 shadow-lg',
    icon: <Star className="w-5 h-5 text-purple-500 fill-purple-500" />,
  },
};

const MASTERY_COLORS = [
  { min: 0, color: 'bg-red-500' },
  { min: 25, color: 'bg-orange-500' },
  { min: 50, color: 'bg-amber-500' },
  { min: 75, color: 'bg-green-500' },
  { min: 90, color: 'bg-emerald-500' },
];

const getMasteryColor = (mastery: number) => {
  for (let i = MASTERY_COLORS.length - 1; i >= 0; i--) {
    if (mastery >= MASTERY_COLORS[i].min) return MASTERY_COLORS[i].color;
  }
  return MASTERY_COLORS[0].color;
};

const SkillTree: React.FC<SkillTreeProps> = ({ nodes, targetElective, onNodeClick, className = '' }) => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<SkillNode | null>(null);

  // Organize nodes into levels
  const levels = useMemo(() => {
    const prereqs = nodes.filter(n => n.type === 'prerequisite');
    const targets = nodes.filter(n => n.type === 'target');
    const electives = nodes.filter(n => n.type === 'elective');

    // Group prerequisites by semester
    const semesterGroups = new Map<number, SkillNode[]>();
    prereqs.forEach(n => {
      const sem = n.semester || 0;
      if (!semesterGroups.has(sem)) semesterGroups.set(sem, []);
      semesterGroups.get(sem)!.push(n);
    });

    const sortedSemesters = Array.from(semesterGroups.entries()).sort(([a], [b]) => a - b);

    return [
      ...sortedSemesters.map(([sem, nodes]) => ({
        label: sem > 0 ? `Semester ${sem}` : 'Foundation',
        nodes,
        type: 'prerequisite' as const,
      })),
      ...(targets.length > 0 ? [{ label: 'Core Skills', nodes: targets, type: 'target' as const }] : []),
      ...(electives.length > 0 ? [{ label: targetElective, nodes: electives, type: 'elective' as const }] : []),
    ];
  }, [nodes, targetElective]);

  const totalMastery = useMemo(() => {
    const completable = nodes.filter(n => n.type !== 'elective');
    if (completable.length === 0) return 0;
    return Math.round(completable.reduce((sum, n) => sum + n.mastery, 0) / completable.length);
  }, [nodes]);

  const completedCount = nodes.filter(n => n.status === 'completed' || n.status === 'mastered').length;

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-5 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-black flex items-center gap-2">
              <Target className="w-6 h-6" /> Skill Tree
            </h2>
            <p className="text-sm text-white/70 mt-1">Path to {targetElective}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-black">{totalMastery}%</p>
            <p className="text-xs text-white/70">{completedCount}/{nodes.length} mastered</p>
          </div>
        </div>
        <div className="mt-4 h-3 bg-white/20 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${totalMastery}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="h-full bg-white/60 rounded-full"
          />
        </div>
      </div>

      {/* Tree Levels */}
      <div className="relative">
        {levels.map((level, levelIdx) => (
          <div key={level.label} className="mb-8 last:mb-0">
            {/* Level Label */}
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white ${
                level.type === 'elective' ? 'bg-gradient-to-br from-pink-500 to-rose-600' :
                level.type === 'target' ? 'bg-gradient-to-br from-purple-500 to-indigo-600' :
                'bg-gradient-to-br from-blue-500 to-cyan-600'
              }`}>
                {levelIdx + 1}
              </div>
              <div>
                <h3 className="font-bold text-gray-900 dark:text-white text-sm">{level.label}</h3>
                <p className="text-xs text-gray-500">
                  {level.nodes.filter(n => n.status === 'completed' || n.status === 'mastered').length}/{level.nodes.length} complete
                </p>
              </div>
              {level.type === 'elective' && (
                <span className="ml-auto text-xs bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 px-2 py-0.5 rounded-full font-medium">
                  🎯 Goal
                </span>
              )}
            </div>

            {/* Connection line */}
            {levelIdx < levels.length - 1 && (
              <div className="absolute left-[15px] h-8 w-0.5 bg-gray-300 dark:bg-gray-600" style={{ top: `calc(${levelIdx + 1} * 160px - 32px)` }} />
            )}

            {/* Nodes Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 ml-11">
              {level.nodes.map((node, nodeIdx) => {
                const style = NODE_STYLES[node.status];
                const isHovered = hoveredNode === node.id;
                const isClickable = node.status !== 'locked';

                return (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: levelIdx * 0.1 + nodeIdx * 0.05 }}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    onClick={() => {
                      if (isClickable) {
                        setSelectedNode(node);
                        onNodeClick(node);
                      }
                    }}
                    className={`relative p-4 rounded-xl border-2 transition-all cursor-pointer ${style.bg} ${style.border} ${style.glow} ${
                      isClickable ? 'hover:scale-[1.03]' : 'opacity-60 cursor-not-allowed'
                    }`}
                  >
                    {/* Status icon */}
                    <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-white dark:bg-gray-800 border-2 border-current flex items-center justify-center">
                      {style.icon}
                    </div>

                    {/* Node content */}
                    <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-2 pr-4 leading-tight">
                      {node.name}
                    </h4>

                    {/* Mastery bar */}
                    <div className="mb-2">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-500">Mastery</span>
                        <span className="font-medium text-gray-700 dark:text-gray-300">{node.mastery}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${node.mastery}%` }}
                          transition={{ duration: 0.8, delay: levelIdx * 0.1 + nodeIdx * 0.05 }}
                          className={`h-full rounded-full ${getMasteryColor(node.mastery)}`}
                        />
                      </div>
                    </div>

                    {/* XP & Grade */}
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-amber-500 font-medium flex items-center gap-0.5">
                        <Zap className="w-3 h-3" /> {node.xp} XP
                      </span>
                      {node.grade && (
                        <span className={`font-bold ${
                          ['O', 'A+', 'A'].includes(node.grade) ? 'text-green-600' :
                          ['B+', 'B'].includes(node.grade) ? 'text-blue-600' :
                          'text-red-600'
                        }`}>
                          {node.grade}
                        </span>
                      )}
                    </div>

                    {/* Hover tooltip */}
                    <AnimatePresence>
                      {isHovered && node.status === 'locked' && (
                        <motion.div
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 5 }}
                          className="absolute -bottom-10 left-0 right-0 mx-auto bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg z-10 text-center"
                        >
                          Complete prerequisites first
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Selected Node Detail */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 shadow-lg"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white">{selectedNode.name}</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600 text-sm">✕</button>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Mastery</p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">{selectedNode.mastery}%</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">XP Earned</p>
                <p className="text-xl font-bold text-amber-600">{selectedNode.xp}</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Status</p>
                <p className="text-sm font-bold capitalize text-gray-900 dark:text-white">{selectedNode.status.replace('_', ' ')}</p>
              </div>
            </div>
            {selectedNode.status !== 'locked' && (
              <div className="flex gap-2">
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all">
                  <Brain className="w-4 h-4" /> Theory
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all">
                  <Award className="w-4 h-4" /> Practice
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-xl text-sm font-medium hover:shadow-lg transition-all">
                  <Code className="w-4 h-4" /> Code
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SkillTree;
