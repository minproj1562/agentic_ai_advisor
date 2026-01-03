// src/components/dashboard/sections/ResearchAreas.tsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, Plus, Edit, Trash2, Tag, Users,
  TrendingUp, Calendar, ExternalLink, Search
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { cn } from '../../../utils/cn';
import { useAuth } from '../../../contexts/AuthContext';
import { auth } from '../../../services/firebase.config'; // Import auth directly for getIdToken

interface ResearchArea {
  id: string;
  title: string;
  description: string;
  tags: string[];
  collaborators: number;
  publications: number;
  lastUpdated: Date;
  status: 'active' | 'completed' | 'planning';
  progress: number;
}

const ResearchAreas: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const { user } = useAuth();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedArea, setSelectedArea] = useState<ResearchArea | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const queryClient = useQueryClient();

  const { data: researchAreas, isLoading } = useQuery({
    queryKey: ['researchAreas', facultyId],
    queryFn: async () => {
      // Use auth.currentUser for getIdToken instead of the User type from AuthContext
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/research-areas`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      return response.json();
    }
  });

  const addResearchArea = useMutation({
    mutationFn: async (newArea: Partial<ResearchArea>) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/research-areas`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(newArea)
        }
      );
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['researchAreas', facultyId] });
      toast.success('Research area added successfully');
      setIsAddModalOpen(false);
    }
  });

  const filteredAreas = researchAreas?.filter((area: ResearchArea) =>
    area.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    area.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    area.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Research Areas
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your research focus areas and collaborations
          </p>
        </div>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Research Area
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search research areas..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Research Areas Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredAreas?.map((area: ResearchArea) => (
          <motion.div
            key={area.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6"
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {area.title}
                </h3>
                <span className={cn(
                  'inline-block px-2 py-1 text-xs font-medium rounded-full mt-2',
                  area.status === 'active' && 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
                  area.status === 'completed' && 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
                  area.status === 'planning' && 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                )}>
                  {area.status}
                </span>
              </div>
              <div className="flex gap-2">
                <button className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                  <Edit className="w-4 h-4" />
                </button>
                <button className="p-2 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {area.description}
            </p>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                <span>Progress</span>
                <span>{area.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${area.progress}%` }}
                />
              </div>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-4">
              {area.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-full"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-center">
                <Users className="w-5 h-5 mx-auto mb-1 text-gray-500 dark:text-gray-400" />
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {area.collaborators}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Collaborators</p>
              </div>
              <div className="text-center">
                <BookOpen className="w-5 h-5 mx-auto mb-1 text-gray-500 dark:text-gray-400" />
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {area.publications}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Publications</p>
              </div>
              <div className="text-center">
                <Calendar className="w-5 h-5 mx-auto mb-1 text-gray-500 dark:text-gray-400" />
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {new Date(area.lastUpdated).toLocaleDateString()}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Last Updated</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Add Research Area Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Add New Research Area
              </h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                // Handle form submission
              }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Title
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="Enter research area title"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Description
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      rows={4}
                      placeholder="Describe your research area"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="e.g., AI, Machine Learning, NLP"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Add Research Area
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ResearchAreas;