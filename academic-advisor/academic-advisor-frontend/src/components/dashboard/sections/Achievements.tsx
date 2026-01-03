// src/components/dashboard/sections/Achievements.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, Award, Medal, Star, Target, TrendingUp,
  Calendar, Plus, ExternalLink, Filter, Download,
  Share2, MoreVertical, Edit, Trash2, Eye, CheckCircle, X, FileText
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config';
import toast from 'react-hot-toast';
import { CSVLink } from 'react-csv';
import { useQueryClient, useQuery, useMutation, QueryKey } from '@tanstack/react-query';

interface Achievement {
  id: string;
  title: string;
  description: string;
  date: Date;
  category: 'award' | 'certification' | 'milestone' | 'recognition' | 'grant';
  icon?: string;
  organization?: string;
  url?: string;
  amount?: number;
  collaborators?: string[];
  tags: string[];
  visibility: 'public' | 'private';
  verified: boolean;
  impact_score?: number;
  attachments?: Array<{
    name: string;
    url: string;
    type: string;
  }>;
}

interface AchievementFormData {
  title: string;
  description: string;
  category: Achievement['category'];
  organization: string;
  date: string;
  url?: string;
  amount?: number;
  tags: string[];
  visibility: 'public' | 'private';
}

const Achievements: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'timeline' | 'table'>('grid');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);
  const [sortBy, setSortBy] = useState<'date' | 'impact' | 'category'>('date');
  const [filterTags, setFilterTags] = useState<string[]>([]);
  const queryClient = useQueryClient();

  const { data: achievements, isLoading, error } = useQuery({
    queryKey: ['achievements', facultyId, selectedCategory, sortBy],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/achievements?category=${selectedCategory}&sort=${sortBy}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch achievements');
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  });

  const { data: analytics } = useQuery({
    queryKey: ['achievements-analytics', facultyId],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/achievements/analytics`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    }
  });

  const addAchievement = useMutation({
    mutationFn: async (data: AchievementFormData) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/achievements`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        }
      );
      if (!response.ok) throw new Error('Failed to add achievement');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['achievements', facultyId] as QueryKey });
      toast.success('Achievement added successfully');
      setIsAddModalOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const deleteAchievement = useMutation({
    mutationFn: async (achievementId: string) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `http://localhost:8000/api/v1/faculty/${facultyId}/achievements/${achievementId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (!response.ok) throw new Error('Failed to delete achievement');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['achievements', facultyId] as QueryKey });
      toast.success('Achievement deleted');
    },
  });

  const categories = [
    { 
      id: 'all', 
      label: 'All', 
      icon: Trophy, 
      color: 'from-gray-500 to-gray-600',
      count: achievements?.length || 0
    },
    { 
      id: 'award', 
      label: 'Awards', 
      icon: Award, 
      color: 'from-yellow-500 to-yellow-600',
      count: achievements?.filter((a: Achievement) => a.category === 'award').length || 0
    },
    { 
      id: 'certification', 
      label: 'Certifications', 
      icon: Medal, 
      color: 'from-blue-500 to-blue-600',
      count: achievements?.filter((a: Achievement) => a.category === 'certification').length || 0
    },
    { 
      id: 'milestone', 
      label: 'Milestones', 
      icon: Target, 
      color: 'from-green-500 to-green-600',
      count: achievements?.filter((a: Achievement) => a.category === 'milestone').length || 0
    },
    { 
      id: 'recognition', 
      label: 'Recognition', 
      icon: Star, 
      color: 'from-purple-500 to-purple-600',
      count: achievements?.filter((a: Achievement) => a.category === 'recognition').length || 0
    }
  ];

  const filteredAchievements = useMemo(() => {
    let filtered = achievements || [];
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((a: Achievement) => a.category === selectedCategory);
    }
    
    if (filterTags.length > 0) {
      filtered = filtered.filter((a: Achievement) => 
        a.tags.some(tag => filterTags.includes(tag))
      );
    }
    
    return filtered;
  }, [achievements, selectedCategory, filterTags]);

  const exportData = useMemo(() => {
    return filteredAchievements.map((achievement: Achievement) => ({
      Title: achievement.title,
      Category: achievement.category,
      Organization: achievement.organization,
      Date: format(new Date(achievement.date), 'yyyy-MM-dd'),
      'Impact Score': achievement.impact_score,
      Verified: achievement.verified ? 'Yes' : 'No'
    }));
  }, [filteredAchievements]);

  const getIconForCategory = (category: string) => {
    const categoryObj = categories.find(c => c.id === category);
    return categoryObj?.icon || Trophy;
  };

  const getColorForCategory = (category: string) => {
    const categoryObj = categories.find(c => c.id === category);
    return categoryObj?.color || 'from-gray-500 to-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">
            Achievements & Recognition
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track your professional accomplishments and milestones
          </p>
        </div>
        <div className="flex gap-3">
          <CSVLink
            data={exportData}
            filename={`achievements-${format(new Date(), 'yyyy-MM-dd')}.csv`}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
          >
            <Download className="w-5 h-5" />
            Export
          </CSVLink>
          <button 
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 transition-all transform hover:scale-105 shadow-lg"
          >
            <Plus className="w-5 h-5" />
            Add Achievement
          </button>
        </div>
      </div>

      {/* Analytics Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 p-6 rounded-xl"
          >
            <Trophy className="w-8 h-8 text-yellow-600 dark:text-yellow-400 mb-2" />
            <p className="text-3xl font-bold text-yellow-900 dark:text-yellow-100">
              {analytics.total_achievements}
            </p>
            <p className="text-sm text-yellow-700 dark:text-yellow-300">Total Achievements</p>
            <div className="mt-2 flex items-center text-xs text-green-600 dark:text-green-400">
              <TrendingUp className="w-3 h-3 mr-1" />
              +{analytics.growth_rate}% this year
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-6 rounded-xl"
          >
            <Star className="w-8 h-8 text-blue-600 dark:text-blue-400 mb-2" />
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
              {analytics.verified_count}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">Verified</p>
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              {((analytics.verified_count / analytics.total_achievements) * 100).toFixed(0)}% verification rate
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 p-6 rounded-xl"
          >
            <TrendingUp className="w-8 h-8 text-green-600 dark:text-green-400 mb-2" />
            <p className="text-3xl font-bold text-green-900 dark:text-green-100">
              {analytics.avg_impact_score.toFixed(1)}
            </p>
            <p className="text-sm text-green-700 dark:text-green-300">Avg Impact Score</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-6 rounded-xl"
          >
            <Calendar className="w-8 h-8 text-purple-600 dark:text-purple-400 mb-2" />
            <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
              {analytics.this_year_count}
            </p>
            <p className="text-sm text-purple-700 dark:text-purple-300">This Year</p>
          </motion.div>
        </div>
      )}

      {/* Filters and View Controls */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        {/* Category Filters */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-xl transition-all whitespace-nowrap',
                  selectedCategory === category.id
                    ? 'bg-gradient-to-r text-white shadow-lg transform scale-105'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:shadow-md'
                )}
                style={{
                  backgroundImage: selectedCategory === category.id 
                    ? `linear-gradient(to right, ${category.color.split(' ')[1]}, ${category.color.split(' ')[3]})` 
                    : undefined
                }}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{category.label}</span>
                <span className={cn(
                  'px-2 py-0.5 rounded-full text-xs',
                  selectedCategory === category.id
                    ? 'bg-white/20'
                    : 'bg-gray-200 dark:bg-gray-600'
                )}>
                  {category.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* View Mode and Sort */}
        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
          >
            <option value="date">Sort by Date</option>
            <option value="impact">Sort by Impact</option>
            <option value="category">Sort by Category</option>
          </select>
          
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {(['grid', 'timeline', 'table'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  'px-3 py-1 rounded-md text-sm font-medium capitalize transition-colors',
                  viewMode === mode
                    ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                )}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Achievement Display */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredAchievements?.map((achievement: Achievement, index: number) => {
              const Icon = getIconForCategory(achievement.category);
              return (
                <motion.div
                  key={achievement.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all group"
                >
                  <div className={`h-2 bg-gradient-to-r ${getColorForCategory(achievement.category)}`} />
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className={`p-3 rounded-lg bg-gradient-to-r ${getColorForCategory(achievement.category)} bg-opacity-10`}>
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                      <div className="flex gap-2">
                        {achievement.verified && (
                          <div className="p-1.5 bg-green-100 dark:bg-green-900/30 rounded-full">
                            <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                          </div>
                        )}
                        <div className="relative group/menu">
                          <button className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                            <MoreVertical className="w-5 h-5 text-gray-500" />
                          </button>
                          <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-xl hidden group-hover/menu:block z-10">
                            <button 
                              onClick={() => setSelectedAchievement(achievement)}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
                            >
                              <Eye className="w-4 h-4" />
                              View Details
                            </button>
                            <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                              <Edit className="w-4 h-4" />
                              Edit
                            </button>
                            <button className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                              <Share2 className="w-4 h-4" />
                              Share
                            </button>
                            <button 
                              onClick={() => deleteAchievement.mutate(achievement.id)}
                              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                      {achievement.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                      {achievement.description}
                    </p>

                    {achievement.impact_score && (
                      <div className="mb-3">
                        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                          <span>Impact Score</span>
                          <span>{achievement.impact_score}/100</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${achievement.impact_score}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {achievement.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {achievement.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full"
                          >
                            #{tag}
                          </span>
                        ))}
                        {achievement.tags.length > 3 && (
                          <span className="px-2 py-1 text-xs text-gray-500">
                            +{achievement.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-700">
                      <span className="font-medium">{achievement.organization}</span>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDistanceToNow(new Date(achievement.date), { addSuffix: true })}
                      </div>
                    </div>

                    {achievement.url && (
                      <a
                        href={achievement.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-3 flex items-center gap-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300"
                      >
                        <ExternalLink className="w-4 h-4" />
                        View Certificate
                      </a>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {viewMode === 'timeline' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Achievement Timeline
          </h3>
          <div className="relative">
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-yellow-500 via-orange-500 to-red-500" />
            {filteredAchievements?.map((achievement: Achievement, index: number) => (
              <motion.div
                key={achievement.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex items-start mb-8 group"
              >
                <div className={`absolute left-5 w-6 h-6 rounded-full bg-gradient-to-r ${getColorForCategory(achievement.category)} border-4 border-white dark:border-gray-800 shadow-lg`} />
                <div className="ml-16 flex-1">
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                          {format(new Date(achievement.date), 'MMMM d, yyyy')}
                        </p>
                        <h4 className="font-semibold text-gray-900 dark:text-white text-lg">
                          {achievement.title}
                        </h4>
                      </div>
                      {achievement.verified && (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      {achievement.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className="font-medium">{achievement.organization}</span>
                      <span className="px-2 py-1 bg-gray-200 dark:bg-gray-600 rounded-full capitalize">
                        {achievement.category}
                      </span>
                      {achievement.impact_score && (
                        <span className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-yellow-500" />
                          Impact: {achievement.impact_score}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {viewMode === 'table' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Achievement
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Organization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Impact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredAchievements?.map((achievement: Achievement, index: number) => (
                  <motion.tr
                    key={achievement.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className={`p-2 rounded-lg bg-gradient-to-r ${getColorForCategory(achievement.category)} bg-opacity-10 mr-3`}>
                          {React.createElement(getIconForCategory(achievement.category), {
                            className: 'w-5 h-5 text-gray-700 dark:text-gray-300'
                          })}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {achievement.title}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 max-w-xs truncate">
                            {achievement.description}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full capitalize">
                        {achievement.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {achievement.organization}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {format(new Date(achievement.date), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {achievement.impact_score ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{ width: `${achievement.impact_score}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600 dark:text-gray-400">
                            {achievement.impact_score}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {achievement.verified ? (
                        <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                          <CheckCircle className="w-4 h-4" />
                          Verified
                        </span>
                      ) : (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button 
                          onClick={() => setSelectedAchievement(achievement)}
                          className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => deleteAchievement.mutate(achievement.id)}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Achievement Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <AchievementModal
            onClose={() => setIsAddModalOpen(false)}
            onSubmit={addAchievement.mutate}
            isLoading={addAchievement.isPending}
          />
        )}
      </AnimatePresence>

      {/* Achievement Detail Modal */}
      <AnimatePresence>
        {selectedAchievement && (
          <AchievementDetailModal
            achievement={selectedAchievement}
            onClose={() => setSelectedAchievement(null)}
          />
        )}
      </AnimatePresence>

      {/* Empty State */}
      {filteredAchievements?.length === 0 && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl">
          <Trophy className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No achievements found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {selectedCategory === 'all'
              ? 'Start tracking your achievements by adding your first one'
              : `No ${selectedCategory}s found. Try a different category.`
            }
          </p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 transition-all"
          >
            <Plus className="w-5 h-5" />
            Add Your First Achievement
          </button>
        </div>
      )}
    </div>
  );
};

// Achievement Modal Component
const AchievementModal: React.FC<{
  onClose: () => void;
  onSubmit: (data: AchievementFormData) => void;
  isLoading: boolean;
}> = ({ onClose, onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<AchievementFormData>({
    title: '',
    description: '',
    category: 'award',
    organization: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    url: '',
    tags: [],
    visibility: 'public'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
            Add New Achievement
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Title *
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Best Research Paper Award"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description *
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              rows={4}
              placeholder="Describe your achievement..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category *
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              >
                <option value="award">Award</option>
                <option value="certification">Certification</option>
                <option value="milestone">Milestone</option>
                <option value="recognition">Recognition</option>
                <option value="grant">Grant</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Date *
              </label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Organization *
            </label>
            <input
              type="text"
              required
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              placeholder="Organization/Institution name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Certificate URL (optional)
            </label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Visibility
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={formData.visibility === 'public'}
                  onChange={() => setFormData({ ...formData, visibility: 'public' })}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Public</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  checked={formData.visibility === 'private'}
                  onChange={() => setFormData({ ...formData, visibility: 'private' })}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Private</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-lg hover:from-yellow-700 hover:to-orange-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Achievement'
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

// Achievement Detail Modal Component
const AchievementDetailModal: React.FC<{
  achievement: Achievement;
  onClose: () => void;
}> = ({ achievement, onClose }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-start gap-4">
            <div className={`p-4 rounded-xl bg-gradient-to-r ${getColorForCategory(achievement.category)} bg-opacity-10`}>
              {React.createElement(getIconForCategory(achievement.category), {
                className: 'w-8 h-8 text-gray-700 dark:text-gray-300'
              })}
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {achievement.title}
              </h3>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm capitalize">
                  {achievement.category}
                </span>
                {achievement.verified && (
                  <span className="flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    Verified
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Description
            </h4>
            <p className="text-gray-900 dark:text-white">
              {achievement.description}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Organization
              </h4>
              <p className="text-gray-900 dark:text-white">
                {achievement.organization}
              </p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Date
              </h4>
              <p className="text-gray-900 dark:text-white">
                {format(new Date(achievement.date), 'MMMM d, yyyy')}
              </p>
            </div>
          </div>

          {achievement.impact_score && (
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Impact Score
              </h4>
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full"
                    style={{ width: `${achievement.impact_score}%` }}
                  />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {achievement.impact_score}/100
                </span>
              </div>
            </div>
          )}

          {achievement.collaborators && achievement.collaborators.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Collaborators
              </h4>
              <div className="flex flex-wrap gap-2">
                {achievement.collaborators.map((collab, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-full text-sm"
                  >
                    {collab}
                  </span>
                ))}
              </div>
            </div>
          )}

          {achievement.tags.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Tags
              </h4>
              <div className="flex flex-wrap gap-2">
                {achievement.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {achievement.attachments && achievement.attachments.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                Attachments
              </h4>
              <div className="space-y-2">
                {achievement.attachments.map((attachment, idx) => (
                  <a
                    key={idx}
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                  >
                    <FileText className="w-5 h-5 text-gray-500" />
                    <span className="flex-1 text-sm text-gray-900 dark:text-white">
                      {attachment.name}
                    </span>
                    <ExternalLink className="w-4 h-4 text-gray-400" />
                  </a>
                ))}
              </div>
            </div>
          )}

          {achievement.url && (
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <a
                href={achievement.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <ExternalLink className="w-5 h-5" />
                View Certificate
              </a>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

function getColorForCategory(category: string): string {
  const colors = {
    'award': 'from-yellow-500 to-yellow-600',
    'certification': 'from-blue-500 to-blue-600',
    'milestone': 'from-green-500 to-green-600',
    'recognition': 'from-purple-500 to-purple-600',
    'grant': 'from-pink-500 to-pink-600'
  };
  return colors[category as keyof typeof colors] || 'from-gray-500 to-gray-600';
}

function getIconForCategory(category: string) {
  const icons = {
    'award': Award,
    'certification': Medal,
    'milestone': Target,
    'recognition': Star,
    'grant': Trophy
  };
  return icons[category as keyof typeof icons] || Trophy;
}

export default Achievements;