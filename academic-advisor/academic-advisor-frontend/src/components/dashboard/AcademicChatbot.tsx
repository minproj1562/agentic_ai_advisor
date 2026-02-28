// academic-advisor-frontend/src/components/dashboard/AcademicChatbot.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Send, Bot, User, Loader2, RefreshCw, Lightbulb, X,
  Minimize2, Maximize2, Wifi, WifiOff, AlertCircle,
  BookOpen, GraduationCap, Users, Briefcase, Sparkles,
  Calendar, ThumbsUp, ThumbsDown, Star, ChevronRight,
  TrendingUp, TrendingDown, Minus, MapPin, DollarSign,
} from 'lucide-react';
import { useChatbot } from '../../hooks/useChatbot';
import type {
  ChatMessage, ChatResponseContent, CareerGuidance,
  PerformanceAnalysis, StudyPlan, ElectiveRecommendation,
} from '../../types/chatbot.types';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  isFloating?: boolean;
  defaultOpen?: boolean;
  className?: string;
}

const AcademicChatbot: React.FC<Props> = ({
  isFloating = true,
  defaultOpen = false,
  className = '',
}) => {
  const {
    messages, isLoading, suggestions, sessionToken,
    isOnline, sendMessage, clearSession, submitFeedback, retryConnection,
  } = useChatbot();

  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [feedbackMsgId, setFeedbackMsgId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState(0);

  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scroll = useCallback(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), []);
  useEffect(scroll, [messages, scroll]);

  const handleSend = async (msg: string = inputValue) => {
    if (!msg.trim() || isLoading) return;
    setInputValue('');
    setShowSuggestions(false);
    await sendMessage(msg);
  };

  // ── Intent icon ───────────────────────────────────────

  const intentIcon = (intent?: string) => {
    const map: Record<string, React.ReactNode> = {
      SYLLABUS_QUERY: <BookOpen className="w-4 h-4 text-blue-500" />,
      FACULTY_QUERY: <Users className="w-4 h-4 text-green-500" />,
      PERFORMANCE_QUERY: <GraduationCap className="w-4 h-4 text-purple-500" />,
      ELECTIVE_QUERY: <Sparkles className="w-4 h-4 text-yellow-500" />,
      CAREER_QUERY: <Briefcase className="w-4 h-4 text-indigo-500" />,
      STUDY_PLAN_QUERY: <Calendar className="w-4 h-4 text-teal-500" />,
    };
    return map[intent || ''] || <Bot className="w-4 h-4 text-gray-500" />;
  };

  // ── Feedback widget ───────────────────────────────────

  const FeedbackWidget: React.FC<{ msgId: string }> = ({ msgId }) => {
    if (feedbackMsgId === msgId && feedbackRating > 0) {
      return (
        <div className="flex items-center gap-1 mt-1 text-xs text-green-600">
          <ThumbsUp className="w-3 h-3" /> Thanks for your feedback!
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 mt-2">
        <span className="text-xs text-gray-400">Helpful?</span>
        <button
          onClick={async () => {
            setFeedbackMsgId(msgId);
            setFeedbackRating(5);
            await submitFeedback({
              session_id: sessionToken || '', message_id: msgId,
              rating: 5, was_helpful: true,
            });
          }}
          className="p-1 hover:bg-green-50 rounded transition-colors"
        >
          <ThumbsUp className="w-3.5 h-3.5 text-gray-400 hover:text-green-500" />
        </button>
        <button
          onClick={async () => {
            setFeedbackMsgId(msgId);
            setFeedbackRating(2);
            await submitFeedback({
              session_id: sessionToken || '', message_id: msgId,
              rating: 2, was_helpful: false,
            });
          }}
          className="p-1 hover:bg-red-50 rounded transition-colors"
        >
          <ThumbsDown className="w-3.5 h-3.5 text-gray-400 hover:text-red-500" />
        </button>
      </div>
    );
  };

  // ── Confidence badge ──────────────────────────────────

  const ConfBadge: React.FC<{ c: string }> = ({ c }) => {
    const cfg: Record<string, { bg: string; tx: string; icon: string }> = {
      High: { bg: 'bg-green-100 dark:bg-green-900/30', tx: 'text-green-700 dark:text-green-400', icon: '✓' },
      Medium: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', tx: 'text-yellow-700 dark:text-yellow-400', icon: '~' },
      Low: { bg: 'bg-red-100 dark:bg-red-900/30', tx: 'text-red-700 dark:text-red-400', icon: '!' },
    };
    const { bg, tx, icon } = cfg[c] || cfg.Medium;
    return (
      <span className={`text-xs px-2 py-0.5 rounded ${bg} ${tx}`}>
        {icon} {c} confidence
      </span>
    );
  };

  // ════════════════════════════════════════════════════════
  //  RENDER STRUCTURED RESPONSES
  // ════════════════════════════════════════════════════════

  const renderStructured = (resp: ChatResponseContent, msgId: string) => {
    const { type, content, confidence } = resp;

    // ── Career Guidance (Person B) ────────────────────
    if (type === 'career_guidance') {
      const d = content as CareerGuidance['career'] extends infer T ? any : never;
      const career = d.career;
      const roadmap = d.roadmap || [];
      return (
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-500" />
            <h4 className="font-bold text-base">{career?.title}</h4>
            {career?.market_demand && (
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
                {career.market_demand} Demand
              </span>
            )}
          </div>

          <p className="text-sm text-gray-700 dark:text-gray-300">{career?.description}</p>

          {/* Salary */}
          {career?.salary_range && (
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
              <h5 className="text-sm font-semibold flex items-center gap-1 text-green-700 dark:text-green-400">
                <DollarSign className="w-4 h-4" /> Salary Range (India)
              </h5>
              <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                <div><span className="text-gray-500">Entry:</span> <span className="font-medium">{career.salary_range.entry_level}</span></div>
                <div><span className="text-gray-500">Mid:</span> <span className="font-medium">{career.salary_range.mid_level}</span></div>
                <div><span className="text-gray-500">Senior:</span> <span className="font-medium">{career.salary_range.senior_level}</span></div>
                <div><span className="text-gray-500">Top:</span> <span className="font-medium">{career.salary_range.top_companies}</span></div>
              </div>
            </div>
          )}

          {/* Skills */}
          {career?.required_skills?.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold mb-1">Required Skills</h5>
              <div className="flex flex-wrap gap-1">
                {career.required_skills.map((s: string, i: number) => (
                  <span key={i} className="text-xs bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400 px-2 py-0.5 rounded-full">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Gap Analysis */}
          {d.gap_analysis && (
            <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3">
              <h5 className="text-sm font-semibold text-orange-700 dark:text-orange-400">Skill Gap Analysis</h5>
              <div className="mt-1 text-xs space-y-1">
                <div className="flex items-center gap-2">
                  <span>Match: </span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: `${d.gap_analysis.skill_match_pct}%` }} />
                  </div>
                  <span className="font-medium">{d.gap_analysis.skill_match_pct}%</span>
                </div>
                {d.gap_analysis.missing_skills?.length > 0 && (
                  <div>
                    <span className="text-orange-600">Skills to learn: </span>
                    {d.gap_analysis.missing_skills.slice(0, 5).join(', ')}
                  </div>
                )}
                <div>
                  CGPA: {d.gap_analysis.your_cgpa}/{d.gap_analysis.recommended_cgpa}{' '}
                  {d.gap_analysis.cgpa_meets ? '✅' : '⚠️'}
                </div>
              </div>
            </div>
          )}

          {/* Roadmap */}
          {roadmap.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold mb-2 flex items-center gap-1">
                <MapPin className="w-4 h-4" /> Roadmap
              </h5>
              <div className="space-y-2">
                {roadmap.map((s: any) => (
                  <div key={s.step} className="flex items-start gap-2">
                    <div className="w-6 h-6 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-xs font-bold text-indigo-600 flex-shrink-0 mt-0.5">
                      {s.step}
                    </div>
                    <div className="text-xs">
                      <span className="font-medium">{s.title}</span>
                      <span className="text-gray-500"> ({s.duration})</span>
                      <p className="text-gray-600 dark:text-gray-400">{s.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Companies */}
          {career?.top_companies_india?.length > 0 && (
            <div className="text-xs">
              <span className="font-medium">Top Companies (India): </span>
              <span className="text-gray-600 dark:text-gray-400">{career.top_companies_india.join(', ')}</span>
            </div>
          )}

          {/* Personalized advice */}
          {d.personalized_advice && (
            <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg text-sm border-l-2 border-purple-400">
              <span className="font-semibold text-purple-700 dark:text-purple-400">🤖 AI Advice: </span>
              <span className="text-purple-800 dark:text-purple-300">{d.personalized_advice}</span>
            </div>
          )}

          {/* Next steps */}
          {d.next_steps?.length > 0 && (
            <div className="text-xs space-y-1">
              <h5 className="font-semibold">Next Steps:</h5>
              {d.next_steps.map((s: string, i: number) => (
                <div key={i} className="flex items-center gap-1">
                  <ChevronRight className="w-3 h-3 text-indigo-500" />
                  <span>{s}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Career List ──────────────────────────────────
    if (type === 'career_list') {
      return (
        <div className="space-y-2">
          <p className="text-sm text-gray-700 dark:text-gray-300">{content.message}</p>
          <div className="space-y-1">
            {(content.careers || []).map((c: any, i: number) => (
              <button
                key={i}
                onClick={() => handleSend(`Tell me about ${c.title} career`)}
                className="w-full text-left p-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors text-sm"
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium">{c.title}</span>
                  <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded">{c.demand}</span>
                </div>
                <p className="text-xs text-gray-500 mt-0.5">{c.description}</p>
              </button>
            ))}
          </div>
          {content.hint && <p className="text-xs text-gray-400 italic">{content.hint}</p>}
          <FeedbackWidget msgId={msgId} />
        </div>
      );
    }

    // ── Performance Analysis (Person B) ─────────────
    if (type === 'performance_analysis') {
      const d = content as PerformanceAnalysis;
      const trendIcon = d.trend_direction === 'improving'
        ? <TrendingUp className="w-4 h-4 text-green-500" />
        : d.trend_direction === 'declining'
        ? <TrendingDown className="w-4 h-4 text-red-500" />
        : <Minus className="w-4 h-4 text-yellow-500" />;

      return (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-purple-500" />
            <h4 className="font-bold">Performance Analysis</h4>
            {trendIcon}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-purple-600">{d.current_cgpa?.toFixed(2) || '–'}</p>
              <p className="text-xs text-gray-500">CGPA</p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-blue-600">{d.latest_sgpa?.toFixed(2) || '–'}</p>
              <p className="text-xs text-gray-500">Latest SGPA</p>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-green-600 capitalize">{d.trend_direction}</p>
              <p className="text-xs text-gray-500">Trend</p>
            </div>
          </div>

          {/* Subject analysis */}
          {d.subject_analysis?.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold mb-1">Subject Breakdown</h5>
              <div className="space-y-1">
                {d.subject_analysis.slice(0, 6).map((s: any, i: number) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <span className="truncate flex-1">{s.subject}</span>
                    <div className="flex items-center gap-2 ml-2">
                      <div className="w-16 bg-gray-200 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            s.status === 'strong' ? 'bg-green-500' :
                            s.status === 'weak' ? 'bg-red-500' : 'bg-yellow-500'
                          }`}
                          style={{ width: `${Math.min(s.score, 100)}%` }}
                        />
                      </div>
                      <span className={`w-8 text-right font-medium ${
                        s.status === 'strong' ? 'text-green-600' :
                        s.status === 'weak' ? 'text-red-600' : 'text-yellow-600'
                      }`}>
                        {s.score}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insights */}
          {d.insights?.length > 0 && (
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 space-y-1">
              {d.insights.map((ins: string, i: number) => (
                <p key={i} className="text-xs">{ins}</p>
              ))}
            </div>
          )}

          {/* AI insights */}
          {d.ai_insights && (
            <div className="bg-purple-50 dark:bg-purple-900/20 p-2 rounded-lg text-xs border-l-2 border-purple-400">
              <span className="font-semibold text-purple-700">🤖 </span>
              {d.ai_insights}
            </div>
          )}

          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Study Plan (Person B) ───────────────────────
    if (type === 'study_plan') {
      const d = content as StudyPlan;
      return (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-teal-500" />
            <h4 className="font-bold">Study Plan</h4>
            <span className="text-xs text-gray-500">
              {d.total_daily_hours}h/day
            </span>
          </div>

          {/* Schedule */}
          {d.daily_schedule?.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold mb-1">Daily Schedule</h5>
              <div className="space-y-1">
                {d.daily_schedule.map((s: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded bg-gray-50 dark:bg-gray-800 text-xs">
                    <div className="flex items-center gap-2">
                      {s.priority === 'high' && <span className="w-2 h-2 bg-red-500 rounded-full" />}
                      {s.priority === 'normal' && <span className="w-2 h-2 bg-blue-500 rounded-full" />}
                      <span className="font-medium">{s.subject}</span>
                    </div>
                    <span className="text-gray-500">{s.suggested_hours}h</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Focus areas */}
          {d.focus_areas?.length > 0 && (
            <div>
              <h5 className="text-sm font-semibold mb-1">🎯 Focus Areas</h5>
              <div className="flex flex-wrap gap-1">
                {d.focus_areas.map((a: string, i: number) => (
                  <span key={i} className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-full">{a}</span>
                ))}
              </div>
            </div>
          )}

          {/* Goals */}
          {d.weekly_goals?.length > 0 && (
            <div className="text-xs space-y-0.5">
              <h5 className="font-semibold">Weekly Goals</h5>
              {d.weekly_goals.map((g: string, i: number) => (
                <div key={i} className="flex items-start gap-1">
                  <span className="text-teal-500 mt-0.5">•</span>
                  <span>{g}</span>
                </div>
              ))}
            </div>
          )}

          {d.ai_study_tips && (
            <div className="bg-teal-50 dark:bg-teal-900/20 p-2 rounded text-xs border-l-2 border-teal-400">
              <span className="font-semibold text-teal-700">🤖 </span>
              {d.ai_study_tips}
            </div>
          )}

          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Elective Recommendation (Person B) ──────────
    if (type === 'elective_recommendation') {
      const d = content as any;
      return (
        <div className="space-y-3">
          <h4 className="font-bold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            Elective Recommendations
          </h4>
          {d.recommendations?.map((r: any, i: number) => (
            <div key={i} className="border dark:border-gray-700 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <h5 className="font-medium text-sm">{r.name}</h5>
                  <span className="text-xs text-gray-500">{r.code} • {r.credits} credits</span>
                </div>
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{r.category}</span>
              </div>
              {r.description && <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">{r.description}</p>}
              {r.career_paths?.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {r.career_paths.map((p: string, j: number) => (
                    <span key={j} className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">→ {p}</span>
                  ))}
                </div>
              )}
              {r.reasons?.length > 0 && (
                <div className="mt-1 text-xs text-gray-500">
                  {r.reasons.map((reason: string, k: number) => (
                    <span key={k} className="mr-2">✓ {reason}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {d.advice && <p className="text-xs text-gray-500 italic">{d.advice}</p>}
          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Concept Explanation (Person A — pass-through) ─
    if (type === 'concept_explanation') {
      return (
        <div className="space-y-3">
          {content.definition && (
            <div>
              <h4 className="font-semibold text-sm text-blue-600 dark:text-blue-400 flex items-center gap-1">
                <BookOpen className="w-4 h-4" /> Definition
              </h4>
              <p className="text-gray-700 dark:text-gray-300 mt-1 text-sm">{content.definition}</p>
            </div>
          )}
          {content.key_points?.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm text-blue-600">Key Points</h4>
              <ul className="list-disc list-inside space-y-0.5 mt-1 text-sm text-gray-700 dark:text-gray-300">
                {content.key_points.map((p: string, i: number) => <li key={i}>{p}</li>)}
              </ul>
            </div>
          )}
          {content.related_topics?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {content.related_topics.map((t: string, i: number) => (
                <button key={i} onClick={() => handleSend(`Explain ${t}`)}
                  className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full hover:bg-blue-200 transition-colors">
                  {t}
                </button>
              ))}
            </div>
          )}
          {content.exam_relevance && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-2 rounded text-sm border-l-2 border-yellow-400">
              📝 <span className="font-semibold">Exam: </span>{content.exam_relevance}
            </div>
          )}
          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Faculty recommendation / list (Person A — pass-through) ─
    if (type === 'faculty_recommendation' || type === 'faculty_list') {
      const list = content.recommendations || content.faculty || [];
      return (
        <div className="space-y-3">
          <h4 className="font-semibold flex items-center gap-1">
            <Users className="w-4 h-4 text-green-500" />
            {type === 'faculty_recommendation' ? 'Recommended Faculty' : `Faculty (${content.count || list.length})`}
          </h4>
          {list.slice(0, 5).map((f: any, i: number) => (
            <div key={i} className="border dark:border-gray-700 rounded-lg p-3 bg-white dark:bg-gray-800">
              <div className="flex justify-between items-start">
                <div>
                  <h5 className="font-medium text-sm">{f.name}</h5>
                  <p className="text-xs text-gray-500">{f.department}</p>
                </div>
                {f.rating && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">⭐ {f.rating}</span>}
              </div>
              {(f.subjects || f.subjects_taught) && (
                <p className="text-xs text-gray-600 mt-1">
                  <span className="font-medium">Subjects: </span>
                  {(f.subjects || f.subjects_taught)?.join(', ')}
                </p>
              )}
              {f.research_areas && (
                <p className="text-xs text-gray-600">
                  <span className="font-medium">Research: </span>
                  {f.research_areas.join(', ')}
                </p>
              )}
              {f.reasoning?.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1">
                  {f.reasoning.map((r: string, j: number) => (
                    <span key={j} className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">✓ {r}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {content.selection_criteria && <p className="text-xs text-gray-500 italic">{content.selection_criteria}</p>}
          <div className="flex items-center justify-between">
            <ConfBadge c={confidence} />
            <FeedbackWidget msgId={msgId} />
          </div>
        </div>
      );
    }

    // ── Text / default ──────────────────────────────
    return (
      <div className="space-y-2">
        <p className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
          {content.message || JSON.stringify(content)}
        </p>
        {content.suggestions?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {content.suggestions.map((s: string, i: number) => (
              <button key={i} onClick={() => handleSend(s)}
                className="text-xs bg-gray-100 hover:bg-blue-50 text-gray-700 hover:text-blue-600 px-2 py-1 rounded-lg transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between">
          {confidence && <ConfBadge c={confidence} />}
          <FeedbackWidget msgId={msgId} />
        </div>
      </div>
    );
  };

  // ── Render single message ──────────────────────────

  const renderMsg = (msg: ChatMessage) => {
    if (msg.isLoading) {
      return (
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          <span className="text-gray-500 text-sm">Thinking...</span>
        </div>
      );
    }

    if (typeof msg.content === 'string') {
      const oos = msg.content === 'Beyond my scope';
      return (
        <div className={oos ? 'text-orange-600' : ''}>
          {oos && <AlertCircle className="w-4 h-4 inline mr-1" />}
          <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
        </div>
      );
    }

    return renderStructured(msg.content as ChatResponseContent, msg.id);
  };

  // ════════════════════════════════════════════════════════
  //  MAIN LAYOUT
  // ════════════════════════════════════════════════════════

  // Floating button
  if (isFloating && !isOpen) {
    return (
      <motion.button
        initial={{ scale: 0 }} animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg flex items-center justify-center z-50"
      >
        <Bot className="w-6 h-6" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
      </motion.button>
    );
  }

  const container = isFloating
    ? `fixed bottom-6 right-6 w-[420px] ${isMinimized ? 'h-14' : 'h-[620px]'} bg-white dark:bg-gray-900 rounded-xl shadow-2xl flex flex-col z-50 transition-all duration-300 border border-gray-200 dark:border-gray-700`
    : `w-full h-full bg-white dark:bg-gray-900 rounded-xl shadow-lg flex flex-col ${className}`;

  return (
    <div className={container}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b dark:border-gray-700 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Bot className="w-7 h-7" />
            <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white ${isOnline ? 'bg-green-400' : 'bg-yellow-400'}`} />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Academic Assistant</h3>
            {!isMinimized && (
              <p className="text-xs text-white/70 flex items-center gap-1">
                {isOnline ? <><Wifi className="w-3 h-3" /> Online</> : <><WifiOff className="w-3 h-3" /> Offline</>}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          {!isOnline && (
            <button onClick={retryConnection} className="p-1 hover:bg-white/20 rounded" title="Retry">
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <button onClick={clearSession} className="p-1 hover:bg-white/20 rounded" title="Clear">
            <RefreshCw className="w-4 h-4" />
          </button>
          {isFloating && (
            <>
              <button onClick={() => setIsMinimized(!isMinimized)} className="p-1 hover:bg-white/20 rounded">
                {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
              </button>
              <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {!isMinimized && (
        <>
          {!isOnline && (
            <div className="px-3 py-1.5 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200">
              <p className="text-xs text-yellow-700 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Offline — limited features
              </p>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center py-6">
                <div className="w-14 h-14 mx-auto bg-gradient-to-r from-blue-100 to-purple-100 rounded-full flex items-center justify-center mb-3">
                  <Bot className="w-7 h-7 text-blue-600" />
                </div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">Academic Guidance Assistant</h4>
                <p className="text-xs text-gray-500 mt-1 max-w-xs mx-auto">
                  Syllabus • Faculty • Performance • Electives • Career • Study Plans
                </p>
                <div className="mt-3 grid grid-cols-3 gap-2 max-w-xs mx-auto">
                  {[
                    { icon: <GraduationCap className="w-3.5 h-3.5" />, text: 'Performance', q: 'Show my performance' },
                    { icon: <Briefcase className="w-3.5 h-3.5" />, text: 'Career', q: 'Career in data science' },
                    { icon: <Calendar className="w-3.5 h-3.5" />, text: 'Study Plan', q: 'Create a study plan' },
                  ].map((item, idx) => (
                    <button key={idx} onClick={() => handleSend(item.q)}
                      className="flex flex-col items-center gap-1 px-2 py-2 rounded-lg text-xs bg-gray-50 hover:bg-blue-50 dark:bg-gray-800 dark:hover:bg-blue-900/20 transition-colors text-gray-700 dark:text-gray-300">
                      {item.icon}
                      {item.text}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {showSuggestions && suggestions.length > 0 && messages.length === 0 && (
              <div className="space-y-2">
                <div className="flex items-center text-xs text-gray-500">
                  <Lightbulb className="w-3.5 h-3.5 mr-1 text-yellow-500" /> Try:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {suggestions.map((s, i) => (
                    <motion.button key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                      onClick={() => handleSend(s)}
                      className="text-xs bg-gray-100 dark:bg-gray-800 hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-700 dark:text-gray-300 px-2.5 py-1.5 rounded-lg transition-colors border border-transparent hover:border-blue-200">
                      {s}
                    </motion.button>
                  ))}
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map(msg => (
                <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[88%] rounded-xl p-3 ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                      : msg.isError
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-800 border border-red-200'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                  }`}>
                    <div className="flex items-start gap-2">
                      {msg.role === 'assistant' && (
                        <div className="mt-0.5 flex-shrink-0">
                          {msg.isError ? <AlertCircle className="w-4 h-4 text-red-500" /> : intentIcon(msg.intent)}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">{renderMsg(msg)}</div>
                      {msg.role === 'user' && <User className="w-4 h-4 mt-0.5 text-white/80 flex-shrink-0" />}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            <div ref={endRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-b-xl">
            <form onSubmit={e => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2">
              <input ref={inputRef} type="text" value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder="Ask about academics..."
                className="flex-1 px-3 py-2 border dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                disabled={isLoading} />
              <button type="submit" disabled={isLoading || !inputValue.trim()}
                className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg transition-all shadow-md disabled:shadow-none">
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </form>
            <p className="text-[10px] text-gray-400 mt-1 text-center">
              Academic queries only • {isOnline ? 'Connected' : 'Offline'}
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default AcademicChatbot;