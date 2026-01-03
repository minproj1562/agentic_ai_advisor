// modules/agent1/shared/components/InsightPanel.tsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Info,
  ChevronRight,
  RefreshCw,
  Share2,
  Bookmark,
  MessageSquare
} from 'lucide-react';

interface Insight {
  id: string;
  type: 'improvement' | 'warning' | 'tip' | 'achievement';
  title: string;
  description: string;
  metric?: {
    value: number;
    change: number;
    label: string;
  };
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
  source?: string;
  confidence?: number;
  timestamp?: string;
}

interface InsightPanelProps {
  insights: Insight[];
  title?: string;
  onRefresh?: () => void;
  onShare?: (insight: Insight) => void;
  onSave?: (insight: Insight) => void;
  loading?: boolean;
  className?: string;
}

const InsightPanel: React.FC<InsightPanelProps> = ({
  insights,
  title = 'AI Insights',
  onRefresh,
  onShare,
  onSave,
  loading = false,
  className = ''
}) => {
  const [selectedInsight, setSelectedInsight] = useState<string | null>(null);
  const [savedInsights, setSavedInsights] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<string>('all');

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'improvement':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'achievement':
        return <Brain className="w-5 h-5 text-purple-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'improvement':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'achievement':
        return 'bg-purple-50 border-purple-200';
      default:
        return 'bg-blue-50 border-blue-200';
    }
  };

  const handleSave = (insight: Insight) => {
    setSavedInsights(prev => new Set(prev).add(insight.id));
    onSave?.(insight);
  };

  const filteredInsights = insights.filter(insight => 
    filterType === 'all' || insight.type === filterType
  );

  return (
    <div className={`bg-white rounded-xl shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
            {insights.length} insights
          </span>
        </div>
        
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-4 pb-4 border-b border-gray-200">
        {['all', 'improvement', 'warning', 'tip', 'achievement'].map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              filterType === type
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </button>
        ))}
      </div>

      {/* Insights List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        <AnimatePresence>
          {filteredInsights.map((insight, index) => (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.1 }}
              className={`border rounded-lg p-4 cursor-pointer transition-all ${
                getInsightColor(insight.type)
              } ${selectedInsight === insight.id ? 'ring-2 ring-purple-500' : ''}`}
              onClick={() => setSelectedInsight(
                selectedInsight === insight.id ? null : insight.id
              )}
            >
              <div className="flex items-start gap-3">
                {getInsightIcon(insight.type)}
                
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{insight.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                  
                  {/* Metric Display */}
                  {insight.metric && (
                    <div className="mt-3 p-2 bg-white rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-500">{insight.metric.label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-gray-900">
                            {insight.metric.value}
                          </span>
                          {insight.metric.change !== 0 && (
                            <span className={`text-sm font-medium ${
                              insight.metric.change > 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {insight.metric.change > 0 ? '+' : ''}{insight.metric.change}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Expanded Content */}
                  <AnimatePresence>
                    {selectedInsight === insight.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="mt-3"
                      >
                        {/* Actions */}
                        {insight.actions && insight.actions.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {insight.actions.map((action, idx) => (
                              <button
                                key={idx}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  action.action();
                                }}
                                className="px-3 py-1 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 transition-colors"
                              >
                                {action.label}
                              </button>
                            ))}
                          </div>
                        )}
                        
                        {/* Metadata */}
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <div className="flex items-center gap-3">
                            {insight.source && (
                              <span>Source: {insight.source}</span>
                            )}
                            {insight.confidence && (
                              <span>Confidence: {(insight.confidence * 100).toFixed(0)}%</span>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSave(insight);
                              }}
                              className={`p-1 rounded transition-colors ${
                                savedInsights.has(insight.id)
                                  ? 'text-purple-600'
                                  : 'text-gray-400 hover:text-gray-600'
                              }`}
                            >
                              <Bookmark className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onShare?.(insight);
                              }}
                              className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
                            >
                              <Share2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
                
                <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform ${
                  selectedInsight === insight.id ? 'rotate-90' : ''
                }`} />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredInsights.length === 0 && (
        <div className="text-center py-8">
          <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No insights available</p>
        </div>
      )}
    </div>
  );
};

export default InsightPanel;