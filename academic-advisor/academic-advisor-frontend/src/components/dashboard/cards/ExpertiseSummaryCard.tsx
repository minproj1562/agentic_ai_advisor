import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  Brain,
  TrendingUp,
  Award,
  Target,
  BookOpen,
  Sparkles,
  ChevronRight,
  Info
} from 'lucide-react';
import { CVMetadata } from '../../../types/dashboard.types';
import { cn } from '../../../utils/cn';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Cell
} from 'recharts';

interface ExpertiseSummaryCardProps {
  cvMetadata: CVMetadata | null;
  expertise: string[];
}

const ExpertiseSummaryCard: React.FC<ExpertiseSummaryCardProps> = ({
  cvMetadata,
  expertise
}) => {
  const [activeTab, setActiveTab] = useState<'skills' | 'research' | 'overview'>('overview');

  const skillsData = useMemo(() => {
    if (!cvMetadata) return [];
    
    const grouped = cvMetadata.extractedSkills.reduce((acc, skill) => {
      if (!acc[skill.category]) {
        acc[skill.category] = [];
      }
      acc[skill.category].push(skill);
      return acc;
    }, {} as Record<string, typeof cvMetadata.extractedSkills>);

    return Object.entries(grouped).map(([category, skills]) => ({
      category,
      confidence: Math.round(
        skills.reduce((sum, skill) => sum + skill.confidence, 0) / skills.length
      ),
      count: skills.length,
      skills
    }));
  }, [cvMetadata]);

  const radarData = useMemo(() => {
    if (!cvMetadata) return [];
    return cvMetadata.extractedSkills
      .slice(0, 6)
      .map(skill => ({
        skill: skill.name,
        value: skill.confidence,
        fullMark: 100
      }));
  }, [cvMetadata]);

  const barData = useMemo(() => {
    if (!cvMetadata) return [];
    return cvMetadata.extractedSkills
      .slice(0, 8)
      .map(skill => ({
        name: skill.name.length > 10 ? skill.name.substring(0, 10) + '...' : skill.name,
        fullName: skill.name,
        value: skill.confidence,
        category: skill.category
      }));
  }, [cvMetadata]);

  const getColorByCategory = (category: string) => {
    const colors = {
      'Technical': '#3b82f6',
      'Research': '#8b5cf6',
      'Soft Skill': '#10b981'
    };
    return colors[category as keyof typeof colors] || '#6b7280';
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload[0]) {
      return (
        <div className="bg-white dark:bg-gray-800 p-2 rounded shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-900 dark:text-white">
            {payload[0].payload.fullName || payload[0].payload.skill || payload[0].name}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Confidence: {payload[0].value}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (!cvMetadata && expertise.length === 0) {
    return (
      <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 transition-colors duration-200')}>
        {/* Removed getThemeTransition() and added default transition */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Expertise Summary
        </h3>
        <div className="text-center py-8">
          <Brain className="w-12 h-12 mx-auto text-gray-400" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Upload your CV to see expertise analysis
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 transition-colors duration-200')}>
      {/* Removed getThemeTransition() and added default transition */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Expertise Summary
        </h3>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-yellow-500" />
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            AI Analyzed
          </span>
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        {['overview', 'skills', 'research'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={cn(
              'flex-1 py-2 px-3 rounded-lg text-sm font-medium capitalize transition-colors',
              activeTab === tab
                ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="min-h-[300px]">
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Overall Expertise Level
                </span>
                <Award className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div className="flex items-end gap-2">
                <span className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                  Expert
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400 pb-1">
                  Level 4/5
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <motion.div
                  className="h-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: '80%' }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Key Strengths
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {expertise.slice(0, 4).map((item, index) => (
                  <motion.div
                    key={item}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <Target className="w-4 h-4 text-indigo-500" />
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {item}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {cvMetadata?.extractedSkills.length || 0}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Skills</p>
              </div>
              <div className="text-center p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                  {cvMetadata?.researchAreas.length || 0}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Research</p>
              </div>
              <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-lg font-bold text-green-600 dark:text-green-400">
                  {cvMetadata?.publications || 0}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Papers</p>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'skills' && cvMetadata && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#e5e7eb" strokeDasharray="3 3" className="dark:opacity-20" />
                  <PolarAngleAxis dataKey="skill" tick={{ fontSize: 10 }} className="text-gray-600 dark:text-gray-400" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} className="text-gray-600 dark:text-gray-400" />
                  <Radar name="Skills" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                  <Tooltip content={<CustomTooltip />} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-2">
              {skillsData.map((category, index) => (
                <motion.div
                  key={category.category}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {category.category}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {category.count} skills
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <motion.div
                        className="h-2 rounded-full"
                        style={{ backgroundColor: getColorByCategory(category.category) }}
                        initial={{ width: 0 }}
                        animate={{ width: `${category.confidence}%` }}
                        transition={{ duration: 0.5, delay: index * 0.1 }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      {category.confidence}%
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'research' && cvMetadata && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <div>
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Research Focus Areas
              </h4>
              <div className="space-y-2">
                {cvMetadata.researchAreas.map((area, index) => (
                  <motion.div
                    key={area}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg group cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {area}
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 group-hover:translate-x-1 transition-all" />
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Academic Profile
                </span>
                <Info className="w-4 h-4 text-gray-400" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    Experience
                  </span>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {cvMetadata.experience}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    Publications
                  </span>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {cvMetadata.publications} papers
                  </span>
                </div>
              </div>
            </div>

            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} className="text-gray-600 dark:text-gray-400" />
                  <YAxis tick={{ fontSize: 10 }} className="text-gray-600 dark:text-gray-400" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {barData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getColorByCategory(entry.category)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ExpertiseSummaryCard;