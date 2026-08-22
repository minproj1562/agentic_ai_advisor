// src/components/dashboard/sections/Publications.tsx
import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, FileText, Eye, Download, ExternalLink, Plus,
  Search, Filter, Star, TrendingUp, Users, Calendar,
  Award, Target, BarChart3, ChevronDown, Edit, Trash2,
  Share2, Link2, Copy, CheckCircle, AlertCircle, Clock,
  Globe, Quote, Bookmark, Heart, MessageSquare, Upload,
  X
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, formatDistanceToNow } from 'date-fns';
import { cn } from '../../../utils/cn';
import { auth } from '../../../services/firebase.config'; // Use auth directly
import toast from 'react-hot-toast';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { CSVLink } from 'react-csv';

interface Publication {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  conference?: string;
  year: number;
  month: string;
  volume?: string;
  issue?: string;
  pages?: string;
  doi?: string;
  isbn?: string;
  url?: string;
  pdfUrl?: string;
  abstract: string;
  keywords: string[];
  type: 'journal' | 'conference' | 'book' | 'chapter' | 'preprint';
  status: 'published' | 'accepted' | 'submitted' | 'under_review' | 'draft';
  citations: number;
  views: number;
  downloads: number;
  impactFactor?: number;
  quartile?: 'Q1' | 'Q2' | 'Q3' | 'Q4';
  indexed: string[]; // Scopus, WoS, PubMed, etc.
  collaborators: Array<{
    name: string;
    affiliation: string;
    email?: string;
  }>;
  funding?: Array<{
    agency: string;
    grantNumber: string;
    amount?: number;
  }>;
  metrics: {
    altmetricScore?: number;
    readership?: number;
    socialMedia?: {
      twitter: number;
      facebook: number;
      linkedin: number;
    };
  };
  createdAt: Date;
  updatedAt: Date;
}

interface PublicationMetrics {
  totalPublications: number;
  totalCitations: number;
  hIndex: number;
  i10Index: number;
  avgImpactFactor: number;
  citationsThisYear: number;
  publicationsThisYear: number;
  citationsPerYear: Array<{
    year: number;
    citations: number;
  }>;
  typeDistribution: Array<{
    type: string;
    count: number;
  }>;
  topCited: Publication[];
  recentPublications: Publication[];
  collaborationNetwork: Array<{
    name: string;
    count: number;
  }>;
}

const Publications: React.FC<{ facultyId: string }> = ({ facultyId }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'citations' | 'impact'>('date');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline'>('grid');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedPublication, setSelectedPublication] = useState<Publication | null>(null);
  const [showMetrics, setShowMetrics] = useState(true);
  const queryClient = useQueryClient();

  // Fetch publications
  const { data: publications, isLoading } = useQuery({
    queryKey: ['publications', facultyId, selectedType, selectedStatus, sortBy],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/publications?type=${selectedType}&status=${selectedStatus}&sort=${sortBy}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch publications');
      return response.json() as Promise<Publication[]>;
    },
    staleTime: 5 * 60 * 1000
  });

  // Fetch metrics
  const { data: metrics } = useQuery({
    queryKey: ['publication-metrics', facultyId],
    queryFn: async () => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/publications/metrics`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to fetch metrics');
      return response.json() as Promise<PublicationMetrics>;
    }
  });

  // Add publication mutation
  const addPublication = useMutation({
    mutationFn: async (data: Partial<Publication>) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/publications`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(data)
        }
      );
      if (!response.ok) throw new Error('Failed to add publication');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications', facultyId] });
      queryClient.invalidateQueries({ queryKey: ['publication-metrics', facultyId] });
      toast.success('Publication added successfully');
      setIsAddModalOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    }
  });

  // Delete publication mutation
  const deletePublication = useMutation({
    mutationFn: async (publicationId: string) => {
      const token = await auth.currentUser?.getIdToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/faculty/${facultyId}/publications/${publicationId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (!response.ok) throw new Error('Failed to delete publication');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications', facultyId] });
      toast.success('Publication deleted');
    }
  });


  // Filter publications
  const filteredPublications = useMemo(() => {
    if (!publications) return [];
    
    return publications.filter(pub => {
      const matchesSearch = pub.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          pub.authors.some(a => a.toLowerCase().includes(searchQuery.toLowerCase())) ||
                          pub.journal.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesType = selectedType === 'all' || pub.type === selectedType;
      const matchesStatus = selectedStatus === 'all' || pub.status === selectedStatus;
      
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [publications, searchQuery, selectedType, selectedStatus]);

  const publicationTypes = [
    { id: 'all', label: 'All Publications', icon: BookOpen, color: 'from-gray-500 to-gray-600' },
    { id: 'journal', label: 'Journal Articles', icon: FileText, color: 'from-blue-500 to-blue-600' },
    { id: 'conference', label: 'Conference Papers', icon: Users, color: 'from-purple-500 to-purple-600' },
    { id: 'book', label: 'Books', icon: BookOpen, color: 'from-green-500 to-green-600' },
    { id: 'chapter', label: 'Book Chapters', icon: FileText, color: 'from-orange-500 to-orange-600' },
    { id: 'preprint', label: 'Preprints', icon: FileText, color: 'from-pink-500 to-pink-600' }
  ];

  const getTypeIcon = (type: string) => {
    const typeObj = publicationTypes.find(t => t.id === type);
    return typeObj?.icon || FileText;
  };

  const getTypeColor = (type: string) => {
    const typeObj = publicationTypes.find(t => t.id === type);
    return typeObj?.color || 'from-gray-500 to-gray-600';
  };

  const getStatusBadge = (status: Publication['status']) => {
    const statusConfig = {
      published: { color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', label: 'Published' },
      accepted: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', label: 'Accepted' },
      submitted: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', label: 'Submitted' },
      under_review: { color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300', label: 'Under Review' },
      draft: { color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', label: 'Draft' }
    };
    
    const config = statusConfig[status];
    return (
      <span className={cn('px-2 py-1 text-xs font-medium rounded-full', config.color)}>
        {config.label}
      </span>
    );
  };

  const chartColors = {
    primary: '#6366f1',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    purple: '#8b5cf6'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Research Publications
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and track your research output and impact
          </p>
        </div>
        
        <div className="flex gap-3">
          <CSVLink
            data={filteredPublications.map(p => ({
              Title: p.title,
              Authors: p.authors.join(', '),
              Journal: p.journal,
              Year: p.year,
              Citations: p.citations,
              Type: p.type,
              Status: p.status
            }))}
            filename={`publications-${format(new Date(), 'yyyy-MM-dd')}.csv`}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-all"
          >
            <Download className="w-5 h-5" />
            Export
          </CSVLink>
          
          <button 
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
          >
            <Plus className="w-5 h-5" />
            Add Publication
          </button>
        </div>
      </div>

      {/* Metrics Dashboard */}
      {showMetrics && metrics && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 p-6 rounded-xl border border-blue-200 dark:border-blue-800">
            <BookOpen className="w-8 h-8 text-blue-600 dark:text-blue-400 mb-2" />
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
              {metrics.totalPublications}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">Total Publications</p>
            <div className="mt-2 text-xs text-green-600 dark:text-green-400">
              +{metrics.publicationsThisYear} this year
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 p-6 rounded-xl border border-purple-200 dark:border-purple-800">
            <Quote className="w-8 h-8 text-purple-600 dark:text-purple-400 mb-2" />
            <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
              {metrics.totalCitations}
            </p>
            <p className="text-sm text-purple-700 dark:text-purple-300">Total Citations</p>
            <div className="mt-2 text-xs text-green-600 dark:text-green-400">
              +{metrics.citationsThisYear} this year
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 p-6 rounded-xl border border-green-200 dark:border-green-800">
            <Award className="w-8 h-8 text-green-600 dark:text-green-400 mb-2" />
            <p className="text-3xl font-bold text-green-900 dark:text-green-100">
              {metrics.hIndex}
            </p>
            <p className="text-sm text-green-700 dark:text-green-300">H-Index</p>
            <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              i10-Index: {metrics.i10Index}
            </p>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 p-6 rounded-xl border border-orange-200 dark:border-orange-800">
            <TrendingUp className="w-8 h-8 text-orange-600 dark:text-orange-400 mb-2" />
            <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
              {metrics.avgImpactFactor.toFixed(2)}
            </p>
            <p className="text-sm text-orange-700 dark:text-orange-300">Avg Impact Factor</p>
          </div>

          <div className="bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 p-6 rounded-xl border border-indigo-200 dark:border-indigo-800">
            <BarChart3 className="w-8 h-8 text-indigo-600 dark:text-indigo-400 mb-2" />
            <p className="text-3xl font-bold text-indigo-900 dark:text-indigo-100">
              {metrics.topCited.length > 0 ? metrics.topCited[0].citations : 0}
            </p>
            <p className="text-sm text-indigo-700 dark:text-indigo-300">Top Cited Paper</p>
          </div>
        </motion.div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Citations Over Time */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Citations Over Time
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={metrics?.citationsPerYear || []}>
              <defs>
                <linearGradient id="colorCitations" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="citations"
                stroke={chartColors.primary}
                strokeWidth={2}
                fill="url(#colorCitations)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Publication Type Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Publication Types
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={metrics?.typeDistribution || []}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="count"
                label={(entry: any) => entry.type}
              >
                {metrics?.typeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={Object.values(chartColors)[index % 6]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search publications, authors, journals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            {publicationTypes.map(type => (
              <option key={type.id} value={type.id}>{type.label}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">All Status</option>
            <option value="published">Published</option>
            <option value="accepted">Accepted</option>
            <option value="submitted">Submitted</option>
            <option value="under_review">Under Review</option>
            <option value="draft">Draft</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="date">Sort by Date</option>
            <option value="citations">Sort by Citations</option>
            <option value="impact">Sort by Impact</option>
          </select>

          {/* View Mode */}
          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {(['grid', 'list', 'timeline'] as const).map((mode) => (
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

      {/* Publications Display */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence mode="popLayout">
            {filteredPublications.map((publication, index) => {
              const Icon = getTypeIcon(publication.type);
              return (
                <motion.div
                  key={publication.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all group"
                >
                  <div className={`h-2 bg-gradient-to-r ${getTypeColor(publication.type)}`} />
                  
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className={`p-2 rounded-lg bg-gradient-to-r ${getTypeColor(publication.type)} bg-opacity-10`}>
                        <Icon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
                      </div>
                      {getStatusBadge(publication.status)}
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                      {publication.title}
                    </h3>

                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      {publication.authors.slice(0, 3).join(', ')}
                      {publication.authors.length > 3 && ` +${publication.authors.length - 3} more`}
                    </p>

                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-3 line-clamp-1">
                      {publication.journal || publication.conference}
                    </p>

                    <div className="flex items-center gap-4 mb-3 text-xs text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {publication.year}
                      </div>
                      <div className="flex items-center gap-1">
                        <Quote className="w-3 h-3" />
                        {publication.citations} citations
                      </div>
                      <div className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {publication.views}
                      </div>
                    </div>

                    {publication.impactFactor && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                          <span>Impact Factor</span>
                          <span className="font-medium">{publication.impactFactor.toFixed(2)}</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-1.5 rounded-full"
                            style={{ width: `${Math.min((publication.impactFactor / 10) * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {publication.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {publication.keywords.slice(0, 3).map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full"
                          >
                            {keyword}
                          </span>
                        ))}
                        {publication.keywords.length > 3 && (
                          <span className="px-2 py-1 text-xs text-gray-500">
                            +{publication.keywords.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                      <div className="flex gap-2">
                        {publication.url && (
                          <a
                            href={publication.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            title="View Online"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                        {publication.pdfUrl && (
                          <a
                            href={publication.pdfUrl}
                            download
                            className="p-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            title="Download PDF"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        )}
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(publication.doi || publication.url || '');
                            toast.success('Link copied to clipboard');
                          }}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                          title="Copy Link"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      
                      <div className="flex gap-1">
                        <button
                          onClick={() => setSelectedPublication(publication)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deletePublication.mutate(publication.id)}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {viewMode === 'list' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Journal/Conference
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Year
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Citations
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
              {filteredPublications.map((publication, index) => (
                <motion.tr
                  key={publication.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                >
                  <td className="px-6 py-4">
                    <div className="max-w-md">
                      <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">
                        {publication.title}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {publication.authors.slice(0, 2).join(', ')}
                        {publication.authors.length > 2 && ` +${publication.authors.length - 2}`}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                    {publication.journal || publication.conference}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                    {publication.year}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                    {publication.citations}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                    {publication.impactFactor?.toFixed(2) || 'N/A'}
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(publication.status)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setSelectedPublication(publication)}
                        className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deletePublication.mutate(publication.id)}
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
      )}

      {viewMode === 'timeline' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Publication Timeline
          </h3>
          <div className="relative">
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-500 via-purple-500 to-pink-500" />
            
            {filteredPublications.map((publication, index) => (
              <motion.div
                key={publication.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative flex items-start mb-8 group"
              >
                <div className={`absolute left-5 w-6 h-6 rounded-full bg-gradient-to-r ${getTypeColor(publication.type)} border-4 border-white dark:border-gray-800 shadow-lg z-10`} />
                
                <div className="ml-16 flex-1 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                        {publication.month} {publication.year}
                      </p>
                      <h4 className="font-semibold text-gray-900 dark:text-white text-lg mb-2">
                        {publication.title}
                      </h4>
                    </div>
                    {getStatusBadge(publication.status)}
                  </div>
                  
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {publication.journal || publication.conference}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      <Quote className="w-3 h-3" />
                      {publication.citations} citations
                    </span>
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />
                      {publication.views} views
                    </span>
                    {publication.impactFactor && (
                      <span className="flex items-center gap-1">
                        <Star className="w-3 h-3" />
                        IF: {publication.impactFactor.toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {filteredPublications.length === 0 && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl">
          <BookOpen className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No publications found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {searchQuery ? 'Try adjusting your search or filters' : 'Start by adding your first publication'}
          </p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all"
          >
            <Plus className="w-5 h-5" />
            Add Publication
          </button>
        </div>
      )}

      {/* Add Publication Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <PublicationModal
            onClose={() => setIsAddModalOpen(false)}
            onSubmit={addPublication.mutate}
            isLoading={addPublication.isPending} // Changed from isLoading to isPending
          />
        )}
      </AnimatePresence>

      {/* Publication Detail Modal */}
      <AnimatePresence>
        {selectedPublication && (
          <PublicationDetailModal
            publication={selectedPublication}
            onClose={() => setSelectedPublication(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// Add Publication Modal Component
const PublicationModal: React.FC<{
  onClose: () => void;
  onSubmit: (data: Partial<Publication>) => void;
  isLoading: boolean;
}> = ({ onClose, onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<Partial<Publication>>({
    title: '',
    authors: [],
    journal: '',
    year: new Date().getFullYear(),
    month: format(new Date(), 'MMMM'),
    type: 'journal',
    status: 'draft',
    keywords: [],
    abstract: ''
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
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
            Add New Publication
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Form fields here - similar structure to Achievement modal */}
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
              placeholder="Publication title"
            />
          </div>

          {/* Add more form fields for other publication details */}

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
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Adding...
                </>
              ) : (
                'Add Publication'
              )}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

// Publication Detail Modal Component
const PublicationDetailModal: React.FC<{
  publication: Publication;
  onClose: () => void;
}> = ({ publication, onClose }) => {
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
        className="bg-white dark:bg-gray-800 rounded-2xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto"
      >
        {/* Publication details display */}
        <div className="flex justify-between items-start mb-6">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white pr-8">
            {publication.title}
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Rest of publication details */}
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Authors
            </h4>
            <p className="text-gray-900 dark:text-white">
              {publication.authors.join(', ')}
            </p>
          </div>

          {/* Add more detail sections */}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Publications;